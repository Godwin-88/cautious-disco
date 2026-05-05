"""EA Advisor — streaming conversational interface powered by AMD MI300X + Qwen-72B."""

import streamlit as st
from frontend.utils.api_client import stream_chat, chat as api_chat

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


def render_chat_tab():
    st.subheader("EA Advisor")
    st.caption(
        "Conversational AI for enterprise architecture "
        "— AMD MI300X · Qwen-72B · Knowledge Graph RAG · 1,416 capabilities"
    )

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = [{"role": "assistant", "content": _WELCOME}]
    if "_last_chat_sources" not in st.session_state:
        st.session_state["_last_chat_sources"] = []

    # Render existing messages
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            srcs = msg.get("sources") or []
            if srcs:
                with st.expander(f"Knowledge Graph Sources ({len(srcs)})", expanded=False):
                    for src in srcs:
                        name = src.get("name", "")
                        domain = src.get("domain", "")
                        st.caption(f"• **{name}** — {domain}")

    # Chat input
    if prompt := st.chat_input("Ask about enterprise architecture, governance, or capabilities…"):
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        history_for_api = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state["chat_history"][:-1]
        ]

        with st.chat_message("assistant"):
            st.session_state["_last_chat_sources"] = []
            try:
                full_response = st.write_stream(stream_chat(prompt, history_for_api))
            except Exception as exc:
                st.warning(f"Streaming unavailable — using standard mode: {exc}")
                try:
                    resp = api_chat(prompt, history_for_api)
                    full_response = resp.get("reply", "")
                    st.markdown(full_response)
                    st.session_state["_last_chat_sources"] = resp.get("sources", [])
                except Exception as exc2:
                    full_response = f"Error contacting EA Advisor: {exc2}"
                    st.error(full_response)

        sources = list(st.session_state.get("_last_chat_sources", []))
        st.session_state["chat_history"].append(
            {"role": "assistant", "content": full_response, "sources": sources}
        )

        if sources:
            with st.expander(f"Knowledge Graph Sources ({len(sources)})", expanded=False):
                for src in sources:
                    st.caption(f"• **{src.get('name', '')}** — {src.get('domain', '')}")

        if any(kw in prompt.lower() for kw in _ROADMAP_KEYWORDS):
            st.info(
                "Switch to the **Strategic Roadmap** tab to generate a full, "
                "Jira-ready roadmap with Epics, Features, User Stories, and Tasks.",
                icon="🗺️",
            )

    # Clear button
    if st.session_state.get("chat_history", []):
        _, clear_col = st.columns([8, 1])
        with clear_col:
            if st.button("Clear", type="secondary", use_container_width=True):
                st.session_state["chat_history"] = [
                    {"role": "assistant", "content": _WELCOME}
                ]
                st.session_state["_last_chat_sources"] = []
                st.rerun()
