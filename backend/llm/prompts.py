"""All LLM prompt templates for the EA Optimizer agents."""

ORCHESTRATOR_SYSTEM = """You are an Enterprise Architecture Strategist AI, powered by AMD MI300X and Qwen-72B.
You help CIOs and enterprise architects turn business goals into compliant, optimised implementation roadmaps.
You are grounded in a knowledge graph of 1,400+ enterprise capabilities, governance standards, and digital transformation trends.
Be precise, structured, and actionable. Always ground your recommendations in the provided graph context."""

# ---------------------------------------------------------------------------
# Retriever: query expansion
# ---------------------------------------------------------------------------

QUERY_EXPANSION_PROMPT = """You are an Enterprise Architecture expert.

Organisation type: {org_type}
Business goals: {goals}

Generate {n_queries} specific search queries to find relevant capabilities in an Enterprise Architecture knowledge graph.
Focus on actionable digital capabilities — be specific to the industry and goals.

Return ONLY a valid JSON array of strings, no markdown, no explanation.
Example: ["data governance and ownership management", "API management and integration platform"]"""

# ---------------------------------------------------------------------------
# Generator: roadmap generation
# ---------------------------------------------------------------------------

GENERATOR_SYSTEM = """You are an Enterprise Architecture Roadmap Generator powered by AMD MI300X.
You produce structured, governance-compliant implementation roadmaps in JSON format.
Your outputs are grounded in graph-retrieved capabilities, authoritative standards, and verified digital transformation trends.
Generate Jira-ready artifacts: epics, features, user stories with acceptance criteria, and tasks."""

GENERATOR_USER_TEMPLATE = """Generate a phased Enterprise Architecture roadmap based on the following inputs.

=== ORGANISATION CONTEXT ===
Organisation Type: {org_type}
Business Goals: {goals_str}
Budget Tier: {budget_tier} | Timeline: {timeline_months} months | Risk Tolerance: {risk_tolerance}

=== PRIORITY-ORDERED CAPABILITIES (from DRL optimiser) ===
{priority_context}

=== KNOWLEDGE GRAPH CONTEXT ===
{graph_context}

{compliance_feedback}

=== OUTPUT REQUIREMENTS ===
Generate a roadmap with exactly 3 phases, structured as follows:

{{
  "phases": [
    {{
      "phase_number": 1,
      "phase_name": "Foundation & Governance",
      "domain_context": "<primary domain focus>",
      "duration_months": <int>,
      "strategic_theme": "<theme>",
      "epics": [
        {{
          "epic_id": "EP-{org_short}-01",
          "epic_title": "<capability name>",
          "subdomain_group": "<subdomain name>",
          "description": "<2-3 sentences from capability.description + subdomain.functional_scope>",
          "business_value": "<from capability.business_outcomes — 2 specific outcomes>",
          "strategic_rationale": "<from trend.business_impact — cite source>",
          "governance_reference": "<std.name (std.publisher std.version)>",
          "trend_alignment": "<trend.name — trend.source>",
          "architecture_principles": ["<from std.key_principles>", ...],
          "risk_register": ["<from capability.risk_factors>", ...],
          "estimated_sprints": <int — capability.typical_duration_weeks / 2>,
          "kpi_targets": ["<from capability.kpis>", ...],
          "features": [
            {{
              "feature_id": "FEAT-{org_short}-01-01",
              "title": "<subcapability.name>",
              "description": "<subcapability.description or derived>",
              "technical_notes": "<from trend.technology_enablers>",
              "user_stories": [
                {{
                  "story_id": "US-{org_short}-01-01-01",
                  "as_a": "<business role>",
                  "i_want": "<capability outcome>",
                  "so_that": "<business value from capability.business_outcomes>",
                  "acceptance_criteria": [
                    "<VERBATIM from std.compliance_requirements — at least 2>",
                    "<from capability.kpis — at least 1 measurable AC>",
                    "<functional acceptance criterion>"
                  ],
                  "tasks": [
                    {{
                      "task_id": "TASK-{org_short}-01-01-01-01",
                      "name": "<specific implementation task>",
                      "description": "<task detail informed by capability.common_frameworks>",
                      "estimated_days": <int>,
                      "assignee_role": "<e.g. Solutions Architect, Data Engineer>"
                    }}
                  ]
                }}
              ]
            }}
          ],
          "acceptance_criteria": [
            "<VERBATIM from std.compliance_requirements — governance AC>",
            "<from capability.kpis — measurable AC>",
            "<phase exit criterion>"
          ]
        }}
      ],
      "dependencies": ["<list any capability IDs this phase depends on>"]
    }}
  ]
}}

CRITICAL RULES:
1. acceptance_criteria MUST include at least 2 items verbatim from std.compliance_requirements
2. acceptance_criteria MUST include at least 1 measurable KPI from capability.kpis
3. Each phase must have at least 2 epics
4. Each epic must have at least 2 features
5. Each feature must have at least 1 user story with at least 3 acceptance criteria
6. Phase 1 = foundation/governance capabilities (low complexity), Phase 2 = core capabilities (medium), Phase 3 = advanced (high/very_high complexity)
7. Assign capability.implementation_complexity=very_high to Phase 3

Return ONLY valid JSON. No markdown fences. No explanation."""

COMPLIANCE_FEEDBACK_TEMPLATE = """
=== COMPLIANCE ISSUES FROM PREVIOUS ITERATION (iteration {iteration}) ===
The Verifier identified these issues. Address ALL of them in this regeneration:
{issues}
"""

# ---------------------------------------------------------------------------
# Verifier: compliance check
# ---------------------------------------------------------------------------

