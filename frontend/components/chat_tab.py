"""
EA Advisor — continuous streaming chat with Neo4j session persistence
and automatic DRL graph enrichment.
"""

import uuid
import streamlit as st

from frontend.utils.api_client import (
    stream_chat,
    chat as api_chat,
    create_or_touch_session,
    get_recent_sessions,
    get_session_messages,
    delete_session,
)

_WELCOME = (
    "Hello! I'm your **Enterprise Architecture Advisor**, powered by **AMD MI300X** and "
    "**Qwen-72B** with live access to a knowledge graph of **1,416 capabilities across 44 domains**.\n\n"
    "I can help you:\n"
    "- Explore governance standards and compliance requirements\n"
    "- Identify the right capabilities for your organisation\n"
    "- Understand cross-domain architecture patterns\n"
    "- Generate a strategic transformation roadmap\n\n"
    "What would you like to explore?"
)

_ROADMAP_KEYWORDS = {
    "roadmap", "strategy", "strategic", "plan", "planning",
    "implement", "transform", "programme", "program", "initiative",
}


# ---------------------------------------------------------------------------
# Session management helpers
# ---------------------------------------------------------------------------

def _new_session_id() -> str:
    return uuid.uuid4().hex


def _ensure_session() -> str:
    """Return current session_id, creating a new one if needed."""
    if "chat_session_id" not in st.session_state:
        sid = _new_session_id()
        st.session_state["chat_session_id"] = sid
        st.session_state["chat_history"] = [{"role": "assistant", "content": _WELCOME}]
        create_or_touch_session(sid, "New Conversation")
    return st.session_state["chat_session_id"]


def _load_session(session_id: str, title: str = ""):
    """Load a session from Neo4j into chat_history."""
    messages = get_session_messages(session_id)
    if messages:
        st.session_state["chat_session_id"] = session_id
        st.session_state["chat_session_title"] = title
        history = []
        for m in messages:
            history.append({
                "role": m["role"],
                "content": m["content"],
                "sources": m.get("sources", []),
            })
        st.session_state["chat_history"] = history
    else:
        # Session exists but no messages yet — just switch to it
        st.session_state["chat_session_id"] = session_id
        st.session_state["chat_session_title"] = title
        st.session_state["chat_history"] = [{"role": "assistant", "content": _WELCOME}]


def _start_new_session():
    sid = _new_session_id()
    st.session_state["chat_session_id"] = sid
    st.session_state["chat_session_title"] = "New Conversation"
    st.session_state["chat_history"] = [{"role": "assistant", "content": _WELCOME}]
    st.session_state["_last_chat_sources"] = []
    st.session_state["_last_enrich_info"] = {}
    create_or_touch_session(sid, "New Conversation")


# ---------------------------------------------------------------------------
# Session panel (rendered in sidebar area within the tab)
# ---------------------------------------------------------------------------

