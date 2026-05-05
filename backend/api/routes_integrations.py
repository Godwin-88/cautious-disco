"""Integration endpoints — Jira export (live), ITSM mock, ERP CSV ingest, ArchiMate layer view."""

import csv
import io
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from backend.dependencies import get_neo4j_client
from backend.graph.neo4j_client import Neo4jClient
from backend.graph.cypher_queries import GET_ARCHIMATE_CAPABILITIES

log = logging.getLogger(__name__)
router = APIRouter()


# ── Jira Export ──────────────────────────────────────────────────────────────

class JiraExportRequest(BaseModel):
    jira_url: str
    jira_email: str
    jira_api_token: str
    project_key: str
    phases: list[dict]


@router.post("/integrations/jira/export")
async def jira_export(req: JiraExportRequest):
    import httpx
    base = req.jira_url.rstrip("/")
    auth = (req.jira_email, req.jira_api_token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    created_epics = 0
    created_stories = 0
    errors = []
    first_epic_key = None

    async with httpx.AsyncClient(auth=auth, headers=headers, timeout=30) as client:
        for phase in req.phases:
            for epic in (phase.get("epics") or []):
                # Create Epic
                epic_payload = {
                    "fields": {
                        "project": {"key": req.project_key},
                        "summary": epic.get("title") or epic.get("epic_id") or "EA Epic",
                        "description": {
                            "type": "doc", "version": 1,
                            "content": [{"type": "paragraph", "content": [
                                {"type": "text", "text": epic.get("description") or ""}
                            ]}]
                        },
                        "issuetype": {"name": "Epic"},
                        "labels": ["EA-Optimizer", f"Phase-{phase.get('phase_number',1)}"],
                    }
                }
                try:
                    resp = await client.post(f"{base}/rest/api/3/issue", json=epic_payload)
                    if resp.status_code in (200, 201):
                        epic_key = resp.json().get("key", "")
                        if not first_epic_key:
                            first_epic_key = epic_key
                        created_epics += 1
                        # Create Stories (features → user stories)
                        for feat in (epic.get("features") or []):
                            for story in (feat.get("user_stories") or []):
                                role = story.get("role", "user")
                                want = story.get("want", "")
                                so_that = story.get("so_that", "")
                                acs = story.get("acceptance_criteria") or []
                                ac_text = "\n".join(f"- {a}" for a in acs)
                                story_payload = {
                                    "fields": {
                                        "project": {"key": req.project_key},
                                        "summary": f"As a {role}, I want {want}"[:255],
                                        "description": {
                                            "type": "doc", "version": 1,
                                            "content": [{"type": "paragraph", "content": [
                                                {"type": "text",
                                                 "text": f"So that {so_that}\n\nAcceptance Criteria:\n{ac_text}"}
                                            ]}]
                                        },
                                        "issuetype": {"name": "Story"},
                                        "labels": ["EA-Optimizer"],
                                    }
                                }
                                try:
                                    sr = await client.post(f"{base}/rest/api/3/issue", json=story_payload)
                                    if sr.status_code in (200, 201):
                                        created_stories += 1
                                    else:
                                        errors.append(f"Story: {sr.text[:100]}")
                                except Exception as e:
                                    errors.append(f"Story error: {e}")
                    else:
                        errors.append(f"Epic {epic.get('title','')}: {resp.text[:120]}")
                except Exception as e:
                    errors.append(f"Epic error: {e}")

    browse_url = f"{base}/projects/{req.project_key}" if created_epics else None
    return {
        "created_epics": created_epics,
        "created_stories": created_stories,
        "jira_url": browse_url,
        "errors": errors[:5],
    }


# ── ITSM Mock ────────────────────────────────────────────────────────────────

class ITSMConnectRequest(BaseModel):
    tool: str   # "servicenow" | "azure_devops"
    instance_url: str
    credentials: dict = {}


@router.post("/integrations/itsm/connect")
async def itsm_connect(req: ITSMConnectRequest):
    if req.tool == "servicenow":
        return {
            "status": "connected",
            "tool": "ServiceNow",
            "instance": req.instance_url,
            "sample_work_items": [
                {"type": "change_request", "count": 12, "action": "would create"},
                {"type": "incident", "count": 1204, "action": "would link"},
                {"type": "problem", "count": 34, "action": "would associate"},
            ],
            "message": "ServiceNow ITSM connection validated. EA roadmap items would be synced as Change Requests.",
        }
    elif req.tool == "azure_devops":
        return {
            "status": "connected",
            "tool": "Azure DevOps",
            "instance": req.instance_url,
            "sample_work_items": [
                {"type": "Epic", "count": 6, "action": "would create"},
                {"type": "Feature", "count": 18, "action": "would create"},
                {"type": "User Story", "count": 36, "action": "would create"},
            ],
            "message": "Azure DevOps connection validated. EA initiatives would be pushed as Epics and Features.",
        }
    return {"status": "unsupported", "tool": req.tool}


# ── ERP / CRM CSV Ingest ─────────────────────────────────────────────────────

@router.post("/integrations/erp/ingest")
async def erp_ingest(
    file: UploadFile = File(...),
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)] = None,
):
    content = await file.read()
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    rows_ingested = 0
    systems_found = set()
    capabilities_linked = 0
    errors = []

    for row in reader:
        system_name = (row.get("system_name") or row.get("System Name") or "").strip()
        vendor = (row.get("vendor") or row.get("Vendor") or "").strip()
        business_unit = (row.get("business_unit") or row.get("Business Unit") or "").strip()
        cap_raw = (row.get("capabilities_in_use") or row.get("Capabilities") or "").strip()
        budget = (row.get("annual_budget_usd") or row.get("Budget") or "0").strip()

        if not system_name:
            continue

        systems_found.add(system_name)
        cap_names = [c.strip() for c in cap_raw.split(";") if c.strip()] if cap_raw else []

        try:
            neo4j.run_query(
                """
                MERGE (es:ExternalSystem {name: $name})
                SET es.vendor = $vendor,
                    es.business_unit = $business_unit,
                    es.annual_budget_usd = $budget,
                    es.ingested_at = datetime()
                """,
                name=system_name, vendor=vendor,
                business_unit=business_unit, budget=budget,
            )
            rows_ingested += 1

            for cap_name in cap_names:
                result = neo4j.run_query(
                    """
                    MATCH (c:Capability)
                    WHERE toLower(c.name) CONTAINS toLower($cap_name)
                    WITH c LIMIT 1
                    MATCH (es:ExternalSystem {name: $sys_name})
                    MERGE (es)-[:SUPPORTS]->(c)
                    RETURN c.name AS linked
                    """,
                    cap_name=cap_name, sys_name=system_name,
                )
                if result:
                    capabilities_linked += 1
        except Exception as exc:
            errors.append(str(exc)[:80])

    return {
        "rows_ingested": rows_ingested,
        "systems_found": len(systems_found),
        "capabilities_linked": capabilities_linked,
        "errors": errors[:3],
    }


