#!/usr/bin/env bash
# deploy_hf.sh — Push this project to a Hugging Face Space (Docker SDK)
#
# Usage:
#   ./deploy_hf.sh <hf-space-url>
#
# Example:
#   ./deploy_hf.sh https://huggingface.co/spaces/Godwin-88/amd-ea-optimizer
#
# Prerequisites:
#   - git and git-lfs installed  (sudo apt install git-lfs)
#   - Logged in to HF:  huggingface-cli login

set -euo pipefail

HF_SPACE_URL="${1:-}"
if [[ -z "$HF_SPACE_URL" ]]; then
  echo "Usage: $0 <hf-space-url>"
  echo "  e.g. $0 https://huggingface.co/spaces/Godwin-88/amd-ea-optimizer"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
STAGING=$(mktemp -d)

echo "==> Staging to $STAGING"

# ── HF Space root files ───────────────────────────────────────────────────────
cp "$REPO_ROOT/hf_space/Dockerfile"        "$STAGING/Dockerfile"
cp "$REPO_ROOT/hf_space/README.md"         "$STAGING/README.md"
cp "$REPO_ROOT/hf_space/supervisord.conf"  "$STAGING/supervisord.conf"
cp "$REPO_ROOT/hf_space/entrypoint.sh"     "$STAGING/entrypoint.sh"
chmod +x "$STAGING/entrypoint.sh"

# ── Python requirements ───────────────────────────────────────────────────────
cp "$REPO_ROOT/requirements.backend.txt"   "$STAGING/"
cp "$REPO_ROOT/requirements.frontend.txt"  "$STAGING/"

# ── Application source ────────────────────────────────────────────────────────
cp -r "$REPO_ROOT/backend"                 "$STAGING/"
cp -r "$REPO_ROOT/frontend"               "$STAGING/"
mkdir -p "$STAGING/pipeline"
cp -r "$REPO_ROOT/pipeline/knowledge_sources" "$STAGING/pipeline/"
cp "$REPO_ROOT/pipeline/embed_nodes.py"       "$STAGING/pipeline/"
cp "$REPO_ROOT/pipeline/__init__.py"          "$STAGING/pipeline/"

# ── Neo4j graph seed (plain text Cypher — no LFS required) ───────────────────
mkdir -p "$STAGING/neo4j_backup"
cp "$REPO_ROOT/hf_space/neo4j_backup/seed_graph.cypher" "$STAGING/neo4j_backup/"

# ── Clean Python cache ────────────────────────────────────────────────────────
find "$STAGING" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$STAGING" -name "*.pyc" -delete 2>/dev/null || true

echo "==> Staged files:"
find "$STAGING" -type f | sort
echo "==> Total size: $(du -sh "$STAGING" | cut -f1)"

# ── Git init and push ─────────────────────────────────────────────────────────
cd "$STAGING"
git init -b main

git add .
git commit -m "deploy: AMD EA Strategy Optimizer — Neo4j + FastAPI + Streamlit"

echo ""
echo "==> Pushing to $HF_SPACE_URL"
git remote add huggingface "$HF_SPACE_URL"
git push huggingface main --force

echo ""
echo "======================================================"
echo "  Deployment pushed successfully!"
echo "  Space URL: $HF_SPACE_URL"
echo "  Build takes ~8-12 min (Java + Neo4j + torch CPU)"
echo "  Watch build logs in the HF Space 'Logs' tab"
echo "======================================================"

rm -rf "$STAGING"