def _render_session_panel():
    with st.expander("Conversation History", expanded=False):
        col_new, col_refresh = st.columns([3, 1])
        with col_new:
            if st.button("New Conversation", type="primary", use_container_width=True):
                _start_new_session()
                st.rerun()
        with col_refresh:
            if st.button("↻", help="Refresh session list", use_container_width=True):
                st.session_state.pop("_cached_sessions", None)

        # Load sessions (cached briefly in session state)
        if "_cached_sessions" not in st.session_state:
            st.session_state["_cached_sessions"] = get_recent_sessions()

        sessions = st.session_state["_cached_sessions"]
        current_sid = st.session_state.get("chat_session_id", "")

        if not sessions:
            st.caption("No saved conversations yet.")
        else:
            st.caption(f"{len(sessions)} saved conversation(s)")
            for s in sessions:
                sid = s["session_id"]
                title = s.get("title", "Untitled")[:45]
                n_msgs = s.get("message_count", 0)
                last = (s.get("last_active", "") or "")[:16].replace("T", " ")
                is_current = sid == current_sid

                row_col, del_col = st.columns([5, 1])
                with row_col:
                    label = f"{'▶ ' if is_current else ''}{title}"
                    if st.button(
                        label,
                        key=f"sess_{sid}",
                        disabled=is_current,
                        use_container_width=True,
                        help=f"{n_msgs} messages · {last}",
                    ):
                        _load_session(sid, s.get("title", ""))
                        st.session_state.pop("_cached_sessions", None)
                        st.rerun()
                with del_col:
                    if st.button("🗑", key=f"del_{sid}", help="Delete this conversation"):
                        delete_session(sid)
                        st.session_state.pop("_cached_sessions", None)
                        if is_current:
                            _start_new_session()
                        st.rerun()


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render_chat_tab():
    st.subheader("EA Advisor")
    st.caption(
        "Conversational AI for enterprise architecture "
        "— AMD MI300X · Qwen-72B · Knowledge Graph RAG · 1,416 capabilities"
    )

    # ── Initialise state ──────────────────────────────────────────────────────
    session_id = _ensure_session()
    if "_last_chat_sources" not in st.session_state:
        st.session_state["_last_chat_sources"] = []
    if "_last_enrich_info" not in st.session_state:
        st.session_state["_last_enrich_info"] = {}

    # ── Session panel ─────────────────────────────────────────────────────────
    _render_session_panel()

    # ── DRL enrichment notification ───────────────────────────────────────────
    enrich_info = st.session_state.get("_last_enrich_info", {})
    if enrich_info.get("triggered"):
        domains_str = ", ".join(enrich_info.get("domains", []))
        st.toast(
            f"DRL enrichment started for: {domains_str}",
            icon="🧠",
        )
        st.session_state["_last_enrich_info"] = {}  # show once

    # ── Render all persisted messages ─────────────────────────────────────────
    for msg in st.session_state.get("chat_history", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            srcs = msg.get("sources") or []
            if srcs:
                with st.expander(f"Knowledge Graph Sources ({len(srcs)})", expanded=False):
                    for src in srcs:
                        st.caption(
                            f"• **{src.get('name', '')}** — {src.get('domain', '')}"
                            + (f" · {src.get('standard', '')}" if src.get("standard") else "")
                        )

    # ── Chat input ────────────────────────────────────────────────────────────
    if prompt := st.chat_input("Ask about enterprise architecture, governance, or capabilities…"):
        # 1. Append user message and render immediately
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Build history excluding the message we just appended
        history_for_api = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state["chat_history"][:-1]
        ]

        # 3. Stream assistant response
        st.session_state["_last_chat_sources"] = []
        st.session_state["_last_enrich_info"] = {}

        with st.chat_message("assistant"):
            try:
                full_response = st.write_stream(
                    stream_chat(prompt, history_for_api, session_id)
                )
            except Exception as exc:
                st.warning(f"Streaming unavailable — switching to standard mode: {exc}")
                try:
                    resp = api_chat(prompt, history_for_api, session_id=session_id)
                    full_response = resp.get("reply", "")
                    st.markdown(full_response)
                    st.session_state["_last_chat_sources"] = resp.get("sources", [])
                    st.session_state["_last_enrich_info"] = {
                        "triggered": resp.get("enrich_triggered", False),
                        "domains": resp.get("enrich_domains", []),
                    }
                except Exception as exc2:
                    full_response = f"Error contacting EA Advisor: {exc2}"
                    st.error(full_response)

        # 4. Collect metadata from SSE final event (written by stream_chat generator)
        sources = list(st.session_state.get("_last_chat_sources", []))

        # 5. Append assistant message to history with sources
        st.session_state["chat_history"].append({
            "role": "assistant",
            "content": full_response,
            "sources": sources,
        })

        # 6. Invalidate session cache so panel shows updated message count
        st.session_state.pop("_cached_sessions", None)

        # 7. Roadmap hint
        if any(kw in prompt.lower() for kw in _ROADMAP_KEYWORDS):
            st.info(
                "Switch to the **Strategic Roadmap** tab to generate a full, "
                "Jira-ready roadmap with Epics, Features, User Stories, and Tasks.",
                icon="🗺️",
            )

        # 8. Rerun → cleans render state so the user can type the next message
        #    immediately without stale widget state
        st.rerun()
