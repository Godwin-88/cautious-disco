"""UiPath Maestro BPMN integration endpoints."""

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.dependencies import get_neo4j_client
from backend.graph.neo4j_client import Neo4jClient
from backend.schemas.response import AnalyzeResponse

log = logging.getLogger(__name__)
router = APIRouter()

TaskDecision = Literal["approve", "override", "reject", "escalate"]


class TaskCompleteRequest(BaseModel):
    task_id: str
    assessment_id: str
    decision: TaskDecision
    override_scores: dict[str, float] | None = None
    comment: str | None = None


class TaskCompleteResponse(BaseModel):
    task_id: str
    status: str
    message: str


class ProcessStatusResponse(BaseModel):
    assessment_id: str
    process_status: str
    current_step: str | None = None
    completed: bool = False


class GenerateReportRequest(BaseModel):
    assessment_id: str
    format: Literal["pdf", "json"] = "pdf"


@router.get("/uipath/tasks")
async def list_tasks(neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)]):
    rows = neo4j.run_query(
        "MATCH (ht:HumanTask) RETURN ht.task_id AS task_id, ht.assessment_id AS assessment_id, "
        "ht.title AS title, ht.description AS description, ht.priority AS priority, ht.due_date AS due_date "
        "ORDER BY ht.created_at DESC LIMIT 50"
    )
    return [
        {
            "task_id": r.get("task_id"),
            "assessment_id": r.get("assessment_id"),
            "title": r.get("title"),
            "description": r.get("description", ""),
            "priority": r.get("priority", "medium"),
            "due_date": r.get("due_date"),
        }
        for r in rows if r.get("task_id")
    ]


@router.get("/uipath/processes")
async def list_processes(neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)]):
    rows = neo4j.run_query(
        "MATCH (o:GeneratedOutput) RETURN o.cache_key AS id, o.org_type AS org_type, o.created_at AS created_at "
        "ORDER BY o.created_at DESC LIMIT 20"
    )
    return [
        {
            "name": f"Capability Assessment: {r.get('org_type', 'Unknown')}",
            "description": f"Assessment for {r.get('org_type', 'organisation')} capabilities",
            "status": "completed",
            "id": r.get("id"),
        }
        for r in rows if r.get("id")
    ]


@router.get("/uipath/assessment/{assessment_id}")
async def get_assessment(
    assessment_id: str,
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
):
    rows = neo4j.run_query(
        "MATCH (o:GeneratedOutput {cache_key: $assessment_id}) RETURN o.output_json AS output_json",
        assessment_id=assessment_id,
    )
    if not rows:
        return {"gap_analysis": [], "maturity_scores": {}, "drl_ranking": []}
    try:
        data = AnalyzeResponse.model_validate_json(rows[0]["output_json"])
        drl_ranking = [
            {"capability": cs.capability_name, "score": cs.score}
            for cs in (data.drl_trace.capability_scores if data.drl_trace else [])
        ]
        return {
            "gap_analysis": data.compliance_summary.issues if data.compliance_summary else [],
            "maturity_scores": {},
            "drl_ranking": drl_ranking,
            "roadmap": data.phases,
        }
    except Exception:
        return {"gap_analysis": [], "maturity_scores": {}, "drl_ranking": []}


@router.post("/uipath/task-complete", response_model=TaskCompleteResponse)
async def task_complete(
    request: TaskCompleteRequest,
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
):
    log.info(f"Task {request.task_id}: {request.decision} for assessment {request.assessment_id}")

    if request.decision == "override" and request.override_scores:
        log.info(f"Override scores: {request.override_scores}")

    return TaskCompleteResponse(
        task_id=request.task_id,
        status="processed",
        message=f"Task {request.task_id} {request.decision}d",
    )


@router.get("/uipath/process-status/{assessment_id}", response_model=ProcessStatusResponse)
async def process_status(
    assessment_id: str,
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
):
    rows = neo4j.run_query(
        "MATCH (o:GeneratedOutput {cache_key: $assessment_id}) RETURN o.created_at AS created_at",
        assessment_id=assessment_id,
    )
    exists = bool(rows)

    return ProcessStatusResponse(
        assessment_id=assessment_id,
        process_status="completed" if exists else "pending",
        completed=exists,
    )


@router.post("/uipath/generate-report", response_model=AnalyzeResponse)
async def generate_report(
    request: GenerateReportRequest,
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
):
    rows = neo4j.run_query(
        "MATCH (o:GeneratedOutput {cache_key: $cache_key}) RETURN o.output_json AS output_json",
        cache_key=request.assessment_id,
    )

    if rows and rows[0].get("output_json"):
        return AnalyzeResponse.model_validate_json(rows[0]["output_json"])

    raise HTTPException(status_code=404, detail="Assessment not found")