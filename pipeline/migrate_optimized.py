"""
Optimized two-pass Cypher migrator.

Pass 1: regex-scan the .cypher file, extract all node/relationship records into
        typed Python dicts keyed by ID — deduplicate in memory.
Pass 2: UNWIND batch upserts per node type (MERGE on id), then batch relationship inserts.

Replaces the original migrate.py which re-inserted Domain nodes 81× per child.
Run: python -m pipeline.migrate_optimized
"""

import os
import re
import sys
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BATCH_SIZE = 500
CYPHER_FILE = os.getenv("CYPHER_FILE", "capability_canvas (3).cypher")


@dataclass
class NodeRecord:
    id: str
    name: str
    extra: dict = field(default_factory=dict)


@dataclass
class RelRecord:
    from_id: str
    to_id: str
    rel_type: str


@dataclass
class GraphData:
    domains: dict = field(default_factory=dict)       # id → NodeRecord
    subdomains: dict = field(default_factory=dict)
    capabilities: dict = field(default_factory=dict)
    subcapabilities: dict = field(default_factory=dict)
    epics: dict = field(default_factory=dict)
    features: dict = field(default_factory=dict)
    standards: dict = field(default_factory=dict)
    trends: dict = field(default_factory=dict)
    relationships: list = field(default_factory=list)  # list[RelRecord]


# ─── regex patterns for MERGE / CREATE statements ────────────────────────────
# Cypher uses double-quoted strings and comma-separated MATCH pattern:
#   MERGE (n:Label {id: "xxx"}) SET n.name = "yyy"
#   MATCH (a:Label {id: "xxx"}), (b:Label {id: "yyy"}) MERGE (a)-[:REL]->(b)

_Q = r'"([^"]+)"'   # double-quoted capture group

# MERGE (n:Label {id: "xxx"}) SET n.name = "yyy"
_MERGE_NODE = re.compile(
    r'MERGE\s*\((\w+):(\w+)\s*\{id:\s*' + _Q + r'\}\)'
    r'(?:\s*SET\s+\1\.name\s*=\s*' + _Q + r')?',
    re.IGNORECASE,
)

# MATCH (a:LabelA {id: "x"}), (b:LabelB {id: "y"}) MERGE (a)-[:REL]->(b)
_MERGE_REL = re.compile(
    r'MATCH\s*\(\w+(?::\w+)?\s*\{id:\s*' + _Q + r'\}\)\s*,\s*'
    r'\(\w+(?::\w+)?\s*\{id:\s*' + _Q + r'\}\)\s*'
    r'MERGE\s*\(\w+\)-\[:(\w+)\]->\(\w+\)',
    re.IGNORECASE,
)

# Also match hub-style: MATCH (ch:Domain {name: "..."}), (d:Domain {id: "..."})
_MERGE_HUB_REL = re.compile(
    r'MATCH\s*\(\w+(?::\w+)?\s*\{name:\s*' + _Q + r'\}\)\s*,\s*'
    r'\(\w+(?::\w+)?\s*\{id:\s*' + _Q + r'\}\)\s*'
    r'MERGE\s*\(\w+\)-\[:(\w+)\]->\(\w+\)',
    re.IGNORECASE,
)

_LABEL_MAP = {
    "Domain": "domains",
    "SubDomain": "subdomains",
    "Capability": "capabilities",
    "SubCapability": "subcapabilities",
    "Epic": "epics",
    "Feature": "features",
    "Standard": "standards",
    "Trend": "trends",
}


def parse_cypher_file(path: str) -> GraphData:
    log.info(f"Parsing {path} ...")
    t0 = time.time()
    data = GraphData()

    with open(path, encoding="utf-8") as fh:
        content = fh.read()

    # Split on semicolons that end a complete statement
    statements = [s.strip() for s in content.split(";") if s.strip()]
    log.info(f"  {len(statements):,} statements to scan")

    rel_count = 0
    node_count = 0

    for stmt in statements:
        # Relationship first (longer pattern)
        m_rel = _MERGE_REL.search(stmt)
        if m_rel:
            from_id, to_id, rel_type = m_rel.group(1), m_rel.group(2), m_rel.group(3)
            data.relationships.append(RelRecord(from_id=from_id, to_id=to_id, rel_type=rel_type))
            rel_count += 1
            continue

        # Hub relationship (name-based source, id-based target)
        m_hub = _MERGE_HUB_REL.search(stmt)
        if m_hub:
            # Store hub by name→id reference; will resolve during insert
            _, to_id, rel_type = m_hub.group(1), m_hub.group(2), m_hub.group(3)
            data.relationships.append(RelRecord(from_id="__hub__", to_id=to_id, rel_type=rel_type))
            rel_count += 1
            continue

        # Node MERGE
        m_node = _MERGE_NODE.search(stmt)
        if m_node:
            alias, label, node_id, name = m_node.groups()
            name = name or ""
            bucket_attr = _LABEL_MAP.get(label)
            if bucket_attr:
                bucket: dict = getattr(data, bucket_attr)
                if node_id not in bucket:
                    bucket[node_id] = NodeRecord(id=node_id, name=name)
                    node_count += 1

    elapsed = time.time() - t0
    log.info(
        f"  Parsed in {elapsed:.1f}s: "
        f"domains={len(data.domains)}, subdomains={len(data.subdomains)}, "
        f"capabilities={len(data.capabilities)}, subcapabilities={len(data.subcapabilities)}, "
        f"epics={len(data.epics)}, features={len(data.features)}, "
        f"standards={len(data.standards)}, trends={len(data.trends)}, "
        f"relationships={len(data.relationships)}"
    )
    return data


