# BPMN Process Specification
## Capability Assessment & Investment Prioritisation
### UiPath Maestro BPMN — Process Design Document

---

**Process ID:** `capability-assessment-v1`
**BPMN Version:** 2.0
**UiPath Maestro Version:** Automation Cloud (latest)
**File:** `uipath/capability_assessment.bpmn`

---

## 1. Process Overview

This document specifies the UiPath Maestro BPMN process that orchestrates the full capability assessment workflow — from data ingestion through AI analysis, human review, and Jira export.

**Your existing FastAPI app runs as the intelligence engine behind service tasks. UiPath Maestro is the shell that governs the flow, handles humans, and provides the audit trail.**

### Process Trigger

The process starts via:
- API call to UiPath Orchestrator (`POST /odata/Jobs` with process name)
- Scheduled trigger (configurable, e.g. quarterly)
- Manual trigger from Orchestrator UI

**Input payload:**
```json
{
  "assessment_id": "uuid",
  "organisation_name": "string",
  "organisation_type": "string",
  "requestor_email": "string",
  "data_sources": ["itsm", "erp", "sharepoint"]
}
```

---

## 2. Process Flow Diagram (Text Representation)

```
[Start Event: Assessment Request Received]
         │
         ▼
[Task 1: Data Ingestion] ──────────────────── Lane: UiPath RPA Robot
   RPA Robot harvests org capability data
   from ITSM / ERP / SharePoint
   Output: organisation_profile.json
         │
         ▼
[Gateway 1: Data Quality Check] ───────────── Lane: System
   Is data quality score ≥ threshold (0.7)?
   │                    │
  YES                   NO
   │                    │
   │         [Task 1b: Human Data Review] ─── Lane: Data Engineer
   │         Reviewer fixes/supplements data
   │                    │
   └──────────────┬─────┘
                  ▼
[Parallel Split Gateway] ──────────────────── Lane: System
   Fire both branches simultaneously
   │                              │
   ▼                              ▼
[Task 2a: GraphRAG Analysis]   [Task 2b: Baseline Maturity Scoring]
   POST /api/v1/analyze            POST /api/v1/analyze
   mode=graphrag                   mode=maturity_baseline
   Output: gap_analysis.json       Output: maturity_scores.json
   Lane: AI Agent                  Lane: AI Agent
   │                              │
   └──────────────┬───────────────┘
                  ▼
[Parallel Merge Gateway] ──────────────────── Lane: System
   Wait for both branches
                  │
                  ▼
[Task 3: DRL Investment Prioritisation] ────── Lane: AI Agent
   POST /api/v1/analyze
   mode=drl_prioritise
   Input: gap_analysis + maturity_scores
   Output: priority_ranking.json
                  │
                  ▼
[Task 4: Recommendation Generation] ─────────── Lane: AI Agent
   POST /api/v1/analyze
   mode=generate_recommendation
   Input: gap_analysis + maturity_scores + priority_ranking
   Output: roadmap.json, compliance_score (0-100)
                  │
                  ▼
[Gateway 2: Compliance Score Check] ─────────── Lane: System
   Is compliance_score ≥ 70?
   │                    │
  YES                   NO (max 2 retries)
   │                    │
   │         [Task 4b: Regenerate with Issues]
   │         POST /api/v1/analyze
   │         mode=regenerate, issues=<verifier_output>
   │                    │
   └──────────────┬─────┘
                  ▼
[Gateway 3: Auto-Approve or Human Review?] ──── Lane: System
   Is compliance_score ≥ 90 AND risk_flag = false?
   │                    │
  YES                   NO
   │                    │
   │         [Task 5: Human Review Task] ─────── Lane: Domain SME
   │         UiPath Human Task assigned to SME
   │         Shows: roadmap, gap analysis, scores
   │         Decision: Approve / Override / Reject / Escalate
   │                    │
   │         [Gateway 4: Review Decision]
   │           │          │         │
   │        APPROVE    OVERRIDE   REJECT
   │           │          │         │
   │           │    [Task 5b: Apply │
   │           │    Override &      │
   │           │    Re-validate]    │
   │           │          │         │
   │           └────┬─────┘         │
   │                │               ▼
   │                │      [End Event: Assessment Rejected]
   │                │      Notify requestor, archive
   └──────────┬─────┘
              ▼
[Task 6: Jira Export] ──────────────────────── Lane: Integration Robot
   POST /api/v1/integrations/jira/export
   Creates: Epics (strategic initiatives)
            Stories (feature workstreams)
            Acceptance criteria from governance model
              │
              ▼
[Task 7: Report Generation] ────────────────── Lane: AI Agent
   POST /api/v1/generate-report
   Output: executive_report.pdf
   Stored in: UiPath Orchestrator Storage Bucket
   Emailed to: requestor + stakeholders
              │
              ▼
[Task 8: Audit Close] ──────────────────────── Lane: System
   Write final audit record to Orchestrator
   Fields: assessment_id, start_time, end_time,
           all task outcomes, human decisions,
           llm_provider_used, jira_tickets_created
              │
              ▼
[End Event: Assessment Complete]
   Notify requestor with report link
```

