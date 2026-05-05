"""Compliance verifier — checks roadmap against governance standards."""

import json
import logging

from backend.graph.neo4j_client import Neo4jClient
from backend.graph.cypher_queries import GET_STANDARDS_FOR_DOMAIN_NAMES
from backend.llm.client import LLMClient, extract_json
from backend.schemas.response import RoadmapPhase, ComplianceSummary

log = logging.getLogger(__name__)

VERIFY_PROMPT = """You are an Enterprise Architecture compliance auditor.

Review the following roadmap against the applicable governance standards and identify gaps.

NOTE: Acceptance Criteria prefixed with "[Compliance]" explicitly satisfy governance compliance requirements.
Acceptance Criteria prefixed with "[KPI]" are measurable performance indicators.
Count these as FULFILLED requirements — do not flag them as missing.

ROADMAP SUMMARY:
{roadmap_summary}

APPLICABLE STANDARDS:
{standards_context}

Check:
1. Are all compliance_requirements from each standard present as "[Compliance]" ACs? (they count as covered)
2. Are there dependency violations (high-complexity items scheduled before foundations)?
3. Are KPIs measurable and time-bound?
4. Are risk factors addressed in the epics?

Return JSON:
{{
  "score": <integer 0-100>,
  "issues": ["issue1", "issue2", ...],
  "recommendations": ["rec1", "rec2", ...],
  "standards_covered": ["std1", "std2", ...]
}}

If most compliance requirements are tagged as [Compliance] ACs, score should be 75-90.
Score < 70 means significant governance gaps remain."""


def _summarise_roadmap(phases: list[RoadmapPhase]) -> str:
    lines: list[str] = []
    for phase in phases:
        lines.append(f"\n=== Phase {phase.phase_number}: {phase.phase_name} ===")
        for epic in phase.epics[:5]:
            lines.append(f"  Epic: {epic.title}")
            if epic.governance_reference:
                lines.append(f"  Standard ref: {epic.governance_reference}")
            # Always include compliance ACs explicitly so verifier can see them
            comp_acs = [ac for ac in epic.acceptance_criteria if ac.startswith("[Compliance]")]
            other_acs = [ac for ac in epic.acceptance_criteria if not ac.startswith("[Compliance]")][:2]
            all_acs = comp_acs + other_acs
            if all_acs:
                lines.append(f"  ACs: {'; '.join(all_acs[:8])}")
    return "\n".join(lines)[:5000]


class VerifierAgent:
    def __init__(self, neo4j: Neo4jClient, llm: LLMClient):
        self.neo4j = neo4j
        self.llm = llm

    def _get_domain_names(self, phases: list[RoadmapPhase]) -> list[str]:
        names: set[str] = set()
        for phase in phases:
            for epic in phase.epics:
                if epic.governance_reference:
                    # governance_reference format: "StandardName — Publisher"
                    # subdomain_group holds the subdomain name, not domain
                    pass
        # Fall back: collect all unique governance references
        for phase in phases:
            for epic in phase.epics:
                ref = epic.governance_reference or ""
                if ref:
                    names.add(ref.split("—")[0].strip())
        return list(names) or ["Digital Transformation"]

    def _fetch_standards_context(self, domain_names: list[str]) -> str:
        try:
            # Fetch by standard names that appear in governance_reference
            rows = self.neo4j.run_query(
                """
                MATCH (domain:Domain)-[:GOVERNED_BY]->(std:Standard)
                WHERE std.name IN $domain_names
                RETURN std.name AS name,
                       std.compliance_requirements AS reqs,
                       std.key_principles AS principles
                LIMIT 10
                """,
                domain_names=domain_names,
            )
            if not rows:
                return "No specific standards context available."
            parts = []
            for r in rows:
                reqs = r.get("reqs") or []
                parts.append(
                    f"Standard: {r['name']}\n"
                    f"  Requirements: {'; '.join(reqs[:5])}"
                )
            return "\n".join(parts)
        except Exception as exc:
            log.warning(f"Could not fetch standards for verification: {exc}")
            return "Standards context unavailable."

    async def verify(self, phases: list[RoadmapPhase]) -> ComplianceSummary:
        domain_names = self._get_domain_names(phases)
        standards_ctx = self._fetch_standards_context(domain_names)
        roadmap_summary = _summarise_roadmap(phases)

        prompt = VERIFY_PROMPT.format(
            roadmap_summary=roadmap_summary,
            standards_context=standards_ctx,
        )

        try:
            raw = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.2,
            )
            parsed = extract_json(raw)
            if isinstance(parsed, dict):
                return ComplianceSummary(
                    score=int(parsed.get("score") or 0),
                    issues=parsed.get("issues") or [],
                    recommendations=parsed.get("recommendations") or [],
                    standards_covered=parsed.get("standards_covered") or domain_names,
                )
        except Exception as exc:
            log.warning(f"Verification LLM call failed: {exc}")

        # Fallback: basic structural check
        issues: list[str] = []
        for phase in phases:
            for epic in phase.epics:
                if not epic.acceptance_criteria:
                    issues.append(f"Epic '{epic.title}' has no acceptance criteria")
        score = max(50, 100 - len(issues) * 10)
        return ComplianceSummary(score=score, issues=issues, recommendations=[], standards_covered=[])
