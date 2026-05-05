"""Platform Integrations — ITSM Connector, ERP/CRM Ingest, ArchiMate View."""

import streamlit as st
import pandas as pd

from frontend.utils.api_client import export_to_jira, connect_itsm, ingest_erp_csv, get_archimate

_SAMPLE_CSV = (
    "org_type,business_unit,system_name,vendor,capabilities_in_use,annual_budget_usd\n"
    "Enterprise Bank,Finance,SAP S/4HANA,SAP,"
    '"General Ledger Management,Financial Reporting",2400000\n'
    "Enterprise Bank,HR,Workday HCM,Workday,"
    '"HR Analytics,Talent Management",380000\n'
    "Enterprise Bank,Technology,ServiceNow ITSM,ServiceNow,"
    '"IT Service Management,Change Management",520000\n'
    "Enterprise Bank,Sales,Salesforce CRM,Salesforce,"
    '"Customer Data Management,Sales Analytics",290000\n'
    "Enterprise Bank,Operations,Oracle ERP Cloud,Oracle,"
    '"Supply Chain Management,Procurement Management",1100000\n'
)


def render_integrations_tab(result: dict | None = None):
    st.subheader("Platform Integrations")
    st.caption(
        "Connect your EA roadmap to ITSM tools, ingest ERP/CRM system inventories, "
        "and view capabilities mapped to ArchiMate architecture layers."
    )

    inner = st.tabs(["ITSM Connector", "ERP / CRM Ingest", "ArchiMate View"])
    with inner[0]:
        _render_itsm(result)
    with inner[1]:
        _render_erp_ingest()
    with inner[2]:
        _render_archimate()


# ── ITSM Connector ────────────────────────────────────────────────────────────

def _render_itsm(result: dict | None):
    st.markdown("#### ITSM Connector")

    t1, t2, t3 = st.columns(3)
    with t1:
        st.success("**Jira Cloud** ✓ Live")
    with t2:
        st.info("**ServiceNow** Mock")
    with t3:
        st.info("**Azure DevOps** Mock")

    # ── Jira (Live) ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### Jira Cloud — Live Export")

    c1, c2 = st.columns(2)
    with c1:
        jira_url = st.text_input(
            "Jira URL", placeholder="https://yourorg.atlassian.net", key="jira_url"
        )
        jira_email = st.text_input(
            "Email", placeholder="user@yourorg.com", key="jira_email"
        )
    with c2:
        jira_token = st.text_input("API Token", type="password", key="jira_token")
        project_key = st.text_input("Project Key", value="EAOPT", key="jira_project")

    phases = (result or {}).get("phases", [])
    has_creds = bool(jira_url and jira_email and jira_token and project_key)
    has_roadmap = bool(phases)

    if st.button(
        "Export Roadmap to Jira",
        type="primary",
        disabled=not (has_creds and has_roadmap),
        help=(
            "Generate a roadmap first, then enter Jira credentials."
            if not has_roadmap
            else "Enter Jira credentials to export." if not has_creds
            else ""
        ),
    ):
        with st.spinner("Creating Jira Epics and Stories…"):
            try:
                res = export_to_jira(
                    {
                        "jira_url": jira_url,
                        "jira_email": jira_email,
                        "jira_api_token": jira_token,
                        "project_key": project_key,
                        "phases": phases,
                    }
                )
                errs = res.get("errors", [])
                if errs:
                    st.warning(f"Completed with {len(errs)} warning(s): {errs[:2]}")
                else:
                    st.success(
                        f"Created **{res.get('created_epics', 0)} Epics** and "
                        f"**{res.get('created_stories', 0)} Stories** in "
                        f"`{project_key}`"
                    )
                browse = (
                    jira_url.rstrip("/")
                    + f"/jira/software/projects/{project_key}/boards"
                )
                st.markdown(f"[Open {project_key} in Jira →]({browse})")
            except Exception as exc:
                st.error(f"Jira export failed: {exc}")

    if not has_roadmap:
        st.caption("Generate a strategic roadmap first to enable Jira export.")

    # ── ServiceNow (Mock) ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### ServiceNow — Integration Preview")

    sn_c1, sn_c2 = st.columns([3, 1])
    with sn_c1:
        sn_url = st.text_input(
            "Instance URL",
            placeholder="https://yourinstance.service-now.com",
            key="sn_url",
        )
        sn_user = st.text_input("Username", key="sn_user")
        sn_pass = st.text_input("Password", type="password", key="sn_pass")
    with sn_c2:
        st.write("")
        st.write("")
        sn_connect = st.button("Test Connection", key="sn_connect")

    if sn_connect:
        with st.spinner("Connecting to ServiceNow…"):
            try:
                res = connect_itsm(
                    "servicenow",
                    sn_url or "https://demo.service-now.com",
                    {"username": sn_user, "password": sn_pass},
                )
                items = res.get("sample_work_items", [])
                st.success(
                    f"Connected · {len(items)} sample work items retrieved"
                )
                if items:
                    st.json(items[:2])
            except Exception as exc:
                st.error(f"Connection failed: {exc}")

    # ── Azure DevOps (Mock) ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### Azure DevOps — Integration Preview")

    ado_c1, ado_c2 = st.columns([3, 1])
    with ado_c1:
        ado_org = st.text_input(
            "Organisation URL",
            placeholder="https://dev.azure.com/yourorg",
            key="ado_org",
        )
        ado_pat = st.text_input(
            "Personal Access Token", type="password", key="ado_pat"
        )
    with ado_c2:
        st.write("")
        st.write("")
        ado_connect = st.button("Test Connection", key="ado_connect")

    if ado_connect:
        with st.spinner("Connecting to Azure DevOps…"):
            try:
                res = connect_itsm(
                    "azure_devops",
                    ado_org or "https://dev.azure.com/demo",
                    {"pat": ado_pat},
                )
                items = res.get("sample_work_items", [])
                st.success(f"Connected · {len(items)} sample items retrieved")
                if items:
                    st.json(items[:2])
            except Exception as exc:
                st.error(f"Connection failed: {exc}")


