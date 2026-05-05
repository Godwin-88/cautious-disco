"""
Comprehensive graph cache pre-seeding pipeline.

Generates and stores roadmap outputs for a wide matrix of:
  - Organisation types (investment banks, hospitals, utilities, PE firms, etc.)
  - Domain combinations (all 44 domains, cross-domain pairings)

Results are stored as :GeneratedOutput nodes in Neo4j, so future users
with similar selections get instant cached responses — no LLM re-generation.

Run on the AMD MI300X machine for GPU-accelerated LLM inference.

Usage:
  python -m pipeline.seed_graph_cache                    # full matrix
  python -m pipeline.seed_graph_cache --org "Investment Bank"  # single org type
  python -m pipeline.seed_graph_cache --domains "Aviation,Capital Markets"
  python -m pipeline.seed_graph_cache --episodes 200     # DRL episodes per domain
  python -m pipeline.seed_graph_cache --skip-training    # only seed LLM cache
  python -m pipeline.seed_graph_cache --skip-cache       # only run DRL training
"""

import argparse
import asyncio
import hashlib
import json
import logging
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

from neo4j import GraphDatabase

from backend.config import Settings
from backend.graph.neo4j_client import Neo4jClient
from backend.llm.client import LLMClient
from backend.schemas.request import AnalyzeRequest
from backend.schemas.response import AnalyzeResponse, AMDMetrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Org type matrix — wide coverage of realistic user types
# ---------------------------------------------------------------------------