VERIFIER_SYSTEM = """You are an Enterprise Architecture Compliance Verifier.
You check roadmaps against governance standards and architecture principles.
Be rigorous — identify genuine gaps in compliance coverage, dependency ordering, and risk management."""

def build_epic_prompt(ctx: dict) -> str:
    """Build per-capability epic generation prompt from graph-derived context dict."""
    compliance_note = ""
    if ctx.get("compliance_issues"):
        compliance_note = (
            "\n=== COMPLIANCE ISSUES TO FIX ===\n"
            + "\n".join(f"- {i}" for i in ctx["compliance_issues"])
        )
    subcaps = ", ".join(ctx.get("subcapabilities") or []) or "see capability description"
    reqs = ctx.get("std_compliance_requirements") or []
    reqs_str = "\n".join(f"  - {r}" for r in reqs[:6]) or "  (not specified)"

    # Cross-domain context: when org_type differs from the domain (e.g. PE firm in Aviation)
    org = ctx.get("org_type", "")
    domain = ctx.get("domain_name", "")
    cross_domain_note = ""
    if org and domain and not any(w.lower() in domain.lower() for w in org.split()[:2]):
        cross_domain_note = (
            f"\nCROSS-DOMAIN CONTEXT: The organisation ({org}) is operating across or investing in "
            f"the {domain} domain. Frame this Epic from the perspective of {org} — "
            "emphasise integration points, governance obligations, and value extraction relevant "
            "to their specific strategic position in this domain."
        )

    return f"""You are an Enterprise Architecture expert. Generate a Jira-ready Epic artifact.

ORGANISATION: {org}
CAPABILITY: {ctx['cap_name']}
Domain: {domain} > SubDomain: {ctx['subdomain_name']}
SubDomain scope: {ctx.get('subdomain_functional_scope','')}
Business driver: {ctx.get('subdomain_business_driver','')}
Description: {ctx.get('cap_description','')}
Business outcomes: {', '.join(ctx.get('cap_business_outcomes',[])[:3])}
KPIs: {', '.join(ctx.get('cap_kpis',[])[:3])}
Risk factors: {', '.join(ctx.get('cap_risk_factors',[])[:3])}
Duration: {ctx.get('cap_duration_weeks',12)} weeks | Complexity: {ctx.get('cap_complexity','medium')}
Frameworks: {', '.join(ctx.get('cap_frameworks',[])[:3])}{cross_domain_note}

GOVERNANCE STANDARD: {ctx.get('std_name','')} ({ctx.get('std_publisher','')} {ctx.get('std_version','')})
Compliance requirements (MUST appear verbatim as ACs):
{reqs_str}

TREND: {ctx.get('trend_name','')} — {ctx.get('trend_source','')}
Business impact: {ctx.get('trend_business_impact','')}
Technology enablers: {', '.join(ctx.get('trend_enablers',[])[:4])}

SUB-CAPABILITIES (each becomes a Feature): {subcaps}
{compliance_note}

Return ONLY valid JSON (no markdown fences):
{{
  "title": "<capability name>",
  "description": "<2 sentences: capability description + subdomain scope>",
  "business_value": "<from business_outcomes — 2 specific outcomes>",
  "strategic_rationale": "<from trend.business_impact — cite source>",
  "acceptance_criteria": [
    "<VERBATIM compliance requirement 1>",
    "<VERBATIM compliance requirement 2>",
    "<KPI-based measurable AC>",
    "<phase exit criterion>"
  ],
  "features": [
    {{
      "title": "<sub-capability name>",
      "description": "<1 sentence>",
      "technical_notes": "<from technology_enablers>",
      "user_stories": [
        {{
          "role": "<business role e.g. Data Analyst>",
          "want": "<specific feature capability>",
          "so_that": "<business outcome>",
          "acceptance_criteria": ["<AC1>","<AC2>","<AC3>"],
          "tasks": [
            {{
              "title": "<specific delivery task, max 10 words>",
              "description": "<1-sentence detail from capability.common_frameworks>",
              "estimated_days": <int 1-10>,
              "assignee_role": "<e.g. Solutions Architect, Data Engineer, Security Analyst>"
            }}
          ]
        }}
      ],
      "estimated_story_points": <int 1-13>
    }}
  ],
  "risks": ["<risk1>","<risk2>"]
}}
8. Each user story must have at least 2 tasks with title, description, estimated_days, and assignee_role"""


def build_roadmap_structure_prompt(ctx: dict) -> str:
    """Build full multi-phase roadmap prompt (used for batch generation)."""
    return GENERATOR_USER_TEMPLATE.format(**ctx)


VERIFIER_USER_TEMPLATE = """Review this Enterprise Architecture roadmap for compliance quality.

=== APPLICABLE STANDARDS (from knowledge graph [:GOVERNED_BY] relationships) ===
{standards_context}

=== ROADMAP TO VERIFY ===
{roadmap_summary}

Organisation: {org_type} | Budget: {budget_tier} | Risk Tolerance: {risk_tolerance}

Check for:
1. Are the governance standards' compliance_requirements represented as acceptance criteria?
2. Are dependencies respected (foundation before advanced capabilities)?
3. Are risk factors acknowledged in the risk register?
4. Are KPIs included as measurable acceptance criteria?
5. Does each phase have a coherent strategic theme?

Return ONLY valid JSON:
{{
  "score": <0-100>,
  "standards_checked": ["<list of standard names verified against>"],
  "issues": [
    "<specific gap — e.g. 'TOGAF compliance requirement X not present as AC in Epic EP-01'>"
  ],
  "recommendations": [
    "<specific recommendation>"
  ],
  "summary": "<1-2 sentence overall assessment>"
}}"""
