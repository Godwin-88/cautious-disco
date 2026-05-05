---
title: AMD Enterprise Architecture Optimizer
emoji: ⚡
colorFrom: red
colorTo: blue
sdk: docker
pinned: true
license: apache-2.0
app_port: 7860
---

# AMD Enterprise Architecture Optimizer

**Powered by AMD MI300X + ROCm | Graph-RAG + DRL + Qwen-72B**

Transform business goals into compliance-grounded EA implementation roadmaps in seconds.

## What it does

1. **Graph-RAG Retrieval** — queries 1,400+ enterprise capabilities from Neo4j knowledge graph with vector similarity search
2. **DRL Prioritization** — REINFORCE policy network (trained on AMD ROCm) prioritises capabilities by business value, budget, and risk
3. **Qwen-72B Generation** — derives Jira-ready epics, user stories, and acceptance criteria directly from graph-structured governance standards and transformation trends
4. **Compliance Verification** — self-correcting loop ensures every compliance requirement from TOGAF, ISO 27001, NIST, etc. appears as an acceptance criterion

## Architecture

```
User Input → Graph-RAG Retriever → DRL Optimizer (AMD ROCm)
           → Qwen-72B Generator (AMD MI300X via vLLM)
           → Compliance Verifier → Roadmap Output
```

## Try It

Select a demo scenario (Healthcare, Banking, Energy) or enter your own organisation profile.

## AMD Hackathon 2026 — Track 1: AI Agents & Agentic Workflows