# ─── Neo4j helpers ────────────────────────────────────────────────────────────

def _batched(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def create_indexes(session):
    """Create uniqueness constraints and vector indexes."""
    constraints = [
        ("Domain", "domain_id"),
        ("SubDomain", "subdomain_id"),
        ("Capability", "capability_id"),
        ("SubCapability", "subcapability_id"),
        ("Epic", "epic_id"),
        ("Feature", "feature_id"),
        ("Standard", "standard_id"),
        ("Trend", "trend_id"),
    ]
    for label, name in constraints:
        try:
            session.run(
                f"CREATE CONSTRAINT {name} IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.id IS UNIQUE"
            )
        except Exception as e:
            log.warning(f"Constraint {name}: {e}")

    vector_labels = ["Capability", "SubCapability", "Feature"]
    for label in vector_labels:
        idx_name = f"{label.lower()}_embedding"
        try:
            session.run(
                f"CREATE VECTOR INDEX {idx_name} IF NOT EXISTS "
                f"FOR (n:{label}) ON (n.embedding) "
                f"OPTIONS {{indexConfig: {{`vector.dimensions`: 384, `vector.similarity_function`: 'cosine'}}}}"
            )
        except Exception as e:
            log.warning(f"Vector index {idx_name}: {e}")

    log.info("Indexes and constraints created")


def _insert_nodes(session, label: str, records: dict, batch_size: int = BATCH_SIZE):
    rows = [{"id": r.id, "name": r.name} for r in records.values()]
    if not rows:
        return
    total = 0
    for batch in _batched(rows, batch_size):
        session.run(
            f"UNWIND $rows AS row "
            f"MERGE (n:{label} {{id: row.id}}) "
            f"SET n.name = row.name",
            rows=batch,
        )
        total += len(batch)
    log.info(f"  Upserted {total:,} {label} nodes")


def _insert_hub(session):
    """Insert the domain hub node that links all top-level domains."""
    session.run(
        "MERGE (h:Domain {id: '__hub__'}) SET h.name = 'Enterprise Architecture Hub'"
    )
    log.info("  Hub node ensured")


def _insert_relationships(session, relationships: list, batch_size: int = BATCH_SIZE):
    rows = [{"from_id": r.from_id, "to_id": r.to_id, "rel_type": r.rel_type}
            for r in relationships]
    if not rows:
        return

    # Group by rel_type for targeted UNWIND
    from collections import defaultdict
    by_type: dict = defaultdict(list)
    for r in rows:
        by_type[r["rel_type"]].append({"from_id": r["from_id"], "to_id": r["to_id"]})

    total = 0
    for rel_type, rel_rows in by_type.items():
        for batch in _batched(rel_rows, batch_size):
            try:
                session.run(
                    f"UNWIND $rows AS row "
                    f"MATCH (a {{id: row.from_id}}) "
                    f"MATCH (b {{id: row.to_id}}) "
                    f"MERGE (a)-[:{rel_type}]->(b)",
                    rows=batch,
                )
                total += len(batch)
            except Exception as e:
                log.warning(f"Rel batch {rel_type}: {e}")
    log.info(f"  Upserted {total:,} relationships")


def run_migration(cypher_file: str = CYPHER_FILE, batch_size: int = BATCH_SIZE):
    from neo4j import GraphDatabase

    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")

    if not all([uri, username, password]):
        log.error("Neo4j credentials not set in .env")
        sys.exit(1)

    data = parse_cypher_file(cypher_file)

    log.info(f"Connecting to Neo4j at {uri}...")
    driver = GraphDatabase.driver(uri, auth=(username, password))

    try:
        with driver.session(database=database) as session:
            create_indexes(session)
            _insert_hub(session)

            _insert_nodes(session, "Domain", data.domains, batch_size)
            _insert_nodes(session, "SubDomain", data.subdomains, batch_size)
            _insert_nodes(session, "Capability", data.capabilities, batch_size)
            _insert_nodes(session, "SubCapability", data.subcapabilities, batch_size)
            _insert_nodes(session, "Epic", data.epics, batch_size)
            _insert_nodes(session, "Feature", data.features, batch_size)
            _insert_nodes(session, "Standard", data.standards, batch_size)
            _insert_nodes(session, "Trend", data.trends, batch_size)

            _insert_relationships(session, data.relationships, batch_size)

        log.info("Migration complete.")
    finally:
        driver.close()


if __name__ == "__main__":
    run_migration()
