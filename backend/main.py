"""FastAPI application — startup lifecycle and router registration."""

import logging
import os
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.dependencies import set_neo4j_client, set_llm_client
from backend.graph.neo4j_client import Neo4jClient
from backend.llm.client import LLMClient

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # Neo4j
    client = Neo4jClient(
        uri=settings.neo4j_uri,
        username=settings.neo4j_username,
        password=settings.neo4j_password,
        database=settings.neo4j_database,
    )
    set_neo4j_client(client)
    ok = client.verify_connectivity()
    log.info(f"Neo4j connectivity: {'OK' if ok else 'FAILED'}")

    # LLM
    llm = LLMClient(settings=settings)
    set_llm_client(llm)

    # DRL checkpoint (pre-load so first request isn't slow)
    try:
        from backend.drl.trainer import load_trained_policy
        checkpoint = settings.drl_checkpoint_path
        if os.path.exists(checkpoint):
            policy = load_trained_policy(checkpoint)
            app.state.drl_policy = policy
            log.info(f"DRL policy loaded from {checkpoint}")
        else:
            app.state.drl_policy = None
            log.warning(f"DRL checkpoint not found at {checkpoint}; optimizer will use random priorities")
    except Exception as exc:
        log.warning(f"Could not load DRL policy: {exc}")
        app.state.drl_policy = None

    # GPU info
    if torch.cuda.is_available():
        log.info(f"GPU: {torch.cuda.get_device_name(0)}")
        if getattr(torch.version, "hip", None):
            log.info(f"AMD ROCm: {torch.version.hip}")
    else:
        log.info("No GPU detected — running on CPU")

    yield

    client.close()
    log.info("Neo4j driver closed")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AMD Enterprise Architecture Optimizer",
        description="Agentic EA roadmap generation powered by AMD MI300X + ROCm",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from backend.api.routes_health import router as health_router
    from backend.api.routes_graph import router as graph_router
    from backend.api.routes_analyze import router as analyze_router
    from backend.api.routes_training import router as training_router
    from backend.api.routes_chat import router as chat_router
    from backend.api.routes_integrations import router as integrations_router
    from backend.api.routes_uipath import router as uipath_router
    from backend.api.routes_bpmn import router as bpmn_router

    app.include_router(health_router, prefix="/api/v1", tags=["health"])
    app.include_router(graph_router, prefix="/api/v1", tags=["graph"])
    app.include_router(analyze_router, prefix="/api/v1", tags=["analyze"])
    app.include_router(training_router, prefix="/api/v1", tags=["training"])
    app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
    app.include_router(integrations_router, prefix="/api/v1", tags=["integrations"])
    app.include_router(uipath_router, prefix="/api/v1", tags=["uipath"])
    app.include_router(bpmn_router, prefix="/api/v1", tags=["bpmn"])

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8080, reload=True)