---

## 3. Lanes

| Lane | Actor | UiPath Component |
|---|---|---|
| System | Automated gateway logic | Maestro BPMN engine |
| UiPath RPA Robot | Data harvesting bot | UiPath Studio robot published to Orchestrator |
| AI Agent | LangGraph pipeline | UiPath API Workflow → FastAPI backend |
| Domain SME | Human reviewer | UiPath Human Tasks (Task Portal) |
| Integration Robot | Jira/export automation | UiPath Studio robot or API Workflow |
| Data Engineer | Data quality reviewer | UiPath Human Tasks |

---

## 4. Task Specifications

### Task 1: Data Ingestion

**Type:** UiPath RPA Task
**Actor:** DataIngestionRobot (published to Orchestrator)
**File:** `uipath/robots/DataIngestionRobot.xaml`

**What it does:**
- Connects to configured ITSM (ServiceNow), ERP (SAP), and SharePoint
- Extracts capability evidence records mapped to canvas Capability IDs
- Computes data quality score (completeness × timeliness × source coverage)
- Outputs `organisation_profile.json` to Orchestrator Storage Bucket

**Input variables from Maestro:**
```
assessment_id (string)
organisation_name (string)
data_sources (array of strings)
```

**Output variables to Maestro:**
```
profile_bucket_path (string)   — path in Orchestrator storage
data_quality_score (float)     — 0.0 to 1.0
records_extracted (integer)
extraction_errors (array)
```

**Error handling:**
- Retry up to 3 times on transient failures
- After 3 failures → boundary error event → escalate to Data Engineer human task
- Timeout: 10 minutes

---

### Task 2a: GraphRAG Analysis

**Type:** UiPath API Workflow (Service Task)
**File:** `uipath/api_workflows/analyze_trigger.json`
**Endpoint called:** `POST /api/v1/analyze`

**Request body:**
```json
{
  "assessment_id": "{{assessment_id}}",
  "profile_path": "{{profile_bucket_path}}",
  "mode": "graphrag",
  "org_type": "{{organisation_type}}"
}
```

**What your existing LangGraph pipeline does (unchanged):**
1. Retrieve: 3-tier cascade (exact capability IDs → domain expansion → semantic vector)
2. Optimize: DRL/MLP prioritisation (REINFORCE policy gradient)
3. Generate: Groq Llama 3.3 70B → roadmap with governance criteria
4. Verify: compliance score; regenerate if < 70

**Response mapped to Maestro output variables:**
```json
{
  "gap_analysis": {...},
  "capabilities_retrieved": [...],
  "domains_covered": [...],
  "compliance_score": 85,
  "cache_hit": false
}
```

**Timeout:** 120 seconds
**Error handling:** Boundary event → exception sub-process → notify admin

