FROM python:3.12-slim

WORKDIR /app

# ── System deps ───────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl supervisor netcat-openbsd gnupg \
    openjdk-21-jre-headless && \
    rm -rf /var/lib/apt/lists/*

# ── Neo4j 5.x Community + cypher-shell (official Debian repo) ────────────────
RUN curl -fsSL https://debian.neo4j.com/neotechnology.gpg.key \
    | gpg --dearmor -o /usr/share/keyrings/neo4j.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/neo4j.gpg] https://debian.neo4j.com stable 5" \
    > /etc/apt/sources.list.d/neo4j.list && \
    apt-get update && apt-get install -y neo4j cypher-shell && \
    rm -rf /var/lib/apt/lists/*

# ── Python deps (CPU-only torch keeps image lean) ────────────────────────────
COPY requirements.backend.txt requirements.frontend.txt ./
RUN pip install --no-cache-dir \
    "torch>=2.1.0" --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.backend.txt
RUN pip install --no-cache-dir -r requirements.frontend.txt

# Pre-download embedding model into image (avoids cold-start network hit)
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# ── Application code ──────────────────────────────────────────────────────────
COPY backend/  ./backend/
COPY frontend/ ./frontend/
COPY pipeline/knowledge_sources/ ./pipeline/knowledge_sources/
COPY pipeline/embed_nodes.py     ./pipeline/embed_nodes.py
COPY pipeline/__init__.py        ./pipeline/__init__.py

# ── Graph seed (full enriched export: 44 domains, 1416 caps, training data) ──
COPY neo4j_backup/seed_graph.cypher ./neo4j_backup/seed_graph.cypher

RUN mkdir -p backend/drl/checkpoints

# ── Neo4j memory tuning (fits HF free tier 16 GB RAM comfortably) ─────────────
RUN { \
    echo 'server.memory.heap.initial_size=256m'; \
    echo 'server.memory.heap.max_size=512m'; \
    echo 'server.memory.pagecache.size=128m'; \
    echo 'server.bolt.listen_address=0.0.0.0:7687'; \
    echo 'server.http.listen_address=0.0.0.0:7474'; \
    echo 'dbms.security.procedures.unrestricted=apoc.*'; \
} >> /etc/neo4j/neo4j.conf

# ── Supervisor + entrypoint ───────────────────────────────────────────────────
COPY supervisord.conf /etc/supervisor/conf.d/app.conf
COPY entrypoint.sh    /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && \
    mkdir -p /var/log/supervisor /var/log/neo4j

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV BACKEND_URL=http://localhost:8080

EXPOSE 7860

CMD ["/app/entrypoint.sh"]