# ── ERP / CRM Ingest ─────────────────────────────────────────────────────────

def _render_erp_ingest():
    st.markdown("#### ERP / CRM Data Ingest")
    st.markdown(
        "Upload a system inventory CSV to link your organisation's existing tools "
        "to the knowledge graph as `:ExternalSystem` nodes."
    )

    st.info(
        "**Expected columns:** `org_type`, `business_unit`, `system_name`, `vendor`, "
        "`capabilities_in_use` (comma-separated), `annual_budget_usd`\n\n"
        "**Supported systems:** SAP · Oracle ERP · Salesforce · "
        "ServiceNow · Workday · Microsoft Dynamics"
    )

    st.download_button(
        "Download Sample CSV Template",
        data=_SAMPLE_CSV,
        file_name="erp_inventory_sample.csv",
        mime="text/csv",
    )

    uploaded = st.file_uploader("Upload System Inventory CSV", type=["csv"])
    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            st.caption(f"Preview — {len(df)} rows · {len(df.columns)} columns")
            st.dataframe(df.head(5), use_container_width=True)
        except Exception as exc:
            st.warning(f"Preview error: {exc}")

        uploaded.seek(0)
        if st.button("Ingest into Knowledge Graph", type="primary"):
            with st.spinner("Ingesting ERP/CRM data into Neo4j…"):
                try:
                    res = ingest_erp_csv(uploaded.read(), uploaded.name)
                    st.success(
                        f"Ingested **{res.get('rows_ingested', 0)} rows** · "
                        f"**{res.get('systems_found', 0)} systems** detected · "
                        f"**{res.get('capabilities_linked', 0)} capabilities** linked "
                        f"in the knowledge graph"
                    )
                    st.caption(
                        "ExternalSystem nodes are now visible in the Graph Explorer."
                    )
                except Exception as exc:
                    st.error(f"Ingest failed: {exc}")


# ── ArchiMate View ────────────────────────────────────────────────────────────

_LAYER_ICONS = {"Business": "🏢", "Application": "💻", "Technology": "⚙️"}

_LAYER_HELP = {
    "Business": (
        "Capabilities that model business processes, services, governance, "
        "and organisational roles."
    ),
    "Application": (
        "Capabilities related to software applications, data management, "
        "APIs, analytics, and integration platforms."
    ),
    "Technology": (
        "Capabilities covering infrastructure, cloud platforms, networking, "
        "security, and hardware."
    ),
}


def _render_archimate():
    st.markdown("#### ArchiMate Architecture Layer View")
    st.markdown(
        "Enterprise capabilities mapped to the three ArchiMate 3.1 layers — "
        "**Business**, **Application**, and **Technology** — "
        "derived from the live knowledge graph."
    )

    with st.spinner("Classifying capabilities into ArchiMate layers…"):
        try:
            data = get_archimate()
        except Exception as exc:
            st.error(f"Failed to load ArchiMate data: {exc}")
            return

    business = data.get("business", [])
    application = data.get("application", [])
    technology = data.get("technology", [])
    total = len(business) + len(application) + len(technology)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Mapped", total)
    m2.metric("Business Layer", len(business))
    m3.metric("Application Layer", len(application))
    m4.metric("Technology Layer", len(technology))

    st.write("")

    layer = st.radio(
        "Select Architecture Layer:",
        options=["Business", "Application", "Technology"],
        horizontal=True,
        key="archimate_layer",
    )

    layer_data = {"Business": business, "Application": application, "Technology": technology}[
        layer
    ]

    icon = _LAYER_ICONS[layer]
    help_text = _LAYER_HELP[layer]

    st.markdown(f"**{icon} {layer} Layer** — {len(layer_data)} capabilities")
    st.caption(help_text)

    if not layer_data:
        st.info(f"No capabilities classified in the {layer} layer.")
        return

    df = pd.DataFrame(
        [
            {
                "Capability": item.get("name", ""),
                "Domain": item.get("domain", ""),
                "Sub-Domain": item.get("subdomain", ""),
                "Complexity": item.get("complexity", ""),
            }
            for item in layer_data
        ]
    )

    st.dataframe(
        df,
        use_container_width=True,
        height=520,
        column_config={
            "Capability": st.column_config.TextColumn(width="large"),
            "Domain": st.column_config.TextColumn(width="medium"),
            "Sub-Domain": st.column_config.TextColumn(width="medium"),
            "Complexity": st.column_config.TextColumn(width="small"),
        },
    )
