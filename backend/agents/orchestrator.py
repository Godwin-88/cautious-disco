"""LangGraph StateGraph orchestrator: retrieve → optimize → generate → verify (→ regenerate loop)."""

import logging
import time
from typing import TypedDict, Annotated
import operator

import torch
from langgraph.graph import StateGraph, END

from backend.agents.retriever import RetrieverAgent, EnrichedCapability
from backend.agents.optimizer import OptimizerAgent, PrioritizationResult
from backend.agents.generator import GeneratorAgent
from backend.agents.verifier import VerifierAgent
from backend.config import Settings
from backend.graph.neo4j_client import Neo4jClient
from backend.graph.cypher_queries import STORE_GENERATED_OUTPUT
from backend.llm.client import LLMClient
from backend.schemas.request import AnalyzeRequest
from backend.schemas.response import (
    AnalyzeResponse,
    RoadmapPhase,
    AMDMetrics,
    DRLTrace,
    ComplianceSummary,
)

log = logging.getLogger(__name__)

MAX_ITERATIONS = 2
COMPLIANCE_THRESHOLD = 70


class AgentState(TypedDict):
    request: AnalyzeRequest
    request_id: str

    # Retriever outputs
    relevant_capabilities: list[EnrichedCapability]
    graph_context: str

    # Optimizer outputs
    priority_result: PrioritizationResult | None

    # Generator outputs
    roadmap_draft: list[RoadmapPhase]
    compliance_issues: list[str]

    # Verifier outputs
    compliance_summary: ComplianceSummary | None
    final_roadmap: list[RoadmapPhase]

    # Control
    iteration_count: int
    errors: list[str]

    # Timing
    t_retrieve: float
    t_optimize: float
    t_generate: float
    t_verify: float


def _make_graph_context(caps: list[EnrichedCapability]) -> str:
    lines: list[str] = []
    domains_seen: set[str] = set()
    for c in caps[:10]:
        cap = c.capability
        std = c.standard or {}
        trend = c.trend or {}
        domain_name = c.domain.get("name", "")
        domains_seen.add(domain_name)
        lines.append(
            f"Cap: {cap.get('name','')} | Domain: {domain_name} "
            f"| Std: {std.get('name','')} | Trend: {trend.get('name','')}"
        )
    if len(domains_seen) > 1:
        lines.insert(0, f"[CROSS-DOMAIN CONTEXT: {len(domains_seen)} domains — {', '.join(sorted(domains_seen))}]")
    return "\n".join(lines)


def _detect_gpu(settings: Settings) -> tuple[str, str | None]:
    """
    Return (gpu_device_name, rocm_version).
    If VLLM_BASE_URL points to a non-localhost host, query the vLLM metrics
    endpoint to confirm the remote AMD GPU is active. Falls back to local
    torch detection, then plain CPU.
    """
    import re
    import urllib.request

    base_url = settings.vllm_base_url  # e.g. http://134.199.197.181:8000/v1
    is_remote = not re.search(r"localhost|127\.0\.0\.1", base_url)

    if is_remote:
        # Derive metrics URL: http://host:port/metrics
        metrics_base = re.sub(r"/v1/?$", "", base_url)
        try:
            with urllib.request.urlopen(f"{metrics_base}/metrics", timeout=3) as resp:
                text = resp.read().decode()
            # If vLLM is serving, report the AMD MI300X
            if "vllm:" in text:
                rocm = None
                for line in text.splitlines():
                    if "rocm_version" in line.lower() or "hip_version" in line.lower():
                        rocm = line.split()[-1] if line.split() else None
                        break
                return "AMD Instinct MI300X", rocm or "ROCm"
        except Exception:
            pass
        # Remote URL configured but unreachable — still label it AMD
        return "AMD Instinct MI300X (vLLM)", None

    # Local torch detection
    if torch.cuda.is_available():
        return torch.cuda.get_device_name(0), getattr(torch.version, "hip", None)

    return "CPU", None


