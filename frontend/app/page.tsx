"use client";

import { useState, useEffect } from "react";
import { useChat } from "@/lib/context";
import SidebarNav from "@/components/sidebar-nav";
import ChatTab from "@/components/chat-tab";
import GraphExplorerTab from "@/components/graph-explorer-tab";
import InputForm from "@/components/input-form";
import RoadmapTab from "@/components/roadmap-tab";
import IntegrationsTab from "@/components/integrations-tab";
import TrainingTab from "@/components/training-tab";
import HumanTaskPortal from "@/components/human-task-portal";
import ExportTab from "@/components/export-tab";

export default function Home() {
  const [activeView, setActiveView] = useState<"process" | "agents" | "review" | "graph" | "learning" | "settings" | "export">("process");
  const { result, setResult } = useChat();

  const handleAnalyze = async (payload: any) => {
    const res = await fetch("/api/backend/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    setResult(data);
  };

  const renderView = () => {
    switch (activeView) {
      case "process":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white">Process Flow Dashboard</h2>
              <p className="text-gray-400 text-sm">Monitor and orchestrate BPMN processes across humans, agents, and APIs</p>
            </div>
            <ProcessFlowView />
          </div>
        );
      case "agents":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white">AI Agents</h2>
              <p className="text-gray-400 text-sm">Conversational AI for capability analysis and roadmap generation</p>
            </div>
            <ChatTab />
            {!result && <InputForm onSubmit={handleAnalyze} />}
            {result && (
              <div className="mt-8">
                <RoadmapTab result={result} />
              </div>
            )}
          </div>
        );
      case "review":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white">Human Review & Approval</h2>
              <p className="text-gray-400 text-sm">Review AI-generated assessments and provide human oversight decisions</p>
            </div>
            <HumanTaskPortal />
          </div>
        );
      case "graph":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white">Knowledge Graph Explorer</h2>
              <p className="text-gray-400 text-sm">Explore cross-domain relationships and capability mappings</p>
            </div>
            <GraphExplorerTab />
          </div>
        );
      case "learning":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white">AI Learning Engine</h2>
              <p className="text-gray-400 text-sm">Train and monitor AI models for capability prioritisation</p>
            </div>
            <TrainingTab />
          </div>
        );
      case "settings":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white">Settings</h2>
              <p className="text-gray-400 text-sm">Configure integrations and system connections</p>
            </div>
            <IntegrationsTab result={result} />
          </div>
        );
      case "export":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white">Export & Handover</h2>
              <p className="text-gray-400 text-sm">Export roadmap outputs to Jira, ServiceNow, and other platforms</p>
            </div>
            <ExportTab result={result} />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="pl-64">
      <SidebarNav activeView={activeView} setActiveView={setActiveView} />
      <main className="p-8">
        {renderView()}
      </main>
    </div>
  );
}

function ProcessFlowView() {
  const [processes, setProcesses] = useState<any[]>([]);

  useEffect(() => {
    fetch("/api/backend/uipath/processes")
      .then((r) => r.json())
      .then(setProcesses)
      .catch(() => setProcesses([]));
  }, []);

  return (
    <div className="space-y-4">
      {processes.length === 0 ? (
        <div className="bg-[#161920] border border-gray-800 rounded-lg p-6">
          <div className="text-center text-gray-500 py-8">
            <div className="text-4xl mb-2">🔄</div>
            <p>No active processes. Run an assessment to create a BPMN workflow.</p>
            <p className="text-xs mt-2 text-gray-600">Navigate to AI Agents to start capability analysis.</p>
          </div>
        </div>
      ) : (
        processes.map((p, i) => (
          <div key={i} className="bg-[#161920] border border-gray-800 rounded-lg p-4">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-semibold text-white">{p.name}</h3>
                <p className="text-xs text-gray-400 mt-1">{p.description}</p>
              </div>
              <span className={`text-xs px-2 py-1 rounded ${p.status === "running" ? "bg-blue-900 text-blue-300" : "bg-gray-800 text-gray-400"}`}>
                {p.status}
              </span>
            </div>
          </div>
        ))
      )}
    </div>
  );
}