---

### Task 2b: Baseline Maturity Scoring

**Type:** UiPath API Workflow (Service Task)
**Endpoint called:** `POST /api/v1/analyze`

**Request body:**
```json
{
  "assessment_id": "{{assessment_id}}",
  "profile_path": "{{profile_bucket_path}}",
  "mode": "maturity_baseline"
}
```

**What it does:** Scores each capability in the org profile on a 0–5 maturity scale using the weighted model (implementation depth 40%, integration breadth 30%, uptime 20%, governance 10%).

**Runs in parallel with Task 2a** (parallel gateway).

---

### Task 3: DRL Investment Prioritisation

**Type:** UiPath API Workflow (Service Task)
**Endpoint called:** `POST /api/v1/analyze`

**Request body:**
```json
{
  "assessment_id": "{{assessment_id}}",
  "gap_analysis": "{{gap_analysis}}",
  "maturity_scores": "{{maturity_scores}}",
  "mode": "drl_prioritise"
}
```

**What it does:** Your existing REINFORCE DRL policy network scores each gap by strategic value × dependency multiplier / implementation risk. Returns a ranked investment backlog.

---

### Task 4: Recommendation Generation

**Type:** UiPath API Workflow (Service Task)
**Endpoint called:** `POST /api/v1/analyze`

**Request body:**
```json
{
  "assessment_id": "{{assessment_id}}",
  "gap_analysis": "{{gap_analysis}}",
  "maturity_scores": "{{maturity_scores}}",
  "priority_ranking": "{{priority_ranking}}",
  "mode": "generate_recommendation"
}
```

**What it does:** Groq Llama 3.3 70B generates the full strategic roadmap with Epics, Features, User Stories, and governance acceptance criteria. Self-correcting loop runs if compliance score < 70.

**Output variables:**
```
roadmap_json (string/JSON)
compliance_score (integer, 0-100)
regeneration_count (integer)
llm_provider_used (string)   — groq / gemini / openrouter
```

---

### Task 5: Human Review Task (NEW — key UiPath addition)

**Type:** UiPath Human Task
**Assigned to:** Domain SME role (configured in Orchestrator)
**SLA:** 48 hours (configurable)
**Portal:** UiPath Task Portal (or custom `frontend/components/human_task_portal.py`)

**What the SME sees:**
- Capability gap analysis by domain (from Task 2a)
- Maturity scores per capability (from Task 2b)
- DRL priority ranking (from Task 3)
- Generated roadmap with Epics and Features (from Task 4)
- Compliance score and any verifier issues
- Link to Graph Explorer for deep-dive

**Decision options:**

| Decision | Code | Next Step |
|---|---|---|
| Approve | `APPROVED` | Proceed to Jira Export |
| Approve with comments | `APPROVED_WITH_COMMENTS` | Proceed, comments appended to report |
| Override score(s) | `OVERRIDE` | Apply changes, re-validate, proceed |
| Reject | `REJECTED` | Process ends, requestor notified |
| Escalate | `ESCALATED` | Route to Senior Reviewer (Tier 2) |

**Output variables to Maestro:**
```
review_decision (string)       — APPROVED / REJECTED / OVERRIDE / ESCALATED
reviewer_email (string)
review_timestamp (datetime)
override_details (JSON)        — only populated if OVERRIDE
review_comments (string)
```

**SLA handling:** If 48h elapses with no action → auto-escalate to process owner.

---

### Task 6: Jira Export

**Type:** UiPath API Workflow (Service Task)
**Endpoint called:** `POST /api/v1/integrations/jira/export` (your existing endpoint)

**What it does (unchanged from AMD version):**
- Creates one Jira Epic per strategic initiative
- Creates one Story per feature workstream
- Appends governance acceptance criteria to each Story

**New additions:**
- Tags each Jira item with `assessment_id` for traceability
- Stores Jira ticket IDs back in Maestro as output variables
- Adds UiPath process instance URL as a Jira comment for audit linkage

