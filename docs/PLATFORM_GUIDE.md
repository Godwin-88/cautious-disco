# AMD EA Strategy Optimizer — Platform Guide

> **AMD Developer Hackathon 2026 · Track 1 — AI Agents & Agentic Workflows**

---

## Table of Contents

1. [Platform Overview](#1-platform-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Tab-by-Tab Walkthrough](#3-tab-by-tab-walkthrough)
4. [Architecture Deep-Dive](#4-architecture-deep-dive)
5. [Integration Guide](#5-integration-guide)
6. [AMD Technology Story](#6-amd-technology-story)
7. [Deployment & Configuration](#7-deployment--configuration)
8. [Hackathon Talking Points](#8-hackathon-talking-points)

---

## 1. Platform Overview

The **AMD EA Strategy Optimizer** is an AI-powered Enterprise Architecture platform that transforms business goals into governance-grounded, Jira-ready strategic roadmaps. It combines:

| Component | Technology |
|-----------|-----------|
| LLM Inference | Qwen/Qwen2.5-72B-Instruct on **AMD Instinct MI300X** via vLLM |
| Knowledge Graph | Neo4j Aura — 44 Domains, 248 SubDomains, **1,416 Capabilities** |
| AI Prioritisation | Deep Reinforcement Learning (REINFORCE policy gradient, PyTorch) |
| Orchestration | LangGraph StateGraph — 4-node agentic pipeline |
| Frontend | Streamlit with Plotly visualisations |
| Backend | FastAPI with async endpoints + SSE streaming |

### Key Numbers

- **1,416** enterprise capabilities across **44** domains and **248** sub-domains
- **20+** governance standards and compliance frameworks
- **200+** digital transformation trends
- **3-phase** self-correcting roadmap generation with compliance verification
- **7-tab** platform interface covering advisory, exploration, roadmapping, and delivery

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Streamlit Frontend (7 Tabs)                          │
│  EA Advisor │ Graph Explorer │ Strategic Roadmap │ Initiatives │ Integrations│
└──────────────────────────┬──────────────────────────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────▼──────────────────────────────────────────────────┐
│                          FastAPI Backend                                     │
│                                                                              │
│  /api/v1/chat  │  /api/v1/analyze  │  /api/v1/integrations  │  /api/v1/graph│
└──────┬─────────────────────┬────────────────────────────────────────────────┘
       │                     │
       │          ┌──────────▼──────────────────────────────────────────────┐
       │          │     LangGraph Agentic Pipeline                           │
       │          │                                                          │
       │          │  ┌──────────┐   ┌──────────┐   ┌──────────┐            │
       │          │  │ Retrieve │──▶│ Optimize │──▶│ Generate │            │
       │          │  └──────────┘   └──────────┘   └──────────┘            │
       │          │       │              │                │                  │
       │          │   [Neo4j RAG]   [DRL Policy]   [Qwen-72B LLM]          │
       │          │                                       │                  │
       │          │                               ┌──────────┐              │
       │          │                               │  Verify  │◀─────────────│
       │          │                               └──────────┘   Regenerate │
       │          │                                    │          if score<70│
       │          │                               [Compliance                │
       │          │                                Check Loop]               │
       │          └─────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────────────────┐
│                        AMD Instinct MI300X                                   │
│                vLLM serving Qwen2.5-72B-Instruct (134.199.197.181:8000)     │
│                SSE streaming · OpenAI-compatible API                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Neo4j Aura (Knowledge Graph)                         │
│                                                                              │
│  (:Domain) ──[:PARENT_OF]──▶ (:SubDomain) ──[:PARENT_OF]──▶ (:Capability)  │
│      │                                                            │          │
│      └──[:ENABLES]──▶ (:Domain)         (:Capability) ──[:GOVERNED_BY]──▶  │
│      └──[:HAS_SECTOR]──▶ (:Domain)              (:Standard)                 │
│                              (:Capability) ──[:ALIGNED_WITH]──▶ (:Trend)   │
│                              (:GeneratedOutput) — cached roadmaps            │
│                              (:ExternalSystem) — ingested ERP/CRM data      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Tab-by-Tab Walkthrough

### Tab 1 — EA Advisor

The primary landing tab. A streaming conversational interface powered by **AMD MI300X + Qwen-72B + Knowledge Graph RAG**.

**What it does:**
- Accepts natural language questions about enterprise architecture, governance standards, or capabilities
- Performs semantic retrieval over the knowledge graph to ground responses in real data
- Streams answers token-by-token direct from the AMD GPU
- Cites specific capabilities, standards, and trends from the knowledge graph
- Suggests switching to the Strategic Roadmap tab for roadmap-oriented queries

**How it works:**
1. User message → intent classification (roadmap / explore / general QA)
2. RetrieverAgent fetches top-6 enriched capabilities from Neo4j
3. Graph context prepended to conversation history
4. `LLMClient.chat_stream()` → SSE stream → `st.write_stream()`
5. Final SSE event delivers source citations stored in session state

**Tech:** SSE streaming via FastAPI `StreamingResponse`, Streamlit `st.write_stream()`, RAG from Neo4j

---

### Tab 2 — Graph Explorer

Interactive force-directed network visualisation of the **44 enterprise domains** and their relationships.

**What it shows:**
- **Nodes:** 44 domains, coloured by sector, sized by DRL training status (larger = DRL trained)
- **Edges:** ENABLES (blue), ORCHESTRATES (orange), HAS_SECTOR (green) relationships
- **Hover:** Domain name, sector, DRL training status, node ID
- **Domain Detail Panel:** Select any domain to drill into its capability areas

**How it works:**
- `GET /api/v1/graph/network` returns `{nodes, edges}` from Neo4j
- `networkx.spring_layout(seed=42, k=2.5)` computes force-directed positions
- Plotly `go.Scatter` renders nodes and edge traces on dark background
- Sub-domain detail loaded on-demand via `GET /api/v1/subdomains`

**Tech:** networkx, Plotly graph_objects, Neo4j Cypher (`GET_NETWORK_GRAPH`)

---

### Tab 3 — Strategic Roadmap

**The core feature.** Hierarchical questionnaire → agentic pipeline → phased roadmap.

**Questionnaire (4 steps):**
1. **Domain Selection:** Choose from 44 enterprise domains (friendly labels)
2. **Capability Areas:** Multi-select sub-domains filtered to selected domains
3. **Strategic Capabilities:** Individual capabilities with complexity indicators
4. **Constraints:** Org type, budget tier, timeline, risk tolerance, goals

**Roadmap Output:**
- 3 phases: Foundation & Governance → Core Capabilities → Advanced Transformation
- Each phase contains **Epics → Features → User Stories → Tasks**
- Gantt chart timeline, compliance score gauge, AMD metrics panel
- DRL trace showing AI prioritisation scores

**Agentic Pipeline:**
```
Retrieve → Optimize (DRL) → Generate (Qwen-72B) → Verify → [Regenerate if score < 70]
```

**3-tier Retrieval Cascade:**
1. Exact capability IDs from questionnaire
2. Domain names with keyword expansion
3. Semantic vector similarity fallback

**Caching:** MD5(sorted capability IDs + org_type) → `:GeneratedOutput` node in Neo4j. Cache hits skip the entire pipeline and return in <100ms.

---

### Tab 4 — Initiatives & Scenarios

Deep-dive into the Epics generated by the pipeline.

**What it shows:**
- Expandable Epic cards with governance references and trend alignment
- Features (workstreams) within each Epic
- User Stories with role / want / so-that format and acceptance criteria
- Delivery Tasks with estimated days and assignee role
- Compliance badges on acceptance criteria

---

### Tab 5 — Integrations

Three inner sections: ITSM Connector, ERP/CRM Ingest, ArchiMate View.

See [Integration Guide](#5-integration-guide) below for full details.

---

### Tab 6 — Export & Handover

Export the generated roadmap to multiple formats:
- JSON (full structured output)
- Markdown report
- CSV summary

---

### Tab 7 — AI Learning Engine

DRL training dashboard showing:
- Training runs per domain (episodes, rewards, policy improvement)
- Coverage heatmap: which of the 44 domains have been DRL-trained
- Trigger ad-hoc training runs
- Policy network architecture details (20-dim state, 10-dim action, 3-layer MLP)

---

## 4. Architecture Deep-Dive

### LangGraph Pipeline

The pipeline is a directed StateGraph with conditional regeneration:

```python
retrieve → optimize → generate → verify
                                    │
                         score < 70 │ iteration < 2
                                    ↓
                                generate (retry)
```

**AgentState** carries: request, enriched capabilities, graph context, priority result, roadmap draft, compliance summary, final roadmap, iteration count, timing per node.

### DRL Policy Network

**EAPolicyNetwork** — 3-layer MLP:
```
Linear(20→128) → ReLU → Dropout(0.1) →
Linear(128→128) → ReLU → Dropout(0.1) →
Linear(128→64) → ReLU → Linear(64→10) → LogSoftmax
```

- **State vector (20-dim):** budget tier, timeline, risk tolerance, domain distribution, complexity distribution, trend alignment scores
- **Action space (10 slots):** ranked capability priority ordering
- **Training:** REINFORCE with Gumbel-top-k sampling (sample without replacement)
- **Reward:** composite of complexity alignment + budget feasibility + domain coverage

DRL runs on AMD ROCm (GPU) if available, otherwise CPU. LLM inference always runs on remote AMD MI300X via vLLM.

### Neo4j Graph Schema

```
(:Domain {id, name, sector, drl_trained})
  -[:PARENT_OF]→ (:SubDomain {id, name, functional_scope, business_driver})
    -[:PARENT_OF]→ (:Capability {
        id, name, description, implementation_complexity,
        typical_duration_weeks, business_outcomes[], kpis[],
        risk_factors[], common_frameworks[], technical_requirements[]
    })
      -[:GOVERNED_BY]→ (:Standard {
          id, name, publisher, version,
          compliance_requirements[], key_principles[]
      })
      -[:ALIGNED_WITH]→ (:Trend {
          id, name, source, business_impact,
          technology_enablers[]
      })
      -[:HAS_SUBCAPABILITY]→ (:Capability)  ← sub-capabilities

(:GeneratedOutput {cache_key, org_type, output_json, hit_count, last_accessed})
(:ExternalSystem {name, vendor, business_unit})
  -[:SUPPORTS]→ (:Capability)

(:TrainingRun {domain_id, episodes, avg_reward, timestamp})
```

### Retrieval Cascade

```
Tier 1: GET_CAPABILITIES_BY_IDS
  └─ exact match on selected_capability_ids from questionnaire

Tier 2: GET_ENRICHED_CAPABILITIES_BY_DOMAIN_NAMES
  └─ match domain names → strip "Manage " / " Core Operations" prefixes
  └─ keyword fallback via GET_DOMAINS_BY_KEYWORD

Tier 3: Semantic vector similarity (LLM query expansion → cosine search)
  └─ GET_CAPABILITIES_BROAD
```

### Output Caching

```python
cache_key = MD5("|".join(sorted(capability_ids)) + "|" + org_type)[:16]

# On hit: MATCH (o:GeneratedOutput {cache_key}) RETURN o.output_json
# On store: MERGE (:GeneratedOutput {cache_key}) SET o.output_json = $json, ...
```

Full `AnalyzeResponse` serialized with `model_dump_json()`, deserialized with `model_validate_json()`. Cache hits bypass the entire agentic pipeline.

### SSE Streaming

```
FastAPI GET /api/v1/chat/stream
  → async generator → StreamingResponse(media_type="text/event-stream")
  → each token: data: {"text": "..."}\n\n
  → final event: data: {"sources": [...], "done": true}\n\n

Streamlit stream_chat() generator
  → requests.get(..., stream=True)
  → parse SSE data: lines → yield text chunks
  → on done event → write sources to st.session_state["_last_chat_sources"]
  → st.write_stream(stream_chat(...)) renders tokens as they arrive
```

---

## 5. Integration Guide

### Jira Cloud (Live)

The platform uses Jira REST API v3 to create Epics and Stories directly in your project.

**Setup:**
1. Generate an API token at [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Enter your Jira Cloud URL (e.g., `https://yourorg.atlassian.net`)
3. Enter your email and API token in the Integrations → ITSM Connector tab
4. Enter your project key (e.g., `EAOPT`)
5. Generate a roadmap first, then click **Export Roadmap to Jira**

**What gets created:**
- One **Epic** per roadmap initiative (with description, acceptance criteria)
- One **Story** per Feature within each Epic (linked to parent Epic)
- Returns counts: `{created_epics, created_stories, errors}`

**API used:** `POST /rest/api/3/issue` with Basic Auth `(email, api_token)`

---

### ServiceNow (Mock)

The ServiceNow integration demonstrates the integration pattern with sample work items. No real HTTP call is made — the mock returns a structured preview of what would be synced:

```json
{
  "status": "connected",
  "tool": "servicenow",
  "sample_work_items": [
    {"sys_id": "001", "number": "CHG001", "type": "change_request", "state": "ready"},
    {"sys_id": "002", "number": "CHG002", "type": "change_request", "state": "assess"}
  ]
}
```

---

### Azure DevOps (Mock)

Similarly mocked — demonstrates the work item structure that would be pushed to Azure Boards:

```json
{
  "status": "connected",
  "tool": "azure_devops",
  "sample_work_items": [
    {"id": 1001, "type": "Feature", "title": "Data Governance Foundation", "state": "New"},
    {"id": 1002, "type": "Feature", "title": "API Management Platform", "state": "Active"}
  ]
}
```

---

### ERP / CRM Data Ingest

Upload a CSV with your organisation's existing system inventory. The platform links each system to matching capabilities in the knowledge graph.

**CSV Format:**

| Column | Description |
|--------|-------------|
| `org_type` | Organisation type (e.g., "Enterprise Bank") |
| `business_unit` | Department (e.g., "Finance", "HR") |
| `system_name` | System name (e.g., "SAP S/4HANA") |
| `vendor` | Vendor name |
| `capabilities_in_use` | Comma-separated list of capability names |
| `annual_budget_usd` | Annual spend (integer) |

**What happens on ingest:**
1. CSV parsed row by row
2. `MERGE (:ExternalSystem {name: system_name})` in Neo4j
3. Each `capabilities_in_use` entry matched against `(:Capability)` nodes by name
4. `MERGE (es)-[:SUPPORTS]->(c)` links system to capability
5. Returns: `{rows_ingested, systems_found, capabilities_linked}`

Download the sample CSV template from the Integrations tab.

---

### ArchiMate Layer View

Capabilities are automatically classified into three ArchiMate 3.1 architecture layers based on their properties:

| Layer | Classification Logic |
|-------|---------------------|
| **Technology** | Name or `technical_requirements` contains: infrastructure, cloud, network, security, hardware, server, storage, platform infrastructure |
| **Business** | Name or `business_outcomes` contains: governance, management, service, process, compliance, risk, audit, reporting, analytics, strategy |
| **Application** | Everything else (default: software, data, API, integration, application capabilities) |

Data sourced from `GET_ARCHIMATE_CAPABILITIES` — up to 500 capabilities with domain, sub-domain, complexity, frameworks, and business outcomes.

---

## 6. AMD Technology Story

### AMD Instinct MI300X

The platform's LLM inference runs on **AMD Instinct MI300X** — the world's highest-memory AI accelerator:

- **192 GB HBM3** unified CPU+GPU memory — critical for 72B parameter models
- **5.2 TB/s** peak memory bandwidth
- Running **Qwen2.5-72B-Instruct** via vLLM at `134.199.197.181:8000`
- OpenAI-compatible API with SSE streaming
- vLLM metrics endpoint queried on startup to confirm GPU health and ROCm version

### ROCm + PyTorch DRL

The DRL policy network uses PyTorch with ROCm support:

```python
# get_device() in backend/drl/policy_network.py
rocm_version = getattr(torch.version, "hip", None)  # HIP = ROCm
if torch.cuda.is_available():
    return torch.device("cuda:0")  # ROCm exposes as "cuda"
```

DRL training (`pipeline/seed_graph_cache.py`) runs all 44 domains through 200 episodes each, storing `TrainingRun` nodes in Neo4j.

### Performance Characteristics

| Operation | Typical Latency |
|-----------|----------------|
| Cache hit (Neo4j lookup) | < 100ms |
| Graph retrieval (Neo4j Cypher) | 200–800ms |
| DRL prioritisation | < 50ms (CPU/GPU) |
| LLM generation (Qwen-72B, MI300X) | 8–25 seconds |
| Full pipeline (3 phases, no cache) | 30–90 seconds |
| SSE first token latency | ~1–2 seconds |

### Why AMD MI300X for Enterprise AI

- **Large context windows** — 72B model fits in single GPU due to 192GB HBM3
- **Batch efficiency** — vLLM continuous batching maximises MI300X throughput
- **Enterprise-grade reliability** — validated for production workloads
- **ROCm open ecosystem** — no vendor lock-in, full PyTorch compatibility

---

## 7. Deployment & Configuration

### Environment Variables

```bash
# Backend
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
VLLM_BASE_URL=http://134.199.197.181:8000/v1
VLLM_MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
DRL_CHECKPOINT_PATH=backend/drl/checkpoints/policy.pt

# Frontend
BACKEND_URL=http://localhost:8080
```

### Running the Platform

```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install networkx httpx

# 2. Start the backend
uvicorn backend.main:app --host 0.0.0.0 --port 8080

# 3. Start the frontend (separate terminal)
streamlit run frontend/app.py --server.port 8501

# 4. (Optional) Seed DRL training and output cache
python -m pipeline.seed_graph_cache --episodes 200
```

### Running DRL Pre-training

```bash
# Train all 44 domains, 200 episodes each
python -m pipeline.seed_graph_cache --episodes 200

# Train a specific domain only
python -m pipeline.seed_graph_cache --domains "Banking & Finance" --episodes 100

# Skip training, seed cache only
python -m pipeline.seed_graph_cache --skip-training

# Seed cache for specific org type
python -m pipeline.seed_graph_cache --org "NHS Trust" --skip-training
```

---

## 8. Hackathon Talking Points

### Opening Statement

> "We've built a production-ready Enterprise Architecture platform that turns a 10-minute questionnaire into a governance-grounded, Jira-ready strategic roadmap — powered by AMD MI300X, a 1,416-capability knowledge graph, and a Deep Reinforcement Learning priority engine. Let me show you."

---

### EA Advisor Tab

**Demo:** Type *"What governance frameworks apply to data management in banking?"*

> "Watch this — the question hits our RetrieverAgent, which searches 1,416 capabilities in Neo4j in real-time. The answer is generated by Qwen-72B running on our AMD MI300X with 192GB HBM3 memory. You're seeing tokens stream directly from the GPU. Try asking it anything about enterprise architecture — it cites specific standards, capabilities, and transformation trends."

**Talking point:** Real-time knowledge-grounded AI advisory, not a chatbot with static answers. Every response is grounded in live graph data.

---

### Graph Explorer Tab

**Demo:** Show the 44-domain force-directed network, hover over nodes, click on Banking & Finance.

> "This is the live knowledge graph — 44 enterprise domains, their ENABLES and ORCHESTRATES relationships, all computed with networkx spring layout from live Neo4j data. Nodes sized by DRL training status — larger nodes have been trained by our reinforcement learning engine. Click Banking & Finance to see its 12 capability areas. This is Ardoq-style graph intelligence, backed by a real knowledge graph."

**Talking point:** Visual knowledge graph exploration — judges can see the AI's knowledge base, not just its outputs.

---

### Strategic Roadmap Tab

**Demo:** Select Airport + Capital Markets domains as a PE firm, generate roadmap.

> "I've selected an Airport domain and Capital Markets — modelling a private equity firm investing in an airport. Our three-tier retrieval cascade finds capabilities across both domains. The DRL engine prioritises them based on budget, timeline, and risk tolerance. Qwen-72B on MI300X generates a 3-phase roadmap with Epics, Features, User Stories, and Tasks. Then the compliance verifier checks it against governance standards and regenerates if the score is below 70. The whole pipeline — retrieve, prioritise, generate, verify — is orchestrated by LangGraph."

**Talking point:** Cross-domain synthesis. Not just retrieval-augmented generation — full agentic pipeline with self-correction.

---

### Initiatives & Scenarios Tab

**Demo:** Expand an Epic, drill into a Feature's User Stories and Tasks.

> "Every Epic is Jira-ready. Acceptance criteria come verbatim from governance standards like TOGAF, COBIT, ISO 27001. KPIs are extracted from the knowledge graph. Tasks have estimated days and assignee roles. This isn't a demo output — it's a real deliverable a CIO could hand to their architecture team tomorrow."

**Talking point:** Depth of output. Other platforms stop at Epics — we go to Tasks with assignee roles and governance-grounded acceptance criteria.

---

### Integrations Tab — Jira

**Demo:** Enter Jira credentials, click Export, show Epics appearing in Jira.

> "One click. Our roadmap is now 6 Jira Epics and 18 Stories in your project. Live API call to Jira Cloud v3. The governance acceptance criteria are acceptance criteria in Jira. The KPI targets are story acceptance criteria. An enterprise architect could run this on Monday morning and have their sprint board populated by 9 AM."

**Talking point:** Not a prototype — live Jira integration, real enterprise delivery artifact.

---

### Integrations Tab — ArchiMate

**Demo:** Open ArchiMate View, switch between Business / Application / Technology layers.

> "We automatically classify all 1,416 capabilities into ArchiMate 3.1 layers — Business, Application, Technology — using the capability metadata from the knowledge graph. A Chief Architect can use this view to understand where their organisation's capabilities sit in the architecture stack. Standard EA notation, live data."

**Talking point:** Standards compliance. ArchiMate is the industry standard for EA modelling — we implement it automatically from graph data.

---

### AI Learning Engine Tab

**Demo:** Show training coverage heatmap, trigger a training run.

> "The DRL engine hasn't just been trained once — it's been trained 200 episodes per domain across all 44 domains. You can see the reward curves, the domains covered, and trigger a new training run. As the knowledge graph grows, the DRL engine learns better prioritisation strategies. This is self-improving enterprise AI."

**Talking point:** Continuous learning. The AI gets smarter as the organisation's knowledge graph grows.

---

### Closing Statement

> "To summarise: AMD MI300X powers real-time 72B model inference for both advisory and roadmap generation. ROCm PyTorch trains our DRL prioritisation engine. Neo4j gives us 1,416 grounded capabilities. LangGraph orchestrates a self-correcting agentic pipeline. And the output is a Jira-ready strategic roadmap with governance compliance built in. This is what enterprise AI looks like in production."

---

## Appendix: API Reference

### Chat

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/chat` | POST | Non-streaming chat with RAG |
| `/api/v1/chat/stream` | GET | SSE streaming chat with RAG |

### Roadmap

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/analyze` | POST | Full agentic pipeline — returns `AnalyzeResponse` |
| `/api/v1/domains` | GET | All 44 domains |
| `/api/v1/subdomains` | GET | SubDomains filtered by domain names |
| `/api/v1/subdomain-capabilities` | GET | Capabilities filtered by subdomain IDs |

### Graph

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/graph/network` | GET | `{nodes, edges}` for Graph Explorer |
| `/api/v1/graph/stats` | GET | Node/relationship counts |

### Integrations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/integrations/jira/export` | POST | Live Jira Epic/Story creation |
| `/api/v1/integrations/itsm/connect` | POST | Mock ITSM connection test |
| `/api/v1/integrations/erp/ingest` | POST | CSV upload → ExternalSystem nodes |
| `/api/v1/integrations/archimate` | GET | Capabilities by ArchiMate layer |

### Training

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/training/metrics` | GET | Training runs from Neo4j |
| `/api/v1/training/coverage` | GET | DRL coverage per domain |
| `/api/v1/training/run` | POST | Trigger a training run |

---

*AMD EA Strategy Optimizer · AMD Developer Hackathon 2026 · Built with AMD MI300X, ROCm, Qwen-72B, LangGraph, Neo4j*
