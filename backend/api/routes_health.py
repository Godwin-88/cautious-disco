from datetime import datetime
from typing import Annotated

import torch
from fastapi import APIRouter, Depends

from backend.config import Settings, get_settings
from backend.dependencies import get_neo4j_client
from backend.graph.neo4j_client import Neo4jClient

router = APIRouter()


@router.get("/health")
async def health(
    settings: Annotated[Settings, Depends(get_settings)],
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
):
    neo4j_ok = neo4j.verify_connectivity()

    gpu_info: dict = {"available": False}
    if torch.cuda.is_available():
        gpu_info = {
            "available": True,
            "device": torch.cuda.get_device_name(0),
            "rocm": getattr(torch.version, "hip", None),
        }

    return {
        "status": "ok" if neo4j_ok else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "neo4j": "connected" if neo4j_ok else "unreachable",
        "gpu": gpu_info,
        "embedding_model": settings.embedding_model,
        "llm_model": settings.vllm_model,
    }