# ── ArchiMate Layer Classification ───────────────────────────────────────────

_BUSINESS_KEYWORDS = {
    "governance", "compliance", "policy", "management", "service", "process",
    "strategy", "operating", "organisation", "reporting", "risk", "audit",
    "procurement", "finance", "hr", "legal", "contract",
}
_TECHNOLOGY_KEYWORDS = {
    "infrastructure", "cloud", "network", "server", "hardware", "storage",
    "devops", "ci/cd", "kubernetes", "container", "monitoring", "observability",
    "security", "firewall", "vpn", "iam", "identity", "access",
}


def _classify_layer(cap: dict) -> str:
    name_lower = (cap.get("name") or "").lower()
    desc_lower = (cap.get("description") or "").lower()
    outcomes = " ".join(cap.get("business_outcomes") or []).lower()
    frameworks = " ".join(cap.get("frameworks") or []).lower()
    tech_reqs = " ".join(cap.get("technical_requirements") or []).lower()
    combined = f"{name_lower} {desc_lower} {frameworks} {tech_reqs}"

    # Technology layer check first
    if any(kw in combined for kw in _TECHNOLOGY_KEYWORDS):
        return "technology"
    # Business layer
    if any(kw in combined for kw in _BUSINESS_KEYWORDS) or outcomes:
        return "business"
    # Default: application layer
    return "application"


@router.get("/integrations/archimate")
async def archimate_view(
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
):
    rows = neo4j.run_query(GET_ARCHIMATE_CAPABILITIES)
    result: dict[str, list] = {"business": [], "application": [], "technology": []}

    for r in rows:
        layer = _classify_layer(r)
        result[layer].append({
            "id": r.get("id"),
            "name": r.get("name"),
            "domain": r.get("domain_name"),
            "subdomain": r.get("subdomain_name"),
            "complexity": r.get("complexity"),
            "business_outcomes": (r.get("business_outcomes") or [])[:2],
        })

    return result
