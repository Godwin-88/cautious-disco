"""
Knowledge Graph Enrichment Pipeline.

Enriches empty Standard and Trend scaffolding nodes with real authoritative content,
adds SubDomain descriptions, and enriches Capability nodes with business context.

Order of operations:
  1. Fetch all Domain nodes from Neo4j
  2. For each Domain: match against curated catalogs → populate Standard + Trend nodes
  3. Fetch all SubDomain nodes → enrich with functional scope descriptions
  4. Fetch all Capability/SubCapability nodes → enrich with business context (catalog first, LLM fallback)
  5. UNWIND-batch SET all properties

Run after migrate_optimized.py, before embed_nodes.py.
"""

import os
import sys
import json
import logging
import asyncio
import time
from typing import Optional
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Add repo root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.knowledge_sources.standards_catalog import get_standards_for_domain, StandardData
from pipeline.knowledge_sources.trends_catalog import get_trends_for_domain, TrendData
from pipeline.knowledge_sources.capability_enrichments import (
    get_capability_enrichment,
    get_subdomain_enrichment,
    CapabilityEnrichment,
)
from backend.graph.cypher_queries import (
    GET_ALL_DOMAINS,
    GET_ALL_SUBDOMAINS,
    SET_STANDARD_PROPERTIES,
    SET_TREND_PROPERTIES,
    SET_SUBDOMAIN_PROPERTIES,
    SET_CAPABILITY_PROPERTIES,
)

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _batch(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


class GraphEnricher:
    def __init__(self, driver, database: str = "neo4j", llm_client=None):
        self._driver = driver
        self._database = database
        self._llm = llm_client  # Optional: passed in for LLM fallback

    def _session(self):
        return self._driver.session(database=self._database)

    # ------------------------------------------------------------------
    # Domain → Standard enrichment
    # ------------------------------------------------------------------

    def enrich_standards(self, batch_size: int = 50):
        log.info("Enriching Standard nodes...")
        with self._session() as session:
            domains = session.run(GET_ALL_DOMAINS).data()
            if not domains:
                log.warning("No Domain nodes found. Run migrate_optimized.py first.")
                return

            rows = []
            for domain in domains:
                domain_name = domain.get("name", "")
                domain_id = domain.get("id", "")
                std_id = f"STD_{domain_id}"

                standards = get_standards_for_domain(domain_name)
                if not standards:
                    continue

                # Pick the most domain-specific standard (first non-universal match)
                primary_std = standards[0]  # TOGAF is always first; pick best fit
                for s in standards[1:]:
                    if any(domain_name.lower() in d.lower() for d in (s.applicable_domains or [])):
                        primary_std = s
                        break

                rows.append({
                    "id": std_id,
                    "name": primary_std.name,
                    "full_name": primary_std.full_name,
                    "publisher": primary_std.publisher,
                    "version": primary_std.version,
                    "year": primary_std.year,
                    "description": primary_std.description,
                    "key_principles": primary_std.key_principles,
                    "compliance_requirements": primary_std.compliance_requirements,
                    "applicable_domains": primary_std.applicable_domains,
                    "maturity_model": primary_std.maturity_model,
                    "certification_body": primary_std.certification_body,
                    "source_url": primary_std.source_url,
                    "industry_relevance": primary_std.industry_relevance,
                    "tags": primary_std.tags,
                })

            log.info(f"  Setting properties on {len(rows)} Standard nodes...")
            for chunk in _batch(rows, batch_size):
                session.run(SET_STANDARD_PROPERTIES, rows=chunk)

        log.info(f"  Standard enrichment complete: {len(rows)} nodes updated")

    # ------------------------------------------------------------------
    # Domain → Trend enrichment
    # ------------------------------------------------------------------

    def enrich_trends(self, batch_size: int = 50):
        log.info("Enriching Trend nodes...")
        with self._session() as session:
            domains = session.run(GET_ALL_DOMAINS).data()
            rows = []
            for domain in domains:
                domain_name = domain.get("name", "")
                domain_id = domain.get("id", "")
                trend_id = f"TRD_{domain_id}"

                trends = get_trends_for_domain(domain_name)
                if not trends:
                    continue

                # Use the most impactful trend as the primary node enrichment
                # (the node represents "the trend signal" for this domain)
                primary = next((t for t in trends if t.impact_level == "transformational"), trends[0])

                rows.append({
                    "id": trend_id,
                    "name": primary.name,
                    "description": primary.description,
                    "source": primary.source,
                    "source_type": primary.source_type,
                    "publication_year": primary.publication_year,
                    "impact_level": primary.impact_level,
                    "maturity": primary.maturity,
                    "time_horizon": primary.time_horizon,
                    "business_impact": primary.business_impact,
                    "technology_enablers": primary.technology_enablers,
                    "related_standards": primary.related_standards,
                    "adoption_rate": primary.adoption_rate,
                    "industry_applicability": primary.industry_applicability,
                    "citations": primary.citations,
                    "tags": primary.tags,
                })

            log.info(f"  Setting properties on {len(rows)} Trend nodes...")
            for chunk in _batch(rows, batch_size):
                session.run(SET_TREND_PROPERTIES, rows=chunk)

        log.info(f"  Trend enrichment complete: {len(rows)} nodes updated")

    # ------------------------------------------------------------------
    # SubDomain enrichment
    # ------------------------------------------------------------------

    def enrich_subdomains(self, batch_size: int = 100):
        log.info("Enriching SubDomain nodes...")
        with self._session() as session:
            subdomains = session.run(GET_ALL_SUBDOMAINS).data()
            rows = []
            llm_needed = []

            for sd in subdomains:
                sd_id = sd.get("id", "")
                sd_name = sd.get("name", "")
                domain_name = sd.get("domain_name", "")

                enrichment = get_subdomain_enrichment(sd_name)
                if enrichment:
                    rows.append({
                        "id": sd_id,
                        "description": enrichment.description,
                        "functional_scope": enrichment.functional_scope,
                        "business_driver": enrichment.business_driver,
                        "grouping_rationale": enrichment.grouping_rationale,
                    })
                else:
                    llm_needed.append({"id": sd_id, "name": sd_name, "domain": domain_name})

            # Batch-generate for uncovered subdomains using LLM fallback
            if llm_needed and self._llm:
                log.info(f"  LLM fallback for {len(llm_needed)} SubDomain nodes...")
                llm_rows = self._llm_enrich_subdomains_batch(llm_needed)
                rows.extend(llm_rows)
            elif llm_needed:
                log.info(f"  {len(llm_needed)} SubDomains have no curated enrichment and no LLM client — generating defaults")
                for sd in llm_needed:
                    rows.append({
                        "id": sd["id"],
                        "description": f"Manages {sd['name'].lower()} capabilities within the {sd['domain']} domain.",
                        "functional_scope": f"Covers capabilities related to {sd['name'].lower()}",
                        "business_driver": f"Enables {sd['domain']} digital transformation objectives",
                        "grouping_rationale": f"Capabilities share a common {sd['name'].lower()} operational lifecycle",
                    })

            log.info(f"  Setting properties on {len(rows)} SubDomain nodes...")
            for chunk in _batch(rows, batch_size):
                session.run(SET_SUBDOMAIN_PROPERTIES, rows=chunk)

        log.info(f"  SubDomain enrichment complete: {len(rows)} nodes updated")

    def _llm_enrich_subdomains_batch(self, subdomains: list[dict]) -> list[dict]:
        """Synchronous LLM call for subdomain enrichment batches."""
        rows = []
        # Process in batches of 10 to keep prompt manageable
        for batch_group in _batch(subdomains, 10):
            items_str = "\n".join(
                f'{i+1}. Name: "{sd["name"]}" | Domain: "{sd["domain"]}"'
                for i, sd in enumerate(batch_group)
            )
            prompt = f"""For each of the following Enterprise Architecture SubDomains, provide enrichment data.

{items_str}

Return a JSON array with one object per item:
[
  {{
    "index": 1,
    "description": "<2 sentences describing what this subdomain manages>",
    "functional_scope": "<specific capabilities and processes in scope>",
    "business_driver": "<why this subdomain matters for digital transformation>",
    "grouping_rationale": "<why capabilities in this subdomain are grouped together>"
  }}
]

Return ONLY valid JSON array, no markdown."""

            try:
                import asyncio
                response = asyncio.run(
                    self._llm.chat([{"role": "user", "content": prompt}], max_tokens=1500, temperature=0.2)
                )
                from backend.llm.client import extract_json
                parsed = extract_json(response)
                if isinstance(parsed, list):
                    for item in parsed:
                        idx = item.get("index", 1) - 1
                        if 0 <= idx < len(batch_group):
                            sd = batch_group[idx]
                            rows.append({
                                "id": sd["id"],
                                "description": item.get("description", ""),
                                "functional_scope": item.get("functional_scope", ""),
                                "business_driver": item.get("business_driver", ""),
                                "grouping_rationale": item.get("grouping_rationale", ""),
                            })
            except Exception as e:
                log.warning(f"LLM subdomain enrichment batch failed: {e}")
                # Add defaults for failed batch
                for sd in batch_group:
                    rows.append({
                        "id": sd["id"],
                        "description": f"Manages {sd['name'].lower()} capabilities within the {sd['domain']} domain.",
                        "functional_scope": f"Covers capabilities related to {sd['name'].lower()}",
                        "business_driver": f"Enables {sd['domain']} digital transformation objectives",
                        "grouping_rationale": f"Capabilities share a common {sd['name'].lower()} operational lifecycle",
                    })
        return rows

    # ------------------------------------------------------------------
    # Capability enrichment
    # ------------------------------------------------------------------

    def enrich_capabilities(self, batch_size: int = 100):
        log.info("Enriching Capability nodes...")
        with self._session() as session:
            capabilities = session.run(
                "MATCH (n:Capability) RETURN n.id AS id, n.name AS name, "
                "[(sd:SubDomain)-[:PARENT_OF]->(n) | sd.name][0] AS subdomain_name, "
                "[(d:Domain)-[:PARENT_OF*1..3]->(n) | d.name][0] AS domain_name"
            ).data()

            rows = []
            llm_needed = []

            for cap in capabilities:
                cap_id = cap.get("id", "")
                cap_name = cap.get("name", "")
                domain_name = cap.get("domain_name", "") or ""
                subdomain_name = cap.get("subdomain_name", "") or ""

                enrichment = get_capability_enrichment(cap_name)
                if enrichment:
                    rows.append(self._enrichment_to_row(cap_id, enrichment))
                else:
                    llm_needed.append({
                        "id": cap_id,
                        "name": cap_name,
                        "domain": domain_name,
                        "subdomain": subdomain_name,
                    })

            log.info(f"  Catalog matched: {len(rows)} | LLM needed: {len(llm_needed)}")

            # LLM fallback for unmatched capabilities
            if llm_needed and self._llm:
                log.info(f"  LLM enriching {len(llm_needed)} capabilities (in batches of 5)...")
                llm_rows = self._llm_enrich_capabilities_batch(llm_needed, batch_of=5)
                rows.extend(llm_rows)
            elif llm_needed:
                for cap in llm_needed:
                    rows.append(self._default_capability_row(cap))

            log.info(f"  Setting properties on {len(rows)} Capability nodes...")
            for chunk in _batch(rows, batch_size):
                session.run(SET_CAPABILITY_PROPERTIES, rows=chunk)

        log.info(f"  Capability enrichment complete: {len(rows)} nodes updated")

    def _enrichment_to_row(self, cap_id: str, e: CapabilityEnrichment) -> dict:
        return {
            "id": cap_id,
            "description": e.description,
            "business_outcomes": e.business_outcomes,
            "technical_requirements": e.technical_requirements,
            "implementation_complexity": e.implementation_complexity,
            "risk_factors": e.risk_factors,
            "typical_duration_weeks": e.typical_duration_weeks,
            "common_frameworks": e.common_frameworks,
            "solution_patterns": e.solution_patterns,
            "kpis": e.kpis,
            "industry_applicability": e.industry_applicability,
        }

    def _default_capability_row(self, cap: dict) -> dict:
        return {
            "id": cap["id"],
            "description": f"Manages {cap['name'].lower()} within the {cap.get('subdomain', cap.get('domain', ''))} context.",
            "business_outcomes": [f"Improved {cap['name'].lower()} efficiency", "Reduced operational risk"],
            "technical_requirements": ["Enterprise platform integration", "API-based integration layer"],
            "implementation_complexity": "medium",
            "risk_factors": ["Integration complexity with legacy systems", "Change management requirements"],
            "typical_duration_weeks": 16,
            "common_frameworks": ["TOGAF 10", "COBIT 2019"],
            "solution_patterns": ["Service-oriented architecture", "API-first design"],
            "kpis": ["Implementation on time and budget", "User adoption > 80% within 3 months"],
            "industry_applicability": ["All sectors"],
        }

    def _llm_enrich_capabilities_batch(self, capabilities: list[dict], batch_of: int = 5) -> list[dict]:
        rows = []
        total = len(capabilities)
        for i, batch_group in enumerate(_batch(capabilities, batch_of)):
            log.info(f"  LLM cap batch {i+1}/{(total + batch_of - 1)//batch_of}")
            items_str = "\n".join(
                f'{j+1}. Capability: "{c["name"]}" | SubDomain: "{c["subdomain"]}" | Domain: "{c["domain"]}"'
                for j, c in enumerate(batch_group)
            )
            prompt = f"""You are an Enterprise Architecture expert. For each capability, provide enrichment.

{items_str}

Return a JSON array:
[
  {{
    "index": 1,
    "description": "<2 sentences — what this capability manages and its purpose>",
    "business_outcomes": ["<outcome 1>", "<outcome 2>", "<outcome 3>"],
    "technical_requirements": ["<req 1>", "<req 2>"],
    "implementation_complexity": "<low|medium|high|very_high>",
    "risk_factors": ["<risk 1>", "<risk 2>"],
    "typical_duration_weeks": <int 8-40>,
    "common_frameworks": ["<framework 1>"],
    "solution_patterns": ["<pattern 1>"],
    "kpis": ["<kpi 1 with measurable target>", "<kpi 2>"],
    "industry_applicability": ["<sector 1>", "All sectors"]
  }}
]

Return ONLY valid JSON array."""

            try:
                import asyncio
                response = asyncio.run(
                    self._llm.chat([{"role": "user", "content": prompt}], max_tokens=2000, temperature=0.2)
                )
                from backend.llm.client import extract_json
                parsed = extract_json(response)
                if isinstance(parsed, list):
                    for item in parsed:
                        idx = item.get("index", 1) - 1
                        if 0 <= idx < len(batch_group):
                            cap = batch_group[idx]
                            rows.append({
                                "id": cap["id"],
                                "description": item.get("description", ""),
                                "business_outcomes": item.get("business_outcomes", []),
                                "technical_requirements": item.get("technical_requirements", []),
                                "implementation_complexity": item.get("implementation_complexity", "medium"),
                                "risk_factors": item.get("risk_factors", []),
                                "typical_duration_weeks": item.get("typical_duration_weeks", 16),
                                "common_frameworks": item.get("common_frameworks", []),
                                "solution_patterns": item.get("solution_patterns", []),
                                "kpis": item.get("kpis", []),
                                "industry_applicability": item.get("industry_applicability", ["All sectors"]),
                            })
                        else:
                            rows.append(self._default_capability_row(batch_group[idx] if idx < len(batch_group) else cap))
            except Exception as e:
                log.warning(f"LLM capability batch failed: {e}")
                for cap in batch_group:
                    rows.append(self._default_capability_row(cap))

            time.sleep(0.5)  # Rate limit courtesy
        return rows

    # ------------------------------------------------------------------
    # Run all enrichment steps
    # ------------------------------------------------------------------

    def run(self, batch_size: int = 100):
        log.info("=== Starting Graph Enrichment Pipeline ===")
        t0 = time.time()
        self.enrich_standards(batch_size)
        self.enrich_trends(batch_size)
        self.enrich_subdomains(batch_size)
        self.enrich_capabilities(batch_size)
        elapsed = time.time() - t0
        log.info(f"=== Graph Enrichment Complete in {elapsed:.1f}s ===")


def run_enrichment(use_llm: bool = True):
    """Entry point for running enrichment pipeline."""
    from dotenv import load_dotenv
    load_dotenv()

    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    fallback_key = os.getenv("FALLBACK_API_KEY", "")

    if not all([uri, username, password]):
        log.error("Neo4j credentials not found in .env")
        sys.exit(1)

    driver = GraphDatabase.driver(uri, auth=(username, password))

    llm_client = None
    if use_llm and fallback_key:
        from backend.config import get_settings
        from backend.llm.client import LLMClient
        settings = get_settings()
        llm_client = LLMClient(settings)
        log.info("LLM client initialised for capability enrichment fallback")
    else:
        log.info("No LLM client — using catalog + default enrichments only")

    try:
        enricher = GraphEnricher(driver, database, llm_client)
        enricher.run()
    finally:
        driver.close()


if __name__ == "__main__":
    run_enrichment(use_llm=True)
