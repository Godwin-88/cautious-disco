# Digital Capability Canvas Intelligence Platform
### UiPath AgentHack 2026 · Track 2 — UiPath Maestro BPMN

> **Adapted from:** AMD EA Strategy Optimizer (AMD Developer Hackathon 2026)
> **Original repo:** https://github.com/Godwin-88/cautious-disco
> **New submission:** UiPath AgentHack 2026 — Track 2: UiPath Maestro BPMN

An AI-powered **Enterprise Architecture Assessment & Investment Prioritisation** platform that orchestrates GraphRAG intelligence, Deep Reinforcement Learning prioritisation, and human-in-the-loop review through a **UiPath Maestro BPMN process** — delivering board-ready capability roadmaps and Jira-ready investment backlogs.

---

## What Changed from the AMD Submission

| Component | AMD Version | UiPath Version |
|---|---|---|
| LLM | Qwen2.5-72B on AMD MI300X (vLLM) | **Groq Llama 3.3 70B** (free, OpenAI-compatible) |
| Orchestration | LangGraph StateGraph only | **UiPath Maestro BPMN** wraps LangGraph as a service task |
| Data Ingestion | Manual CSV upload | **UiPath RPA Robot** harvests from enterprise systems |
| Human Review | None | **UiPath Human Task** — Domain SME validates before export |
| Audit Trail | None | **UiPath Orchestrator** logs every BPMN event |
| Frontend | Streamlit 7-tab app | Streamlit app + **UiPath Task Portal** for reviewer inbox |

Everything else — Neo4j graph, LangGraph pipeline, DRL prioritisation, Jira export — is carried over directly.

---

## Platform Architecture

```
UiPath Automation Cloud (Orchestration & Governance Layer)
│
├── Maestro BPMN Process: "Capability Assessment"
│       │
│       ├── [Task 1] UiPath RPA Robot ──► harvest org data from ITSM/ERP/SharePoint
│       │
│       ├── [Task 2] Service Task ────────► POST /api/v1/analyze  ◄──────────────────┐
│       │                                         │                                   │
│       │                              LangGraph Pipeline                             │
│       │                         ┌────────────────────────┐                         │
│       │                         │  Retrieve  (Neo4j RAG) │                         │
│       │                         │  Optimize  (DRL/MLP)   │                         │
│       │                         │  Generate  (Groq LLM)  │                         │
│       │                         │  Verify    (score ≥ 70)│──► regenerate if needed ┘
│       │                         └────────────────────────┘
│       │
│       ├── [Gateway] Exclusive: Auto-approve OR Human Review?
│       │
│       ├── [Task 3] Human Task ──────────► UiPath Task Portal (Domain SME review)
│       │
│       ├── [Task 4] Service Task ────────► POST /api/v1/integrations/jira/export
│       │
│       └── [End Event] Audit log written to Orchestrator
│
├── Agent Builder (GraphRAG Query Agent)
├── API Workflows (service task bridge)
└── Orchestrator (monitoring, SLA, audit)

Knowledge Graph (Neo4j Aura)
  44 Domains · 223 SubDomains · 1,295 Capabilities · 20+ Standards · 200+ Trends

LLM Inference (Free Tier Stack)
  Primary:  Groq — Llama 3.3 70B (30 RPM, OpenAI-compatible, ~300 tok/s)
  Fallback: Google AI Studio — Gemini 2.5 Flash (1,500 req/day, 1M context)
  Overflow: OpenRouter — auto:free (Llama 4, Qwen3, DeepSeek R1)
```

---

## UiPath Components Used

| Component | Role in Platform |
|---|---|
| **UiPath Maestro BPMN** | Core orchestration — models and runs the full assessment process end-to-end |
| **UiPath RPA (Studio)** | Data ingestion robot — harvests capability evidence from ITSM, ERP, SharePoint |
| **UiPath Agent Builder** | GraphRAG query agent — natural language to Cypher traversal |
| **UiPath API Workflows** | Bridge between Maestro BPMN tasks and FastAPI backend |
| **UiPath Human Tasks** | Domain SME review inbox — approve, override, or escalate agent outputs |
| **UiPath Orchestrator** | Process monitoring, SLA enforcement, audit trail, storage buckets |
| **UiPath Automation Cloud** | Unified hosting and governance layer for all of the above |

> All orchestration and agent logic runs through UiPath Automation Cloud. External services (Neo4j, Groq, Jira) are called via API.

---

## Coding Agent Usage

This project uses **Groq OpenCode CLI** (free) and **Cursor** as coding agents to build and iterate on:
- The UiPath API Workflow bridge layer
- The LLM client swap from vLLM to Groq
- The human task portal frontend component
- The BPMN process definition files

