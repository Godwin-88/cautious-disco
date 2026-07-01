"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";

const BpmnModeler = dynamic(() => import("@/components/bpmn-modeler"), { ssr: false });

type BpmnModel = {
  id: string;
  name: string;
  bpmn_xml: string;
  created_at: string;
  updated_at: string;
  assessment_id?: string;
};

type Assessment = {
  assessment_id: string;
  org_name: string;
  org_sector: string;
  created_at: string;
};

// Utility to generate a unique local ID
const uid = () => `local_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

const BPMN_TEMPLATES: Record<string, string> = {
  "customer-onboarding": `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_Onboarding" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" name="Customer Application Received" />
    <bpmn:serviceTask id="Task_Validate" name="Validate Customer Data" />
    <bpmn:exclusiveGateway id="Gateway_Approval" name="Document Review?" />
    <bpmn:serviceTask id="Task_ManualReview" name="Manual Document Review" />
    <bpmn:serviceTask id="Task_AutomatedKYC" name="Automated KYC Check" />
    <bpmn:serviceTask id="Task_CreateAccount" name="Create Customer Account" />
    <bpmn:endEvent id="EndEvent_Complete" name="Onboarding Complete" />
    <bpmn:sequenceFlow id="Flow_StartToValidate" sourceRef="StartEvent_1" targetRef="Task_Validate" />
    <bpmn:sequenceFlow id="Flow_ValidateToGateway" sourceRef="Task_Validate" targetRef="Gateway_Approval" />
    <bpmn:sequenceFlow id="Flow_ManualReview" sourceRef="Gateway_Approval" targetRef="Task_ManualReview"><bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">Manual Review Needed</bpmn:conditionExpression></bpmn:sequenceFlow>
    <bpmn:sequenceFlow id="Flow_AutoKYC" sourceRef="Gateway_Approval" targetRef="Task_AutomatedKYC"><bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">Auto-approval Criteria Met</bpmn:conditionExpression></bpmn:sequenceFlow>
    <bpmn:sequenceFlow id="Flow_MergeToAccount" sourceRef="Task_ManualReview" targetRef="Task_CreateAccount" />
    <bpmn:sequenceFlow id="Flow_AutoToAccount" sourceRef="Task_AutomatedKYC" targetRef="Task_CreateAccount" />
    <bpmn:sequenceFlow id="Flow_AccountToEnd" sourceRef="Task_CreateAccount" targetRef="EndEvent_Complete" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_Onboarding">
      <bpmndi:BPMNShape id="Shape_StartEvent_1" bpmnElement="StartEvent_1"><dc:Bounds x="100" y="200" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Task_Validate" bpmnElement="Task_Validate"><dc:Bounds x="200" y="178" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Gateway_Approval" bpmnElement="Gateway_Approval"><dc:Bounds x="370" y="193" width="50" height="50" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Task_ManualReview" bpmnElement="Task_ManualReview"><dc:Bounds x="490" y="100" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Task_AutomatedKYC" bpmnElement="Task_AutomatedKYC"><dc:Bounds x="490" y="260" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Task_CreateAccount" bpmnElement="Task_CreateAccount"><dc:Bounds x="660" y="178" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_EndEvent_Complete" bpmnElement="EndEvent_Complete"><dc:Bounds x="830" y="200" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Edge_Flow_StartToValidate" bpmnElement="Flow_StartToValidate"><di:waypoint x="136" y="218" /><di:waypoint x="200" y="218" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_ValidateToGateway" bpmnElement="Flow_ValidateToGateway"><di:waypoint x="300" y="218" /><di:waypoint x="370" y="218" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_ManualReview" bpmnElement="Flow_ManualReview"><di:waypoint x="395" y="193" /><di:waypoint x="395" y="140" /><di:waypoint x="490" y="140" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_AutoKYC" bpmnElement="Flow_AutoKYC"><di:waypoint x="395" y="243" /><di:waypoint x="395" y="300" /><di:waypoint x="490" y="300" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_MergeToAccount" bpmnElement="Flow_MergeToAccount"><di:waypoint x="590" y="140" /><di:waypoint x="710" y="140" /><di:waypoint x="710" y="218" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_AutoToAccount" bpmnElement="Flow_AutoToAccount"><di:waypoint x="590" y="300" /><di:waypoint x="710" y="300" /><di:waypoint x="710" y="258" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_AccountToEnd" bpmnElement="Flow_AccountToEnd"><di:waypoint x="760" y="218" /><di:waypoint x="830" y="218" /></bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>`,
  "it-deployment": `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_ITDeployment" isExecutable="true">
    <bpmn:startEvent id="StartEvent_IT" name="Deployment Initiated" />
    <bpmn:serviceTask id="Task_EnvironmentPrep" name="Prepare Deployment Environment" />
    <bpmn:parallelGateway id="Gateway_Parallel" name="Parallel Tracks" />
    <bpmn:serviceTask id="Task_CodeDeploy" name="Deploy Application Code" />
    <bpmn:serviceTask id="Task_DBMigrate" name="Run Database Migration" />
    <bpmn:serviceTask id="Task_Configure" name="Configure Services" />
    <bpmn:parallelGateway id="Gateway_Join" name="All Tracks Complete" />
    <bpmn:exclusiveGateway id="Gateway_HealthCheck" name="Health Check Passed?" />
    <bpmn:serviceTask id="Task_Rollback" name="Rollback Deployment" />
    <bpmn:endEvent id="EndEvent_Success" name="Deployment Successful" />
    <bpmn:endEvent id="EndEvent_Failed" name="Deployment Failed" />
    <bpmn:sequenceFlow id="Flow_IT_Start" sourceRef="StartEvent_IT" targetRef="Task_EnvironmentPrep" />
    <bpmn:sequenceFlow id="Flow_Prep_Parallel" sourceRef="Task_EnvironmentPrep" targetRef="Gateway_Parallel" />
    <bpmn:sequenceFlow id="Flow_Parallel_Code" sourceRef="Gateway_Parallel" targetRef="Task_CodeDeploy" />
    <bpmn:sequenceFlow id="Flow_Parallel_DB" sourceRef="Gateway_Parallel" targetRef="Task_DBMigrate" />
    <bpmn:sequenceFlow id="Flow_Parallel_Config" sourceRef="Gateway_Parallel" targetRef="Task_Configure" />
    <bpmn:sequenceFlow id="Flow_Code_Join" sourceRef="Task_CodeDeploy" targetRef="Gateway_Join" />
    <bpmn:sequenceFlow id="Flow_DB_Join" sourceRef="Task_DBMigrate" targetRef="Gateway_Join" />
    <bpmn:sequenceFlow id="Flow_Config_Join" sourceRef="Task_Configure" targetRef="Gateway_Join" />
    <bpmn:sequenceFlow id="Flow_Join_Health" sourceRef="Gateway_Join" targetRef="Gateway_HealthCheck" />
    <bpmn:sequenceFlow id="Flow_Health_Success" sourceRef="Gateway_HealthCheck" targetRef="EndEvent_Success"><bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">Health Check Passed</bpmn:conditionExpression></bpmn:sequenceFlow>
    <bpmn:sequenceFlow id="Flow_Health_Rollback" sourceRef="Gateway_HealthCheck" targetRef="Task_Rollback"><bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">Health Check Failed</bpmn:conditionExpression></bpmn:sequenceFlow>
    <bpmn:sequenceFlow id="Flow_Rollback_Failed" sourceRef="Task_Rollback" targetRef="EndEvent_Failed" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_IT">
    <bpmndi:BPMNPlane id="BPMNPlane_IT" bpmnElement="Process_ITDeployment">
      <bpmndi:BPMNShape id="Shape_StartEvent_IT" bpmnElement="StartEvent_IT"><dc:Bounds x="100" y="200" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Task_EnvironmentPrep" bpmnElement="Task_EnvironmentPrep"><dc:Bounds x="200" y="178" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Gateway_Parallel" bpmnElement="Gateway_Parallel"><dc:Bounds x="370" y="193" width="50" height="50" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Task_CodeDeploy" bpmnElement="Task_CodeDeploy"><dc:Bounds x="490" y="80" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Task_DBMigrate" bpmnElement="Task_DBMigrate"><dc:Bounds x="490" y="200" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Task_Configure" bpmnElement="Task_Configure"><dc:Bounds x="490" y="320" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Gateway_Join" bpmnElement="Gateway_Join"><dc:Bounds x="660" y="193" width="50" height="50" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Gateway_HealthCheck" bpmnElement="Gateway_HealthCheck"><dc:Bounds x="780" y="193" width="50" height="50" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Task_Rollback" bpmnElement="Task_Rollback"><dc:Bounds x="900" y="300" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_EndEvent_Success" bpmnElement="EndEvent_Success"><dc:Bounds x="900" y="100" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_EndEvent_Failed" bpmnElement="EndEvent_Failed"><dc:Bounds x="900" y="400" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Edge_Flow_IT_Start" bpmnElement="Flow_IT_Start"><di:waypoint x="136" y="218" /><di:waypoint x="200" y="218" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_Prep_Parallel" bpmnElement="Flow_Prep_Parallel"><di:waypoint x="300" y="218" /><di:waypoint x="370" y="218" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_Parallel_Code" bpmnElement="Flow_Parallel_Code"><di:waypoint x="395" y="193" /><di:waypoint x="395" y="120" /><di:waypoint x="490" y="120" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_Parallel_DB" bpmnElement="Flow_Parallel_DB"><di:waypoint x="395" y="218" /><di:waypoint x="490" y="240" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_Parallel_Config" bpmnElement="Flow_Parallel_Config"><di:waypoint x="395" y="243" /><di:waypoint x="395" y="360" /><di:waypoint x="490" y="360" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_Code_Join" bpmnElement="Flow_Code_Join"><di:waypoint x="590" y="120" /><di:waypoint x="685" y="120" /><di:waypoint x="685" y="218" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_DB_Join" bpmnElement="Flow_DB_Join"><di:waypoint x="590" y="240" /><di:waypoint x="660" y="218" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_Config_Join" bpmnElement="Flow_Config_Join"><di:waypoint x="590" y="360" /><di:waypoint x="685" y="360" /><di:waypoint x="685" y="243" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_Join_Health" bpmnElement="Flow_Join_Health"><di:waypoint x="710" y="218" /><di:waypoint x="780" y="218" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_Health_Success" bpmnElement="Flow_Health_Success"><di:waypoint x="830" y="218" /><di:waypoint x="900" y="118" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_Health_Rollback" bpmnElement="Flow_Health_Rollback"><di:waypoint x="805" y="243" /><di:waypoint x="805" y="340" /><di:waypoint x="900" y="340" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_Rollback_Failed" bpmnElement="Flow_Rollback_Failed"><di:waypoint x="1000" y="340" /><di:waypoint x="1018" y="418" /></bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>`,
  "basic-process": `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_Basic" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" name="Start" />
    <bpmn:serviceTask id="Task_1" name="Task 1" />
    <bpmn:exclusiveGateway id="Gateway_1" name="Decision?" />
    <bpmn:serviceTask id="Task_2A" name="Path A" />
    <bpmn:serviceTask id="Task_2B" name="Path B" />
    <bpmn:serviceTask id="Task_3" name="Final Task" />
    <bpmn:endEvent id="EndEvent_1" name="End" />
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_1" />
    <bpmn:sequenceFlow id="Flow_1_to_Gateway" sourceRef="Task_1" targetRef="Gateway_1" />
    <bpmn:sequenceFlow id="Flow_PathA" sourceRef="Gateway_1" targetRef="Task_2A" />
    <bpmn:sequenceFlow id="Flow_PathB" sourceRef="Gateway_1" targetRef="Task_2B" />
    <bpmn:sequenceFlow id="Flow_A_to_End" sourceRef="Task_2A" targetRef="Task_3" />
    <bpmn:sequenceFlow id="Flow_B_to_End" sourceRef="Task_2B" targetRef="Task_3" />
    <bpmn:sequenceFlow id="Flow_Final" sourceRef="Task_3" targetRef="EndEvent_1" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_Basic">
    <bpmndi:BPMNPlane id="BPMNPlane_Basic" bpmnElement="Process_Basic">
      <bpmndi:BPMNShape id="Shape_StartEvent_1" bpmnElement="StartEvent_1"><dc:Bounds x="100" y="200" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Task_1" bpmnElement="Task_1"><dc:Bounds x="200" y="178" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Gateway_1" bpmnElement="Gateway_1"><dc:Bounds x="370" y="193" width="50" height="50" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Task_2A" bpmnElement="Task_2A"><dc:Bounds x="490" y="100" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Task_2B" bpmnElement="Task_2B"><dc:Bounds x="490" y="260" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_Task_3" bpmnElement="Task_3"><dc:Bounds x="660" y="178" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_EndEvent_1" bpmnElement="EndEvent_1"><dc:Bounds x="830" y="200" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Edge_Flow_1" bpmnElement="Flow_1"><di:waypoint x="136" y="218" /><di:waypoint x="200" y="218" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_1_to_Gateway" bpmnElement="Flow_1_to_Gateway"><di:waypoint x="300" y="218" /><di:waypoint x="370" y="218" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_PathA" bpmnElement="Flow_PathA"><di:waypoint x="395" y="193" /><di:waypoint x="395" y="140" /><di:waypoint x="490" y="140" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_PathB" bpmnElement="Flow_PathB"><di:waypoint x="395" y="243" /><di:waypoint x="395" y="300" /><di:waypoint x="490" y="300" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_A_to_End" bpmnElement="Flow_A_to_End"><di:waypoint x="590" y="140" /><di:waypoint x="710" y="140" /><di:waypoint x="710" y="218" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_B_to_End" bpmnElement="Flow_B_to_End"><di:waypoint x="590" y="300" /><di:waypoint x="710" y="300" /><di:waypoint x="710" y="258" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Edge_Flow_Final" bpmnElement="Flow_Final"><di:waypoint x="760" y="218" /><di:waypoint x="830" y="218" /></bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>`,
};

