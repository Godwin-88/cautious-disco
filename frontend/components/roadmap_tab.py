"""Strategic Roadmap tab — Plotly Gantt chart + AI Prioritisation trace + AMD metrics."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from frontend.utils.terminology import label, domain_label, subdomain_label


PHASE_COLORS = {1: "#00C5E3", 2: "#FF5733", 3: "#27AE60"}


def render_amd_metrics(metrics: dict) -> None:
    st.markdown("#### AMD MI300X Performance")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label("gpu_device"), metrics.get("gpu_device") or "CPU")
    with col2:
        rocm = metrics.get("rocm_version") or "N/A"
        st.metric(label("rocm_version"), rocm)
    with col3:
        st.metric(label("processing_time"), f"{metrics.get('processing_time_seconds', 0):.1f}s")
    with col4:
        st.metric(label("capabilities_retrieved"), metrics.get("capabilities_retrieved", 0))


def render_drl_trace(drl_trace: dict) -> None:
    if not drl_trace:
        return
    with st.expander(label("drl_trace"), expanded=False):
        drl_used = drl_trace.get("drl_used", False)
        mode_label = label("drl_used_true") if drl_used else label("drl_used_false")
        st.caption(f"Mode: {mode_label}")
        cap_scores = drl_trace.get("capability_scores") or []
        if cap_scores:
            df = pd.DataFrame(
                [{"Strategic Capability": c["capability_name"], "Priority Score": round(c["score"], 3)}
                 for c in cap_scores[:10]]
            )
            fig = px.bar(
                df,
                x="Priority Score",
                y="Strategic Capability",
                orientation="h",
                color="Priority Score",
                color_continuous_scale="blues",
                title="AI Capability Prioritisation Scores",
            )
            fig.update_layout(height=350, showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig, width='stretch')


def render_gantt(phases: list[dict]) -> None:
    if not phases:
        st.info("No phases to display.")
        return

    rows: list[dict] = []
    start_month = 0
    for phase in phases:
        phase_num = phase.get("phase_number", 1)
        duration = phase.get("duration_months", 3)
        for epic in (phase.get("epics") or [])[:6]:
            rows.append({
                "Phase": f"Phase {phase_num}: {phase.get('phase_name', '')}",
                "Initiative": subdomain_label(epic.get("title") or "")[:45],
                "Start": start_month,
                "End": start_month + (epic.get("estimated_sprints", 4) * 2),
                "Capability Area": domain_label(epic.get("subdomain_group") or ""),
            })
        start_month += duration

    if not rows:
        return

    df = pd.DataFrame(rows)
    df["Start_Date"] = pd.to_datetime("2025-06-01") + pd.to_timedelta(df["Start"] * 30, unit="D")
    df["End_Date"] = pd.to_datetime("2025-06-01") + pd.to_timedelta(df["End"] * 30, unit="D")

    fig = px.timeline(
        df,
        x_start="Start_Date",
        x_end="End_Date",
        y="Initiative",
        color="Phase",
        hover_data=["Capability Area"],
        title="Strategic Roadmap Timeline",
    )
    fig.update_layout(height=max(400, len(rows) * 25), showlegend=True)
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, width='stretch')


def render_roadmap_tab(result: dict) -> None:
    metrics = result.get("amd_metrics") or {}
    render_amd_metrics(metrics)

    st.divider()
    phases = result.get("phases") or []
    total_initiatives = sum(len(p.get("epics", [])) for p in phases)
    st.markdown(
        f"### Strategic Roadmap — {len(phases)} Phases · "
        f"{total_initiatives} {label('epics')}"
    )

    render_gantt(phases)

    compliance = result.get("compliance_summary") or {}
    if compliance:
        score = compliance.get("score", 0)
        color = "green" if score >= 70 else "orange" if score >= 50 else "red"
        st.markdown(f"**{label('compliance_score')}:** :{color}[{score} / 100]")
        if compliance.get("standards_covered"):
            st.caption(
                f"{label('standards_covered')}: "
                + ", ".join(compliance["standards_covered"][:5])
            )

    render_drl_trace(result.get("drl_trace") or {})
