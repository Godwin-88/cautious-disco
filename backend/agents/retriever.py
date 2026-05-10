"""Graph-RAG retriever — combines Cypher hierarchy traversal + vector similarity search."""

import logging
from dataclasses import dataclass, field

import numpy as np

from backend.graph.neo4j_client import Neo4jClient
from backend.graph.cypher_queries import (
    GET_ENRICHED_CAPABILITIES_FOR_DOMAIN,
    GET_ENRICHED_CAPABILITIES_BY_DOMAIN_NAMES,
    GET_CAPABILITIES_BY_IDS,
    GET_CAPABILITIES_BROAD,
    GET_DOMAINS_BY_KEYWORD,
    VECTOR_SIMILARITY_SEARCH,
)
from backend.llm.client import LLMClient

log = logging.getLogger(__name__)

QUERY_EXPANSION_PROMPT = """Given this enterprise architecture request, generate 3-5 concise
search queries to find the most relevant capabilities in a knowledge graph.

Organization type: {org_type}
Goals: {goals}
Sector focus: {sectors}

Return ONLY a JSON array of strings, e.g.: ["query1", "query2", "query3"]
Each query should be 5-10 words focusing on specific EA capabilities."""


@dataclass
class EnrichedCapability:
    capability: dict
    subdomain: dict
    domain: dict
    standard: dict | None = None
    trend: dict | None = None
    subcapabilities: list[dict] = field(default_factory=list)
    feature_ids: list[str] = field(default_factory=list)
    similarity_score: float = 0.0


