"""
Export the full Neo4j graph as clean, loadable Cypher.
Run against the local neo4j-amd instance:
    python export_seed_cypher.py
Writes: hf_space/neo4j_backup/seed_graph.cypher
"""

import os
import re
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI  = os.getenv("NEO4J_URI",      "bolt://localhost:7688")
USER = os.getenv("NEO4J_USERNAME", "neo4j")
PASS = os.getenv("NEO4J_PASSWORD", "your-password")

OUT  = "hf_space/neo4j_backup/seed_graph.cypher"

# Labels to skip (ephemeral / not needed in the deployed graph)
SKIP_LABELS = {"UNIQUE IMPORT LABEL", "ChatSession", "ChatMessage"}
# Relationship types to skip
SKIP_REL_TYPES = {"HAS_MESSAGE"}


def esc(v) -> str:
    """Escape a Python value to an inline Cypher literal."""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(esc(i) for i in v) + "]"
    # String: escape backslashes then single-quotes
    s = str(v).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{s}'"


def props_map(props: dict) -> str:
    """Render a property map as Cypher {key: value, ...}"""
    if not props:
        return "{}"
    parts = []
    for k, v in props.items():
        safe_key = f"`{k}`" if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', k) else k
        parts.append(f"{safe_key}: {esc(v)}")
    return "{" + ", ".join(parts) + "}"


def main():
    driver = GraphDatabase.driver(URI, auth=(USER, PASS))
    lines = []

    with driver.session() as s:
        # ── Nodes ────────────────────────────────────────────────────────────
        print("Exporting nodes...")
        result = s.run(
            "MATCH (n) WHERE NOT any(lbl IN labels(n) WHERE lbl IN $skip) "
            "RETURN id(n) AS nid, labels(n) AS lbls, properties(n) AS props",
            skip=list(SKIP_LABELS)
        )
        nodes = list(result)
        print(f"  {len(nodes)} nodes")

        for rec in nodes:
            nid   = rec["nid"]
            lbls  = [l for l in rec["lbls"] if l not in SKIP_LABELS]
            props = dict(rec["props"])
            if not lbls:
                continue
            label_str = ":".join(f"`{l}`" if " " in l else l for l in lbls)
            # Use id(n) as a stable import key
            props["_import_id"] = nid
            lines.append(
                f"MERGE (n:{label_str} {{_import_id: {nid}}}) "
                f"SET n += {props_map(props)};"
            )

        # ── Relationships ────────────────────────────────────────────────────
        print("Exporting relationships...")
        result = s.run(
            "MATCH (a)-[r]->(b) "
            "WHERE NOT type(r) IN $skip "
            "  AND NOT any(lbl IN labels(a) WHERE lbl IN $slbls) "
            "  AND NOT any(lbl IN labels(b) WHERE lbl IN $slbls) "
            "RETURN id(a) AS aid, id(b) AS bid, type(r) AS rtype, properties(r) AS props",
            skip=list(SKIP_REL_TYPES),
            slbls=list(SKIP_LABELS)
        )
        rels = list(result)
        print(f"  {len(rels)} relationships")

        for rec in rels:
            aid, bid = rec["aid"], rec["bid"]
            rtype    = rec["rtype"]
            props    = dict(rec["props"])
            prop_str = f" {props_map(props)}" if props else ""
            lines.append(
                f"MATCH (a {{_import_id: {aid}}}), (b {{_import_id: {bid}}}) "
                f"MERGE (a)-[:{rtype}{prop_str}]->(b);"
            )

        # ── Cleanup import key ───────────────────────────────────────────────
        lines.append(
            "MATCH (n) WHERE n._import_id IS NOT NULL "
            "REMOVE n._import_id;"
        )

    driver.close()

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")

    size_mb = os.path.getsize(OUT) / 1_048_576
    print(f"\nWrote {OUT}  ({len(lines)} statements, {size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
