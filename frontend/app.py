"""Streamlit frontend — AMD Enterprise Architecture Strategy Optimizer."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AMD EA Optimizer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from frontend.utils.api_client import get_health, analyze
from frontend.utils.terminology import TABS
from frontend.components.input_form import render_input_form
from frontend.components.roadmap_tab import render_roadmap_tab
from frontend.components.epics_tab import render_epics_tab
from frontend.components.export_tab import render_export_tab
from frontend.components.training_tab import render_training_tab
from frontend.components.chat_tab import render_chat_tab
from frontend.components.graph_explorer_tab import render_graph_explorer_tab
from frontend.components.integrations_tab import render_integrations_tab


def render_sidebar():
    with st.sidebar:
        st.image("https://www.amd.com/content/dam/amd/en/images/logos/amd-logo-2022-black.svg",
                 width=120)
        st.markdown("## EA Strategy Optimizer")
        st.markdown(
            "Powered by **AMD MI300X · ROCm · Qwen-72B**\n\n"
            "Knowledge Graph → AI Prioritiser → Qwen-72B on AMD MI300X → Compliance Validator"
        )
        st.divider()

        health = get_health()
        status = health.get("status", "unknown")
        color = "green" if status == "ok" else "orange" if status == "degraded" else "red"
        st.markdown(f"**Backend:** :{color}[{status}]")

        gpu = health.get("gpu") or {}
        if gpu.get("available"):
            st.markdown(f"**GPU:** {gpu.get('device', '')}")
            if gpu.get("rocm"):
                st.markdown(f"**ROCm:** {gpu['rocm']}")
        else:
            st.caption("GPU: CPU mode")

        neo4j_status = health.get("neo4j", "unknown")
        neo4j_color = "green" if neo4j_status == "connected" else "red"
        st.markdown(f"**Knowledge Graph:** :{neo4j_color}[{neo4j_status}]")

        st.divider()
        st.markdown(
            "**Track 1 — AI Agents & Agentic Workflows**\n\n"
            "AMD Developer Hackathon 2026\n\n"
            "[GitHub](https://github.com) | [HF Space](https://huggingface.co)"
        )


def main():
    render_sidebar()

    st.title("Enterprise Architecture Strategy Optimizer")
    st.markdown(
        "Transform business goals into **governance-grounded strategic roadmaps** — "
        "with Jira-ready initiatives, business scenarios, and regulatory obligations — "
        "powered by **AMD MI300X**, Knowledge Graph-RAG, and AI-driven prioritisation."
    )

    # ── Tabs — EA Advisor is the landing tab ─────────────────────────────────
    (
        tab_chat,
        tab_graph,
        tab_roadmap,
        tab_epics,
        tab_integrations,
        tab_export,
        tab_training,
    ) = st.tabs(TABS)

    # EA Advisor — always rendered
    with tab_chat:
        render_chat_tab()

    # Graph Explorer — always rendered
    with tab_graph:
        render_graph_explorer_tab()

    # Strategic Roadmap — input form + pipeline results
    with tab_roadmap:
        if "result" not in st.session_state:
            st.session_state["result"] = None

        payload = render_input_form()

        if payload is not None:
            with st.spinner(
                "Running agentic pipeline: "
                "Knowledge Graph → AI Prioritiser → Qwen-72B on AMD MI300X → Compliance Validator…"
            ):
                try:
                    result = analyze(payload)
                    st.session_state["result"] = result
                    st.success("Strategic roadmap generated successfully!")
                except Exception as exc:
                    st.error(f"Pipeline failed: {exc}")

        result = st.session_state.get("result")
        if result:
            render_roadmap_tab(result)
        else:
            st.info(
                "Fill in the Organisation Profile above and click **Generate Strategic Roadmap**, "
                "or use one of the demo scenario buttons."
            )

    with tab_epics:
        result = st.session_state.get("result")
        if result:
            render_epics_tab(result)
        else:
            st.info("Generate a strategic roadmap first to view Initiatives & Scenarios.")

    with tab_integrations:
        result = st.session_state.get("result")
        render_integrations_tab(result)

    with tab_export:
        result = st.session_state.get("result")
        if result:
            render_export_tab(result)
        else:
            st.info("Generate a strategic roadmap first to export.")

    # AI Learning Engine — always rendered
    with tab_training:
        render_training_tab()


if __name__ == "__main__":
    main()