ORG_MATRIX = [
    # Financial Services
    {
        "org_type": "Commercial Bank",
        "goals": ["Implement open banking APIs", "Achieve PSD2 compliance", "Modernise core banking platform"],
        "budget_tier": "high", "timeline_months": 24, "risk_tolerance": "medium",
        "domain_keywords": ["Retail Banking", "Capital Markets", "Financial"],
    },
    {
        "org_type": "Investment Bank",
        "goals": ["Build real-time trading analytics", "Achieve MiFID II compliance", "Deploy AI risk models"],
        "budget_tier": "high", "timeline_months": 24, "risk_tolerance": "medium",
        "domain_keywords": ["Capital Markets", "Investment", "Financial Regulation"],
    },
    {
        "org_type": "Private Equity Firm",
        "goals": ["Portfolio company digital transformation", "ESG reporting framework", "Operational efficiency analytics"],
        "budget_tier": "medium", "timeline_months": 18, "risk_tolerance": "medium",
        "domain_keywords": ["Capital Markets", "Professional Services", "Aviation", "Property"],
    },
    {
        "org_type": "Insurance Company",
        "goals": ["Implement InsurTech platform", "Deploy AI-driven underwriting", "Achieve Solvency II compliance"],
        "budget_tier": "high", "timeline_months": 30, "risk_tolerance": "low",
        "domain_keywords": ["Financial Services", "Digital Intelligence"],
    },
    {
        "org_type": "Central Bank",
        "goals": ["Launch CBDC infrastructure", "Enhance financial stability monitoring", "Modernise payment systems"],
        "budget_tier": "high", "timeline_months": 36, "risk_tolerance": "low",
        "domain_keywords": ["Capital Markets", "Financial Regulation", "Government"],
    },
    # Healthcare & Life Sciences
    {
        "org_type": "Healthcare Provider",
        "goals": ["Improve patient data interoperability", "Achieve HIPAA compliance", "Deploy AI diagnostics"],
        "budget_tier": "medium", "timeline_months": 18, "risk_tolerance": "low",
        "domain_keywords": ["Healthcare Provider", "Digital Health"],
    },
    {
        "org_type": "Pharmaceutical Company",
        "goals": ["Accelerate clinical trial data management", "Achieve GxP compliance", "Deploy AI drug discovery"],
        "budget_tier": "high", "timeline_months": 30, "risk_tolerance": "low",
        "domain_keywords": ["Pharmaceutical", "Healthcare Provider"],
    },
    {
        "org_type": "Healthcare Payer",
        "goals": ["Claims processing automation", "Member digital experience", "Value-based care analytics"],
        "budget_tier": "high", "timeline_months": 24, "risk_tolerance": "medium",
        "domain_keywords": ["Healthcare Payer", "Digital Intelligence"],
    },
    {
        "org_type": "Public Health Agency",
        "goals": ["Disease surveillance platform", "Population health analytics", "Interoperability with providers"],
        "budget_tier": "medium", "timeline_months": 24, "risk_tolerance": "low",
        "domain_keywords": ["Health Regulatory", "Government"],
    },
    # Government & Public Sector
    {
        "org_type": "National Government Agency",
        "goals": ["Digital citizen services", "Achieve e-government standards", "Data sovereignty framework"],
        "budget_tier": "high", "timeline_months": 36, "risk_tolerance": "low",
        "domain_keywords": ["Government Excellence", "Court", "Urban Planning"],
    },
    {
        "org_type": "Municipal Government",
        "goals": ["Smart city IoT platform", "Open data initiative", "Digital service delivery"],
        "budget_tier": "medium", "timeline_months": 24, "risk_tolerance": "medium",
        "domain_keywords": ["Urban Planning", "Government"],
    },
    # Energy & Utilities
    {
        "org_type": "Energy Utility",
        "goals": ["Deploy smart grid IoT", "Achieve carbon reporting compliance", "Modernise OT/IT convergence"],
        "budget_tier": "high", "timeline_months": 30, "risk_tolerance": "medium",
        "domain_keywords": ["Clean Energy", "Electricity Transmission"],
    },
    {
        "org_type": "Oil & Gas Company",
        "goals": ["Digital twin for refineries", "Predictive maintenance AI", "ESG emissions tracking"],
        "budget_tier": "high", "timeline_months": 30, "risk_tolerance": "medium",
        "domain_keywords": ["Oil & Gas", "Logistics"],
    },
    # Telecommunications
    {
        "org_type": "Telecommunications Provider",
        "goals": ["5G network slicing", "Customer experience AI", "Achieve GDPR compliance"],
        "budget_tier": "high", "timeline_months": 24, "risk_tolerance": "medium",
        "domain_keywords": ["Telecommunications"],
    },
    # Logistics & Transport
    {
        "org_type": "Logistics Company",
        "goals": ["Supply chain visibility platform", "Last-mile delivery optimisation", "Carbon footprint tracking"],
        "budget_tier": "medium", "timeline_months": 18, "risk_tolerance": "medium",
        "domain_keywords": ["Logistics", "Food Supply"],
    },
    {
        "org_type": "Airport Authority",
        "goals": ["Passenger experience digitalisation", "Smart operations centre", "Cybersecurity framework"],
        "budget_tier": "high", "timeline_months": 30, "risk_tolerance": "low",
        "domain_keywords": ["Airport", "Digital Security"],
    },
    # Retail & Consumer
    {
        "org_type": "Retail Bank",
        "goals": ["Omnichannel digital banking", "AI-powered personalisation", "Open banking ecosystem"],
        "budget_tier": "medium", "timeline_months": 18, "risk_tolerance": "medium",
        "domain_keywords": ["Retail Banking"],
    },
    # Professional Services
    {
        "org_type": "Management Consulting Firm",
        "goals": ["Knowledge management platform", "AI-augmented advisory", "Digital delivery excellence"],
        "budget_tier": "medium", "timeline_months": 12, "risk_tolerance": "high",
        "domain_keywords": ["Professional Services", "Digital Intelligence"],
    },
    # Education
    {
        "org_type": "University",
        "goals": ["Digital learning platform", "Research data management", "Student experience personalisation"],
        "budget_tier": "low", "timeline_months": 24, "risk_tolerance": "medium",
        "domain_keywords": ["Digital Academy"],
    },
    # Property & Real Estate
    {
        "org_type": "Property Developer",
        "goals": ["Smart building IoT platform", "PropTech tenant experience", "ESG-compliant portfolio management"],
        "budget_tier": "medium", "timeline_months": 18, "risk_tolerance": "medium",
        "domain_keywords": ["Property Development"],
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_neo4j(settings: Settings):
    return GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )


def _neo4j_client(settings: Settings) -> Neo4jClient:
    return Neo4jClient(
        uri=settings.neo4j_uri,
        username=settings.neo4j_username,
        password=settings.neo4j_password,
        database=settings.neo4j_database,
    )


def _llm_client(settings: Settings) -> LLMClient:
    return LLMClient(settings=settings)


def _get_domain_caps_for_keywords(neo4j: Neo4jClient, keywords: list[str]) -> list[str]:
    """Return capability IDs for domains whose names contain any of the keywords."""
    results = []
    for kw in keywords:
        rows = neo4j.run_query(
            """
            MATCH (d:Domain)-[:PARENT_OF]->(sd:SubDomain)-[:PARENT_OF]->(c:Capability)
            WHERE toLower(d.name) CONTAINS toLower($kw) AND d.id <> '__hub__'
            RETURN c.id AS id LIMIT 30
            """,
            kw=kw,
        )
        results.extend(r["id"] for r in rows if r.get("id"))
    seen = set()
    return [x for x in results if not (x in seen or seen.add(x))]


def _cache_key(cap_ids: list[str], org_type: str) -> str:
    return hashlib.md5(
        ("|".join(sorted(cap_ids)) + "|" + org_type.lower()).encode()
    ).hexdigest()[:16]


def _already_cached(neo4j: Neo4jClient, key: str) -> bool:
    rows = neo4j.run_query(
        "MATCH (o:GeneratedOutput {cache_key: $k}) RETURN o.cache_key AS k LIMIT 1",
        k=key,
    )
    return bool(rows)


def _store_cache(neo4j: Neo4jClient, key: str, org_type: str,
                 cap_ids: list[str], response: AnalyzeResponse):
    from backend.graph.cypher_queries import STORE_GENERATED_OUTPUT
    resp_slim = AnalyzeResponse(
        request_id=response.request_id,
        org_type=response.org_type,
        phases=response.phases,
        compliance_summary=response.compliance_summary,
        amd_metrics=AMDMetrics(),
        drl_trace=None,
    )
    neo4j.run_query(
        STORE_GENERATED_OUTPUT,
        cache_key=key,
        org_type=org_type,
        output_json=resp_slim.model_dump_json(),
        capability_ids=cap_ids,
        phases_count=len(response.phases),
        epics_count=sum(len(p.epics) for p in response.phases),
    )


# ---------------------------------------------------------------------------
# DRL training (all 44 domains, high episode count)
# ---------------------------------------------------------------------------

def run_drl_training(neo4j_driver, database: str, episodes: int):
    from pipeline.train_on_graph import GraphTrainer
    log.info(f"=== Starting DRL training: {episodes} episodes per domain ===")
    trainer = GraphTrainer(neo4j_driver=neo4j_driver, database=database)
    trainer.run(episodes_per_domain=episodes)
    log.info("=== DRL training complete ===")


# ---------------------------------------------------------------------------
# Cache seeding — LLM pipeline for each org × domain combination
# ---------------------------------------------------------------------------

async def seed_cache_for_org(
    org_config: dict,
    neo4j: Neo4jClient,
    llm: LLMClient,
    settings: Settings,
) -> dict:
    from backend.agents.orchestrator import run_pipeline

    org_type = org_config["org_type"]
    goals = org_config["goals"]
    budget_tier = org_config["budget_tier"]
    timeline_months = org_config["timeline_months"]
    risk_tolerance = org_config["risk_tolerance"]
    domain_keywords = org_config.get("domain_keywords", [])

    cap_ids = _get_domain_caps_for_keywords(neo4j, domain_keywords)
    if not cap_ids:
        log.warning(f"  No capabilities found for {org_type} keywords {domain_keywords} — skipping")
        return {"org_type": org_type, "status": "skipped", "reason": "no_caps"}

    key = _cache_key(cap_ids, org_type)
    if _already_cached(neo4j, key):
        log.info(f"  [{org_type}] Cache HIT — already stored, skipping generation")
        return {"org_type": org_type, "status": "cached_existing", "caps": len(cap_ids)}

    request = AnalyzeRequest(
        org_type=org_type,
        goals=goals,
        budget_tier=budget_tier,
        timeline_months=timeline_months,
        risk_tolerance=risk_tolerance,
        sector_focus=domain_keywords,
        selected_capability_ids=cap_ids,
    )

    t0 = time.time()
    log.info(f"  [{org_type}] Generating roadmap for {len(cap_ids)} capabilities...")
    try:
        request_id = str(uuid.uuid4())
        result = await run_pipeline(request, neo4j, llm, settings, request_id)
        elapsed = round(time.time() - t0, 1)
        phases = len(result.phases)
        epics = sum(len(p.epics) for p in result.phases)
        features = sum(len(e.features) for p in result.phases for e in p.epics)
        stories = sum(len(f.user_stories) for p in result.phases for e in p.epics for f in e.features)
        tasks = sum(len(s.tasks) for p in result.phases for e in p.epics for f in e.features for s in f.user_stories)
        log.info(
            f"  [{org_type}] Generated in {elapsed}s — "
            f"{phases} phases, {epics} epics, {features} features, {stories} stories, {tasks} tasks"
        )
        # Store in graph cache
        _store_cache(neo4j, key, org_type, cap_ids, result)
        log.info(f"  [{org_type}] Cached under key {key}")
        return {
            "org_type": org_type, "status": "seeded",
            "caps": len(cap_ids), "phases": phases, "epics": epics,
            "features": features, "stories": stories, "tasks": tasks,
            "elapsed_s": elapsed,
        }
    except Exception as exc:
        log.error(f"  [{org_type}] FAILED: {exc}")
        return {"org_type": org_type, "status": "error", "error": str(exc)}


async def run_cache_seeding(
    neo4j: Neo4jClient,
    llm: LLMClient,
    settings: Settings,
    filter_org: str | None = None,
    filter_domains: list[str] | None = None,
):
    log.info("=== Starting cache seeding ===")
    matrix = ORG_MATRIX

    if filter_org:
        matrix = [o for o in matrix if filter_org.lower() in o["org_type"].lower()]
        if not matrix:
            log.warning(f"No org match for '{filter_org}' — running all")
            matrix = ORG_MATRIX

    if filter_domains:
        for org in matrix:
            org["domain_keywords"] = filter_domains

    results = []
    for i, org_config in enumerate(matrix):
        log.info(f"\n[{i+1}/{len(matrix)}] Seeding: {org_config['org_type']}")
        r = await seed_cache_for_org(org_config, neo4j, llm, settings)
        results.append(r)
        # Brief pause to avoid overwhelming vLLM
        await asyncio.sleep(2)

    # Summary
    seeded = [r for r in results if r["status"] == "seeded"]
    existing = [r for r in results if r["status"] == "cached_existing"]
    errors = [r for r in results if r["status"] == "error"]
    skipped = [r for r in results if r["status"] == "skipped"]

    log.info("\n" + "=" * 60)
    log.info(f"CACHE SEEDING COMPLETE")
    log.info(f"  Newly generated : {len(seeded)}")
    log.info(f"  Already cached  : {len(existing)}")
    log.info(f"  Errors          : {len(errors)}")
    log.info(f"  Skipped (no caps): {len(skipped)}")
    if seeded:
        total_epics = sum(r.get("epics", 0) for r in seeded)
        total_features = sum(r.get("features", 0) for r in seeded)
        total_stories = sum(r.get("stories", 0) for r in seeded)
        total_tasks = sum(r.get("tasks", 0) for r in seeded)
        log.info(f"  Total epics     : {total_epics}")
        log.info(f"  Total features  : {total_features}")
        log.info(f"  Total stories   : {total_stories}")
        log.info(f"  Total tasks     : {total_tasks}")
    if errors:
        for e in errors:
            log.info(f"  ERROR — {e['org_type']}: {e.get('error', '')}")
    log.info("=" * 60)
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Seed Neo4j graph with DRL training + LLM output cache")
    parser.add_argument("--episodes", type=int, default=200,
                        help="DRL training episodes per domain (default 200)")
    parser.add_argument("--org", type=str, default=None,
                        help="Filter to a single org type, e.g. 'Investment Bank'")
    parser.add_argument("--domains", type=str, default=None,
                        help="Comma-separated domain keywords override, e.g. 'Aviation,Capital Markets'")
    parser.add_argument("--skip-training", action="store_true",
                        help="Skip DRL training, only seed LLM output cache")
    parser.add_argument("--skip-cache", action="store_true",
                        help="Skip LLM cache seeding, only run DRL training")
    args = parser.parse_args()

    settings = Settings()
    neo4j_client = _neo4j_client(settings)
    llm = _llm_client(settings)

    filter_domains = [d.strip() for d in args.domains.split(",")] if args.domains else None

    # Step 1: DRL training on all 44 domains
    if not args.skip_training:
        driver = _make_neo4j(settings)
        try:
            run_drl_training(driver, settings.neo4j_database, episodes=args.episodes)
        finally:
            driver.close()
    else:
        log.info("Skipping DRL training (--skip-training)")

    # Step 2: Seed LLM output cache for all org types
    if not args.skip_cache:
        asyncio.run(run_cache_seeding(
            neo4j=neo4j_client,
            llm=llm,
            settings=settings,
            filter_org=args.org,
            filter_domains=filter_domains,
        ))
    else:
        log.info("Skipping cache seeding (--skip-cache)")


if __name__ == "__main__":
    main()
