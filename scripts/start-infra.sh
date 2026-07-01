#!/bin/bash

cd /home/ed/projects/cautious-disco

# Setup Python virtual environment if not exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
    echo "Installing backend dependencies..."
    .venv/bin/pip install -r requirements.backend.txt
fi

# Activate virtual environment
source .venv/bin/activate

# Kill any existing processes on these ports
lsof -ti:8080 | xargs -r kill 2>/dev/null || true
lsof -ti:3000 | xargs -r kill 2>/dev/null || true

echo "Starting Neo4j..."
docker compose up neo4j -d

# Wait for Neo4j
echo "Waiting for Neo4j to be ready..."
for i in {1..30}; do
  curl -s http://localhost:7475 > /dev/null 2>&1 && break
  sleep 1
done
echo "Neo4j is ready"

echo "Starting Backend on http://localhost:8080..."
nohup python -m uvicorn backend.main:app --host 0.0.0.0 --port 8080 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

echo "Starting Frontend on http://localhost:3000..."
cd frontend && nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo ""
echo "Services running:"
echo "  - Backend API: http://localhost:8080"
echo "  - Frontend:    http://localhost:3000"
echo "  - Neo4j Browser: http://localhost:7475"
echo ""
echo "Logs: /tmp/backend.log, /tmp/frontend.log"
echo "Stop with: kill $BACKEND_PID $FRONTEND_PID && docker compose stop neo4j"