import asyncio
import logging
import time
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.config import Settings, get_settings
from backend.dependencies import get_neo4j_client, get_llm_client
from backend.graph.neo4j_client import Neo4jClient
from backend.llm.client import LLMClient
from backend.schemas.request import AnalyzeRequest
from backend.schemas.response import AnalyzeResponse, AMDMetrics

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
    llm: Annotated[LLMClient, Depends(get_llm_client)],
):
    from backend.agents.orchestrator import run_pipeline

    request_id = str(uuid.uuid4())
    t0 = time.time()
    log.info(f"[{request_id}] analyze request: org_type={request.org_type}")

    try:
        result = await run_pipeline(request, neo4j, llm, settings, request_id)
    except Exception as exc:
        log.exception(f"[{request_id}] pipeline failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    elapsed = time.time() - t0
    if result.amd_metrics:
        result.amd_metrics.processing_time_seconds = round(elapsed, 2)
    else:
        result.amd_metrics = AMDMetrics(processing_time_seconds=round(elapsed, 2))
    
    # Store assessment result
    try:
        output_json = result.model_dump_json()
        neo4j.run_query(
            """
            MERGE (a:Assessment {assessment_id: $assessment_id})
            SET a.org_name = $org_name,
                a.org_sector = $org_sector,
                a.org_type = $org_type,
                a.status = 'COMPLETE',
                a.compliance_score = $compliance_score,
                a.output_json = $output_json,
                a.created_at = datetime()
            """,
            assessment_id=request_id,
            org_name=request.org_type,
            org_sector=request.sector_focus[0] if request.sector_focus else "Unknown",
            org_type=request.org_type,
            compliance_score=result.compliance_summary.score if result.compliance_summary else 0,
            output_json=output_json,
        )
    except Exception as exc:
        log.warning(f"[{request_id}] Failed to store assessment: {exc}")
    
    return result

@router.get("/assessments")
async def list_assessments(
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
):
    rows = neo4j.run_query(
        """
        MATCH (a:Assessment)
        RETURN a.assessment_id AS assessment_id,
               a.org_name AS org_name,
               a.org_sector AS org_sector,
               a.status AS status,
               a.compliance_score AS compliance_score,
               toString(a.created_at) AS created_at
        ORDER BY a.created_at DESC
        LIMIT 50
        """
    )
    return rows
