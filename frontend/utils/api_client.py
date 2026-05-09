"""HTTP client for FastAPI backend."""

import os
import requests
from typing import Any

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")


def _url(path: str) -> str:
    return f"{BACKEND_URL}{path}"


def get_health() -> dict:
    try:
        r = requests.get(_url("/api/v1/health"), timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"status": "unreachable", "error": str(exc)}


def get_domains() -> list[dict]:
    try:
        r = requests.get(_url("/api/v1/domains"), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def get_subdomains(domain_names: list[str]) -> list[dict]:
    try:
        r = requests.get(
            _url("/api/v1/subdomains"),
            params=[("domain_names", n) for n in domain_names],
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def get_subdomain_capabilities(subdomain_ids: list[str]) -> list[dict]:
    try:
        r = requests.get(
            _url("/api/v1/subdomain-capabilities"),
            params=[("subdomain_ids", sid) for sid in subdomain_ids],
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def analyze(payload: dict, timeout: int = 600) -> dict:
    r = requests.post(_url("/api/v1/analyze"), json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def get_training_metrics() -> list[dict]:
    try:
        r = requests.get(_url("/api/v1/training/metrics"), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def get_training_coverage() -> list[dict]:
    try:
        r = requests.get(_url("/api/v1/training/coverage"), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def trigger_training(episodes_per_domain: int = 50, domain: str | None = None) -> dict:
    payload: dict = {"episodes_per_domain": episodes_per_domain}
    if domain:
        payload["domain"] = domain
    try:
        r = requests.post(_url("/api/v1/training/run"), json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

def chat(
    message: str,
    history: list[dict],
    domain_filter: str | None = None,
    session_id: str | None = None,
) -> dict:
    """Non-streaming chat — returns {reply, sources, suggested_action, enrich_triggered}."""
    try:
        payload: dict = {"message": message, "history": history}
        if domain_filter:
            payload["domain_filter"] = domain_filter
        if session_id:
            payload["session_id"] = session_id
        r = requests.post(_url("/api/v1/chat"), json=payload, timeout=120)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"reply": f"Error: {exc}", "sources": [], "suggested_action": None,
                "enrich_triggered": False, "enrich_domains": []}


def stream_chat(message: str, history: list[dict], session_id: str = ""):
    """
    Generator: streams SSE tokens from /api/v1/chat/stream.
    Yields text chunks. Final SSE event stores sources + enrichment info
    in st.session_state['_last_chat_sources'] and ['_last_enrich_info'].
    """
    import json as _json

    params = {"message": message, "history": _json.dumps(history), "session_id": session_id}
    try:
        with requests.get(
            _url("/api/v1/chat/stream"), params=params, stream=True, timeout=600
        ) as r:
            r.raise_for_status()
            for raw in r.iter_lines():
                if not raw:
                    continue
                line = raw if isinstance(raw, str) else raw.decode("utf-8", errors="replace")
                if not line.startswith("data: "):
                    continue
                try:
                    event = _json.loads(line[6:])
                except Exception:
                    continue
                if event.get("text"):
                    yield event["text"]
                elif event.get("done"):
                    try:
                        import streamlit as _st
                        _st.session_state["_last_chat_sources"] = event.get("sources", [])
                        _st.session_state["_last_enrich_info"] = {
                            "triggered": event.get("enrich_triggered", False),
                            "domains": event.get("enrich_domains", []),
                            "run_id": event.get("enrich_run_id"),
                        }
                    except Exception:
                        pass
    except Exception as exc:
        yield f"\n\n*Stream error: {exc}*"


# ---------------------------------------------------------------------------
# Chat session management
# ---------------------------------------------------------------------------

def create_or_touch_session(session_id: str, title: str = "") -> dict:
    """POST /api/v1/chat/sessions — create or touch a session."""
    try:
        r = requests.post(
            _url("/api/v1/chat/sessions"),
            params={"session_id": session_id, "title": title},
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"session_id": session_id, "error": str(exc)}


def get_recent_sessions() -> list[dict]:
    """GET /api/v1/chat/sessions — list recent sessions."""
    try:
        r = requests.get(_url("/api/v1/chat/sessions"), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def get_session_messages(session_id: str) -> list[dict]:
    """GET /api/v1/chat/sessions/{id}/messages — load full session history."""
    try:
        r = requests.get(_url(f"/api/v1/chat/sessions/{session_id}/messages"), timeout=10)
        r.raise_for_status()
        return r.json().get("messages", [])
    except Exception:
        return []


def delete_session(session_id: str) -> bool:
    """DELETE /api/v1/chat/sessions/{id}."""
    try:
        r = requests.delete(_url(f"/api/v1/chat/sessions/{session_id}"), timeout=10)
        return r.status_code == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Graph network
# ---------------------------------------------------------------------------

def get_network_graph() -> dict:
    """Returns {nodes: [...], edges: [...]} for the knowledge graph explorer."""
    try:
        r = requests.get(_url("/api/v1/graph/network"), timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {"nodes": [], "edges": []}


# ---------------------------------------------------------------------------
# Integrations
# ---------------------------------------------------------------------------

def export_to_jira(payload: dict) -> dict:
    """POST to /api/v1/integrations/jira/export — returns {created_epics, created_stories, errors}."""
    r = requests.post(_url("/api/v1/integrations/jira/export"), json=payload, timeout=120)
    r.raise_for_status()
    return r.json()


def connect_itsm(tool: str, instance_url: str, credentials: dict) -> dict:
    """POST to /api/v1/integrations/itsm/connect — mock integration test."""
    payload = {"tool": tool, "instance_url": instance_url, "credentials": credentials}
    r = requests.post(_url("/api/v1/integrations/itsm/connect"), json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def ingest_erp_csv(file_bytes: bytes, filename: str) -> dict:
    """POST multipart CSV to /api/v1/integrations/erp/ingest."""
    files = {"file": (filename, file_bytes, "text/csv")}
    r = requests.post(_url("/api/v1/integrations/erp/ingest"), files=files, timeout=60)
    r.raise_for_status()
    return r.json()


def get_archimate() -> dict:
    """GET /api/v1/integrations/archimate — returns {business, application, technology}."""
    try:
        r = requests.get(_url("/api/v1/integrations/archimate"), timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {"business": [], "application": [], "technology": []}