function getBlankXml(): string {
  const procId = `Process_${Date.now()}`;
  return `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="${procId}" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" name="Start" />
    <bpmn:endEvent id="EndEvent_1" name="End" />
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="EndEvent_1" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="${procId}">
      <bpmndi:BPMNShape id="Shape_StartEvent_1" bpmnElement="StartEvent_1"><dc:Bounds x="100" y="200" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_EndEvent_1" bpmnElement="EndEvent_1"><dc:Bounds x="300" y="200" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Edge_Flow_1" bpmnElement="Flow_1"><di:waypoint x="136" y="218" /><di:waypoint x="300" y="218" /></bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>`;
}

export default function BpmnStudioPage() {
  const [models, setModels] = useState<BpmnModel[]>([]);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [selectedModel, setSelectedModel] = useState<BpmnModel | null>(null);
  const [activeXml, setActiveXml] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const fetchModels = async () => {
    try {
      const res = await fetch("/api/backend/bpmn/models");
      const data = await res.json();
      setModels(Array.isArray(data) ? data : []);
    } catch {
      setModels([]);
    }
  };

  const fetchAssessments = async () => {
    try {
      const res = await fetch("/api/backend/assessments");
      const data = await res.json();
      setAssessments(Array.isArray(data) ? data : []);
    } catch {
      setAssessments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
    fetchAssessments();
  }, []);

  // Create a local model (works offline, no backend needed)
  const createLocalModel = (name: string, bpmnXml: string) => {
    const model: BpmnModel = {
      id: uid(),
      name,
      bpmn_xml: bpmnXml,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    setModels(prev => [model, ...prev]);
    setSelectedModel(model);
    setActiveXml(bpmnXml);
    return model;
  };

  const handleCreateModel = async (name: string, bpmn_xml?: string, assessmentId?: string) => {
    const xml = bpmn_xml || getBlankXml();
    // Try backend first, fall back to local
    try {
      const res = await fetch("/api/backend/bpmn/models", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, bpmn_xml: xml, assessment_id: assessmentId }),
      });
      if (res.ok) {
        const model = await res.json();
        setModels(prev => [model, ...prev]);
        setSelectedModel(model);
        setActiveXml(model.bpmn_xml);
        return;
      }
    } catch {
      // Backend unavailable - use local model
    }
    createLocalModel(name, xml);
  };

  const handleCreateFromTemplate = (templateKey: string) => {
    const name = `Template: ${templateKey.replace(/-/g, " ")}`;
    const xml = BPMN_TEMPLATES[templateKey];
    if (xml) {
      createLocalModel(name, xml);
    }
  };

  const handleSaveModel = async (xml: string) => {
    if (!selectedModel) return;
    try {
      const res = await fetch(`/api/backend/bpmn/models/${selectedModel.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bpmn_xml: xml }),
      });
      if (res.ok) {
        const updated = await res.json();
        setModels(prev => prev.map(m => m.id === updated.id ? updated : m));
        setSelectedModel(updated);
        return;
      }
    } catch {
      // Backend unavailable
    }
    // Local save: update in-place
    setModels(prev => prev.map(m => m.id === selectedModel.id ? { ...m, bpmn_xml: xml, updated_at: new Date().toISOString() } : m));
    setSelectedModel(prev => prev ? { ...prev, bpmn_xml: xml, updated_at: new Date().toISOString() } : null);
  };

  const handleDeleteModel = (id: string) => {
    if (!confirm("Delete this BPMN model?")) return;
    // Try backend
    fetch(`/api/backend/bpmn/models/${id}`, { method: "DELETE" }).catch(() => {});
    setModels(prev => prev.filter(m => m.id !== id));
    if (selectedModel?.id === id) {
      setSelectedModel(null);
      setActiveXml(null);
    }
  };

  const handleGenerateWithAgent = async (assessmentId: string) => {
    try {
      const res = await fetch("/api/backend/bpmn/generate-from-assessment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ assessment_id: assessmentId }),
      });
      const data = await res.json();
      const model = await fetch("/api/backend/bpmn/models", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: `BPMN from ${assessments.find(a => a.assessment_id === assessmentId)?.org_name || "Assessment"}`,
          bpmn_xml: data.bpmn_xml,
          assessment_id: assessmentId,
        }),
      }).then(r => r.json());
      setModels(prev => [model, ...prev]);
      setSelectedModel(model);
      setActiveXml(model.bpmn_xml);
    } catch {
      // Backend unavailable
    }
  };

  const bgPrimary = theme === "dark" ? "#111827" : "#ffffff";
  const bgSecondary = theme === "dark" ? "#161920" : "#f9fafb";
  const borderColor = theme === "dark" ? "#374151" : "#d1d5e7";
  const textPrimary = theme === "dark" ? "#e5e7eb" : "#111827";
  const textSecondary = theme === "dark" ? "#9ca3af" : "#6b7280";
  const hoverBg = theme === "dark" ? "#374151" : "#e5e7eb";

  if (loading) {
    return (
      <div className="p-8" style={{ backgroundColor: bgPrimary, minHeight: "100vh" }}>
        <div style={{ color: textSecondary }}>Loading BPMN Studio...</div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6" style={{ backgroundColor: bgPrimary, minHeight: "100vh" }}>
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold" style={{ color: textPrimary }}>BPMN Studio</h2>
          <p className="text-sm" style={{ color: textSecondary }}>Create, edit, and save BPMN 2.0 workflow diagrams with AI agent assistance</p>
        </div>
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="p-2 rounded border"
          style={{ backgroundColor: bgSecondary, borderColor, color: textPrimary }}
          title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
        >
          {theme === "dark" ? "☀️" : "🌙"}
        </button>
      </div>

      <div className="grid grid-cols-12 gap-6 h-[calc(100vh-200px)]">
        {/* Sidebar */}
        <div className={`${sidebarCollapsed ? "col-span-1" : "col-span-3"} transition-all duration-300 space-y-4`}>
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="mb-2 p-1 rounded border"
            style={{ backgroundColor: bgSecondary, borderColor, color: textPrimary }}
            title={sidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {sidebarCollapsed ? "→" : "←"}
          </button>

          {!sidebarCollapsed && (
            <>
              {/* Templates */}
              <div className="border rounded-lg p-4" style={{ backgroundColor: bgSecondary, borderColor }}>
                <h3 className="text-sm font-semibold mb-3" style={{ color: textPrimary }}>Workflow Templates</h3>
                <div className="space-y-1">
                  <button onClick={() => handleCreateFromTemplate("customer-onboarding")}
                    className="w-full text-left p-2 rounded text-xs transition-colors" style={{ color: textPrimary, backgroundColor: bgSecondary }} onMouseEnter={(e) => e.currentTarget.style.backgroundColor = hoverBg} onMouseLeave={(e) => e.currentTarget.style.backgroundColor = bgSecondary}>Customer Onboarding</button>
                  <button onClick={() => handleCreateFromTemplate("it-deployment")}
                    className="w-full text-left p-2 rounded text-xs transition-colors" style={{ color: textPrimary, backgroundColor: bgSecondary }} onMouseEnter={(e) => e.currentTarget.style.backgroundColor = hoverBg} onMouseLeave={(e) => e.currentTarget.style.backgroundColor = bgSecondary}>IT Deployment</button>
                  <button onClick={() => handleCreateFromTemplate("basic-process")}
                    className="w-full text-left p-2 rounded text-xs transition-colors" style={{ color: textPrimary, backgroundColor: bgSecondary }} onMouseEnter={(e) => e.currentTarget.style.backgroundColor = hoverBg} onMouseLeave={(e) => e.currentTarget.style.backgroundColor = bgSecondary}>Basic Process</button>
                </div>
              </div>

              {/* My Models */}
              <div className="border rounded-lg p-4" style={{ backgroundColor: bgSecondary, borderColor }}>
                <h3 className="text-sm font-semibold mb-3" style={{ color: textPrimary }}>My Models</h3>
                <button
                  onClick={() => handleCreateModel(`Untitled Model ${models.length + 1}`)}
                  className="w-full mb-3 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-xs font-medium"
                >
                  + New Blank Model
                </button>
                <div className="space-y-1 max-h-[200px] overflow-y-auto">
                  {models.map(m => (
                    <div key={m.id} className="group flex items-center justify-between p-2 rounded cursor-pointer transition-colors"
                      style={{ color: textPrimary, backgroundColor: selectedModel?.id === m.id ? hoverBg : bgSecondary }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = hoverBg}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = selectedModel?.id === m.id ? hoverBg : bgSecondary}
                      onClick={() => { setSelectedModel(m); setActiveXml(m.bpmn_xml); }}>
                      <span className="text-sm truncate">{m.name}</span>
                      <button onClick={(e) => { e.stopPropagation(); handleDeleteModel(m.id); }}
                        className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 text-xs">✕</button>
                    </div>
                  ))}
                  {models.length === 0 && <p className="text-xs" style={{ color: textSecondary }}>No saved models</p>}
                </div>
              </div>

              {/* Generate from Assessment */}
              <div className="border rounded-lg p-4" style={{ backgroundColor: bgSecondary, borderColor }}>
                <h3 className="text-sm font-semibold mb-3" style={{ color: textPrimary }}>Generate from Assessment</h3>
                <div className="space-y-2 max-h-[150px] overflow-y-auto">
                  {assessments.map(a => (
                    <button key={a.assessment_id} onClick={() => handleGenerateWithAgent(a.assessment_id)}
                      className="w-full text-left p-2 rounded text-xs truncate transition-colors" style={{ color: textPrimary, backgroundColor: bgSecondary }} onMouseEnter={(e) => e.currentTarget.style.backgroundColor = hoverBg} onMouseLeave={(e) => e.currentTarget.style.backgroundColor = bgSecondary}>
                      {a.org_name}
                    </button>
                  ))}
                  {assessments.length === 0 && <p className="text-xs" style={{ color: textSecondary }}>No assessments available</p>}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Main workspace */}
        <div className={`${sidebarCollapsed ? "col-span-11" : "col-span-9"} flex flex-col`}>
          {activeXml ? (
            <BpmnModeler xml={activeXml} onChange={setActiveXml} onSave={handleSaveModel} model={selectedModel} theme={theme} />
          ) : (
            <div className="h-full flex items-center justify-center border rounded-lg" style={{ backgroundColor: bgSecondary, borderColor }}>
              <div className="text-center">
                <p className="mb-4" style={{ color: textSecondary }}>Select a model or create a new one to begin editing</p>
                <button onClick={() => handleCreateModel(`Untitled Model ${models.length + 1}`)}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">
                  Create New BPMN Model
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}