"""Chat endpoints — streaming EA Advisor powered by AMD MI300X + Knowledge Graph RAG."""

import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.config import Settings, get_settings
from backend.dependencies import get_neo4j_client, get_llm_client
from backend.graph.neo4j_client import Neo4jClient
from backend.llm.client import LLMClient

log = logging.getLogger(__name__)
router = APIRouter()

CHAT_SYSTEM = """You are an Enterprise Architecture Advisor powered by AMD MI300X and Qwen-72B.
You have access to a knowledge graph containing 1,416 enterprise capabilities across 44 strategic domains,
44 governance standards, and 44 digital transformation trends.
Answer questions about enterprise architecture, digital transformation, governance, compliance, and technology strategy.
Be specific and actionable. Cite specific capabilities, governance standards, and trends from the context provided.
When relevant, mention which domain or subdomain a capability belongs to.
If asked to generate a roadmap, suggest the user use the Strategic Roadmap tab for a full structured output."""


def _classify_intent(message: str) -> str:
    msg = message.lower()
    if any(kw in msg for kw in ["roadmap", "transformation plan", "implementation plan", "strategy plan"]):
        return "generate_roadmap"
    if any(kw in msg for kw in ["show me", "list", "what domains", "what capabilities", "explore"]):
        return "explore_domain"
    return "general_qa"


async def _build_rag_context(
    message: str,
    neo4j: Neo4jClient,
    llm: LLMClient,
) -> tuple[str, list[dict]]:
    """Run graph RAG: embed query → retrieve enriched capabilities → build context string."""
    from backend.agents.retriever import RetrieverAgent
    retriever = RetrieverAgent(neo4j=neo4j, llm=llm)
    try:
        caps = await retriever.retrieve(
            org_type=message[:80],
            goals=[message],
            sectors=[],
        )
    except Exception as exc:
        log.warning(f"RAG retrieval failed: {exc}")
        caps = []

    sources = []
    context_lines = []
    for c in caps[:6]:
        cap = c.capability
        std = c.standard or {}
        trend = c.trend or {}
        name = cap.get("name", "")
        domain = c.domain.get("name", "")
        outcomes = (cap.get("business_outcomes") or [])[:2]
        std_name = std.get("name", "")
        trend_name = trend.get("name", "")

        context_lines.append(
            f"- Capability: {name} (Domain: {domain})\n"
            f"  Outcomes: {'; '.join(outcomes)}\n"
            f"  Governance: {std_name}\n"
            f"  Trend: {trend_name}"
        )
        sources.append({"name": name, "domain": domain, "standard": std_name, "trend": trend_name})

    context = "\n".join(context_lines) if context_lines else "No specific capabilities matched."
    return context, sources


def _build_messages(history: list[dict], user_message: str, context: str) -> list[dict]:
    messages = []
    # Include last 6 turns of history to keep context manageable
    for msg in history[-6:]:
        if msg.get("role") in ("user", "assistant") and msg.get("content"):
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({
        "role": "user",
        "content": (
            f"KNOWLEDGE GRAPH CONTEXT:\n{context}\n\n"
            f"QUESTION: {user_message}"
        ),
    })
    return messages


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    domain_filter: str | None = None


@router.post("/chat")
async def chat(
    request: ChatRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
    llm: Annotated[LLMClient, Depends(get_llm_client)],
):
    intent = _classify_intent(request.message)
    context, sources = await _build_rag_context(request.message, neo4j, llm)
    messages = _build_messages(request.history, request.message, context)

    suggested_action = intent if intent != "general_qa" else None
    if intent == "generate_roadmap":
        suggested_action = "generate_roadmap"

    reply = await llm.chat(
        messages=messages,
        system=CHAT_SYSTEM,
        max_tokens=settings.llm_max_tokens,
        temperature=0.4,
    )
    return {"reply": reply, "sources": sources, "suggested_action": suggested_action}


@router.get("/chat/stream")
async def chat_stream(
    message: str = Query(...),
    history: str = Query(default="[]"),
    settings: Annotated[Settings, Depends(get_settings)] = None,
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)] = None,
    llm: Annotated[LLMClient, Depends(get_llm_client)] = None,
):
    history_list: list[dict] = []
    try:
        history_list = json.loads(history)
    except Exception:
        pass

    context, sources = await _build_rag_context(message, neo4j, llm)
    messages = _build_messages(history_list, message, context)

    async def generate():
        try:
            async for chunk in llm.chat_stream(
                messages=messages,
                system=CHAT_SYSTEM,
                max_tokens=settings.llm_max_tokens,
            ):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
        except Exception as exc:
            log.error(f"Stream error: {exc}")
            yield f"data: {json.dumps({'text': f' [Error: {exc}]'})}\n\n"
        finally:
            yield f"data: {json.dumps({'sources': sources, 'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
