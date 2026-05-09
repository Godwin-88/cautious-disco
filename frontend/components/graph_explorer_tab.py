"""Knowledge Graph Explorer — force-directed network of 44 enterprise domains."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from frontend.utils.api_client import get_network_graph, get_subdomains
from frontend.utils.terminology import domain_label, subdomain_label


def render_graph_explorer_tab():
    st.subheader("Knowledge Graph Explorer")
    st.caption(
        "Live network of 44 enterprise domains — nodes sized by DRL training status, "
        "coloured by sector, edges show inter-domain relationships"
    )

    try:
        import networkx as nx
    except ImportError:
        st.error(
            "`networkx` is not installed. "
            "Run `pip install networkx` and restart the app."
        )
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

    # ── Colour by sector ─────────────────────────────────────────────────────
    sectors = sorted({n.get("sector", "Other") or "Other" for n in nodes})
    palette = px.colors.qualitative.Plotly + px.colors.qualitative.D3
    colour_map = {s: palette[i % len(palette)] for i, s in enumerate(sectors)}

    # ── Edge traces by relationship type ─────────────────────────────────────
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

    # ── Node arrays ───────────────────────────────────────────────────────────
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
            f"DRL Trained: {'✓' if trained else '○'}<br>"
            f"ID: {nid}"
        )

    # ── Build Plotly figure ───────────────────────────────────────────────────
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
            text=(
                f"Knowledge Graph — {len(nodes)} Domains · "
                f"{len(edges)} Relationships"
            ),
            font=dict(size=14, color="#ccc"),
            x=0.01,
        ),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )

    st.plotly_chart(fig, width='stretch')

    # ── Summary metrics ───────────────────────────────────────────────────────
    drl_count = sum(1 for n in nodes if n.get("drl_trained"))
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Domains", len(nodes))
    m2.metric("Relationships", len(edges))
    m3.metric("Sectors", len(sectors))
    m4.metric("DRL Trained", drl_count)

    st.divider()

    # ── Domain detail panel ───────────────────────────────────────────────────
    friendly_names = sorted(label_to_raw.keys())
    selected = st.selectbox(
        "Explore a domain in detail:",
        options=["— select a domain —"] + friendly_names,
    )
    if selected and selected != "— select a domain —":
        raw_name = label_to_raw.get(selected, selected)
        _render_domain_detail(selected, raw_name)


def _render_domain_detail(friendly_name: str, raw_name: str):
    st.markdown(f"### {friendly_name}")

    with st.spinner("Loading capability areas…"):
        try:
            subdomains = get_subdomains([raw_name])
        except Exception as exc:
            st.error(f"Could not load capability areas: {exc}")
            return

    if not subdomains:
        st.caption("No capability areas found for this domain.")
        return

    st.caption(f"{len(subdomains)} Capability Areas in this domain")

    for sd in subdomains[:15]:
        name = subdomain_label(sd.get("name", ""))
        scope = sd.get("functional_scope", "")
        driver = sd.get("business_driver", "")
        with st.container():
            st.markdown(f"**{name}**")
            if scope:
                st.caption(scope)
            if driver:
                st.caption(f"Driver: {driver}")
