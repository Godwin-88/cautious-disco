# UiPath Maestro BPMN Integration Plan

## Goal
Transform the existing AMD EA Optimizer into a UiPath AgentHack 2026 submission with Maestro BPMN orchestration, human-in-the-loop review, and multi-provider LLM routing.

## Current State (Verified)
- Next.js 16 frontend with 7 tabs running on port 3000
- FastAPI backend on port 8080
- Neo4j database seeded with 4,386 nodes (44 domains, 1,295 capabilities)
- LLM client uses vLLM + fallback (AMD MI300X primary)
- LangGraph pipeline: retriever → optimizer → generator → verifier

## Missing / Required Changes

### 1. LLM Provider Multi-Provider Routing (High Priority)
**File:** `backend/config.py`, `backend/llm/client.py`

**Current:** vLLM primary + single fallback  
**Target:** Groq → Gemini → OpenRouter fallback chain per specs

**Tasks:**
- Add `groq_api_key`, `groq_model`, `groq_base_url` settings
- Add `gemini_api_key`, `gemini_model` settings  
- Add `openrouter_api_key`, `openrouter_model` settings
- Refactor `LLMClient.__init__` to build provider list dynamically
- Add `/api/v1/analyze` endpoint mode parameter support (graphrag, maturity_baseline, drl_prioritise, generate_recommendation, regenerate)

### 2. Human Task Portal Tab (High Priority)
**File:** `frontend/components/human-task-portal.tsx` (new)

**Features needed:**
- Task inbox: fetch pending UiPath human tasks
- Assessment detail view: gap analysis, maturity scores, DRL ranking, roadmap
- Decision panel: Approve / Override / Reject / Escalate buttons
- Override editor: inline score editing with mandatory comment
- POST to `/api/v1/uipath/task-complete`

### 3. UiPath Bridge Endpoints (Medium Priority)
**File:** `backend/api/routes_uipath.py` (new)

**Endpoints:**
- `POST /api/v1/uipath/task-complete` - receive human task decisions
- `GET /api/v1/uipath/process-status/{assessment_id}` - live process status
- `POST /api/v1/generate-report` - PDF executive report generation

### 4. ENABLES Cross-Domain Visualization (Medium Priority)
**File:** `frontend/components/graph-explorer-tab.tsx`

**Current:** Shows only HAS_SECTOR edges  
**Target:** Show ENABLES relationships as force-directed network graph per spec section 5.1.3

### 5. Assessment Dashboard (Medium Priority)
**File:** Add new tab or enhance Graph Explorer

**Features:**
- Assessment run tracker (per spec section 4.2.1)
- BPMN process status integration
- Historical assessment comparison

### 6. Environment Configuration (.env.example)
Update to include UiPath and multi-provider LLM variables:
```
GROQ_API_KEY=gsk_xxx
GEMINI_API_KEY=AIzaSy_xxx
OPENROUTER_API_KEY=sk-or-xxx
UIPATH_TENANT=
UIPATH_CLIENT_ID=
UIPATH_CLIENT_SECRET=
UIPATH_ORCHESTRATOR_URL=
```

## Implementation Order

| Priority | Task | Complexity |
|----------|------|------------|
| 1 | LLM client multi-provider refactoring | Medium |
| 2 | Human Task Portal tab component | High |
| 3 | UiPath bridge API endpoints | Medium |
| 4 | ENABLES visualization in Graph Explorer | Medium |
| 5 | Report generation endpoint | Medium |
| 6 | Assessment dashboard | Medium |

## Risks & Decisions

**LLM Provider Migration:** Remove all vendor-specific branding (AMD MI300X/Qwen-72B/Groq). Use generic "AI" language throughout.

**Human Task Authentication:** Implement full UiPath Identity Server OAuth2 integration with token-based auth for Orchestrator API.

## Validation Points
- [ ] LLM fallback chain works (Groq → Gemini → OpenRouter)
- [ ] Human task portal renders and accepts decisions
- [ ] Process status endpoint returns valid state
- [ ] ENABLES graph shows cross-domain dependencies
- [ ] Report generation produces PDF output

## Out of Scope (per spec docs)
- UiPath RPA robots (DataIngestionRobot.xaml) - mock only in UI
- Actual BPMN file deployment (capability_assessment.bpmn) - handled by UiPath
- BPMN.js frontend component - redundant with UiPath Task Portal
- Audit trail persistence in Orchestrator - rely on existing Neo4j caching

## Decisions Confirmed
- LLM branding: Generic "AI" (no vendor lock-in)
- Human Task auth: Full UiPath Identity Server OAuth2
- Database seed: capability_canvas (3).cypher has ENABLES relationships (123 edges)

## Stretch Goals (Optional)
- Natural language → BPMN process generation endpoint
- BPMN.js viewer for process visualization in frontend
- Process template library for common assessment workflows