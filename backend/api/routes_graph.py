from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.dependencies import get_neo4j_client
from backend.graph.neo4j_client import Neo4jClient
from backend.graph.cypher_queries import (
    GET_ALL_DOMAINS,
    GET_CAPABILITIES_FOR_DOMAIN,
    GET_DOMAIN_STATS,
)

router = APIRouter()


@router.get("/domains")
async def list_domains(neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)]):
    rows = neo4j.run_query(GET_ALL_DOMAINS)
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "capability_count": r.get("capability_count", 0),
        }
        for r in rows
    ]


@router.get("/capabilities")
async def list_capabilities(
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
    domain_id: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
):
    rows = neo4j.run_query(GET_CAPABILITIES_FOR_DOMAIN, domain_id=domain_id, limit=limit)
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "domain": r.get("domain_name"),
            "subdomain": r.get("subdomain_name"),
            "description": r.get("description"),
        }
        for r in rows
    ]


@router.get("/stats")
async def graph_stats(neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)]):
    rows = neo4j.run_query(GET_DOMAIN_STATS)
    return {"node_counts": {r["label"]: r["count"] for r in rows}}


@router.get("/graph/network")
async def graph_network(neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)]):
    from backend.graph.cypher_queries import GET_NETWORK_GRAPH
    rows = neo4j.run_query(GET_NETWORK_GRAPH)
    if not rows:
        return {"nodes": [], "edges": []}
    row = rows[0]
    return {
        "nodes": row.get("nodes") or [],
        "edges": [e for e in (row.get("edges") or []) if e],
    }


@router.get("/subdomains")
async def list_subdomains(
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
    domain_names: list[str] = Query(default=[]),
):
    from backend.graph.cypher_queries import GET_SUBDOMAINS_FOR_DOMAINS
    rows = neo4j.run_query(GET_SUBDOMAINS_FOR_DOMAINS, domain_names=domain_names)
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "domain_name": r.get("domain_name", ""),
            "functional_scope": r.get("functional_scope", ""),
        }
        for r in rows
    ]


@router.get("/subdomain-capabilities")
async def list_subdomain_capabilities(
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
    subdomain_ids: list[str] = Query(default=[]),
):
    from backend.graph.cypher_queries import GET_CAPABILITIES_FOR_SUBDOMAINS
    rows = neo4j.run_query(GET_CAPABILITIES_FOR_SUBDOMAINS, subdomain_ids=subdomain_ids)
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "subdomain": r.get("subdomain_name", ""),
            "subdomain_id": r.get("subdomain_id", ""),
            "description": r.get("description", ""),
            "complexity": r.get("complexity", ""),
            "duration_weeks": r.get("duration_weeks"),
        }
        for r in rows
    ]
