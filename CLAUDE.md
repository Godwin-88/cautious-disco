# CLAUDE.md — Project Context for Claude Code

This file is auto-loaded by Claude Code when working in this repository.
It captures the project goals, architecture, current state, and working conventions
so any future Claude session starts with full context.

---

## Project: AMD EA Strategy Optimizer

**Event:** AMD Developer Hackathon 2026 on Lablab.ai
**Deadline:** May 10, 2026 (10:00 PM East Africa Time)
**Tracks:** Track 1 — AI Agents & Agentic Workflows ($2,500 1st), Hugging Face Special Prize (most-liked HF Space)
**Judging criteria:** Application of Technology, Presentation, Business Value, Originality

### What it does

Transforms a 10-minute questionnaire into governance-grounded, Jira-ready strategic roadmaps.
Full agentic pipeline: Knowledge Graph RAG → DRL Prioritiser → Qwen-72B on AMD MI300X → Compliance Verifier.

---

## Repository Layout

```
backend/
  agents/          LangGraph nodes: retriever, optimizer, generator, verifier
  api/             FastAPI routers: analyze, chat, graph, integrations, training, health
  drl/             Policy network (3-layer MLP), REINFORCE trainer, checkpoints
  graph/           Neo4j client (neo4j_client.py), all Cypher queries (cypher_queries.py)
  llm/             LLMClient (vLLM primary + fallback), prompts
  schemas/         Pydantic request/response models
  config.py        Settings via pydantic-settings (reads .env)
  main.py          FastAPI app factory + lifespan (Neo4j, LLM, DRL pre-load)

frontend/
  app.py           Streamlit entry point — 7 tabs
  components/      One file per tab + input_form.py
  utils/
    api_client.py  All HTTP calls to FastAPI (sync requests + SSE streaming)
    terminology.py TABS list and friendly label mappings

pipeline/
  seed_graph_cache.py  DRL pre-training (200 eps × 44 domains) + output cache seeding

docs/
  PLATFORM_GUIDE.md    Full platform guide + hackathon talking points
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM Inference | Qwen/Qwen2.5-72B-Instruct on AMD Instinct MI300X via vLLM |
| LLM Fallback | Together.ai / AIML API (OpenAI-compatible) — set `FALLBACK_API_KEY` |
| Knowledge Graph | Neo4j Aura (connected: neo4j+s://14b59f2c.databases.neo4j.io) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (384-dim) |
| Agentic Orchestration | LangGraph StateGraph |
| DRL Training | PyTorch (ROCm-compatible), REINFORCE + Gumbel-top-k |
| Backend | FastAPI + async + SSE streaming |
| Frontend | Streamlit + Plotly + networkx |
| ITSM Integration | Jira REST API v3 (live) · ServiceNow / Azure DevOps (mock) |

---

## Environment Variables (`.env`)

| Variable | Description |
|----------|-------------|
| `NEO4J_URI` | `neo4j+s://14b59f2c.databases.neo4j.io` |
| `NEO4J_USERNAME` | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j Aura password |
| `VLLM_BASE_URL` | AMD MI300X vLLM endpoint (e.g. `http://134.199.197.181:8000/v1`) |
| `VLLM_MODEL` | `Qwen/Qwen2.5-72B-Instruct` |
| `FALLBACK_API_KEY` | Together.ai / AIML API key — required if MI300X is offline |
| `FALLBACK_BASE_URL` | `https://api.together.xyz/v1` (default) |
| `FALLBACK_MODEL` | `Qwen/Qwen2.5-72B-Instruct-Turbo` (default) |
| `DRL_CHECKPOINT_PATH` | `backend/drl/checkpoints/ea_policy_v1.pt` |
| `BACKEND_URL` | Frontend → backend URL (default `http://localhost:8080`) |

---

## Running Locally

```bash
# Backend (port 8080)
uvicorn backend.main:app --host 0.0.0.0 --port 8080

# Frontend (port 8501)
streamlit run frontend/app.py --server.port 8501

# DRL pre-training (optional — all 44 domains, 200 episodes each)
python -m pipeline.seed_graph_cache --episodes 200
```

Docker: `docker-compose up --build` (backend :8080, frontend :8501)

---

## Current State (as of 2026-05-09)

### Recently shipped

1. **Chat session persistence** (`backend/api/routes_chat.py`, `frontend/components/chat_tab.py`)
   - Every user↔assistant exchange is stored in Neo4j as `(:ChatSession)-[:HAS_MESSAGE]→(:ChatMessage)`.
   - New endpoints: `POST /api/v1/chat/sessions`, `GET /api/v1/chat/sessions`,
     `GET /api/v1/chat/sessions/{id}/messages`, `DELETE /api/v1/chat/sessions/{id}`.
   - Conversation History panel in the EA Advisor tab: switch, reload, and delete sessions.