All coding agent prompts and generated code are committed with attribution comments in the source files.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Orchestration** | UiPath Maestro BPMN |
| **Automation** | UiPath RPA Studio, UiPath Agent Builder |
| **LLM — Primary** | Groq API — Llama 3.3 70B (free tier, OpenAI-compatible) |
| **LLM — Fallback** | Google AI Studio — Gemini 2.5 Flash (free tier) |
| **LLM — Overflow** | OpenRouter — auto:free routing |
| **Knowledge Graph** | Neo4j Aura (free tier) |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 |
| **Agentic Pipeline** | LangGraph StateGraph |
| **DRL Training** | PyTorch REINFORCE policy gradient |
| **Backend** | FastAPI + async + SSE streaming |
| **Frontend** | Streamlit + Plotly + networkx |
| **ITSM Integration** | Jira REST API v3 (live), ServiceNow/Azure DevOps (mock) |
| **Containerisation** | Docker + docker-compose |

---

## Prerequisites

- Python 3.11+
- Neo4j Aura account (free tier — seed with `capability_canvas (3).cypher`)
- **Groq API key** — sign up free at [console.groq.com](https://console.groq.com) (no credit card)
- **Google AI Studio key** (optional fallback) — sign up free at [ai.google.dev](https://ai.google.dev)
- **UiPath Automation Cloud** account — request access via [UiPath Labs](https://uipath.com/labs)
- Jira Cloud account (for export integration)

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/Godwin-88/cautious-disco.git
cd cautious-disco

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.backend.txt
pip install -r requirements.frontend.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

**Key environment variables (updated from AMD version):**

```env
# Neo4j (unchanged)
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# LLM — replace vLLM/AMD with Groq (free)
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_BASE_URL=https://api.groq.com/openai/v1

# LLM Fallback — Google AI Studio (free, no credit card)
GEMINI_API_KEY=AIzaSy_xxxxxxxxxxxxxxxxxxxx
GEMINI_MODEL=gemini-2.5-flash

# LLM Overflow — OpenRouter (free models)
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxx
OPENROUTER_MODEL=meta-llama/llama-4-maverick:free

# UiPath Automation Cloud
UIPATH_CLOUD_URL=https://cloud.uipath.com
UIPATH_TENANT=your_tenant
UIPATH_CLIENT_ID=your_client_id
UIPATH_CLIENT_SECRET=your_client_secret
UIPATH_ORCHESTRATOR_URL=https://cloud.uipath.com/your_org/your_tenant/orchestrator_

# Jira (unchanged)
JIRA_URL=https://yourorg.atlassian.net
JIRA_EMAIL=you@yourorg.com
JIRA_API_TOKEN=your_token
JIRA_PROJECT_KEY=EAOPT
```

### 3. Seed the Knowledge Graph

```bash
# Option A: Neo4j Browser — paste capability_canvas (3).cypher
# Option B: cypher-shell
cypher-shell -u neo4j -p <password> -f "capability_canvas (3).cypher"
```

### 4. Run the Application

```bash
# Terminal 1 — Backend
uvicorn backend.main:app --host 0.0.0.0 --port 8080

# Terminal 2 — Frontend
streamlit run frontend/app.py --server.port 8501
```

Open http://localhost:8501

### 5. Run via Docker

```bash
docker-compose up --build
```

Backend: http://localhost:8080 · Frontend: http://localhost:8501

### 6. (Optional) Pre-train DRL

```bash
python -m pipeline.seed_graph_cache --episodes 200
```

---

## UiPath Maestro BPMN — Setup

### Deploy the BPMN Process

1. Log into [UiPath Automation Cloud](https://cloud.uipath.com)
2. Navigate to **Maestro → Processes → Import**
3. Upload `uipath/capability_assessment.bpmn` from this repository
4. Configure service task endpoints to point to your deployed FastAPI backend
5. Assign human task roles in **Orchestrator → Users & Roles**

### Configure API Workflow Bridge

The UiPath API Workflow (`uipath/api_workflows/analyze_trigger.json`) bridges Maestro service tasks to the FastAPI backend:

```
Maestro Service Task
        ↓
UiPath API Workflow (hosted on Automation Cloud)
        ↓
POST https://your-backend/api/v1/analyze
        ↓
LangGraph Pipeline Response
        ↓
Back to Maestro as task output variable
```

Import the API Workflow from `uipath/api_workflows/` in UiPath Orchestrator.

### RPA Robot Setup

1. In UiPath Studio, open `uipath/robots/DataIngestionRobot.xaml`
2. Configure connection strings for your ITSM/ERP in the robot's config file
3. Publish to Orchestrator and assign to the BPMN Data Ingestion task

---

## LLM Client Changes (from AMD Version)

The `backend/llm/client.py` now supports multi-provider routing. The change from AMD MI300X vLLM to Groq is a one-line config swap — the OpenAI-compatible interface is identical:

```python
# Old (AMD MI300X)
# VLLM_BASE_URL=http://134.x.x.x:8000/v1
# model=Qwen/Qwen2.5-72B-Instruct

# New (Groq — free, same interface)
# GROQ_BASE_URL=https://api.groq.com/openai/v1
# model=llama-3.3-70b-versatile

client = OpenAI(
    base_url=settings.llm_base_url,   # reads from LLM_PROVIDER env var
    api_key=settings.llm_api_key,
)
```

Fallback chain: Groq → Gemini → OpenRouter:free. If all three are exhausted, the system serves a cached response from Neo4j (existing cache mechanism unchanged).

---

## Project Structure

```
├── backend/
│   ├── agents/          # LangGraph nodes: retriever, optimizer, generator, verifier
│   ├── api/             # FastAPI routes: analyze, chat, graph, integrations, training
│   ├── drl/             # Policy network (MLP), trainer, REINFORCE
│   ├── graph/           # Neo4j client, Cypher queries
│   ├── llm/             # LLM client (updated: Groq/Gemini/OpenRouter routing)
│   ├── schemas/         # Pydantic models
│   └── config.py
├── frontend/
│   ├── app.py           # Streamlit 7-tab app (unchanged)
│   ├── components/      # Tab components + NEW: human_task_portal.py
│   └── utils/
├── uipath/              # NEW: UiPath platform assets
│   ├── capability_assessment.bpmn     # Maestro BPMN process definition
│   ├── api_workflows/
│   │   ├── analyze_trigger.json       # API Workflow: trigger LangGraph pipeline
│   │   └── jira_export_trigger.json   # API Workflow: trigger Jira export
│   └── robots/
│       └── DataIngestionRobot.xaml    # UiPath RPA robot for data harvesting
├── pipeline/
│   └── seed_graph_cache.py
├── docs/
│   ├── PLATFORM_GUIDE.md
│   └── BPMN_PROCESS_SPEC.md          # NEW: full BPMN process specification
├── docker-compose.yml
├── .env.example
└── requirements.*.txt
```

---

## API Reference

### Core (unchanged from AMD version)

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/health` | GET | Backend + Neo4j + LLM health |
| `/api/v1/analyze` | POST | Full agentic pipeline (called by Maestro) |
| `/api/v1/domains` | GET | All 44 domains |
| `/api/v1/subdomains` | GET | SubDomains filtered by domain |
| `/api/v1/subdomain-capabilities` | GET | Capabilities filtered by subdomain |

### Chat & Sessions (unchanged)

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/chat/stream` | GET | SSE streaming RAG chat |
| `/api/v1/chat/sessions` | POST/GET | Create/list sessions |
| `/api/v1/chat/sessions/{id}/messages` | GET | Full message history |

### UiPath Bridge (NEW)

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/uipath/task-complete` | POST | Receive human task decision from Orchestrator |
| `/api/v1/uipath/process-status` | GET | Return current process instance status |
| `/api/v1/uipath/audit-log` | POST | Receive and store Orchestrator audit events |

Full interactive docs: http://localhost:8080/docs

---

## Demo Video Outline (5 min)

1. **0:00–0:30** — Architecture overview: canvas graph + LangGraph + Maestro BPMN
2. **0:30–1:30** — Trigger the BPMN process: RPA robot harvests org data → Maestro fires
3. **1:30–3:00** — LangGraph pipeline runs: GraphRAG retrieval → DRL optimization → Groq LLM generation → self-correction loop
4. **3:00–4:00** — Human review task: Domain SME approves roadmap in UiPath Task Portal
5. **4:00–4:30** — Jira export: Epics and Stories created automatically on approval
6. **4:30–5:00** — Orchestrator audit trail and process monitoring dashboard

---

## License

MIT

---

## Hackathon Submission Notes

- **Track:** Track 2 — UiPath Maestro BPMN
- **UiPath as orchestration layer:** Yes — all process flow, human tasks, and audit governance run through UiPath Automation Cloud
- **External frameworks:** LangGraph (agentic pipeline), LangChain (GraphRAG), PyTorch (DRL)
- **Coding agent used:** Cursor + Groq OpenCode CLI (free alternatives to Claude Code)
- **Original project:** AMD Developer Hackathon 2026 submission, substantially extended with UiPath orchestration layer, human-in-the-loop review, and multi-provider LLM routing