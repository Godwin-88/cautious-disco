"""DRL-based capability prioritizer — wraps the trained REINFORCE policy."""

import logging
from dataclasses import dataclass

import numpy as np

from backend.agents.retriever import EnrichedCapability

log = logging.getLogger(__name__)

BUDGET_SCORES = {"low": 0.33, "medium": 0.67, "high": 1.0}
RISK_SCORES = {"low": 0.33, "medium": 0.67, "high": 1.0}
COMPLEXITY_SCORES = {"low": 0.2, "medium": 0.5, "high": 0.75, "very_high": 1.0}

DOMAIN_FLAGS = [
    "intelligence", "banking", "health", "govern", "cloud", "security", "supply"
]


@dataclass
class PrioritizationResult:
    ordered_capabilities: list[EnrichedCapability]
    priority_scores: list[float]
    drl_used: bool
    state_vector: list[float]


def _capability_business_value(cap: EnrichedCapability) -> float:
    """Heuristic business value: count enriched properties as proxy for importance."""
    score = 0.5
    c = cap.capability
    if c.get("business_outcomes"):
        score += 0.15 * min(len(c["business_outcomes"]), 3) / 3
    if c.get("kpis"):
        score += 0.1
    if cap.trend and cap.trend.get("impact_level") == "transformational":
        score += 0.2
    elif cap.trend and cap.trend.get("impact_level") == "high":
        score += 0.1
    if cap.standard:
        score += 0.05
    return min(score, 1.0)


def _build_state_vector(
    caps: list[EnrichedCapability],
    budget_tier: str,
    timeline_months: int,
    risk_tolerance: str,
) -> np.ndarray:
    top10 = caps[:10]
    bv_scores = [_capability_business_value(c) for c in top10]
    while len(bv_scores) < 10:
        bv_scores.append(0.0)

    budget_score = BUDGET_SCORES.get(budget_tier, 0.67)
    timeline_score = min(timeline_months / 36.0, 1.0)
    risk_score = RISK_SCORES.get(risk_tolerance, 0.67)

    domain_flags = [0.0] * len(DOMAIN_FLAGS)
    for cap in top10:
        domain_name = (cap.domain.get("name") or "").lower()
        for i, flag in enumerate(DOMAIN_FLAGS):
            if flag in domain_name:
                domain_flags[i] = 1.0

    state = bv_scores + [budget_score, timeline_score, risk_score] + domain_flags
    return np.array(state, dtype=np.float32)


class OptimizerAgent:
    def __init__(self, policy=None):
        self.policy = policy

    def prioritize(
        self,
        caps: list[EnrichedCapability],
        budget_tier: str = "medium",
        timeline_months: int = 18,
        risk_tolerance: str = "medium",
    ) -> PrioritizationResult:
        if not caps:
            return PrioritizationResult(
                ordered_capabilities=[],
                priority_scores=[],
                drl_used=False,
                state_vector=[],
            )

        state_vec = _build_state_vector(caps, budget_tier, timeline_months, risk_tolerance)
        n = min(len(caps), 10)

        if self.policy is not None:
            try:
                import torch
                with torch.no_grad():
                    ranking = self.policy.get_priority_ranking(state_vec)
                # ranking is indices 0-9 in priority order; map back to caps
                ordered = []
                seen = set()
                for idx in ranking:
                    if idx < len(caps):
                        ordered.append(caps[idx])
                        seen.add(idx)
                # append remaining caps not in top-10 ranking
                for i, c in enumerate(caps):
                    if i not in seen:
                        ordered.append(c)

                scores = list(state_vec[:n])
                drl_used = True
                log.info(f"DRL policy applied; top cap: {ordered[0].capability.get('name')}")
            except Exception as exc:
                log.warning(f"DRL policy inference failed: {exc}; falling back to heuristic")
                ordered, scores, drl_used = self._heuristic_sort(caps, budget_tier, risk_tolerance)
        else:
            ordered, scores, drl_used = self._heuristic_sort(caps, budget_tier, risk_tolerance)

        return PrioritizationResult(
            ordered_capabilities=ordered,
            priority_scores=scores,
            drl_used=drl_used,
            state_vector=state_vec.tolist(),
        )

    def _heuristic_sort(
        self, caps: list[EnrichedCapability], budget_tier: str, risk_tolerance: str
    ) -> tuple[list[EnrichedCapability], list[float], bool]:
        complexity_penalty = {"low": 0.0, "medium": 0.1, "high": 0.2, "very_high": 0.4}
        risk_weight = RISK_SCORES.get(risk_tolerance, 0.67)

        def sort_key(c: EnrichedCapability) -> float:
            bv = _capability_business_value(c)
            cx = complexity_penalty.get(
                (c.capability.get("implementation_complexity") or "medium").lower(), 0.1
            )
            if risk_tolerance == "low":
                return bv - cx * 1.5
            return bv - cx * 0.5

        sorted_caps = sorted(caps, key=sort_key, reverse=True)
        scores = [_capability_business_value(c) for c in sorted_caps[:10]]
        return sorted_caps, scores, False
