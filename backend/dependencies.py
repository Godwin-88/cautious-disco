"""FastAPI dependency injection — provides shared clients to route handlers."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from backend.config import Settings, get_settings
from backend.graph.neo4j_client import Neo4jClient
from backend.llm.client import LLMClient


_neo4j_client: Neo4jClient | None = None
_llm_client: LLMClient | None = None


def get_neo4j_client(settings: Annotated[Settings, Depends(get_settings)]) -> Neo4jClient:
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient(
            uri=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        )
    return _neo4j_client


def get_llm_client(settings: Annotated[Settings, Depends(get_settings)]) -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(settings=settings)
    return _llm_client


def set_neo4j_client(client: Neo4jClient) -> None:
    global _neo4j_client
    _neo4j_client = client


def set_llm_client(client: LLMClient) -> None:
    global _llm_client
    _llm_client = client
