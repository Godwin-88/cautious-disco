"use client";

import { useState, useEffect } from "react";
import { useChat } from "@/lib/context";
import SidebarNav from "@/components/sidebar-nav";
import InputForm from "@/components/input-form";
import RoadmapTab from "@/components/roadmap-tab";
import IntegrationsTab from "@/components/integrations-tab";
import TrainingTab from "@/components/training-tab";
import HumanTaskPortal from "@/components/human-task-portal";
import dynamic from "next/dynamic";

const NetworkGraph = dynamic(() => import("@/components/enables-network-graph"), { ssr: false });
const BpmnStudioPage = dynamic(() => import("./bpmn-studio/page"), { ssr: false });

export default function Home() {
  const [activeView, setActiveView] = useState<"canvas" | "assessments" | "bpmn" | "review" | "analytics" | "settings">("canvas");
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
      case "canvas":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white">Canvas Explorer</h2>
              <p className="text-gray-400 text-sm">44-domain capability hierarchy, ENABLES network graph, and gap heatmap</p>
            </div>
            <CanvasView result={result} onAnalyze={handleAnalyze} />
          </div>
        );
      case "assessments":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white">Assessments Dashboard</h2>
              <p className="text-gray-400 text-sm">All past and in-progress capability assessments</p>
            </div>
            <AssessmentsView setResult={setResult} />
          </div>
        );
      case "bpmn":
        return <div className="h-screen"><BpmnStudioPage /></div>;
      case "review":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white">Review Portal</h2>
              <p className="text-gray-400 text-sm">Human-in-the-loop review and approval of AI-generated roadmaps</p>
            </div>
            <HumanTaskPortal />
          </div>
        );
      case "analytics":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white">Analytics</h2>
              <p className="text-gray-400 text-sm">Platform metrics and assessment analytics</p>
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
            <IntegrationsTab />
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

function CanvasView({ result, onAnalyze }: { result: any; onAnalyze: (payload: any) => void }) {
  const [domains, setDomains] = useState<any[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetch("/api/backend/domains")
      .then((r) => r.json())
      .then((data) => setDomains(Array.isArray(data) ? data : []))
      .catch(() => setDomains([]));
  }, []);

  const filtered = domains.filter(d => 
    d.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Assessment Intake</h3>
        {!result ? (
          <InputForm onSubmit={onAnalyze} />
        ) : (
          <div className="flex gap-2">
            <button 
              onClick={() => {
                const a = document.createElement('a');
                a.href = 'data:application/xml,' + encodeURIComponent(result.bpmn_xml || '');
                a.download = 'roadmap.bpmn';
                a.click();
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm"
            >
              Export BPMN
            </button>
            <button 
              onClick={() => {}}
              className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm"
            >
              View Report
            </button>
          </div>
        )}
      </div>

      <div>
        <h3 className="text-lg font-semibold text-white mb-3">Domain Hierarchy</h3>
        <div className="relative mb-3">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search domains..."
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>
        <div className="bg-[#161920] border border-gray-800 rounded-lg p-4">
          <div className="grid grid-cols-3 md:grid-cols-5 gap-3 max-h-[300px] overflow-y-auto">
            {filtered.map((d) => (
              <button
                key={d.id}
                className="p-3 rounded border border-gray-700 bg-gray-900 hover:bg-gray-800 text-left"
              >
                <div className="text-sm font-medium text-white truncate">{d.name.replace("Manage ", "")}</div>
                <div className="text-xs text-gray-500">{d.capability_count || 0} capabilities</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-white mb-3">ENABLES Network Graph</h3>
        <NetworkGraph />
      </div>

      {result && (
        <div className="mt-6">
          <RoadmapTab result={result} />
        </div>
      )}
    </div>
  );
}

function AssessmentsView({ setResult }: { setResult: (r: any) => void }) {
  const [assessments, setAssessments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/backend/assessments")
      .then((r) => r.json())
      .then(setAssessments)
      .catch(() => setAssessments([]))
      .finally(() => setLoading(false));
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "COMPLETE": return "bg-green-900 text-green-300";
      case "AWAITING_REVIEW": return "bg-orange-900 text-orange-300";
      case "RUNNING": return "bg-blue-900 text-blue-300";
      case "FAILED": return "bg-red-900 text-red-300";
      default: return "bg-gray-800 text-gray-400";
    }
  };

  return (
    <div className="space-y-4">
      {loading && <p className="text-gray-400">Loading assessments...</p>}

      {!loading && assessments.length === 0 && (
        <div className="bg-[#161920] border border-gray-800 rounded-lg p-6 text-center">
          <p className="text-gray-500">No assessments yet. Run an assessment in Canvas to generate a roadmap.</p>
        </div>
      )}

      {assessments.length > 0 && (
        <div className="bg-[#161920] border border-gray-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-900">
              <tr>
                <th className="text-left px-4 py-3 text-gray-300 font-medium">Org Name</th>
                <th className="text-left px-4 py-3 text-gray-300 font-medium">Sector</th>
                <th className="text-left px-4 py-3 text-gray-300 font-medium">Date</th>
                <th className="text-left px-4 py-3 text-gray-300 font-medium">Status</th>
                <th className="text-left px-4 py-3 text-gray-300 font-medium">Score</th>
                <th className="text-left px-4 py-3 text-gray-300 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {assessments.map((a) => (
                <tr key={a.assessment_id} className="border-t border-gray-800 hover:bg-gray-800/30">
                  <td className="px-4 py-3 text-white">{a.org_name}</td>
                  <td className="px-4 py-3 text-gray-300">{a.org_sector}</td>
                  <td className="px-4 py-3 text-gray-400">{a.created_at?.slice(0, 10) || "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs ${getStatusColor(a.status)}`}>
                      {a.status.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-white font-mono">
                    {a.compliance_score ? `${a.compliance_score.toFixed(0)}%` : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => setResult(a)}
                      className="text-xs text-blue-400 hover:text-blue-300"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
