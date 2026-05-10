#!/bin/bash
set -e

echo "Starting AMD EA Optimizer infrastructure..."

# Build and start all services
docker compose up --build -d

echo "Waiting for services to be ready..."
sleep 10

# Show status
docker compose ps

echo ""
echo "Services started:"
echo "  - Backend API: http://localhost:8080"
echo "  - Frontend:    http://localhost:3000"
echo "  - Neo4j:       http://localhost:7475"
echo ""
echo "View logs with: docker compose logs -f"