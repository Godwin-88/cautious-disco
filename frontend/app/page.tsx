"use client";

import { useState } from "react";
import { TABS } from "@/lib/terminology";
import { useChat } from "@/lib/context";
import ChatTab from "@/components/chat-tab";
import GraphExplorerTab from "@/components/graph-explorer-tab";
import InputForm from "@/components/input-form";
import RoadmapTab from "@/components/roadmap-tab";
import EpicsTab from "@/components/epics-tab";
import IntegrationsTab from "@/components/integrations-tab";
import ExportTab from "@/components/export-tab";
import TrainingTab from "@/components/training-tab";

export default function Home() {
  const [activeTab, setActiveTab] = useState<(typeof TABS)[number]>(TABS[0]);
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

  const renderTab = () => {
    switch (activeTab) {
      case "EA Advisor":
        return <ChatTab />;
      case "Graph Explorer":
        return <GraphExplorerTab />;
      case "Strategic Roadmap":
        return (
          <div className="space-y-6">
            <InputForm onSubmit={handleAnalyze} />
            {result && <RoadmapTab result={result} />}
          </div>
        );
      case "Initiatives & Scenarios":
        return <EpicsTab result={result} />;
      case "Integrations":
        return <IntegrationsTab result={result} />;
      case "Export & Handover":
        return <ExportTab result={result} />;
      case "AI Learning Engine":
        return <TrainingTab />;
      default:
        return null;
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-white mb-2">Enterprise Architecture Strategy Optimizer</h1>
      <p className="text-gray-400 mb-6 max-w-4xl">
        Transform business goals into <strong className="text-white">governance-grounded strategic roadmaps</strong> — with Jira-ready initiatives, business scenarios, and regulatory obligations — powered by <strong className="text-white">AMD MI300X</strong>, Knowledge Graph-RAG, and AI-driven prioritisation.
      </p>

      <nav className="flex flex-wrap gap-2 mb-8">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
              activeTab === tab
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-300 hover:bg-gray-700"
            }`}
          >
            {tab}
          </button>
        ))}
      </nav>

      <section className="min-h-[500px]">{renderTab()}</section>
    </div>
  );
}
