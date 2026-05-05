"""Pydantic v2 response models."""

from typing import Optional
from pydantic import BaseModel, Field


class AMDMetrics(BaseModel):
    gpu_device: str = "CPU"
    rocm_version: Optional[str] = None
    processing_time_seconds: float = 0.0
    capabilities_retrieved: int = 0
    iterations: int = 1
    tokens_per_second: float = 0.0
    total_tokens_generated: int = 0


class CapabilityScore(BaseModel):
    capability_id: str
    capability_name: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)


class DRLTrace(BaseModel):
    drl_used: bool = False
    state_vector: list[float] = Field(default_factory=list)
    capability_scores: list[CapabilityScore] = Field(default_factory=list)


class Task(BaseModel):
    title: str
    description: str = ""
    estimated_days: int = 3
    assignee_role: str = ""


class UserStory(BaseModel):
    role: str
    want: str
    so_that: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)


class Feature(BaseModel):
    title: str
    description: str = ""
    technical_notes: str = ""
    user_stories: list[UserStory] = Field(default_factory=list)
    estimated_story_points: Optional[int] = None


class EpicArtifact(BaseModel):
    epic_id: str
    title: str
    subdomain_group: str = ""
    description: str = ""
    business_value: str = ""
    strategic_rationale: str = ""
    governance_reference: str = ""
    trend_alignment: str = ""
    risk_register: list[str] = Field(default_factory=list)
    estimated_sprints: int = 4
    features: list[Feature] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    phase: int = 1


class RoadmapPhase(BaseModel):
    phase_number: int
    phase_name: str
    duration_months: int
    epics: list[EpicArtifact] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    key_milestones: list[str] = Field(default_factory=list)


class ComplianceSummary(BaseModel):
    score: int = Field(default=0, ge=0, le=100)
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    standards_covered: list[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    request_id: str
    org_type: str
    phases: list[RoadmapPhase] = Field(default_factory=list)
    compliance_summary: Optional[ComplianceSummary] = None
    amd_metrics: Optional[AMDMetrics] = None
    drl_trace: Optional[DRLTrace] = None