---

### Task 7: Report Generation

**Type:** UiPath API Workflow (Service Task)
**Endpoint called:** `POST /api/v1/generate-report` (new endpoint to add to FastAPI)

**What it does:**
- Compiles all assessment outputs into a PDF executive report
- Stores in Orchestrator Storage Bucket
- Sends email to requestor and configured stakeholders via UiPath notification service

---

### Task 8: Audit Close

**Type:** UiPath System Task (automatic)

**Writes to Orchestrator audit log:**
```json
{
  "assessment_id": "uuid",
  "start_time": "ISO8601",
  "end_time": "ISO8601",
  "organisation_name": "string",
  "data_quality_score": 0.85,
  "compliance_score": 87,
  "regeneration_count": 0,
  "llm_provider_used": "groq",
  "human_review_required": true,
  "reviewer_email": "sme@org.com",
  "review_decision": "APPROVED",
  "jira_tickets_created": 12,
  "report_bucket_path": "assessments/uuid/report.pdf",
  "total_cycle_time_minutes": 47
}
```

---

## 5. Gateway Specifications

### Gateway 1: Data Quality Check

**Type:** Exclusive Gateway
**Condition:** `data_quality_score >= 0.7`
- TRUE → proceed to parallel analysis tasks
- FALSE → route to human data review task

### Gateway 2: Compliance Score Check

**Type:** Exclusive Gateway (with loop)
**Condition:** `compliance_score >= 70`
- TRUE → proceed to auto-approve check
- FALSE AND `regeneration_count < 2` → re-run Task 4 with verifier issues
- FALSE AND `regeneration_count >= 2` → force proceed with warning flag

### Gateway 3: Auto-Approve or Human Review

**Type:** Exclusive Gateway
**Condition:** `compliance_score >= 90 AND risk_flag == false`
- TRUE → skip human review, proceed directly to Jira export
- FALSE → route to human review task

**Purpose:** Low-stakes, high-confidence assessments don't need human review. High-stakes or low-confidence ones always do.

### Gateway 4: Review Decision

**Type:** Exclusive Gateway
**Conditions:**
- `review_decision == "APPROVED" OR "APPROVED_WITH_COMMENTS"` → Jira export
- `review_decision == "OVERRIDE"` → apply overrides, re-validate, then Jira export
- `review_decision == "REJECTED"` → end event (rejected)
- `review_decision == "ESCALATED"` → new human task assigned to Tier 2 reviewer

---

## 6. Error Handling & Exception Sub-Processes

### Exception Sub-Process: Agent Failure

Triggered by: boundary error events on Tasks 2a, 2b, 3, 4

Steps:
1. Log error details to Orchestrator
2. Notify platform admin via email
3. If retry count < 3: retry the failed task after 30-second delay
4. If retry count >= 3: pause process, create human task for admin to investigate
5. SLA pauses during exception handling

### Exception Sub-Process: LLM Provider Failure

Triggered by: HTTP 429/503 from Groq API

Steps:
1. Switch to fallback provider (Gemini 2.5 Flash)
2. Log provider switch to audit trail
3. If Gemini also fails: switch to OpenRouter:free
4. If all providers fail: serve cached response from Neo4j (existing cache mechanism)
5. If no cache available: pause process and notify admin

---

## 7. SLA Configuration

| Task | SLA | Escalation Action |
|---|---|---|
| Task 1: Data Ingestion | 10 minutes | Notify admin, retry |
| Task 2a/2b: AI Analysis | 3 minutes each | Retry, then escalate |
| Task 3: DRL Prioritisation | 2 minutes | Retry, then escalate |
| Task 4: Recommendation | 5 minutes | Retry, then escalate |
| Task 5: Human Review | 48 hours | Auto-escalate to Tier 2 |
| Task 6: Jira Export | 5 minutes | Retry, then notify admin |
| Task 7: Report Generation | 2 minutes | Retry, then notify admin |
| **Total Process (excl. human)** | **< 20 minutes** | Admin alert |

