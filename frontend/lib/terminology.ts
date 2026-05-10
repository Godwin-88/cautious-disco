export const TABS = [
  "EA Advisor",
  "Graph Explorer",
  "Strategic Roadmap",
  "Initiatives & Scenarios",
  "Integrations",
  "Export & Handover",
  "AI Learning Engine",
] as const;

export const DOMAIN_OVERRIDES: Record<string, string> = {
  "Manage Generic Core": "Enterprise Architecture Core",
  "Manage Digital Intelligence": "Digital Intelligence & Data",
  "Manage Digital IT": "Technology Operations",
  "Manage Digital Inter-Operability & Automation": "Integration & Automation",
  "Manage Digital Experience Orchestration": "Customer Experience",
  "Manage Digital Service Orchestration": "Service Delivery",
  "Manage Digital MarCom Orchestration": "Marketing & Communications",
  "Manage Digital Backoffice": "Business Operations",
  "Manage Digital GPRC": "Governance, Risk & Compliance",
  "Manage Digital Workspace": "Workforce & Collaboration",
  "Manage Digital Security": "Cybersecurity & Trust",
};

export function domainLabel(graphName: string): string {
  if (!graphName) return graphName;
  if (DOMAIN_OVERRIDES[graphName]) return DOMAIN_OVERRIDES[graphName];
  let label = graphName;
  label = label.replace(/^Manage\s+/, "");
  for (const suffix of [" Core Operations", " Core Operation"]) {
    if (label.endsWith(suffix)) {
      label = label.slice(0, -suffix.length);
      break;
    }
  }
  return label.trim();
}

export function subdomainLabel(graphName: string): string {
  if (!graphName) return graphName;
  return graphName.replace(/^Manage\s+/, "").trim();
}

export const LABELS: Record<string, string> = {
  epic: "Strategic Initiative",
  epics: "Strategic Initiatives",
  feature: "Workstream",
  features: "Workstreams",
  user_story: "Business Scenario",
  user_stories: "Business Scenarios",
  acceptance_criteria: "Delivery Standards",
  subdomain: "Capability Area",
  standard: "Governance Framework",
  trend: "Innovation Driver",
  subcapability: "Operational Capability",
  capability: "Strategic Capability",
  risk_register: "Risk Landscape",
  processing_time: "AI Analysis Time",
  capabilities_retrieved: "Strategic Capabilities Analysed",
  gpu_device: "GPU Device",
  rocm_version: "ROCm Version",
  compliance_score: "Governance Readiness Score",
  standards_covered: "Governance Frameworks Verified",
  governance_reference: "Regulatory Anchor",
  trend_alignment: "Innovation Alignment",
  strategic_rationale: "Strategic Rationale",
  business_value: "Business Value",
  drl_used_true: "AMD-Powered AI Prioritisation",
  drl_used_false: "Heuristic Prioritisation",
  drl_trace: "AI Capability Prioritisation",
  "[Compliance]": "Regulatory Obligation",
  "[KPI]": "Performance Target",
};

export function label(key: string): string {
  return LABELS[key] ?? key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function acBadge(ac: string): string {
  if (ac.startsWith("[Compliance]")) {
    return "🔒 " + ac.replace(/^\[Compliance\]\s*/, "");
  }
  if (ac.startsWith("[KPI]")) {
    return "📊 " + ac.replace(/^\[KPI\]\s*/, "");
  }
  return ac;
}
