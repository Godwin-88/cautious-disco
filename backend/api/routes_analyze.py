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
    return result