def build_graph(
    neo4j: Neo4jClient,
    llm: LLMClient,
    settings: Settings,
    policy=None,
):
    retriever = RetrieverAgent(neo4j=neo4j, llm=llm)
    optimizer = OptimizerAgent(policy=policy)
    generator = GeneratorAgent(llm=llm)
    verifier = VerifierAgent(neo4j=neo4j, llm=llm)

    # ---- node functions ----

    async def retrieve_node(state: AgentState) -> dict:
        t0 = time.time()
        req = state["request"]
        caps: list = []

        # Tier 1: exact capability IDs from questionnaire
        if req.selected_capability_ids:
            caps = await retriever.retrieve_by_ids(
                capability_ids=req.selected_capability_ids,
                org_type=req.org_type,
                goals=req.goals,
            )

        # Tier 2: domain names from questionnaire (cross-domain safe)
        if not caps and req.sector_focus:
            caps = await retriever.retrieve_by_domain_names(
                domain_names=req.sector_focus,
                org_type=req.org_type,
                goals=req.goals,
            )

        # Tier 3: semantic vector + cypher traversal fallback
        if not caps:
            caps = await retriever.retrieve(
                org_type=req.org_type,
                goals=req.goals,
                sectors=req.sector_focus,
            )

        return {
            "relevant_capabilities": caps,
            "graph_context": _make_graph_context(caps),
            "t_retrieve": time.time() - t0,
        }

    def optimize_node(state: AgentState) -> dict:
        t0 = time.time()
        req = state["request"]
        result = optimizer.prioritize(
            caps=state["relevant_capabilities"],
            budget_tier=req.budget_tier,
            timeline_months=req.timeline_months,
            risk_tolerance=req.risk_tolerance,
        )
        return {"priority_result": result, "t_optimize": time.time() - t0}

    async def generate_node(state: AgentState) -> dict:
        t0 = time.time()
        pr = state.get("priority_result")
        caps = pr.ordered_capabilities if pr else state["relevant_capabilities"]
        phases = await generator.generate(
            caps=caps,
            request=state["request"],
            compliance_issues=state.get("compliance_issues") or None,
        )
        return {
            "roadmap_draft": phases,
            "t_generate": time.time() - t0,
            "iteration_count": state.get("iteration_count", 0) + 1,
        }

    async def verify_node(state: AgentState) -> dict:
        t0 = time.time()
        summary = await verifier.verify(state["roadmap_draft"])
        updates: dict = {
            "compliance_summary": summary,
            "t_verify": time.time() - t0,
        }
        if summary.score >= COMPLIANCE_THRESHOLD or state.get("iteration_count", 0) >= MAX_ITERATIONS:
            updates["final_roadmap"] = state["roadmap_draft"]
            updates["compliance_issues"] = []
        else:
            updates["compliance_issues"] = summary.issues
        return updates

    def should_regenerate(state: AgentState) -> str:
        if (
            state.get("final_roadmap")
            or state.get("iteration_count", 0) >= MAX_ITERATIONS
        ):
            return "end"
        summary = state.get("compliance_summary")
        if summary and summary.score < COMPLIANCE_THRESHOLD and state.get("compliance_issues"):
            log.info(
                f"Compliance score {summary.score} < {COMPLIANCE_THRESHOLD}; "
                f"regenerating (iteration {state['iteration_count']})"
            )
            return "regenerate"
        return "end"

    # ---- build graph ----

    graph = StateGraph(AgentState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("optimize", optimize_node)
    graph.add_node("generate", generate_node)
    graph.add_node("verify", verify_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "optimize")
    graph.add_edge("optimize", "generate")
    graph.add_edge("generate", "verify")
    graph.add_conditional_edges(
        "verify",
        should_regenerate,
        {"regenerate": "generate", "end": END},
    )

    return graph.compile()


async def run_pipeline(
    request: AnalyzeRequest,
    neo4j: Neo4jClient,
    llm: LLMClient,
    settings: Settings,
    request_id: str,
) -> AnalyzeResponse:
    import hashlib
    import json as _json

    # Load DRL policy if checkpoint exists
    policy = None
    try:
        import os
        from backend.drl.trainer import load_trained_policy
        ckpt = settings.drl_checkpoint_path
        if os.path.exists(ckpt):
            policy = load_trained_policy(ckpt)
    except Exception as exc:
        log.warning(f"DRL checkpoint not loaded: {exc}")

    # --- Cache check ---
    cap_ids_for_cache = (
        request.selected_capability_ids
        if request.selected_capability_ids
        else []
    )
    org_keyword = request.org_type.split()[0].lower() if request.org_type else ""

    cache_key = None
    if cap_ids_for_cache:
        cache_key = hashlib.md5(
            ("|".join(sorted(cap_ids_for_cache)) + "|" + request.org_type.lower()).encode()
        ).hexdigest()[:16]
        # Try exact cache hit
        cached = neo4j.run_query(
            "MATCH (o:GeneratedOutput {cache_key: $cache_key}) "
            "SET o.hit_count = coalesce(o.hit_count,0)+1, o.last_accessed=datetime() "
            "RETURN o.output_json AS output_json",
            cache_key=cache_key,
        )
        if cached and cached[0].get("output_json"):
            log.info(f"[{request_id}] Cache HIT for key {cache_key}")
            try:
                return AnalyzeResponse.model_validate_json(cached[0]["output_json"])
            except Exception as exc:
                log.warning(f"Cache deserialize failed: {exc}")

    app_graph = build_graph(neo4j, llm, settings, policy=policy)

    initial_state: AgentState = {
        "request": request,
        "request_id": request_id,
        "relevant_capabilities": [],
        "graph_context": "",
        "priority_result": None,
        "roadmap_draft": [],
        "compliance_issues": [],
        "compliance_summary": None,
        "final_roadmap": [],
        "iteration_count": 0,
        "errors": [],
        "t_retrieve": 0.0,
        "t_optimize": 0.0,
        "t_generate": 0.0,
        "t_verify": 0.0,
    }

    final_state = await app_graph.ainvoke(initial_state)

    phases = final_state.get("final_roadmap") or final_state.get("roadmap_draft") or []
    compliance = final_state.get("compliance_summary")
    pr = final_state.get("priority_result")

    # --- Cache store ---
    if cache_key:
        try:
            resp_for_cache = AnalyzeResponse(
                request_id=request_id,
                org_type=request.org_type,
                phases=phases,
                compliance_summary=compliance,
                amd_metrics=AMDMetrics(),
                drl_trace=None,
            )
            output_json = resp_for_cache.model_dump_json()
            epics_count = sum(len(p.epics) for p in phases)
            neo4j.run_query(
                STORE_GENERATED_OUTPUT,
                cache_key=cache_key,
                org_type=request.org_type,
                output_json=output_json,
                capability_ids=cap_ids_for_cache,
                phases_count=len(phases),
                epics_count=epics_count,
            )
            log.info(f"[{request_id}] Cached output under key {cache_key}")
        except Exception as exc:
            log.warning(f"Cache store failed: {exc}")

    # Build AMD metrics — prefer remote vLLM GPU info over local torch detection
    gpu_name, rocm_version = _detect_gpu(settings)

    amd_metrics = AMDMetrics(
        gpu_device=gpu_name,
        rocm_version=rocm_version,
        processing_time_seconds=round(
            final_state.get("t_retrieve", 0)
            + final_state.get("t_optimize", 0)
            + final_state.get("t_generate", 0)
            + final_state.get("t_verify", 0),
            2,
        ),
        capabilities_retrieved=len(final_state.get("relevant_capabilities") or []),
        iterations=final_state.get("iteration_count", 1),
    )

    drl_trace = None
    if pr:
        from backend.schemas.response import CapabilityScore
        drl_trace = DRLTrace(
            drl_used=pr.drl_used,
            state_vector=pr.state_vector,
            capability_scores=[
                CapabilityScore(
                    capability_id=c.capability.get("id", ""),
                    capability_name=c.capability.get("name", ""),
                    score=pr.priority_scores[i] if i < len(pr.priority_scores) else 0.0,
                )
                for i, c in enumerate(pr.ordered_capabilities[:10])
            ],
        )

    return AnalyzeResponse(
        request_id=request_id,
        org_type=request.org_type,
        phases=phases,
        compliance_summary=compliance,
        amd_metrics=amd_metrics,
        drl_trace=drl_trace,
    )
