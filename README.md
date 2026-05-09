# AMD EA Strategy Optimizer

> **AMD Developer Hackathon 2026 · Track 1 — AI Agents & Agentic Workflows**

An AI-powered **Enterprise Architecture platform** that transforms business goals into governance-grounded, Jira-ready strategic roadmaps — powered by **AMD Instinct MI300X**, a 1,416-capability knowledge graph, Deep Reinforcement Learning prioritisation, and a self-correcting LangGraph agentic pipeline.

---

## Changelog (latest first)

| Date | What changed |
|------|-------------|
| 2026-05-07 | Chat session persistence (Neo4j-backed), DRL enrichment triggered per chat turn, `llm_max_tokens` fix (was hard-coded 1024) |
| 2026-05-03 | Full platform: EA Advisor, Graph Explorer, Integrations, DRL pipeline, initial docs |

---

## Platform Tabs

| Tab | Description |
|-----|-------------|
| **EA Advisor** | Streaming conversational AI with Neo4j-persisted sessions and automatic DRL enrichment |
| **Graph Explorer** | Interactive force-directed network of 44 enterprise domains |
| **Strategic Roadmap** | Hierarchical questionnaire → 3-phase Epics → Features → User Stories → Tasks |
| **Initiatives & Scenarios** | Deep-dive into every Epic with governance acceptance criteria and tasks |
| **Integrations** | Live Jira export · ServiceNow/Azure DevOps mock · ERP/CRM CSV ingest · ArchiMate view |
| **Export & Handover** | JSON / Markdown / CSV export of the full roadmap |
| **AI Learning Engine** | DRL training dashboard — coverage heatmap, reward curves, trigger training |

---

## Architecture

```
Streamlit (7 tabs)
        │ HTTP / SSE
FastAPI Backend
        │
        ├── /api/v1/chat/stream  ──────────────────────────────────────────────────┐
        │                                                                           │
        └── /api/v1/analyze                                                        │
                │                                                         AMD MI300X
           LangGraph Pipeline                                          Qwen2.5-72B-Instruct
                │                                                       via vLLM (SSE)
          ┌─────▼──────┐   ┌──────────────┐   ┌─────────────┐              │
          │  Retrieve  │──▶│  Optimize    │──▶│  Generate  │──────────────┘
          │  (Neo4j)   │   │  (DRL/MLP)   │   │  (Qwen-72B)│
          └────────────┘   └──────────────┘   └─────────────┘
                                                      │
                                               ┌──────▼──────┐
                                               │   Verify    │ ← regenerate if score < 70
                                               └─────────────┘

Neo4j Aura Knowledge Graph
  44 Domains · 248 SubDomains · 1,416 Capabilities · 20+ Standards · 200+ Trends
```

### Key Design Decisions

- **3-tier retrieval cascade:** exact capability IDs → domain name expansion → semantic vector similarity
- **DRL prioritisation:** REINFORCE policy gradient, 20-dim state, 10-dim action (Gumbel-top-k sampling)
- **Output caching:** MD5(sorted capability IDs + org_type) → `:GeneratedOutput` node in Neo4j; cache hits skip the entire pipeline
- **Cross-domain synthesis:** when org type spans multiple domains (e.g. PE firm + Aviation), the `[CROSS-DOMAIN CONTEXT]` header and per-epic framing adapt the output accordingly
- **Self-correcting loop:** compliance verifier scores the roadmap; if score < 70 and iterations < 2, the generator is re-invoked with specific issues to fix
- **Chat session persistence:** every user↔assistant exchange is stored in Neo4j as `(:ChatSession)-[:HAS_MESSAGE]→(:ChatMessage)` nodes; the Conversation History panel lets users switch, reload, and delete sessions across page refreshes
- **Automatic DRL enrichment:** after each chat turn, domains retrieved from the RAG context that have not yet been DRL-trained trigger a fire-and-forget background training run (50 episodes); a toast notification confirms the trigger
- **Token budget fix:** `LLMClient` now uses `settings.llm_max_tokens` (default 2048) for both streaming and non-streaming calls; the previous hard-coded 1024 cap was causing truncated responses

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM Inference** | Qwen/Qwen2.5-72B-Instruct on **AMD Instinct MI300X** via vLLM |
| **LLM Fallback** | OpenAI-compatible API (AIML API / Together.ai) |
| **Knowledge Graph** | Neo4j Aura |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 |
| **Agentic Orchestration** | LangGraph StateGraph |
| **DRL Training** | PyTorch (ROCm-compatible), REINFORCE |
| **Backend** | FastAPI + async + SSE streaming |
| **Frontend** | Streamlit + Plotly + networkx |
| **ITSM Integration** | Jira REST API v3 (live) · ServiceNow / Azure DevOps (mock) |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Neo4j Aura instance (free tier works — seed with `capability_canvas (3).cypher`)
- AMD Developer Cloud VM with vLLM serving Qwen2.5-72B-Instruct (or use fallback API)

### 1. Clone & install

```bash
git clone https://github.com/Godwin-88/redesigned-goggles.git
cd redesigned-goggles

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.backend.txt
pip install -r requirements.frontend.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — fill in Neo4j credentials, vLLM URL, Jira credentials
```

Key variables:

| Variable | Description |
|----------|-------------|
| `NEO4J_URI` | Neo4j Aura connection URI |
| `NEO4J_PASSWORD` | Neo4j password |
| `VLLM_BASE_URL` | AMD MI300X vLLM endpoint (e.g. `http://134.x.x.x:8000/v1`) |
| `JIRA_URL` | Jira Cloud URL (e.g. `https://yourorg.atlassian.net`) |
| `JIRA_EMAIL` | Jira account email |
| `JIRA_API_TOKEN` | Jira API token — generate at [id.atlassian.com](https://id.atlassian.com/manage-profile/security/api-tokens) |
| `JIRA_PROJECT_KEY` | Target Jira project key (e.g. `EAOPT`) |

### 3. Seed the knowledge graph

```bash
# Import the capability canvas into Neo4j via Neo4j Browser → paste capability_canvas (3).cypher
# Or using cypher-shell:
cypher-shell -u neo4j -p <password> -f "capability_canvas (3).cypher"
```

### 4. Run

```bash
# Terminal 1 — Backend
uvicorn backend.main:app --host 0.0.0.0 --port 8080

# Terminal 2 — Frontend
streamlit run frontend/app.py --server.port 8501
```

Open [http://localhost:8501](http://localhost:8501)

### 5. (Optional) Pre-train DRL and seed output cache

```bash
# Train all 44 domains, 200 episodes each
python -m pipeline.seed_graph_cache --episodes 200

# Seed cache for a specific org type only
python -m pipeline.seed_graph_cache --org "NHS Trust" --skip-training
```

---

## Docker

```bash
docker-compose up --build
```

Backend: `http://localhost:8080` · Frontend: `http://localhost:8501`

---

## Jira Integration Setup

1. Log into Jira Cloud → **Account Settings → Security → API tokens → Create API token**
2. Copy the token immediately
3. Add to `.env`:
   ```
   JIRA_URL=https://yourorg.atlassian.net
   JIRA_EMAIL=you@yourorg.com
   JIRA_API_TOKEN=<your-token>
   JIRA_PROJECT_KEY=EAOPT
   ```
4. In the platform: **Integrations → ITSM Connector → Jira Cloud**
5. Generate a roadmap, then click **Export Roadmap to Jira**

The exporter creates one **Epic** per strategic initiative and one **Story** per feature workstream, with governance-grounded acceptance criteria carried through to Jira.

---

## AMD Technology Story

### AMD Instinct MI300X

LLM inference runs on AMD Instinct MI300X — 192 GB HBM3, 5.2 TB/s memory bandwidth — the only single GPU with enough unified memory to serve Qwen2.5-72B at fp16 without sharding. vLLM continuous batching maximises throughput; SSE streaming delivers first-token latency of ~1–2 seconds.

### ROCm + PyTorch DRL

The DRL policy network is ROCm-compatible. `get_device()` in `backend/drl/policy_network.py` detects ROCm via `torch.version.hip` and returns `cuda:0` on ROCm systems. On CPU-only machines (local dev), it logs a clear message pointing to the remote AMD MI300X for LLM inference.

---

## Project Structure

```
├── backend/
│   ├── agents/          # LangGraph nodes: retriever, optimizer, generator, verifier
│   ├── api/             # FastAPI routes: analyze, chat, graph, integrations, training
│   ├── drl/             # Policy network (MLP), trainer, REINFORCE
│   ├── graph/           # Neo4j client, Cypher queries
│   ├── llm/             # LLM client, prompts
│   ├── schemas/         # Pydantic models: request, response
│   └── config.py
├── frontend/
│   ├── app.py           # Streamlit entry point — 7-tab layout
│   ├── components/      # One file per tab + input_form
│   └── utils/           # api_client.py, terminology.py
├── pipeline/
│   └── seed_graph_cache.py  # DRL pre-training + output cache seeding
├── docs/
│   └── PLATFORM_GUIDE.md    # Full platform guide + hackathon talking points
├── tests/
├── docker-compose.yml
├── .env.example
└── requirements.*.txt
```

---

## API Reference

### Core

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Backend + Neo4j + GPU health |
| `/api/v1/analyze` | POST | Full agentic pipeline |
| `/api/v1/domains` | GET | All 44 domains |
| `/api/v1/subdomains` | GET | SubDomains filtered by domain names |
| `/api/v1/subdomain-capabilities` | GET | Capabilities filtered by subdomain IDs |

### Chat & Sessions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/chat` | POST | Non-streaming RAG chat (persists to session) |
| `/api/v1/chat/stream` | GET | SSE streaming RAG chat (persists to session) |
| `/api/v1/chat/sessions` | POST | Create or touch a chat session |
| `/api/v1/chat/sessions` | GET | List 15 most recent sessions |
| `/api/v1/chat/sessions/{id}/messages` | GET | Full message history for a session |
| `/api/v1/chat/sessions/{id}` | DELETE | Delete a session and all its messages |

### Graph, Integrations & Training

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/graph/network` | GET | `{nodes, edges}` for Graph Explorer |
| `/api/v1/integrations/jira/export` | POST | Live Jira Epic/Story creation |
| `/api/v1/integrations/erp/ingest` | POST | CSV → Neo4j ExternalSystem nodes |
| `/api/v1/integrations/archimate` | GET | Capabilities by ArchiMate layer |
| `/api/v1/training/run` | POST | Trigger DRL training run |

Full interactive docs at `http://localhost:8080/docs`

---

## License

MIT
