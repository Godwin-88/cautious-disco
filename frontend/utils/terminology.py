"""
Shared UI terminology — maps graph node names and technical labels to
judge-friendly language. Import from any component.
"""

# ---------------------------------------------------------------------------
# Domain name → display name
# ---------------------------------------------------------------------------

_DOMAIN_OVERRIDES: dict[str, str] = {
    "Manage Generic Core":                                   "Enterprise Architecture Core",
    "Manage Digital Intelligence":                           "Digital Intelligence & Data",
    "Manage Digital IT":                                     "Technology Operations",
    "Manage Digital Inter-Operability & Automation":         "Integration & Automation",
    "Manage Digital Experience Orchestration":               "Customer Experience",
    "Manage Digital Service Orchestration":                  "Service Delivery",
    "Manage MarCom Orchestration":                           "Marketing & Communications",
    "Manage Digital Backoffice":                             "Business Operations",
    "Manage Digital GPRC":                                   "Governance, Risk & Compliance",
    "Manage Digital Workspace":                              "Workforce & Collaboration",
    "Manage Digital Security":                               "Cybersecurity & Trust",
}


def domain_label(graph_name: str) -> str:
    """Return a human-friendly domain name for display."""
    if not graph_name:
        return graph_name
    if graph_name in _DOMAIN_OVERRIDES:
        return _DOMAIN_OVERRIDES[graph_name]
    label = graph_name
    label = label.removeprefix("Manage ")
    for suffix in (" Core Operations", " Core Operation"):
        if label.endswith(suffix):
            label = label[: -len(suffix)]
            break
    return label.strip()


def subdomain_label(graph_name: str) -> str:
    """Strip 'Manage ' prefix from subdomain names."""
    if not graph_name:
        return graph_name
    return graph_name.removeprefix("Manage ").strip()


# ---------------------------------------------------------------------------
# Fixed label maps
# ---------------------------------------------------------------------------

LABELS = {
    # Node types
    "epic":              "Strategic Initiative",
    "epics":             "Strategic Initiatives",
    "feature":           "Workstream",
    "features":          "Workstreams",
    "user_story":        "Business Scenario",
    "user_stories":      "Business Scenarios",
    "acceptance_criteria": "Delivery Standards",
    "subdomain":         "Capability Area",
    "standard":          "Governance Framework",
    "trend":             "Innovation Driver",
    "subcapability":     "Operational Capability",
    "capability":        "Strategic Capability",
    "risk_register":     "Risk Landscape",

    # Metrics
    "processing_time":          "AI Analysis Time",
    "capabilities_retrieved":   "Strategic Capabilities Analysed",
    "gpu_device":               "GPU Device",
    "rocm_version":             "ROCm Version",
    "compliance_score":         "Governance Readiness Score",
    "standards_covered":        "Governance Frameworks Verified",

    # References
    "governance_reference":     "Regulatory Anchor",
    "trend_alignment":          "Innovation Alignment",
    "strategic_rationale":      "Strategic Rationale",
    "business_value":           "Business Value",

    # DRL / AI
    "drl_used_true":  "AMD-Powered AI Prioritisation",
    "drl_used_false": "Heuristic Prioritisation",
    "drl_trace":      "AI Capability Prioritisation",

    # AC badge prefixes
    "[Compliance]":  "Regulatory Obligation",
    "[KPI]":         "Performance Target",
}


def label(key: str) -> str:
    return LABELS.get(key, key.replace("_", " ").title())


def ac_badge(ac: str) -> str:
    """Replace [Compliance] / [KPI] prefixes with friendly badges."""
    if ac.startswith("[Compliance]"):
        return "🔒 " + ac.removeprefix("[Compliance]").strip()
    if ac.startswith("[KPI]"):
        return "📊 " + ac.removeprefix("[KPI]").strip()
    return ac


# ---------------------------------------------------------------------------
# Tab names (single source of truth)
# ---------------------------------------------------------------------------

TABS = [
    "EA Advisor",
    "Graph Explorer",
    "Strategic Roadmap",
    "Initiatives & Scenarios",
    "Integrations",
    "Export & Handover",
    "AI Learning Engine",
]
