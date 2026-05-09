"""
Chat endpoints — streaming EA Advisor with session persistence and DRL enrichment.
Powered by AMD MI300X + Knowledge Graph RAG.
"""

import asyncio
import json
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.config import Settings, get_settings
from backend.dependencies import get_neo4j_client, get_llm_client
from backend.graph.neo4j_client import Neo4jClient
from backend.graph.cypher_queries import (
    ENSURE_CHAT_SESSION,
    APPEND_CHAT_EXCHANGE,
    GET_SESSION_MESSAGES,
    GET_RECENT_CHAT_SESSIONS,
    DELETE_CHAT_SESSION,
    CHECK_DOMAIN_DRL_STATUS,
)
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify_intent(message: str) -> str:
    msg = message.lower()
    if any(kw in msg for kw in ["roadmap", "transformation plan", "implementation plan"]):
        return "generate_roadmap"
    if any(kw in msg for kw in ["show me", "list", "what domains", "explore"]):
        return "explore_domain"
    return "general_qa"


async def _build_rag_context(
    message: str,
    neo4j: Neo4jClient,
    llm: LLMClient,
) -> tuple[str, list[dict], list[str]]:
    """
    Run graph RAG.
    Returns (context_str, sources_list, domain_names_retrieved).
    """
    from backend.agents.retriever import RetrieverAgent
    retriever = RetrieverAgent(neo4j=neo4j, llm=llm)
    try:
        caps = await retriever.retrieve(org_type=message[:80], goals=[message], sectors=[])
    except Exception as exc:
        log.warning(f"RAG retrieval failed: {exc}")
        caps = []

    sources: list[dict] = []
    context_lines: list[str] = []
    domain_names: list[str] = []

    for c in caps[:6]:
        cap = c.capability
        std = c.standard or {}
        trend = c.trend or {}
        name = cap.get("name", "")
        domain = c.domain.get("name", "")
        outcomes = (cap.get("business_outcomes") or [])[:2]

        context_lines.append(
            f"- Capability: {name} (Domain: {domain})\n"
            f"  Outcomes: {'; '.join(outcomes)}\n"
            f"  Governance: {std.get('name', '')}\n"
            f"  Trend: {trend.get('name', '')}"
        )
        sources.append({
            "name": name,
            "domain": domain,
            "standard": std.get("name", ""),
            "trend": trend.get("name", ""),
        })
        if domain and domain not in domain_names:
            domain_names.append(domain)

    context = "\n".join(context_lines) if context_lines else "No specific capabilities matched."
    return context, sources, domain_names


def _build_messages(history: list[dict], user_message: str, context: str) -> list[dict]:
    messages = []
    for msg in history[-8:]:
        if msg.get("role") in ("user", "assistant") and msg.get("content"):
            # Skip the initial welcome assistant message to avoid invalid conversation order
            if msg["role"] == "assistant" and "Enterprise Architecture Advisor" in msg["content"]:
                continue
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({
        "role": "user",
        "content": f"KNOWLEDGE GRAPH CONTEXT:\n{context}\n\nQUESTION: {user_message}",
    })
    return messages


def _get_untrained_domains(domain_names: list[str], neo4j: Neo4jClient) -> list[str]:
    """Return subset of domain_names that have not yet been DRL-trained."""
    if not domain_names:
        return []
    try:
        rows = neo4j.run_query(CHECK_DOMAIN_DRL_STATUS, domain_names=domain_names)
        return [r["name"] for r in rows if not r.get("trained")]
    except Exception as exc:
        log.warning(f"DRL status check failed: {exc}")
        return []


async def _trigger_drl_enrichment(domain_names: list[str]) -> str:
    """Fire-and-forget background DRL training for untrained domains."""
    run_id = uuid.uuid4().hex[:10]

    async def _run():
        try:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            from neo4j import GraphDatabase
            from pipeline.train_on_graph import GraphTrainer

            driver = GraphDatabase.driver(
                os.getenv("NEO4J_URI"),
                auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
            )
            try:
                trainer = GraphTrainer(driver, os.getenv("NEO4J_DATABASE", "neo4j"))
                loop = asyncio.get_event_loop()
                for domain in domain_names:
                    await loop.run_in_executor(
                        None,
                        lambda d=domain: trainer.run(episodes_per_domain=50, target_domain=d),
                    )
                log.info(f"DRL enrichment {run_id} complete for: {domain_names}")
            finally:
                driver.close()
        except Exception as exc:
            log.warning(f"DRL enrichment {run_id} failed: {exc}")

    asyncio.create_task(_run())
    return run_id


def _store_exchange(
    neo4j: Neo4jClient,
    session_id: str,
    user_content: str,
    asst_content: str,
    sources: list[dict],
    title: str,
) -> None:
    """Persist a user↔assistant exchange to Neo4j."""
    try:
        neo4j.run_query(ENSURE_CHAT_SESSION, session_id=session_id, title=title)
        neo4j.run_query(
            APPEND_CHAT_EXCHANGE,
            session_id=session_id,
            user_msg_id=uuid.uuid4().hex,
            user_content=user_content,
            asst_msg_id=uuid.uuid4().hex,
            asst_content=asst_content,
            sources_json=json.dumps(sources),
        )
    except Exception as exc:
        log.warning(f"Failed to store chat exchange: {exc}")


