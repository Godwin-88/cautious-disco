"""Generator agent — derives structured roadmap artifacts from graph-property context."""

import asyncio
import json
import logging
from typing import Any

from backend.agents.retriever import EnrichedCapability
from backend.llm.client import LLMClient, extract_json
from backend.llm.prompts import build_epic_prompt, build_roadmap_structure_prompt
from backend.schemas.request import AnalyzeRequest
from backend.schemas.response import (
    RoadmapPhase,
    EpicArtifact,
    Feature,
    UserStory,
    Task,
)

log = logging.getLogger(__name__)

COMPLEXITY_TO_PHASE = {
    "low": 1,
    "medium": 1,
    "high": 2,
    "very_high": 3,
}

MATURITY_TO_PHASE = {
    "<1yr": 1,
    "1-2yr": 1,
    "2-5yr": 2,
    "5+yr": 3,
}


def _assign_phase(cap: EnrichedCapability) -> int:
    cx = (cap.capability.get("implementation_complexity") or "medium").lower()
    phase = COMPLEXITY_TO_PHASE.get(cx, 2)
    if cap.trend:
        horizon = cap.trend.get("time_horizon") or "2-5yr"
        trend_phase = MATURITY_TO_PHASE.get(horizon, 2)
        # Use trend phase only if it pushes later, not earlier
        phase = max(phase, trend_phase)
    # Duration-based override: short tasks → earlier phases
    duration = cap.capability.get("typical_duration_weeks") or 12
    if duration <= 8 and phase > 1:
        phase = 1
    elif duration >= 24 and phase < 3:
        phase = min(phase + 1, 3)
    return min(phase, 3)


def _build_epic_from_cap(cap: EnrichedCapability, request: AnalyzeRequest) -> dict:
    """Build the context dict passed to the LLM prompt."""
    c = cap.capability
    std = cap.standard or {}
    trend = cap.trend or {}
    sd = cap.subdomain or {}

    return {
        "org_type": request.org_type,
        "goals": request.goals,
        "budget_tier": request.budget_tier,
        "timeline_months": request.timeline_months,
        "risk_tolerance": request.risk_tolerance,
        "domain_name": cap.domain.get("name", ""),
        "subdomain_name": sd.get("name", ""),
        "subdomain_functional_scope": sd.get("functional_scope", ""),
        "subdomain_business_driver": sd.get("business_driver", ""),
        "cap_name": c.get("name", ""),
        "cap_description": c.get("description", ""),
        "cap_business_outcomes": c.get("business_outcomes") or [],
        "cap_risk_factors": c.get("risk_factors") or [],
        "cap_kpis": c.get("kpis") or [],
        "cap_duration_weeks": c.get("typical_duration_weeks") or 12,
        "cap_complexity": c.get("implementation_complexity") or "medium",
        "cap_frameworks": c.get("common_frameworks") or [],
        "cap_solution_patterns": c.get("solution_patterns") or [],
        "std_name": std.get("name", ""),
        "std_publisher": std.get("publisher", ""),
        "std_version": std.get("version", ""),
        "std_key_principles": std.get("key_principles") or [],
        "std_compliance_requirements": std.get("compliance_requirements") or [],
        "trend_name": trend.get("name", ""),
        "trend_source": trend.get("source", ""),
        "trend_impact": trend.get("impact_level", ""),
        "trend_maturity": trend.get("maturity", ""),
        "trend_horizon": trend.get("time_horizon", ""),
        "trend_business_impact": trend.get("business_impact", ""),
        "trend_enablers": trend.get("technology_enablers") or [],
        "subcapabilities": [sc.get("name", "") for sc in cap.subcapabilities],
    }


