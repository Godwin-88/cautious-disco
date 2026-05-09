"""Hierarchical questionnaire — Domain → Capability Area → Capability → Constraints."""

import streamlit as st

from frontend.utils.api_client import get_domains, get_subdomains, get_subdomain_capabilities
from frontend.utils.terminology import domain_label, subdomain_label


def render_input_form() -> dict | None:
    """Render hierarchical questionnaire. Returns payload dict when submitted."""

    st.subheader("Build Your Strategic Context")
    st.caption(
        "Select your organisation's focus areas step by step — "
        "the AI will generate a governance-grounded roadmap tailored to your selection."
    )

    # ── Step 1: Domain ─────────────────────────────────────────────────────
    st.markdown("##### Step 1 — Select Strategic Domains")
    all_domains = st.session_state.get("_domains_cache") or get_domains()
    st.session_state["_domains_cache"] = all_domains

    domain_label_to_raw: dict[str, str] = {
        domain_label(d["name"]): d["name"] for d in all_domains
    }
    domain_raw_to_obj: dict[str, dict] = {d["name"]: d for d in all_domains}

    selected_domain_labels = st.multiselect(
        "Strategic Domains",
        options=sorted(domain_label_to_raw.keys()),
        default=st.session_state.get("_sel_domain_labels", []),
        help="Choose the enterprise domains relevant to your organisation",
        key="sel_domains",
    )
    st.session_state["_sel_domain_labels"] = selected_domain_labels
    selected_domain_names = [domain_label_to_raw[l] for l in selected_domain_labels]

    # ── Step 2: Capability Areas (SubDomains) ──────────────────────────────
    selected_subdomain_ids: list[str] = []
    if selected_domain_names:
        st.markdown("##### Step 2 — Select Capability Areas")
        cache_key_sd = "subdomains_" + "_".join(sorted(selected_domain_names))
        subdomains = st.session_state.get(cache_key_sd)
        if subdomains is None:
            subdomains = get_subdomains(selected_domain_names)
            st.session_state[cache_key_sd] = subdomains

        sd_label_to_obj: dict[str, dict] = {
            subdomain_label(sd["name"]): sd for sd in subdomains
        }

        selected_sd_labels = st.multiselect(
            "Capability Areas",
            options=sorted(sd_label_to_obj.keys()),
            default=sorted(sd_label_to_obj.keys()),
            help="Capability areas within your selected domains",
            key="sel_subdomains",
        )
        selected_subdomain_ids = [sd_label_to_obj[l]["id"] for l in selected_sd_labels if l in sd_label_to_obj]

        # ── Step 3: Capabilities ────────────────────────────────────────────
        selected_cap_ids: list[str] = []
        if selected_subdomain_ids:
            st.markdown("##### Step 3 — Select Strategic Capabilities")
            cache_key_caps = "caps_" + "_".join(sorted(selected_subdomain_ids))
            capabilities = st.session_state.get(cache_key_caps)
            if capabilities is None:
                capabilities = get_subdomain_capabilities(selected_subdomain_ids)
                st.session_state[cache_key_caps] = capabilities

            # Group by subdomain for display
            if capabilities:
                cap_id_to_obj: dict[str, dict] = {c["id"]: c for c in capabilities}
                cap_options = [c["name"] for c in capabilities]

                selected_cap_names = st.multiselect(
                    f"Strategic Capabilities ({len(cap_options)} available)",
                    options=cap_options,
                    default=cap_options,
                    help="Select the specific capabilities to include in your roadmap",
                    key="sel_caps",
                )
                selected_cap_ids = [
                    c["id"] for c in capabilities if c["name"] in selected_cap_names
                ]

                complexity_map = {c["name"]: c.get("complexity", "") for c in capabilities}
                if selected_cap_names:
                    high = sum(1 for n in selected_cap_names if complexity_map.get(n) in ("high", "very_high"))
                    med = sum(1 for n in selected_cap_names if complexity_map.get(n) == "medium")
                    low = sum(1 for n in selected_cap_names if complexity_map.get(n) == "low")
                    st.caption(f"Selected: {len(selected_cap_names)} capabilities · 🔴 {high} high · 🟡 {med} medium · 🟢 {low} low complexity")
            else:
                st.info("No capabilities found for selected areas.")
                selected_cap_ids = []
        else:
            selected_cap_ids = []
    else:
        selected_cap_ids = []

    st.divider()

    # ── Step 4: Organisation & Constraints ─────────────────────────────────
    st.markdown("##### Step 4 — Organisation Context & Constraints")

    with st.form("analyze_form"):
        col_left, col_right = st.columns(2)
        with col_left:
            org_type = st.text_input(
                "Organisation Type",
                placeholder="e.g. Commercial Bank, Healthcare Provider, Government Agency",
                help="Describe your organisation — used to tailor AI output language and governance references",
            )
            budget_tier = st.select_slider(
                "Budget Tier",
                options=["low", "medium", "high"],
                value="medium",
            )
            risk_tolerance = st.select_slider(
                "Risk Tolerance",
                options=["low", "medium", "high"],
                value="medium",
            )
        with col_right:
            timeline_months = st.slider(
                "Timeline (months)",
                min_value=6,
                max_value=36,
                value=18,
                step=3,
            )
            goals_text = st.text_area(
                "Additional Strategic Goals (optional)",
                height=100,
                placeholder="e.g. Achieve ISO 27001 certification, Deploy AI-driven fraud detection",
                help="Supplements the capability selection above",
            )

        submitted = st.form_submit_button(
            "Generate Strategic Roadmap",
            type="primary",
            width='stretch',
        )

    if submitted:
        if not org_type.strip():
            st.error("Please enter your Organisation Type.")
            return None
        if not selected_cap_ids and not selected_domain_names:
            st.error("Please select at least one Strategic Domain in Step 1.")
            return None

        extra_goals = [g.strip() for g in goals_text.split(",") if g.strip()] if goals_text else []
        goals = extra_goals or [f"Transform {org_type} digital capabilities"]

        return {
            "org_type": org_type.strip(),
            "goals": goals,
            "budget_tier": budget_tier,
            "timeline_months": timeline_months,
            "risk_tolerance": risk_tolerance,
            "sector_focus": selected_domain_names,
            "selected_capability_ids": selected_cap_ids,
            "selected_subdomain_ids": selected_subdomain_ids,
        }

    return None
