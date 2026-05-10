"""Knowledge Graph Explorer — force-directed network of 44 enterprise domains."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from frontend.utils.api_client import get_network_graph, get_domain_detail
from frontend.utils.terminology import domain_label, subdomain_label


# ── Helpers ───────────────────────────────────────────────────────────────────

def _as_list(val) -> list[str]:
    """Normalise a graph property (str | list | None) to a clean list of strings."""
    if not val:
        return []
    if isinstance(val, list):
        return [str(v).strip() for v in val if v and str(v).strip()]
    s = str(val).strip()
    for sep in (";", "\n", "|"):
        if sep in s:
            return [x.strip() for x in s.split(sep) if x.strip()]
    return [s] if s else []


def _complexity_badge(val: str | None) -> str:
    mapping = {
        "low": "🟢 Low",
        "medium": "🟡 Medium",
        "high": "🔴 High",
        "very high": "🔴 Very High",
    }
    return mapping.get((val or "").lower(), val or "—")


def _impact_badge(val: str | None) -> str:
    mapping = {
        "low": "🔵 Low",
        "medium": "🟡 Medium",
        "high": "🔴 High",
        "transformative": "🚀 Transformative",
        "critical": "🔴 Critical",
    }
    return mapping.get((val or "").lower(), val or "—")


def _bullet_list(items: list[str], max_items: int = 6) -> str:
    shown = items[:max_items]
    tail = f"\n  *…and {len(items) - max_items} more*" if len(items) > max_items else ""
    return "\n".join(f"- {i}" for i in shown) + tail


# ── Main render ───────────────────────────────────────────────────────────────

def render_graph_explorer_tab():
    st.subheader("Knowledge Graph Explorer")
    st.caption(
        "Live network of 44 enterprise domains — nodes sized by DRL training status, "
        "coloured by sector, edges show inter-domain relationships"
    )

    try:
        import networkx as nx
    except ImportError:
        st.error("`networkx` is not installed. Run `pip install networkx` and restart.")
        return

    with st.spinner("Loading knowledge graph network…"):
        try:
            data = get_network_graph()
        except Exception as exc:
            st.error(f"Failed to load graph network: {exc}")
            return

    nodes = data.get("nodes") or []
    edges = data.get("edges") or []

    if not nodes:
        st.warning("No domain nodes returned from the knowledge graph.")
        return

    # ── Build networkx graph for layout ──────────────────────────────────────
    G = nx.DiGraph()
    for n in nodes:
        G.add_node(n["id"], **n)
    for e in edges:
        src, tgt = e.get("source"), e.get("target")
        if src and tgt and src in G and tgt in G:
            G.add_edge(src, tgt, rel_type=e.get("type", ""))

    pos = nx.spring_layout(G, seed=42, k=2.5, iterations=80)

    sectors = sorted({n.get("sector", "Other") or "Other" for n in nodes})
    palette = px.colors.qualitative.Plotly + px.colors.qualitative.D3
    colour_map = {s: palette[i % len(palette)] for i, s in enumerate(sectors)}

    edge_colours = {
        "ENABLES": "#3498db",
        "ORCHESTRATES": "#e67e22",
        "HAS_SECTOR": "#2ecc71",
    }
    edge_traces: dict = {}
    for e in edges:
        rt = e.get("type", "RELATED")
        src, tgt = e.get("source"), e.get("target")
        if not src or not tgt or src not in pos or tgt not in pos:
            continue
        x0, y0 = pos[src]
        x1, y1 = pos[tgt]
        if rt not in edge_traces:
            edge_traces[rt] = {"x": [], "y": []}
        edge_traces[rt]["x"] += [x0, x1, None]
        edge_traces[rt]["y"] += [y0, y1, None]

    node_x, node_y = [], []
    node_labels, node_hover = [], []
    node_colours, node_sizes = [], []
    label_to_raw: dict[str, str] = {}

    for n in nodes:
        nid = n["id"]
        if nid not in pos:
            continue
        x, y = pos[nid]
        node_x.append(x)
        node_y.append(y)
        friendly = domain_label(n.get("name", nid))
        label_to_raw[friendly] = n.get("name", nid)
        node_labels.append(friendly)
        sector = n.get("sector", "Other") or "Other"
        node_colours.append(colour_map.get(sector, "#888"))
        trained = bool(n.get("drl_trained"))
        node_sizes.append(22 if trained else 13)
        node_hover.append(
            f"<b>{friendly}</b><br>"
            f"Sector: {sector}<br>"
            f"AI Trained: {'✓' if trained else '○'}<br>"
            f"ID: {nid}"
        )

    fig = go.Figure()
    for rt, xy in edge_traces.items():
        fig.add_trace(go.Scatter(
            x=xy["x"], y=xy["y"],
            mode="lines",
            line=dict(width=1.2, color=edge_colours.get(rt, "#aaa")),
            hoverinfo="none",
            name=rt,
            opacity=0.5,
        ))

    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        marker=dict(
            size=node_sizes,
            color=node_colours,
            line=dict(width=1, color="#ffffff"),
            opacity=0.9,
        ),
        text=node_labels,
        textposition="top center",
        textfont=dict(size=8, color="white"),
        hovertext=node_hover,
        hoverinfo="text",
        name="Domains",
    ))

    fig.update_layout(
        height=700,
        showlegend=True,
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font_color="white",
        legend=dict(bgcolor="#1a1d23", bordercolor="#444", font=dict(size=11)),
        margin=dict(l=10, r=10, t=40, b=10),
        title=dict(
            text=f"Knowledge Graph — {len(nodes)} Domains · {len(edges)} Relationships",
            font=dict(size=14, color="#ccc"),
            x=0.01,
        ),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )

    st.plotly_chart(fig, width='stretch')

    drl_count = sum(1 for n in nodes if n.get("drl_trained"))
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Domains", len(nodes))
    m2.metric("Relationships", len(edges))
    m3.metric("Sectors", len(sectors))
    m4.metric("AI Trained", drl_count)

    st.divider()

    friendly_names = sorted(label_to_raw.keys())
    selected = st.selectbox(
        "Select a domain to explore its full breakdown:",
        options=["— select a domain —"] + friendly_names,
    )
    if selected and selected != "— select a domain —":
        raw_name = label_to_raw.get(selected, selected)
        _render_domain_detail(selected, raw_name)


# ── Domain detail panel ───────────────────────────────────────────────────────

def _render_domain_detail(friendly_name: str, raw_name: str):
    with st.spinner(f"Loading full breakdown for {friendly_name}…"):
        try:
            detail = get_domain_detail(raw_name)
        except Exception as exc:
            st.error(f"Could not load domain detail: {exc}")
            return

    domain = detail.get("domain") or {}
    standard = detail.get("standard") or {}
    trend = detail.get("trend") or {}
    subdomain_groups = detail.get("subdomain_groups") or []

    # ── Header ────────────────────────────────────────────────────────────────
    trained = bool(domain.get("drl_trained"))
    sector = domain.get("sector") or ""
    reward = domain.get("drl_final_reward")

    badge = "🟢 AI-Trained" if trained else "⚪ Not Yet Trained"
    reward_str = f"  ·  Reward score: **{round(reward, 3)}**" if reward is not None else ""
    st.markdown(f"## {friendly_name}")
    st.markdown(
        f"`{sector}`&nbsp;&nbsp;{badge}{reward_str}",
        unsafe_allow_html=True,
    )

    # ── Summary bar ───────────────────────────────────────────────────────────
    all_caps = [
        cap
        for g in subdomain_groups
        for cap in (g.get("capabilities") or [])
    ]
    total_areas = len(subdomain_groups)
    total_caps = len(all_caps)
    complexities = [c.get("implementation_complexity", "") for c in all_caps]
    high_count = sum(1 for x in complexities if (x or "").lower() in ("high", "very high"))
    durations = [
        int(c["typical_duration_weeks"])
        for c in all_caps
        if c.get("typical_duration_weeks") is not None
    ]
    total_weeks = sum(durations) if durations else None

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Capability Areas", total_areas)
    s2.metric("Specific Capabilities", total_caps)
    s3.metric("High Complexity", high_count)
    s4.metric(
        "Est. Total Effort",
        f"{total_weeks} wks" if total_weeks else "—",
        help="Sum of typical_duration_weeks across all capabilities in this domain.",
    )

    st.divider()

    # ── Governance & Innovation cards ─────────────────────────────────────────
    col_std, col_trend = st.columns(2)

    with col_std:
        st.markdown("#### Governance Framework")
        if standard and standard.get("name"):
            pub = standard.get("publisher") or ""
            ver = standard.get("version") or ""
            ver_str = f" v{ver}" if ver else ""
            st.markdown(f"**{standard['name']}**{ver_str}  \n_{pub}_")
            desc = standard.get("description") or ""
            if desc:
                st.caption(desc[:300] + ("…" if len(desc) > 300 else ""))
            principles = _as_list(standard.get("key_principles"))
            if principles:
                st.markdown("**Key Principles**")
                st.markdown(_bullet_list(principles, 5))
            requirements = _as_list(standard.get("compliance_requirements"))
            if requirements:
                st.markdown("**Compliance Requirements**")
                st.markdown(_bullet_list(requirements, 5))
            src = standard.get("source_url") or ""
            if src:
                st.markdown(f"[Reference ↗]({src})", unsafe_allow_html=False)
        else:
            st.caption("No governance framework linked to this domain yet.")

    with col_trend:
        st.markdown("#### Innovation Driver")
        if trend and trend.get("name"):
            impact = _impact_badge(trend.get("impact_level"))
            horizon = trend.get("time_horizon") or ""
            maturity = trend.get("maturity") or ""
            adoption = trend.get("adoption_rate") or ""
            st.markdown(f"**{trend['name']}**")
            meta_parts = [p for p in [impact, horizon, maturity] if p and p != "—"]
            st.caption("  ·  ".join(meta_parts))
            desc = trend.get("description") or ""
            if desc:
                st.caption(desc[:300] + ("…" if len(desc) > 300 else ""))
            biz = trend.get("business_impact") or ""
            if biz:
                st.markdown("**Business Impact**")
                st.markdown(biz[:400])
            enablers = _as_list(trend.get("technology_enablers"))
            if enablers:
                st.markdown("**Technology Enablers**")
                tags = "  ".join(f"`{e}`" for e in enablers[:8])
                st.markdown(tags)
            if adoption:
                st.caption(f"Adoption rate: {adoption}")
        else:
            st.caption("No innovation driver linked to this domain yet.")

    st.divider()
    st.markdown("#### Capability Breakdown")

    if not subdomain_groups:
        st.info("No capabilities found for this domain in the graph.")
        return

    # ── SubDomain expanders ───────────────────────────────────────────────────
    for g in subdomain_groups:
        sd = g.get("subdomain") or {}
        caps = g.get("capabilities") or []
        sd_name = subdomain_label(sd.get("name") or "")
        scope = sd.get("functional_scope") or ""
        driver = sd.get("business_driver") or ""
        rationale = sd.get("grouping_rationale") or ""
        sd_desc = sd.get("description") or ""

        with st.expander(f"**{sd_name}** — {len(caps)} capabilities", expanded=False):
            meta_parts = []
            if scope:
                meta_parts.append(f"Scope: {scope}")
            if driver:
                meta_parts.append(f"Driver: {driver}")
            if meta_parts:
                st.caption("  ·  ".join(meta_parts))
            if sd_desc:
                st.caption(sd_desc)
            if rationale:
                st.caption(f"_{rationale}_")

            if not caps:
                st.caption("No capabilities recorded under this area.")
                continue

            for cap in caps:
                _render_capability_card(cap)


def _render_capability_card(cap: dict):
    name = cap.get("name") or "Unnamed"
    desc = cap.get("description") or ""
    outcomes = _as_list(cap.get("business_outcomes"))
    kpis = _as_list(cap.get("kpis"))
    risks = _as_list(cap.get("risk_factors"))
    frameworks = _as_list(cap.get("common_frameworks"))
    patterns = _as_list(cap.get("solution_patterns"))
    tech_req = _as_list(cap.get("technical_requirements"))
    subcaps = [s for s in (cap.get("subcapability_names") or []) if s]
    complexity = cap.get("implementation_complexity") or ""
    duration = cap.get("typical_duration_weeks")

    st.markdown("---")
    left, right = st.columns([3, 1])

    with left:
        st.markdown(f"##### {name}")
        if desc:
            st.write(desc)
        if outcomes:
            st.markdown("**What this delivers**")
            st.markdown(_bullet_list(outcomes, 4))
        if kpis:
            st.markdown("**How success is measured**")
            st.markdown(_bullet_list(kpis, 4))
        if subcaps:
            st.markdown("**Includes**")
            st.markdown("  ".join(f"`{s}`" for s in subcaps[:10]))

    with right:
        if complexity:
            st.markdown(f"**Effort level**  \n{_complexity_badge(complexity)}")
        if duration is not None:
            st.markdown(f"**Typical duration**  \n⏱ {duration} weeks")
        if risks:
            st.markdown("**Risks**")
            for r in risks[:3]:
                st.caption(f"⚠ {r}")
        if frameworks:
            st.markdown("**Frameworks**")
            st.markdown("  ".join(f"`{f}`" for f in frameworks[:4]))
        if patterns:
            st.markdown("**Patterns**")
            for p in patterns[:3]:
                st.caption(f"› {p}")
        if tech_req:
            st.markdown("**Technical requirements**")
            for t in tech_req[:3]:
                st.caption(f"· {t}")
