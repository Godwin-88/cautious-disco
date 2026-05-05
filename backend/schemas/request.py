"""Pydantic v2 request models."""

from typing import Literal
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    org_type: str = Field(..., description="Organisation type / domain focus (e.g. 'Healthcare Provider', 'Banking')")
    goals: list[str] = Field(..., min_length=1, description="Business transformation goals")
    budget_tier: Literal["low", "medium", "high"] = Field(default="medium")
    timeline_months: int = Field(default=18, ge=6, le=36)
    risk_tolerance: Literal["low", "medium", "high"] = Field(default="medium")
    sector_focus: list[str] = Field(default_factory=list, description="Optional additional domain filters")
    current_capabilities: list[str] = Field(default_factory=list, description="Capability IDs already in place")
    selected_capability_ids: list[str] = Field(default_factory=list, description="Direct capability IDs from questionnaire — bypasses vector search")
    selected_subdomain_ids: list[str] = Field(default_factory=list, description="Direct subdomain IDs from questionnaire")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "org_type": "Banking",
                    "goals": [
                        "Modernise data management and establish data mesh",
                        "Launch open banking APIs for PSD2 compliance",
                        "Improve real-time fraud detection"
                    ],
                    "budget_tier": "high",
                    "timeline_months": 24,
                    "risk_tolerance": "medium",
                    "sector_focus": ["Digital Intelligence", "Security"],
                    "current_capabilities": [],
                }
            ]
        }
    }
