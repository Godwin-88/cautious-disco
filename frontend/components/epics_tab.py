"""Initiatives & Scenarios tab — accordion per phase → initiative → workstreams/scenarios/delivery standards."""

import streamlit as st

from frontend.utils.terminology import label, ac_badge, domain_label, subdomain_label


def render_epics_tab(result: dict) -> None:
    phases = result.get("phases") or []
    if not phases:
        st.info("No strategic initiatives generated yet.")
        return

    for phase in phases:
        phase_num = phase.get("phase_number", 1)
        phase_name = phase.get("phase_name", f"Phase {phase_num}")
        epics = phase.get("epics") or []

        with st.expander(
            f"Phase {phase_num}: {phase_name} — {len(epics)} {label('epics')}",
            expanded=(phase_num == 1),
        ):
            if phase.get("objectives"):
                st.markdown("**Phase Objectives:**")
                for obj in phase["objectives"]:
                    st.markdown(f"- {obj}")

            for epic in epics:
                st.markdown("---")
                title = epic.get("title") or epic.get("epic_id") or label("epic")
                subdomain_raw = epic.get("subdomain_group") or ""
                cap_area = subdomain_label(subdomain_raw)

                st.markdown(f"#### {epic.get('epic_id', 'INI')} — {title}")
                if cap_area:
                    st.caption(f"{label('subdomain')}: {cap_area}")

                col1, col2 = st.columns([2, 1])
                with col1:
                    if epic.get("description"):
                        st.markdown(epic["description"])
                    if epic.get("business_value"):
                        st.markdown(f"**{label('business_value')}:** {epic['business_value']}")
                    if epic.get("strategic_rationale"):
                        st.markdown(f"**{label('strategic_rationale')}:** {epic['strategic_rationale']}")
                with col2:
                    if epic.get("governance_reference"):
                        st.info(f"**{label('governance_reference')}**\n\n{epic['governance_reference']}")
                    if epic.get("trend_alignment"):
                        st.success(f"**{label('trend_alignment')}**\n\n{epic['trend_alignment']}")
                    st.metric("Delivery Sprints", epic.get("estimated_sprints", "—"))

                # Delivery Standards (Acceptance Criteria)
                acs = epic.get("acceptance_criteria") or []
                if acs:
                    compliance_count = sum(1 for ac in acs if ac.startswith("[Compliance]"))
                    kpi_count = sum(1 for ac in acs if ac.startswith("[KPI]"))
                    badge_line = f"{label('acceptance_criteria')} ({len(acs)})"
                    if compliance_count:
                        badge_line += f" · 🔒 {compliance_count} Regulatory Obligations"
                    if kpi_count:
                        badge_line += f" · 📊 {kpi_count} Performance Targets"
                    with st.expander(badge_line, expanded=False):
                        for ac in acs:
                            st.checkbox(
                                ac_badge(ac),
                                value=False,
                                key=f"ac_{epic.get('epic_id', '')}_{ac[:20]}",
                            )

                # Risk Landscape
                risks = epic.get("risk_register") or []
                if risks:
                    with st.expander(f"{label('risk_register')} ({len(risks)})", expanded=False):
                        for r in risks:
                            st.warning(r)

                # Workstreams (Features)
                features = epic.get("features") or []
                if features:
                    with st.expander(f"{label('features')} ({len(features)})", expanded=False):
                        for feat in features:
                            st.markdown(f"**{feat.get('title', '')}**")
                            if feat.get("description"):
                                st.caption(feat["description"])
                            if feat.get("technical_notes"):
                                st.info(f"Technical Notes: {feat['technical_notes']}")

                            for story in (feat.get("user_stories") or []):
                                role = story.get("role") or story.get("as_a") or "User"
                                want = story.get("want") or story.get("i_want") or ""
                                so_that = story.get("so_that") or ""
                                st.markdown(
                                    f"> **{label('user_story')}** — "
                                    f"As a **{role}**, I want **{want}**, "
                                    f"so that **{so_that}**"
                                )
                                story_acs = story.get("acceptance_criteria") or []
                                for sac in story_acs:
                                    st.markdown(f"  - {ac_badge(sac)}")
                                tasks = story.get("tasks") or []
                                if tasks:
                                    with st.expander(f"Delivery Tasks ({len(tasks)})", expanded=False):
                                        for ti, task in enumerate(tasks):
                                            if isinstance(task, dict):
                                                task_title = task.get("title") or task.get("name") or f"Task {ti+1}"
                                                task_desc = task.get("description") or ""
                                                task_days = task.get("estimated_days")
                                                task_role = task.get("assignee_role") or ""
                                                cols = st.columns([3, 1, 1])
                                                with cols[0]:
                                                    st.markdown(f"**{task_title}**")
                                                    if task_desc:
                                                        st.caption(task_desc)
                                                with cols[1]:
                                                    if task_days:
                                                        st.metric("Days", task_days)
                                                with cols[2]:
                                                    if task_role:
                                                        st.caption(f"👤 {task_role}")
                                            else:
                                                st.markdown(f"- {task}")