def _parse_epic_response(raw: dict, cap: EnrichedCapability, phase_num: int) -> EpicArtifact:
    """Parse LLM JSON response into EpicArtifact, injecting compliance ACs if missing."""
    std_reqs = (cap.standard or {}).get("compliance_requirements") or []
    cap_kpis = cap.capability.get("kpis") or []

    features: list[Feature] = []
    for f in raw.get("features") or []:
        stories: list[UserStory] = []
        for s in f.get("user_stories") or []:
            raw_tasks = s.get("tasks") or []
            tasks = []
            for t in raw_tasks:
                if isinstance(t, dict):
                    tasks.append(Task(
                        title=t.get("title") or t.get("name") or "",
                        description=t.get("description") or "",
                        estimated_days=int(t.get("estimated_days") or 3),
                        assignee_role=t.get("assignee_role") or "",
                    ))
                elif isinstance(t, str):
                    tasks.append(Task(title=t))
            stories.append(
                UserStory(
                    role=s.get("role", "architect"),
                    want=s.get("want", ""),
                    so_that=s.get("so_that", ""),
                    acceptance_criteria=s.get("acceptance_criteria") or [],
                    tasks=tasks,
                )
            )
        features.append(
            Feature(
                title=f.get("title", ""),
                description=f.get("description", ""),
                technical_notes=f.get("technical_notes", ""),
                user_stories=stories,
                estimated_story_points=f.get("estimated_story_points"),
            )
        )

    # Ensure compliance ACs appear at epic level
    epic_acs: list[str] = list(raw.get("acceptance_criteria") or [])
    for req in std_reqs:
        if req and not any(req[:30] in ac for ac in epic_acs):
            epic_acs.append(f"[Compliance] {req}")
    for kpi in cap_kpis:
        if kpi and not any(kpi[:30] in ac for ac in epic_acs):
            epic_acs.append(f"[KPI] {kpi}")

    return EpicArtifact(
        epic_id=f"EPIC-{cap.capability.get('id', 'unknown')[:8].upper()}",
        title=raw.get("title") or cap.capability.get("name", ""),
        description=raw.get("description") or cap.capability.get("description") or "",
        business_value=raw.get("business_value") or "",
        strategic_rationale=raw.get("strategic_rationale") or (cap.trend or {}).get("business_impact") or "",
        governance_reference=(
            f"{(cap.standard or {}).get('name','')} — {(cap.standard or {}).get('publisher','')}"
        ).strip(" —"),
        trend_alignment=(cap.trend or {}).get("name") or "",
        acceptance_criteria=epic_acs,
        features=features,
        risk_register=raw.get("risks") or cap.capability.get("risk_factors") or [],
        estimated_sprints=max(1, (cap.capability.get("typical_duration_weeks") or 12) // 2),
        phase=phase_num,
        subdomain_group=cap.subdomain.get("name") or "",
    )


class GeneratorAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def _generate_epic(self, ctx: dict, cap: EnrichedCapability, phase_num: int) -> EpicArtifact:
        prompt = build_epic_prompt(ctx)
        try:
            raw_text = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
                temperature=0.4,
            )
            raw = extract_json(raw_text)
            if isinstance(raw, dict):
                return _parse_epic_response(raw, cap, phase_num)
        except Exception as exc:
            log.warning(f"Epic generation failed for {cap.capability.get('name')}: {exc}")

        # Deterministic fallback from graph properties
        return _parse_epic_response({}, cap, phase_num)

    async def generate(
        self,
        caps: list[EnrichedCapability],
        request: AnalyzeRequest,
        compliance_issues: list[str] | None = None,
    ) -> list[RoadmapPhase]:
        phase_map: dict[int, list[EpicArtifact]] = {1: [], 2: [], 3: []}

        capped = caps[:20]

        async def _process(idx_cap: tuple[int, EnrichedCapability]) -> tuple[int, EpicArtifact]:
            idx, cap = idx_cap
            # Rank-based bucketing ensures phase variety: top third→1, mid→2, bottom→3
            n = len(capped)
            rank_phase = 1 if idx < n // 3 else (2 if idx < 2 * n // 3 else 3)
            # Property-based phase can only push LATER (never earlier than rank suggests)
            prop_phase = _assign_phase(cap)
            phase_num = max(rank_phase, prop_phase) if prop_phase == 3 else rank_phase
            ctx = _build_epic_from_cap(cap, request)
            if compliance_issues:
                ctx["compliance_issues"] = compliance_issues
            epic = await self._generate_epic(ctx, cap, phase_num)
            return phase_num, epic

        results = await asyncio.gather(*[_process((i, c)) for i, c in enumerate(capped)])
        for phase_num, epic in results:
            phase_map[phase_num].append(epic)

        phase_names = {
            1: "Foundation & Quick Wins",
            2: "Core Transformation",
            3: "Advanced Capabilities",
        }
        phase_durations = {
            1: min(request.timeline_months // 3, 6),
            2: min(request.timeline_months // 3, 12),
            3: request.timeline_months - (min(request.timeline_months // 3, 6) + min(request.timeline_months // 3, 12)),
        }

        phases: list[RoadmapPhase] = []
        for num in [1, 2, 3]:
            epics = phase_map[num]
            if not epics:
                continue
            phases.append(
                RoadmapPhase(
                    phase_number=num,
                    phase_name=phase_names[num],
                    duration_months=max(phase_durations[num], 1),
                    epics=epics,
                    objectives=[
                        e.business_value for e in epics[:3] if e.business_value
                    ],
                    key_milestones=[e.title for e in epics[:2]],
                )
            )

        return phases
