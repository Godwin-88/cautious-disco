# Digital Capability Canvas Platform
## Comprehensive Product Specifications Document
### GraphRAG-Powered Agentic Intelligence on UiPath Maestro BPMN

---

**Document Version:** 1.0  
**Date:** June 2026  
**Classification:** Internal — Hackathon Submission (UiPath AgentHack 2026)  
**Track:** Track 2 — UiPath Maestro BPMN  
**Author:** Product & Engineering Team  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Platform Overview](#2-platform-overview)
3. [Architecture Overview](#3-architecture-overview)
4. [Data Model Summary](#4-data-model-summary)
5. [Epics, Features & User Stories](#5-epics-features--user-stories)
   - [Epic 1: Graph Knowledge Base & GraphRAG Engine](#epic-1-graph-knowledge-base--graphrag-engine)
   - [Epic 2: Agentic Financial Risk Intelligence](#epic-2-agentic-financial-risk-intelligence)
   - [Epic 3: UiPath Maestro BPMN Orchestration](#epic-3-uipath-maestro-bpmn-orchestration)
   - [Epic 4: Digital Capability Canvas Explorer](#epic-4-digital-capability-canvas-explorer)
   - [Epic 5: Human-in-the-Loop Decision Portal](#epic-5-human-in-the-loop-decision-portal)
   - [Epic 6: Security, Governance & Audit](#epic-6-security-governance--audit)
   - [Epic 7: Reporting & Analytics](#epic-7-reporting--analytics)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Domain & Capability Registry](#7-domain--capability-registry)
8. [Dependency Map](#8-dependency-map)
9. [Glossary](#9-glossary)

---

## 1. Executive Summary

This document specifies the requirements for the **Digital Capability Canvas Intelligence Platform** — a UiPath AgentHack submission that combines enterprise GraphRAG, financial risk engineering, and AI-driven orchestration to deliver an end-to-end agentic workflow on the UiPath Platform.

The platform ingests a structured Digital Capability Canvas (encoded as a Neo4j-compatible Cypher graph) representing **44 Domains**, **223 Sub-Domains**, **1,295 Capabilities**, and their interdependencies across sectors including Finance, Healthcare, Government, Logistics, Energy, and Telecom. It uses this graph as the intelligence substrate for:

- **GraphRAG traversal** to identify non-obvious capability gaps, risks, and interdependencies.
- **Agentic financial risk scoring** to quantify and rank digital transformation investments.
- **UiPath Maestro BPMN** orchestration to move work predictably from intake to recommendation, through human review, to final decision and audit.

The primary use case is **Enterprise Digital Capability Assessment & Investment Prioritisation** — enabling CIOs, CDOs, and Strategy teams to understand where their organisation sits on the digital maturity curve, what capabilities are missing, and which investments carry the highest risk-adjusted return.

---

## 2. Platform Overview

### 2.1 Problem Statement

Large enterprises undergo digital transformation without a structured, data-driven view of their capability landscape. Key problems include:

- Capability gaps are identified in silos, with no cross-domain visibility.
- Investment decisions are made without understanding second and third-order enabling dependencies.
- Risk assessments are manual, slow, and do not leverage relationship-level intelligence.
- There is no single orchestration layer connecting AI agents, human reviewers, and system integrations.

### 2.2 Solution

The platform resolves these gaps by:

1. Loading the Digital Capability Canvas graph into Neo4j and enabling GraphRAG queries via LangChain.
2. Deploying a **Risk Scoring Agent** (financial engineering) that traverses the graph and produces quantitative capability maturity scores.
3. Orchestrating the end-to-end process through **UiPath Maestro BPMN**, with RPA robots handling data ingestion, agents handling intelligence, and humans handling exception review.
4. Providing a **Canvas Explorer UI** for interactive capability navigation and gap analysis.

### 2.3 Key Stakeholders

| Role | Description |
|---|---|
| CIO / CDO | Primary decision-maker; receives investment recommendation reports |
| Strategy Analyst | Configures assessments, reviews agent outputs, approves recommendations |
| Domain SME | Reviews and validates capability maturity scores in their domain |
| Data Engineer | Maintains graph schema, ingestion pipelines, and model updates |
| Compliance Officer | Reviews audit trails, governance controls, and data protection policies |
| UiPath Platform Admin | Manages orchestration, deployment, access, and monitoring |

---

## 3. Architecture Overview

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    UiPath Automation Cloud                       │
│                                                                 │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────────┐ │
│  │  UiPath RPA │   │ Agent Builder│   │  Maestro BPMN Engine │ │
│  │  Robots     │──▶│  Agents      │──▶│  (Process Orch.)     │ │
│  └─────────────┘   └──────────────┘   └──────────────────────┘ │
│         │                  │                     │               │
│         ▼                  ▼                     ▼               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              API Workflow Layer (UiPath)                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐  ┌──────────────┐  ┌──────────────────────┐
│  Neo4j Graph DB │  │  LangChain   │  │  Financial Risk      │
│  (Capability    │  │  GraphRAG    │  │  Scoring Engine      │
│   Canvas)       │  │  Agent       │  │  (Python/Quant)      │
└─────────────────┘  └──────────────┘  └──────────────────────┘
         │                   │                   │
         └───────────────────┴───────────────────┘
                             │
                    ┌────────▼─────────┐
                    │  Claude Code /   │
                    │  Coding Agent    │
                    │  (Build Layer)   │
                    └──────────────────┘
```

### 3.2 Technology Stack

| Layer | Technology |
|---|---|
| Orchestration | UiPath Maestro BPMN |
| Automation | UiPath RPA (Studio), UiPath Agent Builder |
| Coding Agent | Claude Code (Anthropic) |
| Graph Database | Neo4j (Cypher) |
| RAG Framework | LangChain + GraphRAG |
| LLM | Claude claude-sonnet-4-6 via API |
| Risk Engine | Python (NumPy, SciPy, NetworkX, Pandas) |
| API Layer | UiPath API Workflows / FastAPI |
| Frontend | React + Tailwind CSS |
| Auth | UiPath Identity Server / OAuth 2.0 |
| Observability | UiPath Orchestrator + Datadog |

---

## 4. Data Model Summary

The Digital Capability Canvas graph contains the following node types and relationships:

### 4.1 Node Types

| Node Type | Count | Description |
|---|---|---|
| `Domain` | 44 | Top-level digital domains (e.g., Manage Digital Intelligence, Manage Digital IT) |
| `SubDomain` | 223 | Functional groupings within a Domain (e.g., Intelligence Governance, Manage Finance) |
| `Capability` | 1,295 | Specific business capabilities (e.g., Manage Data Ownership, Manage Risk Assessment) |
| `Epic` | 1,295 | Agile epics mapped 1:1 to Capabilities |
| `Feature` | 1,295 | Feature sets belonging to each Epic |
| `Standard` | 44 | Governance standards associated with each Domain |
| `Trend` | 44 | Industry trends influencing each Domain |

### 4.2 Relationship Types

| Relationship | Source → Target | Meaning |
|---|---|---|
| `HAS_SECTOR` | Domain → Domain | Sector grouping under core digital hub |
| `PARENT_OF` | Domain → SubDomain, SubDomain → Capability | Hierarchical ownership |
| `GOVERNED_BY` | Domain → Standard | Compliance linkage |
| `INFLUENCED_BY` | Domain → Trend | Strategic trend driver |
| `REPRESENTED_BY` | Capability → Epic | Agile backlog linkage |
| `HAS_FEATURE` | Epic → Feature | Feature decomposition |
| `ENABLES` | Domain → Domain | Cross-domain enabling dependencies |

### 4.3 Key Enabling Domains (Cross-Domain Dependencies)

The following domains act as horizontal enablers and are the highest-risk nodes in the graph:

- **Manage Digital IT** — enables 44 domains
- **Manage Digital Security** — enables 44 domains
- **Manage Digital Intelligence** — enables 35+ domains
- **Manage Digital Intelligence (Non Commercial)** — enables 35+ domains
- **Manage Digital Backoffice** — enables financial and operational domains
- **Manage Digital Inter-Operability & Automation** — enables channel and integration domains

---

## 5. Epics, Features & User Stories

---

### EPIC 1: Graph Knowledge Base & GraphRAG Engine

**Epic ID:** EP-001  
**Domain Alignment:** Manage Digital Intelligence → Intelligence Infrastructure  
**Description:** Build, populate, and maintain the Neo4j graph from the Capability Canvas Cypher file, and expose it via a GraphRAG query interface for downstream agents.

---

#### Feature 1.1: Graph Ingestion & Schema Management

**Feature ID:** FEAT-001-01  
**Description:** Automate the loading and validation of the Capability Canvas Cypher file into Neo4j, with schema enforcement and change detection.

---

**User Story 1.1.1 — Cypher Graph Loader**

> *As a Data Engineer, I want to load the Digital Capability Canvas Cypher file into Neo4j automatically, so that the graph is always up to date without manual intervention.*

**Acceptance Criteria:**
- [ ] A UiPath RPA robot monitors a designated file drop location for `.cypher` files.
- [ ] On detection, the robot triggers a UiPath API Workflow that executes the Cypher statements against Neo4j via the Bolt protocol.
- [ ] The system validates that all 44 Domains, 223 SubDomains, and 1,295 Capabilities are successfully created.
- [ ] Failed statements are logged and surfaced as exceptions in UiPath Orchestrator.
- [ ] A completion notification is sent via webhook to the Maestro BPMN process trigger.
- [ ] Re-ingestion supports `MERGE` semantics — no duplicate nodes are created on re-run.

---

**User Story 1.1.2 — Graph Schema Validation**

> *As a Data Engineer, I want the system to validate the graph schema after each ingestion, so that I can detect structural errors before they propagate to downstream agents.*

**Acceptance Criteria:**
- [ ] Post-ingestion, an agent runs a suite of Cypher validation queries (e.g., count nodes by type, verify all `PARENT_OF` chains reach a Domain root).
- [ ] Validation results are stored as a structured JSON report in UiPath Orchestrator storage buckets.
- [ ] Any schema violations trigger a human review task in Maestro BPMN.
- [ ] Schema version is tracked and compared against the previous successful load.
- [ ] A visual diff report is generated when schema changes are detected.

---

**User Story 1.1.3 — Graph Version Control**

> *As a Data Engineer, I want every graph version to be timestamped and stored, so that I can roll back to a previous version if a bad ingestion corrupts the graph.*

**Acceptance Criteria:**
- [ ] Each ingestion creates a versioned snapshot stored in a designated Neo4j database (e.g., `canvas_v{timestamp}`).
- [ ] The latest snapshot is aliased as `canvas_current`.
- [ ] A rollback API endpoint allows reverting to any stored version.
- [ ] Version history is accessible from the Canvas Explorer UI.
- [ ] Rollback triggers a re-validation and Maestro BPMN notification.

---

#### Feature 1.2: GraphRAG Query Engine

**Feature ID:** FEAT-001-02  
**Description:** Implement a LangChain-based GraphRAG agent that translates natural language questions into Cypher queries and returns contextually grounded responses.

---

**User Story 1.2.1 — Natural Language to Cypher Translation**

> *As a Strategy Analyst, I want to ask questions in plain English about the capability canvas (e.g., "Which capabilities in the Healthcare domain are not yet enabled by our Digital IT?"), so that I can explore the graph without knowing Cypher.*

**Acceptance Criteria:**
- [ ] The GraphRAG agent accepts natural language input via a REST API endpoint.
- [ ] The agent uses Claude claude-sonnet-4-6 with a custom system prompt to generate syntactically valid Cypher queries.
- [ ] Generated queries are executed against Neo4j and results are returned with source node references.
- [ ] The agent includes chain-of-thought reasoning in its response explaining how it formulated the query.
- [ ] Response latency is under 10 seconds for standard graph traversals (depth ≤ 4 hops).
- [ ] Invalid or dangerous Cypher (e.g., `DETACH DELETE`) is blocked by a query guard layer.

---

**User Story 1.2.2 — Capability Gap Detection**

> *As a CIO, I want the agent to automatically identify capability gaps in my organisation's profile relative to the full canvas, so that I can understand where we are underprepared.*

**Acceptance Criteria:**
- [ ] The system accepts an organisation capability profile (a list of implemented capability IDs).
- [ ] The GraphRAG agent computes the set difference between the profile and the full canvas.
- [ ] Gap results are enriched with domain context, enabling dependencies, and industry trend metadata.
- [ ] Gaps are prioritised by the number of `ENABLES` relationships that flow from the missing capability.
- [ ] A ranked gap report is produced in JSON and rendered in the Canvas Explorer UI.
- [ ] The agent explains each gap in plain English with a risk rationale.

---

**User Story 1.2.3 — Enabling Dependency Path Analysis**

> *As a Strategy Analyst, I want to understand the full enabling dependency chain for a target capability, so that I can plan what foundational capabilities must be in place first.*

**Acceptance Criteria:**
- [ ] Given a target Capability ID, the agent traces all `ENABLES` and `PARENT_OF` paths up to the root Domain.
- [ ] The full dependency tree is returned as a structured JSON object and visualised as a directed acyclic graph in the UI.
- [ ] The agent flags circular dependencies if any exist in the graph.
- [ ] Results include estimated implementation complexity based on depth and breadth of the dependency tree.
- [ ] Paths are ranked by criticality (number of downstream capabilities impacted).

---

#### Feature 1.3: Graph Embedding & Semantic Search

**Feature ID:** FEAT-001-03  
**Description:** Generate vector embeddings for all Capability nodes to enable semantic similarity search alongside graph traversal.

---

**User Story 1.3.1 — Capability Embedding Generation**

> *As a Data Engineer, I want all Capability names and descriptions to be embedded into a vector store, so that semantic search can find related capabilities even when the terminology differs.*

**Acceptance Criteria:**
- [ ] All 1,295 Capability node names are embedded using Claude's embedding API and stored in a vector index (e.g., Pinecone or Neo4j vector index).
- [ ] Embeddings are regenerated automatically whenever a new canvas version is ingested.
- [ ] A similarity search endpoint returns the top-K most semantically similar capabilities given a query string.
- [ ] Semantic search results are merged with graph traversal results for hybrid retrieval.
- [ ] Embedding latency for the full canvas does not exceed 5 minutes per ingestion.

---

### EPIC 2: Agentic Financial Risk Intelligence

**Epic ID:** EP-002  
**Domain Alignment:** Manage Digital Intelligence → Vertical Intelligence; Manage Capital Core Operations  
**Description:** Deploy quantitative financial risk agents that consume GraphRAG outputs and produce investment risk scores, capability maturity assessments, and portfolio-level recommendations.

---

#### Feature 2.1: Capability Maturity Scoring Agent

**Feature ID:** FEAT-002-01  
**Description:** An agent that scores the maturity of each capability in an organisation's profile using a quantitative framework.

---

**User Story 2.1.1 — Maturity Score Computation**

> *As a Strategy Analyst, I want each capability to be assigned a maturity score (0–5) based on assessment inputs and graph position, so that I can benchmark our organisation against the full canvas.*

**Acceptance Criteria:**
- [ ] The scoring agent accepts a structured assessment input (JSON) with evidence fields per capability.
- [ ] Maturity scores are computed using a weighted multi-criteria model: implementation depth (40%), integration breadth (30%), operational uptime (20%), governance coverage (10%).
- [ ] Graph position adjusts scores: capabilities with more `ENABLES` outgoing edges carry higher strategic weight.
- [ ] Scores are normalised to a 0–5 scale and stored per capability per assessment run.
- [ ] The agent produces a domain-level aggregate score and a full-canvas aggregate score.
- [ ] Score explanations are generated in natural language by the LLM component.

---

**User Story 2.1.2 — Maturity Benchmarking**

> *As a CIO, I want to compare our capability maturity scores against industry benchmarks, so that I can understand how we rank relative to peers.*

**Acceptance Criteria:**
- [ ] The system stores benchmark profiles (anonymised) for at least 5 industry verticals represented in the canvas (e.g., Healthcare, Retail Banking, Oil & Gas, Government, Logistics).
- [ ] A benchmarking report shows the gap between the organisation's scores and the benchmark median for each domain.
- [ ] Benchmark data is sourced from UiPath web search agent or configured static datasets.
- [ ] Visual gap charts are included in the generated report (PDF or dashboard).
- [ ] Benchmarks are updated at configurable intervals (default: quarterly).

---

#### Feature 2.2: Investment Risk Scoring Engine

**Feature ID:** FEAT-002-02  
**Description:** Quantitative financial engineering models that score the risk-adjusted return on investing in specific capability gaps.

---

**User Story 2.2.1 — Risk-Adjusted Priority Score**

> *As a CIO, I want each identified capability gap to be scored by its risk-adjusted investment priority, so that I can allocate budget to the highest-value, lowest-risk capabilities first.*

**Acceptance Criteria:**
- [ ] The risk engine computes a Priority Score = (Strategic Value × Dependency Multiplier) / (Implementation Risk × Time-to-Value).
- [ ] Strategic Value is derived from the number of downstream domains the capability enables (graph metric).
- [ ] Dependency Multiplier accounts for how many other gaps depend on this capability being filled first.
- [ ] Implementation Risk is estimated from complexity indicators (depth in hierarchy, number of integrations required).
- [ ] Time-to-Value is configurable per capability category (default: derived from domain benchmarks).
- [ ] Scores are produced for all identified gaps and ranked in a prioritised investment backlog.

---

**User Story 2.2.2 — Portfolio-Level Risk Simulation**

> *As a Strategy Analyst, I want to run Monte Carlo simulations on investment portfolios of capability gaps, so that I can understand the probability distribution of achieving maturity targets.*

**Acceptance Criteria:**
- [ ] The risk engine accepts a portfolio of selected capability gaps and a total budget constraint.
- [ ] Monte Carlo simulation (minimum 10,000 iterations) is run over cost, time, and value distributions per capability.
- [ ] Results include: P10, P50, P90 estimates for portfolio ROI; probability of reaching target maturity within defined timeframe.
- [ ] Simulation results are stored and can be retrieved for comparison across scenarios.
- [ ] A scenario comparison view is available in the Analytics dashboard.
- [ ] Simulation runtime does not exceed 60 seconds for portfolios of up to 50 capabilities.

---

**User Story 2.2.3 — Contagion Path Risk Detection**

> *As a Risk Officer, I want the system to detect contagion risk paths in the capability graph, so that I can understand how a failure in one domain cascades to others.*

**Acceptance Criteria:**
- [ ] The GraphRAG agent identifies all `ENABLES` chains that pass through a given domain.
- [ ] For each source domain, the maximum depth of downstream impact is computed.
- [ ] Domains with high centrality (betweenness centrality, computed via NetworkX) are flagged as contagion risk nodes.
- [ ] A contagion risk heatmap is rendered in the Canvas Explorer UI.
- [ ] High-risk nodes trigger automated alerts to the Risk Officer via UiPath notification service.
- [ ] Contagion paths are included in the final investment recommendation report.

---

#### Feature 2.3: LLM-Driven Recommendation Agent

**Feature ID:** FEAT-002-03  
**Description:** An LLM agent that synthesises GraphRAG outputs and financial risk scores into natural language investment recommendations.

---

**User Story 2.3.1 — Narrative Investment Recommendation**

> *As a CIO, I want to receive a structured, narrative investment recommendation report, so that I can present capability investment decisions to the board without needing to interpret raw data.*

**Acceptance Criteria:**
- [ ] The recommendation agent receives gap analysis, maturity scores, and risk scores as context.
- [ ] It produces a structured report with: Executive Summary, Top 10 Priority Capabilities, Domain-Level Investment Plan, Risk Mitigation Actions, and Next Steps.
- [ ] The report is generated using Claude claude-sonnet-4-6 with grounded citations to graph nodes.
- [ ] Report is exported as PDF and HTML.
- [ ] Report generation does not exceed 30 seconds.
- [ ] The recommendation cites specific capability IDs and domain names from the graph.

---

**User Story 2.3.2 — Interactive Q&A on Recommendations**

> *As a Strategy Analyst, I want to ask follow-up questions on the recommendation report using natural language, so that I can drill into specific areas without regenerating the full report.*

**Acceptance Criteria:**
- [ ] A conversational chat interface is available after a report is generated.
- [ ] The chat agent retains the full report and graph context in its conversation window.
- [ ] Questions about specific capabilities, domains, or risk scores return grounded, cited answers.
- [ ] Chat history is persisted per report session.
- [ ] The analyst can export any chat exchange as a note appended to the report.

---

### EPIC 3: UiPath Maestro BPMN Orchestration

**Epic ID:** EP-003  
**Domain Alignment:** Manage Digital Inter-Operability & Automation → Manage Automation Infrastructure (Workflows)  
**Description:** Design and deploy the end-to-end BPMN process in UiPath Maestro that orchestrates all agents, robots, humans, and APIs from assessment intake to decision and audit close.

---

#### Feature 3.1: BPMN Process Design & Deployment

**Feature ID:** FEAT-003-01  
**Description:** Model and deploy the core BPMN 2.0 process in UiPath Maestro.

---

**User Story 3.1.1 — Core BPMN Process Deployment**

> *As a UiPath Platform Admin, I want the capability assessment BPMN process to be deployed on UiPath Maestro, so that every assessment follows a consistent, auditable flow.*

**Acceptance Criteria:**
- [ ] A BPMN 2.0 diagram is modelled in UiPath Maestro covering the following lanes: Data Ingestion, Graph Intelligence, Risk Scoring, Human Review, Decision & Output, Audit Close.
- [ ] The process is triggered by an API call with an assessment request payload.
- [ ] Each BPMN task is assigned to the correct actor: RPA robot, AI agent, human reviewer, or API.
- [ ] The process includes at least 2 exclusive gateways: one for graph validation outcome, one for human review decision.
- [ ] Parallel gateways are used to run GraphRAG and financial risk scoring concurrently.
- [ ] The process terminates with either an Approved, Rejected, or Deferred end event.
- [ ] The full process is visible and configurable in UiPath Orchestrator.

---

**User Story 3.1.2 — BPMN Process Monitoring**

> *As a UiPath Platform Admin, I want real-time visibility into all in-flight BPMN process instances, so that I can detect bottlenecks and SLA breaches.*

**Acceptance Criteria:**
- [ ] A monitoring dashboard in UiPath Orchestrator shows all active process instances with current step, elapsed time, and actor.
- [ ] SLA thresholds are configured per task (e.g., human review must be completed within 48 hours).
- [ ] SLA breaches trigger escalation notifications via UiPath notification service.
- [ ] Completed instances are archived with full audit trail.
- [ ] Dashboard metrics include: average cycle time per step, SLA compliance rate, exception rate by step.

---

#### Feature 3.2: RPA Data Ingestion Robot

**Feature ID:** FEAT-003-02  
**Description:** UiPath RPA robots that automate data collection from enterprise systems to populate the organisation capability profile.

---

**User Story 3.2.1 — Enterprise System Data Harvesting**

> *As a Data Engineer, I want RPA robots to extract capability evidence data from enterprise systems (ITSM, ERP, HR platforms), so that the assessment profile is based on real system data rather than self-reported inputs.*

**Acceptance Criteria:**
- [ ] RPA robots connect to at least 3 enterprise system types: ITSM (e.g., ServiceNow), ERP (e.g., SAP), and document repositories (e.g., SharePoint).
- [ ] Extracted data is mapped to capability IDs in the canvas using a configurable field mapping table.
- [ ] Data extraction is scheduled and triggered by the Maestro BPMN process.
- [ ] Extraction failures are retried up to 3 times before raising an exception in Maestro.
- [ ] Extracted data is validated against a schema before passing to the scoring agent.
- [ ] Extraction run logs are stored in UiPath Orchestrator with timestamps and record counts.

---

**User Story 3.2.2 — Assessment Profile Builder**

> *As a Data Engineer, I want the extracted enterprise data to be automatically assembled into a structured organisation capability profile, so that downstream agents receive clean, standardised input.*

**Acceptance Criteria:**
- [ ] A profile builder robot consolidates all extracted data into a JSON document conforming to the assessment schema.
- [ ] The profile includes: organisation ID, assessment date, capability list with evidence pointers, and data source metadata.
- [ ] The profile is stored in UiPath Orchestrator storage buckets and referenced by process instance ID.
- [ ] A data quality score is computed for the profile (completeness, timeliness, source coverage).
- [ ] Profiles with a data quality score below the configured threshold trigger a human data review task in Maestro.

---

#### Feature 3.3: Agent Orchestration Tasks

**Feature ID:** FEAT-003-03  
**Description:** Maestro BPMN tasks that invoke AI agents and handle their outputs.

---

**User Story 3.3.1 — GraphRAG Agent Task Invocation**

> *As a UiPath Platform Admin, I want Maestro to invoke the GraphRAG agent as a BPMN service task and handle the response, so that graph intelligence is seamlessly integrated into the process flow.*

**Acceptance Criteria:**
- [ ] A BPMN service task calls the GraphRAG API endpoint with the organisation capability profile as input.
- [ ] The task waits for the agent response with a configurable timeout (default: 120 seconds).
- [ ] On success, the gap analysis JSON is stored as process data and passed to the Risk Scoring task.
- [ ] On timeout or error, a boundary event routes to an exception handling sub-process.
- [ ] The agent call is idempotent — retrying with the same process instance ID returns the same result if already computed.

---

**User Story 3.3.2 — Parallel Agent Execution Gateway**

> *As a UiPath Platform Admin, I want GraphRAG and Risk Scoring agents to run in parallel within the BPMN process, so that overall process latency is minimised.*

**Acceptance Criteria:**
- [ ] A BPMN parallel split gateway fires both the GraphRAG agent task and the baseline maturity scoring task simultaneously.
- [ ] A parallel merge gateway waits for both tasks to complete before proceeding to recommendation generation.
- [ ] If either parallel branch fails, the merge gateway routes to the exception sub-process.
- [ ] The BPMN diagram shows the parallel gateway with correct BPMN 2.0 notation (double border).
- [ ] Execution logs confirm both branches started within 1 second of each other.

---

### EPIC 4: Digital Capability Canvas Explorer

**Epic ID:** EP-004  
**Domain Alignment:** Manage Digital Channels → Manage Digital Channels (Non Commercial)  
**Description:** An interactive web UI that allows stakeholders to explore the capability canvas graph, view gap analyses, and navigate domain-level intelligence.

---

#### Feature 4.1: Graph Visualisation

**Feature ID:** FEAT-004-01  
**Description:** Interactive visualisation of the capability canvas graph.

---

**User Story 4.1.1 — Domain Hierarchy Explorer**

> *As a Strategy Analyst, I want to visually navigate the Domain → SubDomain → Capability hierarchy, so that I can understand the scope and structure of the full canvas at a glance.*

**Acceptance Criteria:**
- [ ] A collapsible tree view renders all 44 Domains, their SubDomains, and Capabilities.
- [ ] Nodes are colour-coded by type (Domain: blue, SubDomain: teal, Capability: green).
- [ ] Clicking a node opens a detail panel showing: name, ID, standards, trends, epics, and features.
- [ ] A search bar filters nodes by name with live highlighting.
- [ ] The tree supports expand-all and collapse-all controls.
- [ ] Navigation state (expanded nodes) is preserved across browser sessions.

---

**User Story 4.1.2 — Capability Gap Heatmap**

> *As a CIO, I want to see a heatmap of capability gaps across all domains, colour-coded by priority score, so that I can instantly identify the most critical areas for investment.*

**Acceptance Criteria:**
- [ ] A domain-level heatmap renders all 44 domains in a grid.
- [ ] Cell colour encodes the aggregate gap severity: red (critical), amber (moderate), green (adequate).
- [ ] Hovering a cell shows: domain name, number of gaps, top 3 priority capabilities.
- [ ] Clicking a cell drills down to the domain's SubDomain and Capability gap detail view.
- [ ] The heatmap refreshes automatically after each completed BPMN assessment process.
- [ ] Heatmap data is exportable as CSV and PNG.

---

**User Story 4.1.3 — Enabling Dependency Graph**

> *As a Strategy Analyst, I want to visualise the `ENABLES` relationships between domains as a force-directed network graph, so that I can see which domains are the most critical enablers in the architecture.*

**Acceptance Criteria:**
- [ ] A force-directed network graph renders all Domain-to-Domain `ENABLES` relationships.
- [ ] Node size is proportional to the number of outgoing `ENABLES` edges (higher = larger).
- [ ] Edge thickness is proportional to the number of shared enabled domains.
- [ ] Nodes are selectable; selection highlights all paths to/from that node.
- [ ] The graph supports zoom, pan, and node dragging.
- [ ] A legend explains node size and edge thickness encoding.

---

#### Feature 4.2: Assessment Dashboard

**Feature ID:** FEAT-004-02  
**Description:** Dashboard for tracking ongoing and completed assessments.

---

**User Story 4.2.1 — Assessment Run Tracker**

> *As a Strategy Analyst, I want a dashboard that shows all assessment runs with their current BPMN process status, so that I can track progress and identify blocked assessments.*

**Acceptance Criteria:**
- [ ] The dashboard lists all assessment runs with: organisation name, start date, current step, status (In Progress, Awaiting Review, Completed, Failed).
- [ ] Status is fetched from UiPath Orchestrator in real time (polling every 30 seconds).
- [ ] Completed runs link to the generated recommendation report.
- [ ] Failed runs link to the exception log and allow re-trigger of the failed step.
- [ ] The dashboard is filterable by status, date range, and organisation name.
- [ ] A summary card shows: total runs, completion rate, average cycle time, SLA compliance rate.

---

### EPIC 5: Human-in-the-Loop Decision Portal

**Epic ID:** EP-005  
**Domain Alignment:** Manage Digital Backoffice → Manage Backoffice Governance  
**Description:** A task portal for human reviewers to review agent outputs, provide feedback, and make approval decisions within the Maestro BPMN process.

---

#### Feature 5.1: Human Review Task Interface

**Feature ID:** FEAT-005-01  
**Description:** Task interface surfacing agent outputs for human review and decision.

---

**User Story 5.1.1 — Review Task Inbox**

> *As a Domain SME, I want a task inbox showing all BPMN human review tasks assigned to me, so that I can act on pending decisions without leaving the platform.*

**Acceptance Criteria:**
- [ ] The task inbox lists all tasks assigned to the logged-in user via UiPath Orchestrator task assignment.
- [ ] Each task shows: assessment ID, organisation name, domain, agent output summary, due date, SLA status.
- [ ] Tasks can be sorted by due date, priority, and SLA status.
- [ ] Overdue tasks are highlighted in red.
- [ ] Clicking a task opens the full review interface.
- [ ] Task counts are shown per reviewer with workload balancing indicator.

---

**User Story 5.1.2 — Agent Output Review Interface**

> *As a Domain SME, I want to review the GraphRAG gap analysis and risk scores in a structured interface, so that I can efficiently validate or override agent outputs before they proceed to recommendation.*

**Acceptance Criteria:**
- [ ] The review interface presents: gap analysis by domain, maturity scores per capability, risk priority ranking, and contagion path highlights.
- [ ] Each capability gap is shown with the agent's rationale and graph evidence (source node path).
- [ ] The reviewer can: Approve (accept agent output), Override (modify scores with mandatory comment), or Escalate (refer to senior reviewer).
- [ ] Override comments are stored and appended to the audit trail.
- [ ] Bulk approval is available for low-risk items (maturity score deviation < 0.5).
- [ ] The interface shows a confidence indicator per agent output (derived from graph path certainty).

---

**User Story 5.1.3 — Structured Decision Capture**

> *As a Domain SME, I want the system to capture my review decision in a structured format, so that the BPMN process can proceed automatically without ambiguity.*

**Acceptance Criteria:**
- [ ] Decision options are: Approve, Approve with Comments, Override, Reject, Escalate.
- [ ] Each decision requires a structured justification from a predefined taxonomy (e.g., "Insufficient evidence", "Score too conservative", "External factor not captured").
- [ ] Decisions are submitted to UiPath Orchestrator as task completion events.
- [ ] The BPMN gateway receives the decision code and routes accordingly.
- [ ] A confirmation screen summarises the decision before final submission.
- [ ] Submitted decisions cannot be edited; a new review task must be raised for corrections.

---

#### Feature 5.2: Escalation & Exception Management

**Feature ID:** FEAT-005-02  
**Description:** Escalation workflows for high-stakes or disputed review decisions.

---

**User Story 5.2.1 — Escalation Routing**

> *As a Domain SME, I want to escalate a review decision to a senior reviewer when I am uncertain, so that complex cases receive appropriate expert attention.*

**Acceptance Criteria:**
- [ ] An Escalate action in the review interface routes the task to the next reviewer tier in the escalation hierarchy.
- [ ] Escalation notifies the senior reviewer via email and in-platform notification.
- [ ] The escalation reason and original review context are passed to the senior reviewer.
- [ ] Escalation history is visible to all parties in the review chain.
- [ ] A maximum escalation depth of 3 tiers is enforced; beyond that, the process owner is notified.
- [ ] SLA timers reset on escalation with a configurable senior review SLA (default: 24 hours).

---

### EPIC 6: Security, Governance & Audit

**Epic ID:** EP-006  
**Domain Alignment:** Manage Digital Security → Security Governance; Manage Digital Intelligence → Intelligence Governance  
**Description:** Enforce data governance, access controls, audit logging, and compliance across the entire platform.

---

#### Feature 6.1: Role-Based Access Control

**Feature ID:** FEAT-006-01  

---

**User Story 6.1.1 — Role & Permission Management**

> *As a UiPath Platform Admin, I want role-based access control enforced across all platform components, so that users only access data and functions appropriate to their role.*

**Acceptance Criteria:**
- [ ] Roles defined: Admin, Analyst, Domain SME, Reviewer, Read-Only.
- [ ] Role assignments are managed via UiPath Identity Server.
- [ ] API endpoints enforce role-based authorization on every request.
- [ ] Graph query scope is restricted by role (e.g., Domain SME can only query their assigned domains).
- [ ] Access attempts outside role permissions are logged as security events.
- [ ] Role permissions are documented and auditable in the admin console.

---

#### Feature 6.2: Audit Trail & Compliance Logging

**Feature ID:** FEAT-006-02  

---

**User Story 6.2.1 — Full Process Audit Trail**

> *As a Compliance Officer, I want a complete, immutable audit trail for every assessment process instance, so that I can demonstrate regulatory compliance and investigate disputes.*

**Acceptance Criteria:**
- [ ] Every BPMN task execution, agent call, human decision, and system event is logged with: timestamp, actor, action, input, output, and BPMN process instance ID.
- [ ] Audit logs are stored in an append-only log store (e.g., UiPath Orchestrator audit log + external SIEM).
- [ ] Logs are searchable by process instance ID, actor, date range, and event type.
- [ ] Log retention policy is configurable (default: 7 years for financial compliance).
- [ ] Audit reports can be exported in PDF and CSV formats.
- [ ] Tampering with audit logs is technically prevented (hash chaining or equivalent).

---

**User Story 6.2.2 — Data Governance Classification**

> *As a Compliance Officer, I want all data flowing through the platform to be classified by sensitivity level, so that personally identifiable or commercially sensitive data is handled appropriately.*

**Acceptance Criteria:**
- [ ] A data classification scheme is implemented: Public, Internal, Confidential, Restricted.
- [ ] All assessment payloads and agent outputs are auto-classified on creation.
- [ ] Restricted data is encrypted at rest and in transit using AES-256 and TLS 1.3.
- [ ] Data classification metadata is stored alongside each record and is immutable.
- [ ] Access to Restricted data requires MFA re-authentication.
- [ ] Data retention and deletion policies are enforced per classification level.

---

### EPIC 7: Reporting & Analytics

**Epic ID:** EP-007  
**Domain Alignment:** Manage Digital Intelligence → Horizontal Intelligence; Manage Digital Backoffice → Manage Finance  
**Description:** Generate, distribute, and analyse assessment outcomes, maturity trends, and investment impact over time.

---

#### Feature 7.1: Executive Reporting

**Feature ID:** FEAT-007-01  

---

**User Story 7.1.1 — Automated Executive Report Generation**

> *As a CIO, I want the platform to automatically generate a board-ready executive report at the completion of each assessment, so that I have a polished, presentation-ready output without additional effort.*

**Acceptance Criteria:**
- [ ] Report is generated as PDF upon BPMN process completion.
- [ ] Report sections: Executive Summary, Capability Maturity Scorecard, Top 10 Investment Priorities, Risk Register, Domain Heatmap, Recommended Roadmap.
- [ ] All data is sourced from the completed assessment instance; no manual data entry required.
- [ ] Report includes the organisation logo (configurable) and assessment date.
- [ ] Report is stored in UiPath Orchestrator storage and emailed to configured recipients.
- [ ] Report generation time does not exceed 60 seconds.

---

**User Story 7.1.2 — Maturity Trend Analysis**

> *As a CIO, I want to see maturity score trends across multiple assessments over time, so that I can demonstrate progress and identify stagnation.*

**Acceptance Criteria:**
- [ ] A trend dashboard shows maturity scores per domain over all completed assessments.
- [ ] Line charts show score trajectory per domain and overall.
- [ ] Trend anomalies (score drops > 0.5 between assessments) are flagged with alerts.
- [ ] The dashboard supports comparison of any two assessment periods.
- [ ] Trend data is exportable as CSV.
- [ ] Trend analysis is available for organisations with at least 2 completed assessments.

---

#### Feature 7.2: Investment Impact Tracking

**Feature ID:** FEAT-007-02  

---

**User Story 7.2.1 — Recommendation Outcome Tracking**

> *As a Strategy Analyst, I want to track whether recommended capability investments were actioned and what maturity score improvement resulted, so that I can measure the ROI of the platform's recommendations.*

**Acceptance Criteria:**
- [ ] Each recommendation from a completed assessment is assigned a tracking status: Accepted, Deferred, Rejected.
- [ ] For Accepted recommendations, the analyst records the planned and actual implementation dates.
- [ ] Subsequent assessment runs auto-link to prior recommendations and show score change attribution.
- [ ] An impact summary report shows: total recommendations made, acceptance rate, average score improvement for accepted recommendations.
- [ ] Impact data feeds a platform-level ROI dashboard available to platform admins.

---

## 6. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | GraphRAG queries complete in < 10s for traversals ≤ 4 hops. Monte Carlo simulations (10K iterations, 50 capabilities) complete in < 60s. BPMN process average cycle time (ex. human review) < 5 minutes. |
| **Availability** | Platform SLA: 99.5% uptime. UiPath Automation Cloud SLA applies for orchestration layer. |
| **Scalability** | Graph supports up to 10,000 capability nodes without performance degradation. Platform supports concurrent processing of 20 assessment instances. |
| **Security** | All data encrypted at rest (AES-256) and in transit (TLS 1.3). MFA required for all user logins. API authentication via OAuth 2.0 + JWT. Cypher injection prevention via parameterised queries only. |
| **Auditability** | 100% of BPMN events, agent calls, and human decisions are logged. Logs are immutable and retained per configured policy. |
| **Maintainability** | All code in public GitHub repository under MIT licence. README includes setup instructions, prerequisites, and component map. Claude Code used for code generation with commit history preserved. |
| **Interoperability** | Platform exposes REST APIs for all major functions. External LLM frameworks (LangChain, CrewAI) integrate via standard HTTP. UiPath components callable from external orchestrators via published API. |

---

## 7. Domain & Capability Registry

The following table lists the 44 Domains and a representative sample of their SubDomains and Capabilities as encoded in the Digital Capability Canvas. The full list of 1,295 capabilities is stored in the graph database and accessible via the Canvas Explorer.

| Domain | Representative SubDomains | Key Capabilities |
|---|---|---|
| Manage Digital Core (Hub) | — | Cross-domain hub with HAS_SECTOR relationships to all sector domains |
| Manage Digital IT | Govern Digital IT, Manage IT Infrastructure and Hosting, Manage IT Services and Operation, Manage Application Lifecycle | Govern IT Infrastructure Lifecycle, Manage IT Infrastructure Design, Manage IT Infrastructure Operations, Manage Application Development, Manage Application Security |
| Manage Digital Intelligence | Intelligence Governance, Intelligence Infrastructure, Horizontal Intelligence, Vertical Intelligence | Manage Data Ownership, Manage Data Governance, Manage Cognitive Intelligence, Manage Descriptive Analytics, Manage Predictive Analytics, Manage Prescriptive Analytics, Architecture Intelligence (EA) |
| Manage Digital Intelligence (Non Commercial) | — | Enables: Food Supply, Regulatory, Channels (Non-Commercial), Digital Backoffice, Capital Operations, and 30+ more domains |
| Manage Digital Security | Manage Data Security, Manage Network Security, Manage End-point Security, Manage Identity & Access Security, Manage Platform Security, Manage Security Governance | Manage Security Operations Center (SOC), Manage Data Breach, Manage Authentication & Authorisation, Manage Network Firewall, Manage IoT Security, Manage End-point Protection |
| Manage Digital Backoffice | Manage Finance, Manage Human Resources, Manage Legal, Manage Property Facility and Workspace Assets, Manage Enterprise Compliance | Manage Finance Accounting, Manage Core HR, Manage Legal Advisory, Manage Property Operation, Manage Enterprise Risk, Manage Compliance Management |
| Manage Digital Channels | Manage Online Channels (Web), Manage Online Channels (Mobile), Manage Physical Channels, Manage Voice Channels, Manage Field Channels | Manage Web Portals, Manage Mobile Interface, Manage Contact Centers, Manage IVR Interactions, Manage Self Service Kiosks |
| Manage Digital Inter-Operability & Automation | Manage Integration Infrastructure (API), Manage Integration Infrastructure (IoT), Manage Automation Infrastructure (RPA), Manage Automation Infrastructure (Workflows), Manage Automation Infrastructure (Blockchain) | Manage API Gateway, Manage API Lifecycle, Manage Software Robots, Manage Process Orchestration, Manage Blockchain & Transaction Integrity |
| Manage Retail Banking Core Operations | Manage Core Operation (Finance), Manage Customer Care, Manage Service Offering | Manage Loans & Deposits, Manage Cards, Manage Trade Banking, Manage Islamic Banking, Manage Customer Billing |
| Manage Healthcare Provider Core Operations | Manage Clinical Care, Manage Medical Management, Manage Provider Operations | Manage Admissions & Scheduling, Manage Clinical Documentation, Manage Nursing Unit Operations, Manage Patient Safety, Manage Pharmacy |
| Manage Government Excellence Core Operations | Manage Government Strategic Planning, Manage Government Policy Lifecycle, Manage Government Service Excellence | Manage Policy Development, Manage Policy Ratification, Manage Government Best Practices Compliance, Manage Public Satisfaction |
| Manage Oil & Gas Core Operations | Manage Exploration, Manage Upstream Operations, Manage Midstream Operations, Manage Downstream Operations | Manage G&G Survey, Manage Well Design & Development, Manage Pipeline Transport, Manage Refining Distillation, Manage LNG Liquefaction & Storage |
| Manage Logistics 4.0 Core Operations | Manage Core Operation (Logistics), Manage Fleet Assets, Manage Operational Assets | Manage Inbound Logistics, Manage Outbound Logistics, Manage Warehouse, Manage Fleet Operation, Manage Distribution Center Operations |
| Manage Clean Energy Core Operations | Manage Feasibility & Planning, Manage Commissioning & Grid Connection, Manage Operation & Maintenance (O&M), Manage Decommissioning & End-of-Life | Manage Site Identification & Screening, Manage Detailed Resource Assessment, Manage Grid Interconnection Studies, Manage Energy Trading |
| Manage Digital Workspace | Manage Digital Workspace Delivery, Manage Digital Workspace Governance, Manage Digital Workspace Resiliency, Manage Digital Workspace Resources | Manage Digital Workspace Accessibility, Manage Digital Workspace Security, Manage Digital Workspace Experience, Manage Digital Workspace Productivity |
| Manage Digital GPRC | Manage Enterprise Governance, Manage Enterprise Compliance, Manage Enterprise Risk | Manage Compliance Intelligence (GRC), Manage Risk Management Lifecycle, Manage Enterprise Internal Audits, Manage Strategic Risks |
| Manage MarCom Orchestration | Manage Digital MarCom Campaigns, Manage Digital MarCom Governance, Manage Digital MarCom Intelligence | Manage Campaign Planning, Manage Campaign Execution, Manage Digital Marketing Delivery, Manage Digital MarCom Analytics |
| Manage Digital Experience Orchestration | Manage Stakeholder Experience Journey, Manage Stakeholder Interactions, Manage Experience Governance | Manage Experience Journeys, Manage Experience Optimisation, Manage Stakeholder Sentiment, Manage Voice of Customer |
| Manage Capital Core Operations | Manage Investment (Portfolio), Manage Funds (Portfolio), Manage Strategy (Portfolio) | Manage Investment Strategy, Manage Portfolio Construction, Manage Net Asset Valuation (NAV) Calculation, Manage Fund Performance |
| Manage Stock Exchange Core Operation | Manage Market Operations, Manage Market Control, Manage Trading, Manage Registry & Settlements | Manage Market Surveillance Monitoring, Manage Secondary Capital Market, Manage Clearing & Settlement, Manage Depository & Registry |

---

## 8. Dependency Map

The following cross-domain `ENABLES` relationships are critical architectural dependencies that must be modelled in the GraphRAG risk engine:

```
Manage Digital IT ──────────────────────────────────────► All 44 Sector Domains
Manage Digital Security ─────────────────────────────────► All 44 Sector Domains
Manage Digital Intelligence ──────────────────────────────► 35+ Sector Domains
Manage Digital Intelligence (Non Commercial) ────────────► 35+ Sector Domains
Manage Digital Backoffice ────────────────────────────────► Finance, HR, Legal Domains
Manage Digital Channels ─────────────────────────────────► Customer-facing Domains
Manage Digital Inter-Operability & Automation ───────────► Integration-dependent Domains
Manage Digital GPRC ─────────────────────────────────────► All Compliance-regulated Domains
Manage Digital Workspace ────────────────────────────────► All People-process Domains
Manage MarCom Orchestration ─────────────────────────────► Commercial and Public-facing Domains
```

**Highest Centrality Nodes (Contagion Risk):**

1. Manage Digital IT — betweenness centrality: highest (enables all domains)
2. Manage Digital Security — betweenness centrality: highest (enables all domains)
3. Manage Digital Intelligence — betweenness centrality: very high (cross-domain data intelligence)
4. Manage Digital Inter-Operability & Automation — betweenness centrality: high (API and automation layer)
5. Manage Digital Backoffice — betweenness centrality: high (financial and HR backbone)

---

## 9. Glossary

| Term | Definition |
|---|---|
| **Capability** | A specific business function or process skill mapped in the Digital Capability Canvas (1,295 total) |
| **Canvas** | The Digital Capability Canvas — a structured graph of Domains, SubDomains, Capabilities, Standards, Trends, Epics, and Features |
| **Cypher** | The query language used by Neo4j graph databases; the canvas is encoded as Cypher MERGE/MATCH statements |
| **Domain** | A top-level grouping in the canvas (44 total) representing a major digital or sector area |
| **ENABLES** | A graph relationship indicating that one Domain enables the operation of another |
| **Epic** | An agile backlog epic mapped 1:1 to a Capability in the canvas |
| **GraphRAG** | Graph Retrieval-Augmented Generation — combining knowledge graph traversal with LLM generation for grounded AI responses |
| **Maestro BPMN** | UiPath's BPMN 2.0 process modelling and execution engine within the UiPath Automation Cloud |
| **Maturity Score** | A quantitative score (0–5) indicating how fully an organisation has implemented a given capability |
| **Monte Carlo Simulation** | A statistical technique using random sampling to model probability distributions of outcomes |
| **Priority Score** | A composite financial-engineering score ranking capability gaps by risk-adjusted investment priority |
| **PARENT_OF** | A graph relationship indicating hierarchical ownership (Domain → SubDomain → Capability) |
| **RPA** | Robotic Process Automation — software robots that automate repetitive digital tasks |
| **SubDomain** | A mid-level grouping within a Domain (223 total) containing related Capabilities |
| **UiPath Agent Builder** | UiPath's low-code agent development tool within the Automation Cloud |
| **UiPath Orchestrator** | The central UiPath management console for monitoring robots, agents, and process instances |

---

*End of Document*

*This specification is prepared for the UiPath AgentHack 2026 submission under Track 2: UiPath Maestro BPMN.*  
*All capability data sourced from the Digital Capability Canvas (capability_canvas_3.cypher).*  
*Platform to be built using Claude Code as the primary coding agent, with UiPath as the orchestration and governance layer.*