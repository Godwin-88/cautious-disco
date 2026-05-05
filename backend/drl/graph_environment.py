"""
Graph-grounded DRL environment.

Replaces the 10 hardcoded archetypes in EAEnvironment with capabilities
loaded live from Neo4j for a specific domain. Maintains the same
STATE_DIM=20 / ACTION_DIM=10 interface so REINFORCETrainer works unchanged.
"""

import numpy as np
from typing import NamedTuple

from backend.graph.cypher_queries import (
    GET_CAPABILITIES_FOR_TRAINING,
    GET_DOMAIN_RELATIONSHIP_FLAGS,
)


class EAScenario(NamedTuple):
    cap_business_values: np.ndarray
    cap_effort_scores: np.ndarray
    cap_risk_scores: np.ndarray
    dependency_matrix: np.ndarray
    budget_capacity: float
    timeline_score: float
    risk_tolerance: float


_COMPLEXITY_TO_BV = {"low": 0.95, "medium": 0.80, "high": 0.65, "very_high": 0.50}
_COMPLEXITY_TO_EFFORT = {"low": 0.30, "medium": 0.55, "high": 0.75, "very_high": 0.90}


def _build_bv_effort_risk(caps: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    bv, effort, risk = [], [], []
    for c in caps:
        cx = (c.get("complexity") or "medium").lower()
        bv.append(_COMPLEXITY_TO_BV.get(cx, 0.80))
        dur = c.get("duration_weeks") or 16
        effort.append(min(float(dur) / 36.0, 1.0))
        rf = c.get("risk_factors") or []
        risk.append(min(len(rf) / 5.0, 0.90))
    # pad to exactly 10
    while len(bv) < 10:
        bv.append(0.70); effort.append(0.50); risk.append(0.30)
    return (
        np.array(bv[:10], dtype=np.float32),
        np.array(effort[:10], dtype=np.float32),
        np.array(risk[:10], dtype=np.float32),
    )


class GraphEAEnvironment:
    """DRL environment grounded in real Neo4j domain capabilities."""

    STATE_DIM = 20
    ACTION_DIM = 10

    def __init__(self, neo4j_client, domain_name: str, noise_scale: float = 0.08, seed: int | None = None):
        self._client = neo4j_client
        self._domain_name = domain_name
        self._noise = noise_scale
        self._rng = np.random.default_rng(seed)

        caps = self._client.run_query(GET_CAPABILITIES_FOR_TRAINING, domain_name=domain_name)
        self._caps = caps or []
        self._cap_names = [c.get("name", f"Cap-{i}") for i, c in enumerate(self._caps)]

        self._base_bv, self._base_ef, self._base_ri = _build_bv_effort_risk(self._caps)

        # Domain relationship flags (7 dims)
        flags_rows = self._client.run_query(GET_DOMAIN_RELATIONSHIP_FLAGS, domain_name=domain_name)
        if flags_rows:
            f = flags_rows[0]
            self._domain_flags = np.array([
                float(f.get("is_sector_hub", False)),
                float(f.get("is_enabled", False)),
                float(f.get("is_orchestrator", False)),
                float(f.get("is_governed", False)),
                float(f.get("is_sector_child", False)),
                float(f.get("enables_others", False)),
                float(f.get("has_trend", False)),
            ], dtype=np.float32)
        else:
            self._domain_flags = np.zeros(7, dtype=np.float32)

        self.scenario: EAScenario | None = None
        self.current_step = 0

    # ------------------------------------------------------------------
    def reset(self) -> np.ndarray:
        noise = self._rng.uniform(-self._noise, self._noise, 10)
        bv = np.clip(self._base_bv + noise, 0.1, 1.0)
        ef = np.clip(self._base_ef + self._rng.uniform(-self._noise, self._noise, 10), 0.1, 1.0)
        ri = np.clip(self._base_ri + self._rng.uniform(-self._noise / 2, self._noise / 2, 10), 0.05, 0.9)

        dep_matrix = np.zeros((10, 10), dtype=np.float32)
        # Light dependency: later capabilities often depend on earlier ones
        for i in range(min(len(self._caps) - 1, 9)):
            if self._rng.random() > 0.7:
                dep_matrix[i, i + 1] = 1.0

        budget_capacity = float(self._rng.choice([0.4, 0.6, 0.8, 1.0]))
        timeline_score = float(self._rng.choice([6, 12, 18, 24, 36])) / 36.0
        risk_tolerance = float(self._rng.choice([0.33, 0.67, 1.0]))

        self.scenario = EAScenario(bv, ef, ri, dep_matrix, budget_capacity, timeline_score, risk_tolerance)
        self.current_step = 0
        return self._state_vector()

    def _state_vector(self) -> np.ndarray:
        s = self.scenario
        return np.concatenate([
            s.cap_business_values,
            [s.budget_capacity],
            [s.timeline_score],
            [s.risk_tolerance],
            self._domain_flags,
        ]).astype(np.float32)

    def step(self, action_indices: np.ndarray) -> tuple[np.ndarray, float, bool]:
        s = self.scenario
        base_reward = sum(
            s.cap_business_values[idx] * (1.0 - rank / len(action_indices))
            for rank, idx in enumerate(action_indices)
        ) / len(action_indices)

        dep_violations = sum(
            1 for i, di in enumerate(action_indices)
            for j, dj in enumerate(action_indices)
            if s.dependency_matrix[dj, di] == 1.0 and j < i
        )
        dep_penalty = dep_violations * 0.15

        cum_effort, budget_penalty = 0.0, 0.0
        for idx in action_indices:
            cum_effort += s.cap_effort_scores[idx] / 10.0
            if cum_effort > s.budget_capacity:
                budget_penalty += 0.05

        risk_penalty = sum(
            s.cap_risk_scores[idx] * 0.2
            for idx in action_indices[:3]
            if s.cap_risk_scores[idx] > s.risk_tolerance
        )

        reward = float(max(-1.0, min(2.0, base_reward - dep_penalty - budget_penalty - risk_penalty)))
        self.current_step += 1
        return self._state_vector(), reward, True

    def sample_action(self) -> np.ndarray:
        return self._rng.permutation(self.ACTION_DIM).astype(np.int64)

    def get_domain_name(self) -> str:
        return self._domain_name

    def get_capability_names(self) -> list[str]:
        return self._cap_names