# ---------------------------------------------------------------------------
# Session management endpoints
# ---------------------------------------------------------------------------

@router.post("/chat/sessions")
async def create_session(
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
    session_id: str | None = None,
    title: str = "",
):
    """Create or touch a chat session. Returns session_id."""
    sid = session_id or uuid.uuid4().hex
    try:
        neo4j.run_query(ENSURE_CHAT_SESSION, session_id=sid, title=title or "New Conversation")
    except Exception as exc:
        log.warning(f"Session create failed: {exc}")
    return {"session_id": sid}


@router.get("/chat/sessions")
async def list_sessions(neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)]):
    """Return the 15 most recent chat sessions."""
    try:
        rows = neo4j.run_query(GET_RECENT_CHAT_SESSIONS)
        return [
            {
                "session_id": r["session_id"],
                "title": r.get("title", "Untitled"),
                "last_active": r.get("last_active", ""),
                "message_count": r.get("message_count", 0),
            }
            for r in rows
        ]
    except Exception as exc:
        log.warning(f"List sessions failed: {exc}")
        return []


@router.get("/chat/sessions/{session_id}/messages")
async def get_session(
    session_id: str,
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
):
    """Return all messages for a session."""
    try:
        rows = neo4j.run_query(GET_SESSION_MESSAGES, session_id=session_id)
        messages = []
        for r in rows:
            srcs = []
            try:
                srcs = json.loads(r.get("sources_json", "[]"))
            except Exception:
                pass
            messages.append({
                "role": r["role"],
                "content": r["content"],
                "sources": srcs,
                "created_at": r.get("created_at", ""),
            })
        return {"session_id": session_id, "messages": messages}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/chat/sessions/{session_id}")
async def delete_session(
    session_id: str,
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
):
    """Delete a chat session and all its messages."""
    try:
        neo4j.run_query(DELETE_CHAT_SESSION, session_id=session_id)
        return {"deleted": session_id}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Chat endpoints
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    domain_filter: str | None = None
    session_id: str | None = None


@router.post("/chat")
async def chat(
    request: ChatRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
    llm: Annotated[LLMClient, Depends(get_llm_client)],
):
    intent = _classify_intent(request.message)
    context, sources, domain_names = await _build_rag_context(request.message, neo4j, llm)
    messages = _build_messages(request.history, request.message, context)

    reply = await llm.chat(
        messages=messages,
        system=CHAT_SYSTEM,
        max_tokens=settings.llm_max_tokens,
        temperature=0.4,
    )

    # Persist if session provided
    if request.session_id:
        title = request.message[:60]
        _store_exchange(neo4j, request.session_id, request.message, reply, sources, title)

    # Check DRL enrichment
    untrained = _get_untrained_domains(domain_names, neo4j)
    enrich_run_id = None
    if untrained:
        enrich_run_id = await _trigger_drl_enrichment(untrained)
        log.info(f"DRL enrichment triggered for: {untrained} (run {enrich_run_id})")

    return {
        "reply": reply,
        "sources": sources,
        "suggested_action": intent if intent != "general_qa" else None,
        "enrich_triggered": bool(untrained),
        "enrich_domains": untrained,
    }


@router.get("/chat/stream")
async def chat_stream(
    message: str = Query(...),
    history: str = Query(default="[]"),
    session_id: str = Query(default=""),
    settings: Annotated[Settings, Depends(get_settings)] = None,
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)] = None,
    llm: Annotated[LLMClient, Depends(get_llm_client)] = None,
):
    history_list: list[dict] = []
    try:
        history_list = json.loads(history)
    except Exception:
        pass

    context, sources, domain_names = await _build_rag_context(message, neo4j, llm)
    messages = _build_messages(history_list, message, context)

    # Check untrained domains before streaming
    untrained = _get_untrained_domains(domain_names, neo4j)

    async def generate():
        full_chunks: list[str] = []
        try:
            async for chunk in llm.chat_stream(
                messages=messages,
                system=CHAT_SYSTEM,
                max_tokens=settings.llm_max_tokens,
            ):
                full_chunks.append(chunk)
                yield f"data: {json.dumps({'text': chunk})}\n\n"
        except Exception as exc:
            log.error(f"Stream error: {exc}")
            yield f"data: {json.dumps({'text': f' [Stream error: {exc}]'})}\n\n"
        finally:
            full_response = "".join(full_chunks)

            # Persist exchange
            if session_id:
                title = message[:60]
                _store_exchange(neo4j, session_id, message, full_response, sources, title)

            # Trigger DRL enrichment in background
            enrich_run_id = None
            if untrained:
                try:
                    enrich_run_id = await _trigger_drl_enrichment(untrained)
                    log.info(f"DRL enrichment triggered for {untrained} (run {enrich_run_id})")
                except Exception as exc:
                    log.warning(f"DRL trigger failed: {exc}")

            yield f"data: {json.dumps({'sources': sources, 'enrich_triggered': bool(untrained), 'enrich_domains': untrained, 'enrich_run_id': enrich_run_id, 'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
