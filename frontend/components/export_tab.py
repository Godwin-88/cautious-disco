"""Export & Handover tab — Jira JSON, CSV, Markdown download."""

import json
import csv
import io
import streamlit as st

from frontend.utils.terminology import label, ac_badge, subdomain_label


def _to_jira_json(result: dict) -> str:
    issues: list[dict] = []
    phases = result.get("phases") or []
    for phase in phases:
        for epic in (phase.get("epics") or []):
            epic_issue = {
                "externalId": epic.get("epic_id", ""),
                "issueType": "Epic",
                "summary": epic.get("title", ""),
                "description": epic.get("description", ""),
                "labels": [subdomain_label(epic.get("subdomain_group", ""))],
                "customField_EpicName": epic.get("title", ""),
                "priority": "High" if phase.get("phase_number") == 1 else "Medium",
            }
            issues.append(epic_issue)
            for feat in (epic.get("features") or []):
                for story in (feat.get("user_stories") or []):
                    role = story.get("role") or story.get("as_a") or "User"
                    want = story.get("want") or story.get("i_want") or ""
                    so_that = story.get("so_that") or ""
                    acs = story.get("acceptance_criteria") or []
                    story_issue = {
                        "externalId": f"{epic.get('epic_id', '')}-{feat.get('title', '')[:10]}-{role[:5]}",
                        "issueType": "Story",
                        "summary": f"As a {role}, I want {want}",
                        "description": f"As a {role}, I want {want}, so that {so_that}",
                        "acceptanceCriteria": "\n".join(f"- {ac}" for ac in acs),
                        "epicLink": epic.get("epic_id", ""),
                    }
                    issues.append(story_issue)
    return json.dumps({"projects": [{"issues": issues}]}, indent=2)


def _to_csv(result: dict) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Phase",
        "Initiative ID",
        "Initiative Title",
        "Capability Area",
        "Delivery Sprints",
        "Regulatory Anchor",
        "Innovation Driver",
        "Delivery Standards Count",
    ])
    for phase in (result.get("phases") or []):
        for epic in (phase.get("epics") or []):
            writer.writerow([
                f"Phase {phase.get('phase_number', '')} — {phase.get('phase_name', '')}",
                epic.get("epic_id", ""),
                epic.get("title", ""),
                subdomain_label(epic.get("subdomain_group", "")),
                epic.get("estimated_sprints", ""),
                epic.get("governance_reference", ""),
                epic.get("trend_alignment", ""),
                len(epic.get("acceptance_criteria") or []),
            ])
    return buf.getvalue()


def _to_markdown(result: dict) -> str:
    lines: list[str] = [
        f"# Enterprise Architecture Strategic Roadmap — {result.get('org_type', '')}\n"
    ]
    for phase in (result.get("phases") or []):
        lines.append(f"\n## Phase {phase.get('phase_number')}: {phase.get('phase_name', '')}")
        lines.append(f"Duration: {phase.get('duration_months', 0)} months\n")
        for epic in (phase.get("epics") or []):
            lines.append(f"### {epic.get('epic_id', '')} — {epic.get('title', '')}")
            if epic.get("subdomain_group"):
                lines.append(f"*{label('subdomain')}: {subdomain_label(epic['subdomain_group'])}*\n")
            if epic.get("description"):
                lines.append(epic["description"] + "\n")
            if epic.get("governance_reference"):
                lines.append(f"**{label('governance_reference')}:** {epic['governance_reference']}")
            if epic.get("trend_alignment"):
                lines.append(f"**{label('trend_alignment')}:** {epic['trend_alignment']}")
            lines.append(f"**Delivery Sprints:** {epic.get('estimated_sprints', '—')}\n")
            acs = epic.get("acceptance_criteria") or []
            if acs:
                lines.append(f"**{label('acceptance_criteria')}:**")
                for ac in acs:
                    lines.append(f"- [ ] {ac_badge(ac)}")
                lines.append("")
            for feat in (epic.get("features") or []):
                lines.append(f"#### {label('feature')}: {feat.get('title', '')}")
                for story in (feat.get("user_stories") or []):
                    role = story.get("role") or "User"
                    want = story.get("want") or ""
                    so_that = story.get("so_that") or ""
                    lines.append(
                        f"- **{label('user_story')}** — "
                        f"As a **{role}**, I want {want}, so that {so_that}"
                    )
    return "\n".join(lines)


def render_export_tab(result: dict) -> None:
    st.subheader("Export & Handover")
    fmt = st.radio("Format", ["Jira JSON", "CSV", "Markdown"], horizontal=True)

    if fmt == "Jira JSON":
        content = _to_jira_json(result)
        mime = "application/json"
        filename = "ea_roadmap_jira.json"
    elif fmt == "CSV":
        content = _to_csv(result)
        mime = "text/csv"
        filename = "ea_roadmap.csv"
    else:
        content = _to_markdown(result)
        mime = "text/markdown"
        filename = "ea_roadmap.md"

    st.download_button(
        label=f"Download {fmt}",
        data=content,
        file_name=filename,
        mime=mime,
        width='stretch',
        type="primary",
    )

    st.divider()
    st.caption("Preview (first 3000 characters):")
    st.code(
        content[:3000] + ("…" if len(content) > 3000 else ""),
        language="json" if fmt == "Jira JSON" else "markdown",
    )
