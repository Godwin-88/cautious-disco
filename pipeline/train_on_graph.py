"""
Full-graph DRL training pipeline.

Trains the EA policy across every domain in Neo4j, writes TrainingRun
nodes back to the graph, and stamps each Domain with drl_trained status.

Usage:
  python -m pipeline.train_on_graph                         # all 44 domains, 50 eps each
  python -m pipeline.train_on_graph --episodes 20           # faster run
  python -m pipeline.train_on_graph --domain "Healthcare Provider" --episodes 100
"""

import argparse
import json
import logging
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

import numpy as np
from neo4j import GraphDatabase

from backend.drl.graph_environment import GraphEAEnvironment
from backend.drl.policy_network import EAPolicyNetwork, get_device
from backend.drl.trainer import REINFORCETrainer
from backend.graph.cypher_queries import (
    UPSERT_TRAINING_RUN,
    SET_DOMAIN_TRAINING_STATUS,
)
from pipeline.enrich_graph_v2 import (
    get_standard_for_domain,
    get_trends_for_domain,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), "..", "backend", "drl", "checkpoints")
CHECKPOINT_PATH = os.path.join(CHECKPOINT_DIR, "ea_policy_v2_graph.pt")
POLICY_VERSION = "v2_graph"

# Sector inference from domain name
_SECTOR_KEYWORDS = [
    (["retail banking", "bank"], "Retail Banking"),
    (["healthcare provider", "hospital", "clinic"], "Healthcare Provider"),
    (["pharmaceutical", "pharma"], "Pharmaceutical"),
    (["food supply", "food"], "Food Supply"),
    (["oil & gas", "o&g", "petroleum"], "Oil & Gas"),
    (["telco", "telecommunications"], "Telecommunications"),
    (["logistics"], "Logistics"),
    (["clean energy", "electricity transmission", "energy"], "Clean Energy"),
    (["government excellence", "court", "justice", "urban planning", "government"], "Government"),
    (["capital markets", "investment", "stock exchange", "endowment", "development banking"], "Capital Markets"),
    (["health regulatory", "health system", "healthcare payer", "cdc"], "Health"),
    (["professional services"], "Professional Services"),
    (["digital academy", "academy"], "Education"),
    (["airport"], "Aviation"),
    (["property development"], "Property"),
    (["digital financial regulation"], "Financial Regulation"),
    (["digital intelligence"], "Cross-Cutting"),
    (["digital it"], "Cross-Cutting"),
    (["inter-operability", "interoperability", "automation"], "Cross-Cutting"),
    (["digital security", "security"], "Cross-Cutting"),
    (["experience orchestration"], "Cross-Cutting"),
    (["service orchestration"], "Cross-Cutting"),
    (["marcom"], "Cross-Cutting"),
    (["backoffice"], "Cross-Cutting"),
    (["gprc"], "Cross-Cutting"),
    (["workspace"], "Cross-Cutting"),
    (["generic core"], "Cross-Cutting"),
]


def _infer_sector(domain_name: str) -> str:
    name_lower = domain_name.lower()
    for keywords, sector in _SECTOR_KEYWORDS:
        if any(kw in name_lower for kw in keywords):
            return sector
    return "Other"


