# Next.js Frontend Migration

## Goal
Migrate Streamlit frontend to Next.js 14+ with identical functionality, using App Router, TypeScript, and Tailwind. Retain backend as FastAPI.

## Stack
- **Next.js 14+** — App Router, TypeScript, Tailwind CSS
- **Charts** — `plotly.js-dist-min` + `react-plotly.js`
- **Graph** — `vis-network` (force-directed graph for Knowledge Graph Explorer)
- **State** — React Context + `localStorage` for chat sessions/results
- **Proxying** — All API calls routed through `app/api/backend/[...]/route.ts` (single origin, server-side environment injection)

## Migration Steps

### 1. Scaffold Next.js App
```bash
npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir --import-alias "@/*"
```
Rename existing `frontend/` to `frontend_old/`.

### 2. Install Dependencies
```bash
cd frontend
npm install plotly.js-dist-min react-plotly.js vis-network
npm install uuid
npm install -D @types/uuid
```

### 3. Environment Configuration
- Create `frontend/.env.local` with `BACKEND_URL=http://localhost:8080` (default)
- In Next.js API routes, read `BACKEND_URL` server-side to avoid exposing it to the browser

### 4. Create Backend Proxy Routes (`app/api/backend/[...]/path/route.ts`)
Wraps FastAPI endpoints:
- `GET /health` → `GET /api/v1/health`
- `POST /analyze` → `POST /api/v1/analyze`
- `GET /domains` → `GET /api/v1/domains`
- `GET /subdomains` → `GET /api/v1/subdomains`
- `GET /subdomain-capabilities` → `GET /api/v1/subdomain-capabilities`
- `GET/POST /chat` → `/api/v1/chat` (non-streaming)
- `GET /chat/stream` → `/api/v1/chat/stream` (SSE proxy using `ReadableStream`)
- `CRUD /chat/sessions` → `/api/v1/chat/sessions` (create/list/delete)
- `GET /chat/sessions/{id}/messages` → fetch history
- `GET /graph/network` → `/api/v1/graph/network`
- `GET /graph/domain-detail` → `/api/v1/graph/domain-detail`
- `GET /training/metrics`, `/training/coverage`, `/POST /training/run`
- `POST /integrations/jira/export`
- `POST /integrations/itsm/connect`
- `POST /integrations/erp/ingest` (multipart proxied)
- `GET /integrations/archimate`

### 5. Shared Utilities
- `lib/terminology.ts` — mirrors `frontend_old/utils/terminology.py` (LABELS, TABS, badges, label helpers)
- `lib/context.tsx` — React Context for global state (current result, chat history, sessions)

### 6. Page Shell (`app/page.tsx`)
- Server component rendering sidebar (AMD logo, health, GPU, Neo4j status, hackathon footer)
- Tab navigation (7 tabs) using client-side state
- Renders client tab components

### 7. Client Tab Components (`components/`)
Mirror `frontend_old/components/`:

| File | Purpose |
|------|---------|
| `chat-tab.tsx` | EA Advisor streaming chat with SSE, session panel, think-block handling |
| `graph-explorer-tab.tsx` | Force-directed `vis-network` graph + domain detail accordion |
| `input-form.tsx` | Hierarchical questionnaire (domain → subdomain → capability → constraints) |
| `roadmap-tab.tsx` | Plotly Gantt chart, AMD metrics, DRL trace, compliance score |
| `epics-tab.tsx` | Phases/initiatives accordion with workstreams, scenarios, acceptance criteria |
| `integrations-tab.tsx` | Jira export, ServiceNow/Azure DevOps mock, ERP CSV ingest, ArchiMate view |
| `export-tab.tsx` | Jira JSON, CSV, Markdown download |
| `training-tab.tsx` | Heatmap, reward curve, training trigger |

### 8. State Management
- `ChatProvider` in `lib/context.tsx` holds:
  - `chatSessionId` (UUID, persisted `localStorage`)
  - `chatHistory` (array with role/content/sources)
  - `result` (analyze payload, shared across tabs)
  - `lastChatSources`, `enrichInfo`
- Sidebar reads health from proxy on mount

### 9. SSE Handling
`chat-tab.tsx` uses a custom streaming hook fetching `/api/backend/chat/stream` via `fetch` with `ReadableStream` reader, parsing `text/event-stream` lines.

### 10. Styling & Layout
- Tailwind classes match Streamlit dark theme (`bg-[#0e1117]`, `text-white`, `bg-[#1a1d23]`)
- Sidebar fixed left; tab content scrollable
- AMD SVG logo referenced from `public/amd_logo.svg`

## Validation
1. `npm run build` passes with no TypeScript/lint errors
2. All 7 tabs render without backend (graceful empty states)
3. Chat streams with SSE fallback; sessions persist across refresh in `localStorage`
4. Roadmap form submits and populates Epics tab
5. Jira export form submits
6. CSV upload preview + ingest works
7. Graph Explorer loads network (or shows empty state if no backend)
8. Training tab renders heatmap from coverage data

## Rollout
- Build Next.js in `frontend/`
- Rename `frontend/` → `frontend_old/` **only after** parity confirmed
- Update docker-compose to serve Next.js instead of Streamlit
- Remove `requirements.frontend.txt` / Streamlit references from runbook

## Risks
- SSE proxying through Next.js adds minimal latency (< 100 ms on same origin)
- `localStorage` chat persistence is per-browser; for multi-device parity, backend sessions remain source of truth
- `vis-network` bundle size (~1 MB) acceptable; if critical, swap for `react-force-graph` or lazy-load
