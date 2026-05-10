"""AI Learning Engine tab — enrichment heatmap + reward curve + training control."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from frontend.utils.api_client import get_training_metrics, get_training_coverage, trigger_training
from frontend.utils.terminology import domain_label

# ── Tooltip helper ────────────────────────────────────────────────────────────
_TIP = 'cursor:help;border-bottom:1px dotted #9ca3af;text-decoration:none'

def _t(term: str, defn: str) -> str:
    """Wrap a term in an HTML abbr tag — browser shows defn on hover."""
    safe = defn.replace('"', '&quot;').replace("'", "&#39;")
    return f'<abbr title="{safe}" style="{_TIP}">{term}</abbr>'


def render_training_tab():
    st.subheader("AI Learning Engine")
    st.markdown(
        "The "
        + _t("AI Prioritisation Engine",
             "An autonomous reinforcement learning system that trains on every "
             "strategic domain in the knowledge graph. It learns to rank capabilities "
             "by value, feasibility, and governance alignment — producing better "
             "roadmap recommendations with every session.")
        + " trains on every strategic domain in the knowledge graph. "
        "Each learning session is recorded as a node in Neo4j — the graph continuously "
        "improves itself, grounding capability prioritisation in sector-specific "
        + _t("governance frameworks",
             "Industry-recognised standards (e.g. TOGAF, ISO 27001, COBIT) that define "
             "how an enterprise should structure, secure, and operate its architecture.")
        + " and "
        + _t("innovation drivers",
             "Emerging technology trends (e.g. Generative AI, Cloud-Native, ESG) that "
             "signal where investment should be directed to stay competitive.")
        + ".",
        unsafe_allow_html=True,
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
    c1.metric(
        "Strategic Domains Trained",
        f"{trained} / {total}",
        help=(
            "Number of enterprise domains where the AI policy has completed at least one "
            "training run. Trained domains produce significantly better capability "
            "prioritisation — the AI learns the value-vs-complexity trade-off specific "
            "to that domain's real capability data."
        ),
    )
    c2.metric(
        "Governance Frameworks Enriched",
        f"{std_enriched} / {total}",
        help=(
            "Domains linked to an industry standard (e.g. TOGAF, ISO 27001, COBIT) with "
            "detailed compliance requirements loaded. These ground roadmap outputs in "
            "recognised governance structures rather than generic best-guess advice."
        ),
    )
    c3.metric(
        "Innovation Drivers Enriched",
        f"{trend_enriched} / {total}",
        help=(
            "Domains linked to a technology trend (e.g. Generative AI, ESG, Cloud-Native) "
            "with measurable business impact data. Used to weight forward-looking "
            "capabilities higher when generating strategic roadmaps."
        ),
    )
    c4.metric(
        "Avg Prioritisation Reward",
        f"{avg_reward:.4f}" if avg_reward is not None else "—",
        help=(
            "Mean final reward across all AI training sessions. Range: −1.0 to +1.0. "
            "Higher values mean the policy reliably ranks high-value, feasible capabilities "
            "above complex, high-risk ones. A score above 0.5 is considered well-converged."
        ),
    )

    st.divider()

    # ── Section B: Enrichment heatmap ───────────────────────────────────────
    if coverage:
        st.markdown("#### Knowledge Graph Enrichment Coverage")
        st.markdown(
            "Each row is a strategic domain. Columns show three dimensions of "
            "knowledge enrichment: "
            + _t("Governance Framework",
                 "Whether the domain is linked to an industry standard with full "
                 "compliance requirements (e.g. TOGAF for architecture, ISO 27001 "
                 "for security, HL7 FHIR for healthcare).")
            + ", "
            + _t("Innovation Driver",
                 "Whether the domain is linked to a technology trend with documented "
                 "business impact (e.g. Generative AI, ESG Reporting, Blockchain).")
            + ", and "
            + _t("AI Trained",
                 "Whether the reinforcement learning policy has run at least one "
                 "training session on this domain's capability data. "
                 "Green = fully enriched · Red = not yet enriched.")
            + ".",
            unsafe_allow_html=True,
        )

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
        st.markdown(
            "Each point is one domain learning session. The "
            + _t("final reward",
                 "A scalar score computed at the end of each training episode. "
                 "It combines: capability complexity alignment (did the AI deprioritise "
                 "high-risk items?), budget feasibility (do selected capabilities fit "
                 "the effort envelope?), and domain coverage breadth. Range: −1 to +1.")
            + " measures how well the AI ordered that domain's capabilities. "
            "The dashed line is a "
            + _t("5-run rolling average",
                 "The mean reward across the last 5 training sessions. Smooths out "
                 "episode-level noise to reveal the overall learning trend. A rising "
                 "trend means the policy is improving.")
            + " showing the learning trend.",
            unsafe_allow_html=True,
        )

        df = pd.DataFrame(metrics)
        df = df.dropna(subset=["final_reward"])
        if "domain_name" in df.columns:
            df["domain_name"] = df["domain_name"].apply(domain_label)

        if not df.empty:
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
            fig_line.add_trace(go.Scatter(
                x=df.index,
                y=df["final_reward"].rolling(5, min_periods=1).mean(),
                mode="lines",
                name="5-run avg",
                line=dict(color="white", width=2, dash="dash"),
            ))
            fig_line.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig_line, width='stretch')

        if "sector" in df.columns and not df.empty:
            sector_avg = df.groupby("sector")["final_reward"].mean().reset_index()
            sector_avg.columns = ["Sector", "Avg Reward"]
            fig_bar = px.bar(
                sector_avg.sort_values("Avg Reward", ascending=True),
                x="Avg Reward", y="Sector", orientation="h",
                height=300,
                color="Avg Reward",
                color_continuous_scale="RdYlGn",
                title="Average Prioritisation Reward by Sector",
            )
            fig_bar.update_layout(margin=dict(t=40, b=20), coloraxis_showscale=False)
            st.plotly_chart(fig_bar, width='stretch')
    else:
        st.info("No training runs recorded yet. Use the controls below to start training.")

    st.divider()

    # ── Section D: Training control ─────────────────────────────────────────
    st.markdown("#### Run AI Learning Session")
    st.markdown(
        "Uses "
        + _t("REINFORCE",
             "A policy gradient algorithm (Williams, 1992). The AI tries different "
             "capability orderings, observes the reward signal, then adjusts its "
             "policy to make high-reward orderings more likely in future. "
             "No environment model required — learns purely from trial-and-error.")
        + " policy gradient training on the "
        + _t("AMD MI300X via ROCm",
             "AMD's Instinct MI300X is a GPU accelerator optimised for AI workloads. "
             "ROCm is AMD's open-source GPU compute platform — analogous to NVIDIA CUDA "
             "but for AMD hardware. The DRL policy trains in seconds on MI300X vs minutes on CPU.")
        + ". Each strategic domain's capabilities form the learning state — the AI engine "
        "learns optimal prioritisation grounded in real governance frameworks, "
        + _t("effort estimates",
             "typical_duration_weeks: the median number of delivery weeks for a capability "
             "based on industry benchmarks stored in the knowledge graph.")
        + ", and risk data.",
        unsafe_allow_html=True,
    )

    ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 3])
    with ctrl1:
        episodes = st.number_input(
            "Learning episodes per domain",
            min_value=10, max_value=500, value=50, step=10,
            help=(
                "One episode = the AI runs through all capabilities in a domain once, "
                "receives a reward, and updates its policy. More episodes → more "
                "refined prioritisation, but takes longer. 50 is a good starting point; "
                "200+ is recommended for production-quality rankings."
            ),
        )
    with ctrl2:
        domain_filter = st.text_input(
            "Specific domain (blank = all 44)",
            placeholder="e.g. Healthcare Provider",
            help="Leave blank to train all 44 domains sequentially. Enter a domain name to train just that one.",
        )
    with ctrl3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Run AI Learning Session", type="primary", width='stretch'):
            with st.spinner("Submitting training job…"):
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
        st.markdown(
            "_"
            + _t("Prioritisation Reward",
                 "Final reward score at the end of training (range −1 to +1). "
                 "Combines complexity alignment, budget feasibility, and coverage breadth. "
                 "Higher = better capability ordering.")
            + " · "
            + _t("Avg (last 10)",
                 "Rolling mean of the final reward across the last 10 episodes of "
                 "the same training run. A value close to the Final Reward means the "
                 "policy has stabilised; a lower value means it was still improving.")
            + "_",
            unsafe_allow_html=True,
        )
        df_show = pd.DataFrame(metrics[:20])[
            ["domain_name", "sector", "episodes", "final_reward", "avg_reward_last10", "device", "ts"]
        ].copy()
        df_show["domain_name"] = df_show["domain_name"].apply(domain_label)
        df_show.columns = [
            "Strategic Domain", "Sector", "Episodes",
            "Prioritisation Reward", "Avg (last 10)", "Device", "Timestamp",
        ]
        st.dataframe(df_show, width='stretch', hide_index=True)