class RetrieverAgent:
    def __init__(self, neo4j: Neo4jClient, llm: LLMClient, embedding_model=None):
        self.neo4j = neo4j
        self.llm = llm
        self._embed_model = embedding_model

    def _get_embed_model(self):
        if self._embed_model is None:
            from sentence_transformers import SentenceTransformer
            self._embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        return self._embed_model

    async def expand_queries(self, org_type: str, goals: list[str], sectors: list[str]) -> list[str]:
        prompt = QUERY_EXPANSION_PROMPT.format(
            org_type=org_type,
            goals=", ".join(goals),
            sectors=", ".join(sectors) if sectors else "general enterprise",
        )
        try:
            raw = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=256,
                temperature=0.3,
            )
            from backend.llm.client import extract_json
            queries = extract_json(raw)
            if isinstance(queries, list):
                return [str(q) for q in queries[:5]]
        except Exception as exc:
            log.warning(f"Query expansion failed: {exc}")
        # fallback: use org_type + each goal
        return [org_type] + [g[:60] for g in goals[:3]]

    def _vector_search(self, queries: list[str], top_k: int = 20, min_score: float = 0.55) -> list[dict]:
        model = self._get_embed_model()
        seen_ids: set[str] = set()
        results: list[dict] = []

        for query in queries:
            try:
                vec = model.encode([query], normalize_embeddings=True)[0].tolist()
                rows = self.neo4j.run_query(
                    VECTOR_SIMILARITY_SEARCH,
                    index_name="capability_embedding",
                    top_k=top_k,
                    query_vector=vec,
                    min_score=min_score,
                )
                for r in rows:
                    cap = r.get("capability") or {}
                    cap_id = cap.get("id")
                    if cap_id and cap_id not in seen_ids:
                        seen_ids.add(cap_id)
                        results.append(r)
            except Exception as exc:
                log.warning(f"Vector search failed for query '{query}': {exc}")

        return results

    def _cypher_traversal(
        self, org_type: str, sectors: list[str], limit: int = 40,
        expanded_queries: list[str] | None = None,
    ) -> list[dict]:
        # Build keyword candidates from expanded queries first — they are
        # semantically richer than splitting the raw org_type string which
        # for chat messages starts with "What", "How", "Can", etc.
        _stop = {"what", "how", "can", "the", "for", "and", "with", "that",
                 "this", "our", "your", "my", "of", "a", "an", "in", "to",
                 "is", "are", "we", "i", "do", "be", "on"}
        candidates: list[str] = []
        if expanded_queries:
            for q in expanded_queries:
                words = [w for w in q.lower().split() if w not in _stop and len(w) > 3]
                if words:
                    # Try multi-word phrase first (more specific), then first word
                    candidates.append(" ".join(words[:2]))
                    candidates.append(words[0])
        # Fall back to org_type only if no expanded queries
        if not candidates:
            word = (org_type or "digital").split()[0].lower()
            candidates.append(word if word not in _stop else "digital")

        sector_kw = sectors[0] if sectors else candidates[0]

        seen_ids: set[str] = set()
        all_rows: list[dict] = []

        for kw in dict.fromkeys(candidates):  # deduplicated, order-preserving
            rows = self.neo4j.run_query(
                GET_ENRICHED_CAPABILITIES_FOR_DOMAIN,
                org_keyword=kw,
                sector_keyword=sector_kw,
                limit=limit,
            )
            if not rows:
                rows = self.neo4j.run_query(
                    GET_CAPABILITIES_BROAD, keyword=kw, limit=limit,
                )
            for r in rows:
                cap_id = (r.get("capability") or {}).get("id")
                if cap_id and cap_id not in seen_ids:
                    seen_ids.add(cap_id)
                    all_rows.append(r)
            if len(all_rows) >= limit:
                break

        return all_rows

    def _merge_results(
        self,
        cypher_rows: list[dict],
        vector_rows: list[dict],
        max_caps: int = 40,
    ) -> list[EnrichedCapability]:
        seen_ids: set[str] = set()
        merged: list[EnrichedCapability] = []

        def add_row(r: dict, score: float = 0.0):
            cap = r.get("capability") or {}
            cap_id = cap.get("id")
            if not cap_id or cap_id in seen_ids:
                return
            seen_ids.add(cap_id)
            merged.append(
                EnrichedCapability(
                    capability=cap,
                    subdomain=r.get("subdomain") or {},
                    domain=r.get("domain") or {},
                    standard=r.get("standard"),
                    trend=r.get("trend"),
                    subcapabilities=r.get("subcapabilities") or [],
                    feature_ids=r.get("feature_ids") or [],
                    similarity_score=score,
                )
            )

        # Vector results first (sorted by relevance)
        for r in vector_rows:
            add_row(r, score=float(r.get("score") or 0))

        # Cypher traversal adds domain-contextual caps
        for r in cypher_rows:
            add_row(r, score=0.0)

        return merged[:max_caps]

    def _rows_to_caps(self, rows: list[dict], score: float = 0.8) -> list[EnrichedCapability]:
        caps: list[EnrichedCapability] = []
        seen: set[str] = set()
        for r in rows:
            cap = r.get("capability") or {}
            cap_id = cap.get("id")
            if not cap_id or cap_id in seen:
                continue
            seen.add(cap_id)
            caps.append(EnrichedCapability(
                capability=cap,
                subdomain=r.get("subdomain") or {},
                domain=r.get("domain") or {},
                standard=r.get("standard"),
                trend=r.get("trend"),
                subcapabilities=r.get("subcapabilities") or [],
                similarity_score=score,
            ))
        return caps

    async def retrieve_by_ids(
        self,
        capability_ids: list[str],
        org_type: str = "",
        goals: list[str] | None = None,
    ) -> list[EnrichedCapability]:
        """Direct fetch by capability IDs — bypasses vector search."""
        log.info(f"Retriever: direct ID fetch for {len(capability_ids)} capabilities")
        rows = self.neo4j.run_query(GET_CAPABILITIES_BY_IDS, capability_ids=capability_ids)
        caps = self._rows_to_caps(rows, score=1.0)
        log.info(f"Retriever: ID fetch returned {len(caps)} capabilities")
        return caps

    async def retrieve_by_domain_names(
        self,
        domain_names: list[str],
        org_type: str = "",
        goals: list[str] | None = None,
        limit: int = 40,
    ) -> list[EnrichedCapability]:
        """
        Fetch enriched capabilities directly by domain name(s).
        Supports cross-domain selections — Aviation + Capital Markets, etc.
        Falls back to keyword matching when exact names don't resolve.
        """
        log.info(f"Retriever: domain-name fetch for {domain_names}")
        rows = self.neo4j.run_query(
            GET_ENRICHED_CAPABILITIES_BY_DOMAIN_NAMES,
            domain_names=domain_names,
            limit=limit,
        )

        # If some domain names returned nothing, try keyword expansion per name
        if len(rows) < 5:
            for raw_name in domain_names:
                keyword = (
                    raw_name.replace("Manage ", "")
                             .replace(" Core Operations", "")
                             .replace(" Core Operation", "")
                             .strip()
                )
                # Find actual graph domain names matching the keyword
                resolved = self.neo4j.run_query(GET_DOMAINS_BY_KEYWORD, keyword=keyword)
                resolved_names = [r["name"] for r in resolved if r.get("name")]
                if resolved_names:
                    extra = self.neo4j.run_query(
                        GET_ENRICHED_CAPABILITIES_BY_DOMAIN_NAMES,
                        domain_names=resolved_names,
                        limit=20,
                    )
                    rows = rows + extra
                else:
                    # Final fallback: broad text search
                    extra = self.neo4j.run_query(GET_CAPABILITIES_BROAD, keyword=keyword, limit=15)
                    rows = rows + extra

        caps = self._rows_to_caps(rows, score=0.85)
        log.info(f"Retriever: domain-name fetch returned {len(caps)} capabilities")
        return caps

    async def retrieve(
        self,
        org_type: str,
        goals: list[str],
        sectors: list[str],
        top_k: int = 40,
    ) -> list[EnrichedCapability]:
        log.info(f"Retriever: org_type={org_type}, goals={goals[:2]}")

        queries = await self.expand_queries(org_type, goals, sectors)
        log.info(f"Expanded queries: {queries}")

        vector_rows = self._vector_search(queries, top_k=20)
        cypher_rows = self._cypher_traversal(org_type, sectors, limit=40,
                                              expanded_queries=queries)

        caps = self._merge_results(cypher_rows, vector_rows, max_caps=top_k)
        log.info(f"Retriever: {len(caps)} enriched capabilities merged")
        return caps