class GraphTrainer:
    def __init__(self, neo4j_driver, database: str = "neo4j"):
        self._driver = neo4j_driver
        self._database = database
        self._device = get_device()
        os.makedirs(CHECKPOINT_DIR, exist_ok=True)

    def _run(self, cypher: str, **params):
        with self._driver.session(database=self._database) as s:
            return s.run(cypher, **params).data()

    def _all_domains(self) -> list[dict]:
        return self._run(
            "MATCH (d:Domain) WHERE d.id <> '__hub__' "
            "RETURN d.id AS id, d.name AS name ORDER BY d.name"
        )

    def _ensure_enrichment(self, domain_name: str):
        """Ensure Standard and Trend nodes are enriched for this domain."""
        rows = self._run("""
MATCH (d:Domain {name: $name})
OPTIONAL MATCH (d)-[:GOVERNED_BY]->(std:Standard)
OPTIONAL MATCH (d)-[:INFLUENCED_BY]->(trend:Trend)
RETURN std.id AS std_id, std.compliance_requirements AS std_reqs,
       trend.id AS trend_id, trend.business_impact AS trend_impact
""", name=domain_name)
        if not rows:
            return
        r = rows[0]

        # Enrich standard if missing compliance_requirements
        if r.get("std_id") and not r.get("std_reqs"):
            std_data = get_standard_for_domain(domain_name)
            self._run("""
MATCH (n:Standard {id: $id})
SET n.name = $name, n.publisher = $publisher, n.version = $version,
    n.key_principles = $kp, n.compliance_requirements = $cr,
    n.source_url = $url, n.tags = $tags, n.domain_name = $dn
""",
                id=r["std_id"],
                name=std_data.get("name", ""),
                publisher=std_data.get("publisher", ""),
                version=str(std_data.get("version", "")),
                kp=std_data.get("key_principles") or [],
                cr=std_data.get("compliance_requirements") or [],
                url=std_data.get("source_url", ""),
                tags=std_data.get("tags") or [],
                dn=domain_name,
            )
            log.info(f"    Enriched standard for {domain_name}: {std_data['name']}")

        # Enrich trend if missing business_impact
        if r.get("trend_id") and not r.get("trend_impact"):
            trends = get_trends_for_domain(domain_name)
            t = trends[0]
            self._run("""
MATCH (n:Trend {id: $id})
SET n.name = $name, n.source = $source, n.source_type = $st,
    n.publication_year = $yr, n.impact_level = $il, n.maturity = $m,
    n.time_horizon = $th, n.business_impact = $bi,
    n.technology_enablers = $te, n.adoption_rate = $ar, n.domain_name = $dn
""",
                id=r["trend_id"],
                name=t.get("name", ""),
                source=t.get("source", ""),
                st=t.get("source_type", "industry_analyst"),
                yr=t.get("publication_year", 2025),
                il=t.get("impact_level", "high"),
                m=t.get("maturity", "growing"),
                th=t.get("time_horizon", "1-2yr"),
                bi=t.get("business_impact", ""),
                te=t.get("technology_enablers") or [],
                ar=t.get("adoption_rate", ""),
                dn=domain_name,
            )
            log.info(f"    Enriched trend for {domain_name}: {t['name']}")

    def _write_training_run(self, domain_name: str, run_id: str, training_log: list[dict]):
        rewards = [e["reward"] for e in training_log]
        final_reward = rewards[-1] if rewards else 0.0
        avg_last10 = float(np.mean(rewards[-10:])) if rewards else 0.0

        props = {
            "domain_name": domain_name,
            "sector": _infer_sector(domain_name),
            "episodes": len(training_log),
            "final_reward": round(final_reward, 4),
            "avg_reward_last10": round(avg_last10, 4),
            "device": str(self._device),
            "policy_version": POLICY_VERSION,
            "episode_log": json.dumps(training_log[-5:]),  # last 5 eps for debug
        }
        self._run(UPSERT_TRAINING_RUN, run_id=run_id, props=props)

    def _stamp_domain(self, domain_name: str, final_reward: float):
        self._run(
            SET_DOMAIN_TRAINING_STATUS,
            domain_name=domain_name,
            final_reward=round(final_reward, 4),
            policy_version=POLICY_VERSION,
        )

    def run(
        self,
        episodes_per_domain: int = 50,
        target_domain: str | None = None,
    ) -> dict:
        domains = self._all_domains()
        if target_domain:
            domains = [d for d in domains if target_domain.lower() in d["name"].lower()]
            if not domains:
                raise ValueError(f"Domain not found: {target_domain}")

        log.info(f"=== Graph DRL Training ===")
        log.info(f"Device: {self._device} | Domains: {len(domains)} | Episodes/domain: {episodes_per_domain}")

        # Shared policy — trained continuously across all domains
        policy = EAPolicyNetwork().to(self._device)

        # Load existing v2 checkpoint if available
        if os.path.exists(CHECKPOINT_PATH):
            import torch
            ckpt = torch.load(CHECKPOINT_PATH, map_location=self._device)
            policy.load_state_dict(ckpt["policy_state_dict"])
            log.info(f"Resumed from {CHECKPOINT_PATH}")

        session_id = uuid.uuid4().hex[:8]
        results = []
        t_session = time.time()

        for i, domain in enumerate(domains, 1):
            domain_name = domain["name"]
            log.info(f"\n[{i}/{len(domains)}] {domain_name}")

            # Ensure graph enrichment is complete before training
            self._ensure_enrichment(domain_name)

            # Build graph-grounded env
            try:
                env = GraphEAEnvironment(
                    neo4j_client=_NeoJClientAdapter(self._driver, self._database),
                    domain_name=domain_name,
                )
            except Exception as exc:
                log.warning(f"  Could not build env for {domain_name}: {exc} — skipping")
                continue

            cap_count = len([c for c in env._caps])
            if cap_count == 0:
                log.warning(f"  No capabilities found for {domain_name} — skipping")
                continue
            log.info(f"  Capabilities: {cap_count} | Sector: {_infer_sector(domain_name)}")

            # Train
            trainer = REINFORCETrainer(policy=policy, env=env, device=self._device)
            training_log = trainer.train(n_episodes=episodes_per_domain)

            # Write to graph
            run_id = f"{session_id}_{i:03d}"
            self._write_training_run(domain_name, run_id, training_log)
            rewards = [e["reward"] for e in training_log]
            self._stamp_domain(domain_name, rewards[-1] if rewards else 0.0)

            final_r = round(rewards[-1] if rewards else 0.0, 4)
            avg_r = round(float(np.mean(rewards[-10:])), 4)
            log.info(f"  Done — final_reward={final_r}  avg10={avg_r}  run_id={run_id}")
            results.append({"domain": domain_name, "final_reward": final_r, "run_id": run_id})

            # Save checkpoint after each domain
            trainer.save_checkpoint(CHECKPOINT_PATH)

        elapsed = time.time() - t_session
        log.info(f"\n=== Training complete: {len(results)}/{len(domains)} domains in {elapsed:.1f}s ===")

        # Save summary log
        summary_path = CHECKPOINT_PATH.replace(".pt", "_summary.json")
        with open(summary_path, "w") as f:
            json.dump({"session_id": session_id, "domains": results, "elapsed_s": round(elapsed, 1)}, f, indent=2)
        log.info(f"Summary → {summary_path}")

        return {"session_id": session_id, "domains_trained": len(results), "elapsed_s": round(elapsed, 1)}


class _NeoJClientAdapter:
    """Adapts neo4j Driver to the run_query() interface GraphEAEnvironment expects."""
    def __init__(self, driver, database: str):
        self._driver = driver
        self._database = database

    def run_query(self, cypher: str, **params) -> list[dict]:
        with self._driver.session(database=self._database) as s:
            return s.run(cypher, **params).data()


def main():
    parser = argparse.ArgumentParser(description="Full-graph DRL training")
    parser.add_argument("--episodes", type=int, default=50, help="Episodes per domain")
    parser.add_argument("--domain", type=str, default=None, help="Train only this domain (substring match)")
    args = parser.parse_args()

    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")

    driver = GraphDatabase.driver(uri, auth=(username, password))
    try:
        trainer = GraphTrainer(driver, database)
        result = trainer.run(episodes_per_domain=args.episodes, target_domain=args.domain)
        print(f"\nResult: {result}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
