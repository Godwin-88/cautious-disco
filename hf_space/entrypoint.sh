#!/bin/bash
# Startup: set auth → start Neo4j → wait → seed graph → start app services
set -e

NEO4J_PASS="your-password"
SEED_FILE="/app/neo4j_backup/seed_graph.cypher"
SEED_FLAG="/var/lib/neo4j/data/.graph_seeded"

log() { echo "[entrypoint] $(date '+%H:%M:%S') $*"; }

# ── Step 1: Set initial password before first start ──────────────────────────
log "Setting Neo4j password..."
neo4j-admin dbms set-initial-password "$NEO4J_PASS"

# ── Step 2: Fix ownership and start Neo4j ────────────────────────────────────
log "Fixing data directory ownership..."
chown -R neo4j:neo4j /var/lib/neo4j/data /var/lib/neo4j/run /var/log/neo4j 2>/dev/null || true

log "Starting Neo4j..."
su -s /bin/bash neo4j -c \
    "NEO4J_CONF=/etc/neo4j neo4j console >> /var/log/neo4j/console.log 2>&1 &"

# ── Step 3: Wait for bolt (up to 120 s) ──────────────────────────────────────
log "Waiting for bolt on :7687..."
for i in $(seq 1 120); do
    if nc -z localhost 7687 2>/dev/null; then
        log "Bolt ready after ${i}s."
        break
    fi
    if [ "$i" -eq 120 ]; then
        log "ERROR: bolt not ready — check /var/log/neo4j/console.log"; exit 1
    fi
    sleep 1
done

# ── Step 4: Seed the graph (only once per container lifetime) ─────────────────
if [ ! -f "$SEED_FLAG" ]; then
    log "Seeding knowledge graph from $SEED_FILE ..."
    # Extra 5 s grace so system DB is fully accepting auth before we query
    sleep 5
    # Plain MERGE/MATCH statements — pipe each line individually
    # --fail-at-end so one bad statement doesn't abort the whole import
    cypher-shell -u neo4j -p "$NEO4J_PASS" \
        --format plain --fail-at-end \
        < "$SEED_FILE" \
        >> /var/log/neo4j/seed.log 2>&1 \
        && touch "$SEED_FLAG" \
        && log "Graph seeded successfully." \
        || log "WARNING: seed may have partially loaded — check /var/log/neo4j/seed.log"

    # Smoke-test: count nodes
    COUNT=$(cypher-shell -u neo4j -p "$NEO4J_PASS" --format plain \
        "MATCH (n) WHERE n.id <> '__hub__' RETURN count(n) AS c" 2>/dev/null \
        | tail -1 || echo "?")
    log "Node count after seed: ${COUNT}"

    # Build vector embeddings for semantic search
    log "Building capability embeddings (vector search)..."
    export NEO4J_URI="bolt://localhost:7687"
    export NEO4J_USERNAME="neo4j"
    export NEO4J_PASSWORD="$NEO4J_PASS"
    export PYTHONPATH="/app"
    python3 /app/pipeline/embed_nodes.py >> /var/log/neo4j/embed.log 2>&1 \
      && log "Embeddings done." \
      || { log "WARNING: embeddings failed:"; tail -20 /var/log/neo4j/embed.log; }

    # Create vector index so CALL db.index.vector.queryNodes works
    cypher-shell -u neo4j -p "$NEO4J_PASS" --format plain \
      "CREATE VECTOR INDEX capability_embedding IF NOT EXISTS FOR (n:Capability) ON n.embedding OPTIONS {indexConfig: {\`vector.dimensions\`: 384, \`vector.similarity_function\`: 'cosine'}}" \
      >> /var/log/neo4j/seed.log 2>&1 \
      && log "Vector index created." \
      || log "WARNING: vector index creation failed."
else
    log "Graph already seeded — skipping."
fi

# ── Step 5: Hand off to supervisord ──────────────────────────────────────────
log "Starting application services..."
exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
