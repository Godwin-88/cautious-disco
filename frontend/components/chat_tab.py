"""
EA Advisor — continuous streaming chat with Neo4j session persistence
and automatic DRL graph enrichment.
"""

import re
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
# Think-block helpers
# ---------------------------------------------------------------------------

def _split_think(text: str) -> tuple[str, str]:
    """
    Split a model response into (think_content, response_text).

    Returns:
      ("", text)          — no <think> block present
      (partial, "")       — <think> started but </think> not yet seen (still streaming)
      (think, response)   — complete block; response is everything outside the tags
    """
    if not text:
        return "", ""
    start = text.find("<think>")
    if start == -1:
        return "", text
    end = text.find("</think>", start)
    if end == -1:
        return text[start + 7:].strip(), ""
    think_content = text[start + 7:end].strip()
    response = (text[:start] + text[end + 9:]).strip()
    return think_content, response


def _think_html(think_text: str) -> str:
    """Render think content as a collapsible HTML details block."""
    return (
        '<details style="margin-bottom:0.5rem">'
        '<summary style="cursor:pointer;color:#9ca3af;font-size:0.85rem">'
        '💭 Reasoning (click to expand / collapse)'
        '</summary>'
        f'\n\n{think_text}\n\n'
        '</details>'
    )


def _render_message_content(content: str):
    """Render a stored message, collapsing any <think> block."""
    think, response = _split_think(content)
    if think:
        st.markdown(_think_html(think), unsafe_allow_html=True)
    st.markdown(response if response else (content if not think else ""))


def _stream_assistant_response(prompt: str, history_for_api: list, session_id: str) -> str:
    """
    Stream the response into two Streamlit placeholders:
      - think_slot  → collapsed <details> block while model reasons
      - reply_slot  → the actual answer, streamed token-by-token

    Returns the clean response text (no think tags) for storing in history.
    """
    think_slot = st.empty()
    reply_slot = st.empty()

    full = ""
    reply_text = ""

    try:
        for token in stream_chat(prompt, history_for_api, session_id):
            full += token
            think, response = _split_think(full)

            if think and response:
                # Think block fully closed — show collapsed + stream response
                think_slot.markdown(_think_html(think), unsafe_allow_html=True)
                reply_slot.markdown(response + "▌")
                reply_text = response

            elif think and not response:
                # Still inside think block — show live word count
                word_count = len(think.split())
                think_slot.markdown(
                    f'<p style="color:#9ca3af;font-size:0.85rem">'
                    f'💭 Reasoning… ({word_count} words)</p>',
                    unsafe_allow_html=True,
                )

            else:
                # No think block at all — plain response
                reply_slot.markdown(full + "▌")
                reply_text = full

        # Final render — remove cursor, ensure think block is collapsed
        think, response = _split_think(full)
        if think:
            think_slot.markdown(_think_html(think), unsafe_allow_html=True)
        final_reply = response if response else (full if not think else "")
        reply_slot.markdown(final_reply)
        reply_text = final_reply

    except Exception as exc:
        st.warning(f"Streaming unavailable — switching to standard mode: {exc}")
        try:
            resp = api_chat(prompt, history_for_api, session_id=session_id)
            raw = resp.get("reply", "")
            think, response = _split_think(raw)
            if think:
                think_slot.markdown(_think_html(think), unsafe_allow_html=True)
            reply_text = response if response else raw
            reply_slot.markdown(reply_text)
            st.session_state["_last_chat_sources"] = resp.get("sources", [])
            st.session_state["_last_enrich_info"] = {
                "triggered": resp.get("enrich_triggered", False),
                "domains": resp.get("enrich_domains", []),
            }
        except Exception as exc2:
            reply_text = f"Error contacting EA Advisor: {exc2}"
            reply_slot.error(reply_text)

    return reply_text


# ---------------------------------------------------------------------------
# Session management helpers
# ---------------------------------------------------------------------------

def _new_session_id() -> str:
    return uuid.uuid4().hex


def _ensure_session() -> str:
    if "chat_session_id" not in st.session_state:
        sid = _new_session_id()
        st.session_state["chat_session_id"] = sid
        st.session_state["chat_history"] = [{"role": "assistant", "content": _WELCOME}]
        create_or_touch_session(sid, "New Conversation")
    return st.session_state["chat_session_id"]


def _load_session(session_id: str, title: str = ""):
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
# Session panel
# ---------------------------------------------------------------------------

def _render_session_panel():
    with st.expander("Conversation History", expanded=False):
        col_new, col_refresh = st.columns([3, 1])
        with col_new:
            if st.button("New Conversation", type="primary", width='stretch'):
                _start_new_session()
                st.rerun()
        with col_refresh:
            if st.button("↻", help="Refresh session list", width='stretch'):
                st.session_state.pop("_cached_sessions", None)

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
                        width='stretch',
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

    session_id = _ensure_session()
    if "_last_chat_sources" not in st.session_state:
        st.session_state["_last_chat_sources"] = []
    if "_last_enrich_info" not in st.session_state:
        st.session_state["_last_enrich_info"] = {}

    _render_session_panel()

    enrich_info = st.session_state.get("_last_enrich_info", {})
    if enrich_info.get("triggered"):
        domains_str = ", ".join(enrich_info.get("domains", []))
        st.toast(f"DRL enrichment started for: {domains_str}", icon="🧠")
        st.session_state["_last_enrich_info"] = {}

    # ── Render persisted messages ─────────────────────────────────────────────
    for msg in st.session_state.get("chat_history", []):
        with st.chat_message(msg["role"]):
            _render_message_content(msg["content"])
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
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        history_for_api = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state["chat_history"][:-1]
        ]

        st.session_state["_last_chat_sources"] = []
        st.session_state["_last_enrich_info"] = {}

        with st.chat_message("assistant"):
            full_response = _stream_assistant_response(prompt, history_for_api, session_id)

        sources = list(st.session_state.get("_last_chat_sources", []))

        # Store the clean response (think block stripped) so history replays cleanly
        st.session_state["chat_history"].append({
            "role": "assistant",
            "content": full_response,
            "sources": sources,
        })

        st.session_state.pop("_cached_sessions", None)

        if any(kw in prompt.lower() for kw in _ROADMAP_KEYWORDS):
            st.info(
                "Switch to the **Strategic Roadmap** tab to generate a full, "
                "Jira-ready roadmap with Epics, Features, User Stories, and Tasks.",
                icon="🗺️",
            )

        st.rerun()
