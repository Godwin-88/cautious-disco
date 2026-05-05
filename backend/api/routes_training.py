"""Training metrics and control endpoints."""

import asyncio
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.dependencies import get_neo4j_client
from backend.graph.neo4j_client import Neo4jClient
from backend.graph.cypher_queries import GET_TRAINING_METRICS, GET_ENRICHMENT_COVERAGE

log = logging.getLogger(__name__)
router = APIRouter()

_training_tasks: dict[str, str] = {}  # run_id → status


class TrainingRequest(BaseModel):
    episodes_per_domain: int = 50
    domain: str | None = None


@router.get("/training/metrics")
async def training_metrics(neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)]):
    rows = neo4j.run_query(GET_TRAINING_METRICS)
    return [
        {
            "run_id": r.get("run_id"),
            "domain_name": r.get("domain_name"),
            "sector": r.get("sector"),
            "episodes": r.get("episodes"),
            "final_reward": r.get("final_reward"),
            "avg_reward_last10": r.get("avg_reward_last10"),
            "device": r.get("device"),
            "policy_version": r.get("policy_version"),
            "ts": r.get("ts"),
        }
        for r in rows
    ]


@router.get("/training/coverage")
async def training_coverage(neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)]):
    rows = neo4j.run_query(GET_ENRICHMENT_COVERAGE)
    return [
        {
            "domain": r.get("domain"),
            "has_standard": bool(r.get("has_standard")),
            "standard_enriched": bool(r.get("standard_enriched")),
            "has_trend": bool(r.get("has_trend")),
            "trend_enriched": bool(r.get("trend_enriched")),
            "drl_trained": bool(r.get("drl_trained")),
            "drl_reward": r.get("drl_reward"),
            "drl_last_trained": r.get("drl_last_trained"),
        }
        for r in rows
    ]


@router.post("/training/run")
async def trigger_training(
    request: TrainingRequest,
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
):
    run_id = uuid.uuid4().hex[:12]
    _training_tasks[run_id] = "started"

    async def _run():
        try:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            from neo4j import GraphDatabase
            from pipeline.train_on_graph import GraphTrainer, _NeoJClientAdapter

            uri = os.getenv("NEO4J_URI")
            username = os.getenv("NEO4J_USERNAME")
            password = os.getenv("NEO4J_PASSWORD")
            database = os.getenv("NEO4J_DATABASE", "neo4j")
            driver = GraphDatabase.driver(uri, auth=(username, password))
            try:
                trainer = GraphTrainer(driver, database)
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: trainer.run(
                        episodes_per_domain=request.episodes_per_domain,
                        target_domain=request.domain,
                    ),
                )
                _training_tasks[run_id] = f"completed:{result['domains_trained']} domains"
                log.info(f"Background training {run_id} complete: {result}")
            finally:
                driver.close()
        except Exception as exc:
            _training_tasks[run_id] = f"error:{exc}"
            log.exception(f"Background training {run_id} failed")

    asyncio.create_task(_run())
    return {
        "status": "started",
        "run_id": run_id,
        "message": f"Training {request.episodes_per_domain} eps/domain"
                   + (f" on '{request.domain}'" if request.domain else " across all domains")
                   + ". Metrics appear in Neo4j as each domain completes.",
    }


@router.get("/training/status/{run_id}")
async def training_status(run_id: str):
    status = _training_tasks.get(run_id)
    if status is None:
        raise HTTPException(status_code=404, detail="run_id not found")
    return {"run_id": run_id, "status": status}
