"""
EA Digital Twin Simulation Environment for DRL training.

State: 10 capability scores + 3 budget/timeline/risk scalars + 7 domain flags = 20 dims
Action: priority ordering of top-10 capabilities (multinomial sampling)
Reward: business value - dependency violations - budget overrun - risk penalty
"""

import numpy as np
import random
from typing import NamedTuple


class EAScenario(NamedTuple):
    cap_business_values: np.ndarray    # shape (10,) — 0..1
    cap_effort_scores: np.ndarray      # shape (10,) — 0..1
    cap_risk_scores: np.ndarray        # shape (10,) — 0..1
    dependency_matrix: np.ndarray      # shape (10, 10) — dep_matrix[i,j]=1 means i must precede j
    budget_capacity: float             # 0..1 normalised
    timeline_score: float              # months/36
    risk_tolerance: float              # 0..1


# 10 EA capability archetypes (represent real patterns in the graph)
ARCHETYPE_NAMES = [
    "Data Platform",
    "API Management",
    "Customer Portal",
    "Advanced Analytics",
    "Security & Compliance",
    "Process Automation",
    "Cloud Migration",
    "AI/ML Platform",
    "ERP Integration",
    "DevOps Pipeline",
]

# Base business values per archetype (will be perturbed per episode)
BASE_BUSINESS_VALUES = np.array([0.90, 0.80, 0.70, 0.85, 0.95, 0.75, 0.70, 0.80, 0.65, 0.70])
BASE_EFFORT_SCORES = np.array([0.80, 0.50, 0.60, 0.70, 0.60, 0.65, 0.90, 0.85, 0.75, 0.50])
BASE_RISK_SCORES = np.array([0.40, 0.30, 0.30, 0.35, 0.20, 0.40, 0.60, 0.50, 0.55, 0.25])

# Dependency rules: prerequisite → dependent (indices)
BASE_DEPENDENCIES = [
    (0, 1),  # Data Platform → API Management
    (1, 2),  # API Management → Customer Portal
    (0, 3),  # Data Platform → Analytics
    (1, 5),  # API Management → Process Automation
    (6, 7),  # Cloud Migration → AI/ML Platform
    (0, 7),  # Data Platform → AI/ML Platform
]


class EAEnvironment:
    """Simulated Enterprise Architecture environment for REINFORCE training."""

    STATE_DIM = 20
    ACTION_DIM = 10

    def __init__(self, noise_scale: float = 0.1, seed: int | None = None):
        self._rng = np.random.default_rng(seed)
        self._noise = noise_scale
        self.scenario: EAScenario | None = None
        self.current_step = 0

    def reset(self) -> np.ndarray:
        """Generate a new randomised EA scenario and return initial state vector."""
        noise = self._rng.uniform(-self._noise, self._noise, size=10)
        bv = np.clip(BASE_BUSINESS_VALUES + noise, 0.1, 1.0)
        ef = np.clip(BASE_EFFORT_SCORES + self._rng.uniform(-self._noise, self._noise, 10), 0.1, 1.0)
        ri = np.clip(BASE_RISK_SCORES + self._rng.uniform(-self._noise / 2, self._noise / 2, 10), 0.05, 0.9)

        # Randomise dep matrix from base
        dep_matrix = np.zeros((10, 10), dtype=float)
        for (i, j) in BASE_DEPENDENCIES:
            if self._rng.random() > 0.2:  # 80% chance to include each dependency
                dep_matrix[i, j] = 1.0

        budget_capacity = float(self._rng.choice([0.4, 0.6, 0.8, 1.0]))
        timeline_score = float(self._rng.choice([6, 12, 18, 24, 36])) / 36.0
        risk_tolerance = float(self._rng.choice([0.33, 0.67, 1.0]))

        self.scenario = EAScenario(bv, ef, ri, dep_matrix, budget_capacity, timeline_score, risk_tolerance)
        self.current_step = 0
        return self.get_state_vector()

    def get_state_vector(self) -> np.ndarray:
        """Build 20-dim state vector from current scenario."""
        s = self.scenario
        # 7 domain flags — simulate which of 7 EA domain categories are in this scenario
        domain_flags = (s.cap_business_values[:7] > 0.6).astype(float)
        state = np.concatenate([
            s.cap_business_values,        # 10 dims
            [s.budget_capacity],          # 1
            [s.timeline_score],           # 1
            [s.risk_tolerance],           # 1
            domain_flags,                 # 7
        ]).astype(np.float32)
        return state

    def step(self, action_indices: np.ndarray) -> tuple[np.ndarray, float, bool]:
        """
        action_indices: ordered priority list of capability indices (len=10)
        Returns (next_state, reward, done)
        """
        s = self.scenario

        # Base reward: value-weighted rank score
        base_reward = 0.0
        for rank, idx in enumerate(action_indices):
            rank_fraction = rank / len(action_indices)
            base_reward += s.cap_business_values[idx] * (1.0 - rank_fraction)
        base_reward /= len(action_indices)  # normalise to 0..1

        # Dependency penalty
        dep_violations = 0
        for i, dep_i in enumerate(action_indices):
            for j, dep_j in enumerate(action_indices):
                if s.dependency_matrix[dep_j, dep_i] == 1.0 and j < i:
                    dep_violations += 1
        dep_penalty = dep_violations * 0.15

        # Budget penalty — cumulative effort of top-N capped by budget
        cum_effort = 0.0
        budget_penalty = 0.0
        for idx in action_indices:
            cum_effort += s.cap_effort_scores[idx] / 10.0
            if cum_effort > s.budget_capacity:
                budget_penalty += 0.05

        # Risk penalty — high-risk caps in top-3 positions
        risk_penalty = 0.0
        for idx in action_indices[:3]:
            if s.cap_risk_scores[idx] > s.risk_tolerance:
                risk_penalty += s.cap_risk_scores[idx] * 0.2

        reward = float(base_reward - dep_penalty - budget_penalty - risk_penalty)
        reward = max(-1.0, min(2.0, reward))

        self.current_step += 1
        done = True  # single-step environment (one full ordering per episode)
        next_state = self.get_state_vector()
        return next_state, reward, done

    def sample_action(self) -> np.ndarray:
        """Random action for baseline / exploration."""
        return self._rng.permutation(self.ACTION_DIM).astype(np.int64)