2. **Automatic DRL enrichment via chat** (`backend/api/routes_chat.py`)
   - After each chat turn, domains retrieved by the RAG context that have not been DRL-trained
     trigger a fire-and-forget background training run (50 episodes per domain).
   - `CHECK_DOMAIN_DRL_STATUS` Cypher query used to detect untrained domains.
   - Toast notification in the frontend confirms the enrichment trigger.

3. **Token budget fix** (`backend/llm/client.py`, `backend/config.py`)
   - Both `chat()` and `chat_stream()` now use `settings.llm_max_tokens` (default 2048).
   - Previous hard-coded 1024 cap was truncating long architectural responses.

### Known working

- Full LangGraph pipeline: Retrieve → Optimize (DRL) → Generate (Qwen-72B) → Verify → [regenerate if score < 70]
- Neo4j Aura connectivity verified at startup.
- DRL checkpoints: `ea_policy_v1.pt` (CPU/ROCm), `ea_policy_v2_graph.pt` (graph-trained).
- Live Jira export (Epics + Stories via REST API v3).
- ERP/CRM CSV ingest → Neo4j `ExternalSystem` nodes.
- ArchiMate layer classification (Business / Application / Technology).
- SSE streaming with fallback to non-streaming `api_chat()` if stream fails.

### Modified files (uncommitted as of last check)

- `backend/api/routes_chat.py` — session persistence + DRL enrichment
- `backend/config.py` — `llm_max_tokens` default 2048
- `backend/llm/client.py` — uses `settings.llm_max_tokens` in both chat methods
- `frontend/components/chat_tab.py` — session panel + DRL toast
- `frontend/components/export_tab.py`, `graph_explorer_tab.py`, `input_form.py`,
  `integrations_tab.py`, `roadmap_tab.py`, `training_tab.py` — minor UI fixes
- `frontend/utils/api_client.py` — session management API calls + `stream_chat` SSE parser
- `requirements.backend.txt` — dependency updates

---

## Architecture Notes

### LangGraph Pipeline

```
retrieve → optimize → generate → verify
                                    │ score < 70 AND iteration < 2
                                    ↓
                                generate (retry)
```

`AgentState` keys: `request`, `enriched_capabilities`, `graph_context`, `priority_result`,
`roadmap_draft`, `compliance_summary`, `final_roadmap`, `iteration`, `timing`.

### DRL Policy (EAPolicyNetwork)

- 3-layer MLP: Linear(20→128) → ReLU → Dropout(0.1) → Linear(128→128) → ReLU → Dropout(0.1) → Linear(128→64) → ReLU → Linear(64→10) → LogSoftmax
- State (20-dim): budget tier, timeline, risk tolerance, domain distribution, complexity, trend alignment
- Action (10-dim): ranked capability priority ordering
- Training: REINFORCE + Gumbel-top-k sampling (sample without replacement)
- Reward: complexity alignment + budget feasibility + domain coverage

### SSE Streaming Flow

```
GET /api/v1/chat/stream
  → async generator → StreamingResponse(media_type="text/event-stream")
  → each token: data: {"text": "..."}\n\n
  → final event: data: {"sources": [...], "enrich_triggered": bool, "done": true}\n\n

frontend/utils/api_client.py :: stream_chat()
  → requests.get(..., stream=True)
  → parse data: lines → yield text chunks
  → on done event → write to st.session_state["_last_chat_sources"] + ["_last_enrich_info"]
  → st.write_stream(stream_chat(...)) renders tokens live
```

### Output Caching

```python
cache_key = MD5("|".join(sorted(capability_ids)) + "|" + org_type)[:16]
# Hit → MATCH (o:GeneratedOutput {cache_key}) RETURN o.output_json  → < 100ms
# Miss → full pipeline → MERGE (:GeneratedOutput {cache_key}) SET o.output_json = $json
```

### Chat Session Schema (Neo4j)

```
(:ChatSession {session_id, title, created_at, last_active})
  -[:HAS_MESSAGE]→ (:ChatMessage {
      msg_id, role, content, sources_json, created_at
  })
```

---

## Memory Store Location

Claude Code project memory for this repo is persisted at:
`/home/ed/.claude/projects/-home-ed-projects-amd/memory/`

Key files:
- `MEMORY.md` — index
- `project_amd_hackathon.md` — project goals, stack, deadline
