"""BPMN generation endpoint — converts roadmap to BPMN 2.0 XML using ENABLES dependency graph."""

import logging
import uuid
from typing import Annotated
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_neo4j_client
from backend.graph.neo4j_client import Neo4jClient
from backend.graph.cypher_queries import GET_ENABLES_GRAPH

log = logging.getLogger(__name__)
router = APIRouter()


class PhasesRequest(BaseModel):
    phases: list[dict] = []


class BpmnModelCreate(BaseModel):
    name: str = Field(..., min_length=1)
    bpmn_xml: str
    assessment_id: str | None = None


class BpmnModelUpdate(BaseModel):
    bpmn_xml: str


def _generate_bpmn_xml(
    phases: list[dict],
    enables_edges: list[dict],
) -> str:
    """Generate BPMN 2.0 XML from roadmap phases and ENABLES edges."""
    tasks: list[dict] = []
    domains_seen = set()
    
    for phase in phases:
        for epic in phase.get("epics", []):
            domain = epic.get("domain") or epic.get("domain_name", "Unknown")
            domains_seen.add(domain)
            for feat in epic.get("features", []):
                for story in feat.get("user_stories", []):
                    tasks.append({
                        "name": story.get("want", epic.get("title", "Task"))[:50],
                        "domain": domain,
                        "phase": phase.get("phase_number", 1),
                        "priority": epic.get("priority_rank", 1),
                    })
    
    # Build adjacency list from ENABLES edges for ordering
    domain_order = {e["source"]: e["target"] for e in enables_edges}
    
    # Sort tasks by domain centrality (universal enablers first)
    centrality_hubs = {"Manage Digital IT", "Manage Digital Security", "Manage Digital Intelligence"}
    
    def domain_rank(domain: str) -> int:
        if domain in centrality_hubs:
            return 0
        if domain in domain_order:
            return 1
        return 2
    
    tasks.sort(key=lambda t: (domain_rank(t["domain"]), t["priority"]))
    
    # Generate BPMN XML
    bpmn_id = "bpmn_diagram"
    plane_id = f"{bpmn_id}_plane"
    
    # Build lanes (one per domain)
    lanes_xml = ""
    for domain in sorted(domains_seen, key=lambda d: domain_rank(d)):
        lanes_xml += f'''
      <bpmn:laneSet id="lane_set_{domain.replace(" ", "_")}">
        <bpmn:lane id="lane_{domain.replace(" ", "_").lower()}" name="{domain}">
          <bpmn:flowNodeRef>task_{domain.replace(" ", "_").lower()}</bpmn:flowNodeRef>
        </bpmn:lane>
      </bpmn:laneSet>'''
    
    # Build tasks and sequence flows
    tasks_xml = ""
    flows_xml = ""
    task_idx = 0
    
    for task in tasks[:50]:
        task_id = f"task_{task_idx}"
        safe_name = task["name"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        tasks_xml += f'''
      <bpmn:serviceTask id="{task_id}" name="{safe_name}">
        <bpmn:documentation>{safe_name}</bpmn:documentation>
      </bpmn:serviceTask>'''
        if task_idx > 0:
            flows_xml += f'''
      <bpmn:sequenceFlow id="flow_{task_idx}" sourceRef="task_{task_idx-1}" targetRef="{task_id}" />'''
        task_idx += 1
    
    # Add ENABLES edges as labeled flows
    enables_xml = ""
    for edge in enables_edges[:30]:
        safe_source = edge["source"].replace(" ", "_")
        safe_target = edge["target"].replace(" ", "_")
        enables_xml += f'''
      <bpmn:sequenceFlow id="enables_{safe_source}_{safe_target}" sourceRef="lane_{safe_source.lower()}" targetRef="lane_{safe_target.lower()}" label="enables" />'''
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="{bpmn_id}" isExecutable="true">
    <bpmn:startEvent id="start" />
{lanes_xml}
{tasks_xml}
{flows_xml}
    <bpmn:endEvent id="end" />
    <bpmn:sequenceFlow id="start_to_first" sourceRef="start" targetRef="task_0" />
    <bpmn:sequenceFlow id="last_to_end" sourceRef="task_{max(0, task_idx-1)}" targetRef="end" />
{enables_xml}
  </bpmn:process>
  <bpmndi:BPMNDiagram id="{plane_id}">
    <bpmndi:BPMNPlane id="plane_{bpmn_id}" bpmnElement="{bpmn_id}" />
  </bpmndi:BPMNDiagram>
</bpmn:definitions>'''


@router.post("/bpmn/generate")
async def bpmn_generate(
    req: PhasesRequest,
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
):
    """Generate BPMN XML from roadmap phases."""
    try:
        enables_rows = neo4j.run_query(GET_ENABLES_GRAPH)
        enables_edges = [{"source": r["source"], "target": r["target"]} for r in enables_rows]
        
        bpmn_xml = _generate_bpmn_xml(req.phases, enables_edges)
        return {"bpmn_xml": bpmn_xml}
    except Exception as exc:
        log.exception("BPMN generation failed")
        raise HTTPException(status_code=500, detail=str(exc))


class BpmnGenerateFromAssessment(BaseModel):
    assessment_id: str


@router.post("/bpmn/generate-from-assessment")
async def bpmn_generate_from_assessment(
    payload: BpmnGenerateFromAssessment,
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
):
    """Generate BPMN XML for a specific assessment."""
    try:
        result = neo4j.run_query(
            "MATCH (o:GeneratedOutput {assessment_id: $assessment_id}) RETURN o.output_json AS output_json",
            assessment_id=payload.assessment_id,
        )
        if not result:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        output = result[0].get("output_json")
        import json
        data = json.loads(output) if isinstance(output, str) else output
        phases = data.get("phases", [])
        
        enables_rows = neo4j.run_query(GET_ENABLES_GRAPH)
        enables_edges = [{"source": r["source"], "target": r["target"]} for r in enables_rows]
        
        bpmn_xml = _generate_bpmn_xml(phases, enables_edges)
        return {"bpmn_xml": bpmn_xml, "assessment_id": payload.assessment_id}
    except HTTPException:
        raise
    except Exception as exc:
        log.exception("BPMN generation from assessment failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# BPMN Model CRUD operations
# ---------------------------------------------------------------------------

@router.get("/bpmn/models")
async def list_bpmn_models(neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)]):
    """List all saved BPMN models."""
    rows = neo4j.run_query(
        "MATCH (m:BpmnModel) "
        "RETURN m.id AS id, m.name AS name, m.bpmn_xml AS bpmn_xml, "
        "toString(m.created_at) AS created_at, toString(m.updated_at) AS updated_at, "
        "m.assessment_id AS assessment_id "
        "ORDER BY m.updated_at DESC LIMIT 50"
    )
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "bpmn_xml": r["bpmn_xml"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "assessment_id": r.get("assessment_id"),
        }
        for r in rows
    ]


@router.post("/bpmn/models")
async def create_bpmn_model(
    payload: BpmnModelCreate,
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
):
    """Create a new BPMN model."""
    model_id = str(uuid.uuid4())[:8]
    neo4j.run_query(
        "CREATE (m:BpmnModel {id: $id, name: $name, bpmn_xml: $bpmn_xml, "
        "created_at: datetime(), updated_at: datetime(), assessment_id: $assessment_id})",
        id=model_id,
        name=payload.name,
        bpmn_xml=payload.bpmn_xml,
        assessment_id=payload.assessment_id,
    )
    return {"id": model_id, "name": payload.name, "bpmn_xml": payload.bpmn_xml,
            "created_at": "now", "updated_at": "now", "assessment_id": payload.assessment_id}


@router.put("/bpmn/models/{model_id}")
async def update_bpmn_model(
    model_id: str,
    payload: BpmnModelUpdate,
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
):
    """Update a BPMN model's XML."""
    result = neo4j.run_query(
        "MATCH (m:BpmnModel {id: $model_id}) "
        "SET m.bpmn_xml = $bpmn_xml, m.updated_at = datetime() "
        "RETURN m.id AS id, m.name AS name, m.bpmn_xml AS bpmn_xml, "
        "toString(m.created_at) AS created_at, toString(m.updated_at) AS updated_at, "
        "m.assessment_id AS assessment_id",
        model_id=model_id,
        bpmn_xml=payload.bpmn_xml,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Model not found")
    return {
        "id": result[0]["id"],
        "name": result[0]["name"],
        "bpmn_xml": result[0]["bpmn_xml"],
        "created_at": result[0]["created_at"],
        "updated_at": result[0]["updated_at"],
        "assessment_id": result[0].get("assessment_id"),
    }


@router.delete("/bpmn/models/{model_id}")
async def delete_bpmn_model(
    model_id: str,
    neo4j: Annotated[Neo4jClient, Depends(get_neo4j_client)],
):
    """Delete a BPMN model."""
    neo4j.run_query("MATCH (m:BpmnModel {id: $model_id}) DETACH DELETE m", model_id=model_id)
    return {"deleted": model_id}