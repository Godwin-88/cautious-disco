# AGENTS.md - AMD EA Optimizer

## Commands

### Development
- `npm run dev` (in frontend/) - Start Next.js dev server
- `npm run build` (in frontend/) - Build Next.js for production
- `npm run lint` - Run ESLint

### Docker
- `./scripts/start-infra.sh` - Build and start all services
- `docker compose up -d` - Start services
- `docker compose down` - Stop services
- `docker compose ps` - Check service status

### Backend
- `uvicorn backend.main:app --host 0.0.0.0 --port 8080` - Run backend locally
- `python -m backend.main` - Alternative run

## Stack
- Next.js 16.2.9 (App Router) + TypeScript + Tailwind CSS
- Plotly.js for charts
- vis-network for Knowledge Graph
- FastAPI backend
- Neo4j for graph database