---

## 8. Variable Passing Between Tasks

All Maestro process variables are passed between tasks as BPMN data objects:

```
assessment_id              → flows through entire process
organisation_profile       → Task 1 → Task 2a, 2b
gap_analysis               → Task 2a → Task 3, 4, 5
maturity_scores            → Task 2b → Task 3, 4, 5
priority_ranking           → Task 3 → Task 4, 5
roadmap_json               → Task 4 → Task 5, 6, 7
compliance_score           → Task 4 → Gateway 2, 3
review_decision            → Task 5 → Gateway 4
override_details           → Task 5 → Task 4 (if OVERRIDE)
jira_ticket_ids            → Task 6 → Task 7, 8
report_bucket_path         → Task 7 → Task 8, notification
```

---

## 9. New FastAPI Endpoints Required

Add these to `backend/api/` to support the UiPath bridge:

```python
# backend/api/uipath.py

@router.post("/api/v1/uipath/task-complete")
async def receive_task_completion(payload: TaskCompletionPayload):
    """
    Receives human task decisions from UiPath Orchestrator.
    Updates assessment record and signals BPMN process to continue.
    """

@router.get("/api/v1/uipath/process-status/{assessment_id}")
async def get_process_status(assessment_id: str):
    """
    Returns current BPMN process step for a given assessment.
    Used by frontend to show live progress.
    """

@router.post("/api/v1/generate-report")
async def generate_executive_report(payload: ReportPayload):
    """
    Compiles all assessment outputs into PDF executive report.
    Returns: report bytes + metadata
    """

@router.post("/api/v1/analyze")
async def analyze(payload: AnalyzePayload):
    """
    Existing endpoint — add mode parameter:
    mode: graphrag | maturity_baseline | drl_prioritise |
          generate_recommendation | regenerate
    """
```

---

## 10. LLM Provider Routing in backend/llm/client.py

```python
# backend/llm/client.py (updated)

class LLMClient:
    def __init__(self):
        self.providers = [
            {
                "name": "groq",
                "base_url": settings.groq_base_url,
                "api_key": settings.groq_api_key,
                "model": settings.groq_model,   # llama-3.3-70b-versatile
            },
            {
                "name": "gemini",
                "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                "api_key": settings.gemini_api_key,
                "model": "gemini-2.5-flash",
            },
            {
                "name": "openrouter",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": settings.openrouter_api_key,
                "model": "meta-llama/llama-4-maverick:free",
            },
        ]

    async def complete(self, messages, **kwargs):
        for provider in self.providers:
            try:
                client = AsyncOpenAI(
                    base_url=provider["base_url"],
                    api_key=provider["api_key"],
                )
                response = await client.chat.completions.create(
                    model=provider["model"],
                    messages=messages,
                    max_tokens=settings.llm_max_tokens,
                    **kwargs,
                )
                # Log provider used for audit trail
                self._log_provider_used(provider["name"])
                return response
            except (RateLimitError, APIStatusError) as e:
                logger.warning(f"Provider {provider['name']} failed: {e}, trying next")
                continue
        # All providers failed — try Neo4j cache
        return self._serve_from_cache(messages)
```

---

## 11. Frontend Addition: Human Task Portal Tab

Add to `frontend/components/human_task_portal.ts`:

**Features:**
- Task inbox: lists all pending UiPath human tasks assigned to logged-in user
- Assessment detail view: shows gap analysis, maturity scores, DRL ranking, roadmap
- Decision panel: Approve / Override / Reject / Escalate buttons
- Override editor: inline score editing with mandatory comment field
- Submission: POSTs decision to `/api/v1/uipath/task-complete` → Orchestrator picks it up

This tab integrates with UiPath Orchestrator via the `orchestrator_python` SDK:
```python
pip install uipath  # UiPath Python SDK
```

---

*End of BPMN Process Specification*