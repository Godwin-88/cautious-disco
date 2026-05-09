"""Knowledge Graph Training tab — enrichment heatmap + reward curve + training control."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from frontend.utils.api_client import get_training_metrics, get_training_coverage, trigger_training
from frontend.utils.terminology import domain_label


def render_training_tab():
    st.subheader("AI Learning Engine")
    st.markdown(
        "The **AI Prioritisation Engine** trains on every strategic domain in the knowledge graph. "
        "Each learning session is recorded as a node in Neo4j — the graph continuously improves itself, "
        "grounding capability prioritisation in sector-specific governance frameworks and innovation drivers."
    )

    coverage = get_training_coverage()
    metrics = get_training_metrics()

    # ── Section A: Summary metrics ──────────────────────────────────────────
    total = len(coverage)
    trained = sum(1 for d in coverage if d.get("drl_trained"))
    std_enriched = sum(1 for d in coverage if d.get("standard_enriched"))
    trend_enriched = sum(1 for d in coverage if d.get("trend_enriched"))
    rewards = [m["final_reward"] for m in metrics if m.get("final_reward") is not None]
    avg_reward = round(sum(rewards) / len(rewards), 4) if rewards else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Strategic Domains Trained", f"{trained} / {total}", delta=None)
    c2.metric("Governance Frameworks Enriched", f"{std_enriched} / {total}")
    c3.metric("Innovation Drivers Enriched", f"{trend_enriched} / {total}")
    c4.metric("Avg Prioritisation Reward", f"{avg_reward:.4f}" if avg_reward is not None else "—")

    st.divider()

    # ── Section B: Enrichment heatmap ───────────────────────────────────────
    if coverage:
        st.markdown("#### Knowledge Graph Enrichment Coverage")
        st.caption("Green = enriched · Red = missing. Each row is a strategic domain across three knowledge dimensions.")

        domains = [domain_label(d["domain"]) for d in coverage]
        cols = ["Governance Framework", "Innovation Driver", "AI Trained"]
        z = [
            [
                int(d.get("standard_enriched", False)),
                int(d.get("trend_enriched", False)),
                int(d.get("drl_trained", False)),
            ]
            for d in coverage
        ]

        fig_heat = go.Figure(go.Heatmap(
            z=z,
            x=cols,
            y=domains,
            colorscale=[[0, "#e74c3c"], [0.5, "#f39c12"], [1, "#27ae60"]],
            zmin=0, zmax=1,
            showscale=False,
            xgap=2, ygap=1,
        ))
        fig_heat.update_layout(
            height=max(400, len(domains) * 14),
            margin=dict(l=200, r=20, t=20, b=20),
            yaxis=dict(tickfont=dict(size=10)),
        )
        st.plotly_chart(fig_heat, width='stretch')
    else:
        st.info("No coverage data yet. Run training to populate.")

    st.divider()

    # ── Section C: Reward progression ───────────────────────────────────────
    if metrics:
        st.markdown("#### AI Prioritisation Reward Progression")
        st.caption("Each point is one domain learning session. Higher reward = better strategic capability ordering.")

        df = pd.DataFrame(metrics)
        df = df.dropna(subset=["final_reward"])
        if "domain_name" in df.columns:
            df["domain_name"] = df["domain_name"].apply(domain_label)

        if not df.empty:
            # Sort by timestamp if present
            if "ts" in df.columns:
                df = df.sort_values("ts")

            fig_line = px.scatter(
                df,
                x=df.index,
                y="final_reward",
                color="sector",
                hover_data=["domain_name", "episodes", "device", "ts"],
                labels={"index": "Training Run #", "final_reward": "Final Reward"},
                height=350,
            )
            # Add trend line
            fig_line.add_trace(go.Scatter(
                x=df.index,
                y=df["final_reward"].rolling(5, min_periods=1).mean(),
                mode="lines",
                name="5-run avg",
                line=dict(color="white", width=2, dash="dash"),
            ))
            fig_line.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig_line, width='stretch')

        # DRL reward by sector bar chart
        if "sector" in df.columns and not df.empty:
            sector_avg = df.groupby("sector")["final_reward"].mean().reset_index()
            sector_avg.columns = ["Sector", "Avg Reward"]
            fig_bar = px.bar(
                sector_avg.sort_values("Avg Reward", ascending=True),
                x="Avg Reward", y="Sector", orientation="h",
                height=300,
                color="Avg Reward",
                color_continuous_scale="RdYlGn",
                title="Average DRL Reward by Sector",
            )
            fig_bar.update_layout(margin=dict(t=40, b=20), coloraxis_showscale=False)
            st.plotly_chart(fig_bar, width='stretch')
    else:
        st.info("No training runs recorded yet. Use the controls below to start training.")

    st.divider()

    # ── Section D: Training control ─────────────────────────────────────────
    st.markdown("#### Run AI Learning Session")
    st.markdown(
        "Uses **REINFORCE** policy gradient training on the **AMD MI300X via ROCm**. "
        "Each strategic domain's capabilities form the learning state — the AI engine learns "
        "optimal prioritisation grounded in real governance frameworks, effort estimates, "
        "and risk data from the knowledge graph."
    )

    ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 3])
    with ctrl1:
        episodes = st.number_input("Learning episodes per domain", min_value=10, max_value=500, value=50, step=10)
    with ctrl2:
        domain_filter = st.text_input("Specific domain (blank = all 44)", placeholder="e.g. Healthcare Provider")
    with ctrl3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Run AI Learning Session", type="primary", width='stretch'):
            with st.spinner("Submitting training job..."):
                resp = trigger_training(
                    episodes_per_domain=int(episodes),
                    domain=domain_filter.strip() or None,
                )
            if resp.get("status") == "started":
                st.success(
                    f"Training started (run_id: `{resp.get('run_id')}`). "
                    "Metrics appear in the graph as each domain completes. "
                    "Refresh this tab in ~60 seconds."
                )
            else:
                st.error(f"Failed to start training: {resp.get('message', resp)}")

    # Latest runs table
    if metrics:
        st.markdown("##### Latest AI Learning Sessions")
        df_show = pd.DataFrame(metrics[:20])[
            ["domain_name", "sector", "episodes", "final_reward", "avg_reward_last10", "device", "ts"]
        ].copy()
        df_show["domain_name"] = df_show["domain_name"].apply(domain_label)
        df_show.columns = [
            "Strategic Domain", "Sector", "Episodes",
            "Prioritisation Reward", "Avg (last 10)", "Device", "Timestamp",
        ]
        st.dataframe(df_show, width='stretch', hide_index=True)
