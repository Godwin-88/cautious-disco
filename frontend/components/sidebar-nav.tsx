"use client";

import { useState, useEffect } from "react";

type SidebarItem = {
  id: "canvas" | "assessments" | "bpmn" | "review" | "analytics" | "settings";
  label: string;
  icon?: string;
};

const MENU_ITEMS: SidebarItem[] = [
  { id: "canvas", label: "Canvas", icon: "📊" },
  { id: "assessments", label: "Assessments", icon: "📋" },
  { id: "bpmn", label: "BPMN Studio", icon: "🔄" },
  { id: "review", label: "Review", icon: "👤" },
  { id: "analytics", label: "Analytics", icon: "📈" },
  { id: "settings", label: "Settings", icon: "⚙️" },
];

export default function SidebarNav({ activeView, setActiveView }: {
  activeView: "canvas" | "assessments" | "bpmn" | "review" | "analytics" | "settings";
  setActiveView: (view: "canvas" | "assessments" | "bpmn" | "review" | "analytics" | "settings") => void;
}) {
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    fetch("/api/backend/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth({ status: "unreachable" }));
  }, []);

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-[#161920] border-r border-gray-800 p-4 flex flex-col">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-white">Digital Capability Intelligence Platform</h1>
        <p className="text-xs text-gray-500 mt-1">Qwen3-235B · LangGraph · BPMN · Neo4j</p>
      </div>

      <nav className="flex-1 space-y-1">
        {MENU_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveView(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeView === item.id
                ? "bg-blue-600/20 text-blue-300 border border-blue-600/30"
                : "text-gray-400 hover:bg-gray-800 hover:text-gray-200"
            }`}
          >
            <span className="text-lg">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      <div className="pt-3 mt-auto border-t border-gray-800">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-500">Backend:</span>
          <span className={`font-mono ${health?.status === "ok" ? "text-green-400" : "text-orange-400"}`}>
            {health?.status === "ok" ? "● Connected" : "○ Disconnected"}
          </span>
        </div>
        <div className="flex items-center justify-between text-xs mt-1">
          <span className="text-gray-500">Graph:</span>
          <span className={`font-mono ${health?.neo4j === "connected" ? "text-green-400" : "text-red-400"}`}>
            {health?.neo4j === "connected" ? "● Connected" : "○ Disconnected"}
          </span>
        </div>
      </div>

      <div className="text-xs text-gray-600 pt-2">
        Track 4 &mdash; Autopilot Agent
      </div>
    </aside>
  );
}
