"""
Embedding Pipeline — generates sentence embeddings for all Capability, SubCapability,
and Feature nodes and stores them in Neo4j vector indexes.

Uses sentence-transformers/all-MiniLM-L6-v2 (384-dim).
Runs on AMD ROCm (exposed as CUDA) or CPU.
Run after enrich_graph.py.
"""

import os
import sys
import logging
import numpy as np
import time
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

FETCH_NODES_QUERY = """
MATCH (n)
WHERE (n:Capability OR n:SubCapability OR n:Feature)
  AND n.id IS NOT NULL
  AND n.embedding IS NULL
OPTIONAL MATCH (parent)<-[:PARENT_OF*1..3]-(domain:Domain)
WHERE parent = n OR (parent)-[:PARENT_OF*1..2]->(n)
RETURN
  n.id AS node_id,
  labels(n)[0] AS label,
  n.name AS name,
  n.description AS description,
  [(sd:SubDomain)-[:PARENT_OF*0..2]->(n) | sd.name][0] AS subdomain_name,
  [(d:Domain)-[:PARENT_OF*0..4]->(n) | d.name][0] AS domain_name
LIMIT $batch_size
"""

FETCH_NODES_WITH_EMBEDDING = """
MATCH (n)
WHERE (n:Capability OR n:SubCapability OR n:Feature)
  AND n.id IS NOT NULL
RETURN
  n.id AS node_id,
  labels(n)[0] AS label,
  n.name AS name,
  n.description AS description,
  [(sd:SubDomain)-[:PARENT_OF*0..2]->(n) | sd.name][0] AS subdomain_name,
  [(d:Domain)-[:PARENT_OF*0..4]->(n) | d.name][0] AS domain_name
SKIP $skip
LIMIT $batch_size
"""

COUNT_UNEMBEDDED = """
MATCH (n)
WHERE (n:Capability OR n:SubCapability OR n:Feature)
  AND n.embedding IS NULL
RETURN count(n) AS cnt
"""

COUNT_TOTAL_EMBEDDABLE = """
MATCH (n)
WHERE (n:Capability OR n:SubCapability OR n:Feature)
RETURN count(n) AS cnt
"""


def build_node_text(name: str, description: str | None, subdomain: str | None, domain: str | None) -> str:
    """Build enriched text for embedding — includes full path context."""
    parts = []
    if domain:
        parts.append(f"Domain: {domain}")
    if subdomain:
        parts.append(f"SubDomain: {subdomain}")
    parts.append(f"Capability: {name}")
    if description:
        parts.append(description[:300])  # truncate long descriptions
    return " > ".join(parts[:3]) + (f". {description[:200]}" if description else "")


def embed_and_store(driver, database: str, embed_fn, embed_batch_size: int = 128, write_batch_size: int = 50):
    """Fetch all embeddable nodes, generate embeddings, store in Neo4j."""
    from neo4j import GraphDatabase

    with driver.session(database=database) as session:
        total_result = session.run(COUNT_TOTAL_EMBEDDABLE).single()
        total = total_result["cnt"] if total_result else 0
        log.info(f"Total embeddable nodes: {total:,}")

        skip = 0
        total_embedded = 0
        t0 = time.time()

        while True:
            rows = session.run(FETCH_NODES_WITH_EMBEDDING, batch_size=embed_batch_size, skip=skip).data()
            if not rows:
                break

            texts = [
                build_node_text(
                    r.get("name") or "",
                    r.get("description"),
                    r.get("subdomain_name"),
                    r.get("domain_name"),
                )
                for r in rows
            ]
            node_ids = [r["node_id"] for r in rows]

            embeddings = embed_fn(texts)

            # Write embeddings in smaller batches
            for i in range(0, len(rows), write_batch_size):
                chunk_ids = node_ids[i:i+write_batch_size]
                chunk_embs = embeddings[i:i+write_batch_size]
                for node_id, emb in zip(chunk_ids, chunk_embs):
                    try:
                        session.run(
                            "MATCH (n {id: $node_id}) "
                            "CALL db.create.setVectorProperty(n, 'embedding', $embedding) YIELD node "
                            "RETURN node",
                            node_id=node_id,
                            embedding=emb.tolist(),
                        )
                    except Exception as e:
                        # Fallback: store as property directly
                        try:
                            session.run(
                                "MATCH (n {id: $node_id}) SET n.embedding = $embedding",
                                node_id=node_id,
                                embedding=emb.tolist(),
                            )
                        except Exception as e2:
                            log.warning(f"Could not store embedding for {node_id}: {e2}")

            total_embedded += len(rows)
            elapsed = time.time() - t0
            rate = total_embedded / elapsed if elapsed > 0 else 0
            log.info(f"  Embedded {total_embedded:,}/{total:,} ({rate:.0f} nodes/s)")

            skip += embed_batch_size
            if len(rows) < embed_batch_size:
                break

    return total_embedded


def run_embedding_pipeline():
    from neo4j import GraphDatabase
    from dotenv import load_dotenv
    load_dotenv()

    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")

    if not all([uri, username, password]):
        log.error("Neo4j credentials not found")
        sys.exit(1)

    log.info(f"Loading embedding model: {EMBEDDING_MODEL}")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Check for AMD ROCm
    import torch
    if torch.cuda.is_available():
        device = "cuda"
        log.info(f"Using AMD ROCm GPU: {torch.cuda.get_device_name(0)}")
        if hasattr(torch.version, "hip") and torch.version.hip:
            log.info(f"ROCm version: {torch.version.hip}")
        model = model.to(device)
    else:
        device = "cpu"
        log.info("Using CPU for embeddings")

    def embed_fn(texts: list[str]) -> np.ndarray:
        return model.encode(texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True)

    log.info(f"Connecting to Neo4j at {uri}...")
    driver = GraphDatabase.driver(uri, auth=(username, password))

    try:
        total = embed_and_store(driver, database, embed_fn)
        log.info(f"Embedding pipeline complete: {total:,} nodes embedded")
    finally:
        driver.close()


if __name__ == "__main__":
    run_embedding_pipeline()
