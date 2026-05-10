"use client";

import { useState, useEffect } from "react";
import Image from "next/image";

export default function Sidebar() {
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    fetch("/api/backend/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth({ status: "unreachable" }));
  }, []);

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-[#161920] border-r border-gray-800 p-6 flex flex-col">
      <div className="flex items-center gap-3 mb-6">
        <Image src="/amd_logo.svg" alt="AMD" width={32} height={32} />
        <span className="text-lg font-bold text-white">EA Strategy Optimizer</span>
      </div>

      <div className="text-sm text-gray-400 mb-6 leading-relaxed">
        Powered by <strong className="text-white">AMD MI300X · ROCm · Qwen-72B</strong>
        <br />
        <br />
        Knowledge Graph → AI Prioritiser → Qwen-72B on AMD MI300X → Compliance Validator
      </div>

      <div className="h-px bg-gray-700 mb-4" />

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">Backend:</span>
          <span className={`font-mono ${health?.status === "ok" ? "text-green-400" : "text-orange-400"}`}>
            {health?.status || "loading"}
          </span>
        </div>
        {health?.gpu?.available && (
          <>
            <div className="flex justify-between">
              <span className="text-gray-400">GPU:</span>
              <span className="text-white font-mono">{health.gpu.device}</span>
            </div>
            {health.gpu.rocm && (
              <div className="flex justify-between">
                <span className="text-gray-400">ROCm:</span>
                <span className="text-white font-mono">{health.gpu.rocm}</span>
              </div>
            )}
          </>
        )}
        {!health?.gpu?.available && (
          <div className="flex justify-between">
            <span className="text-gray-400">GPU:</span>
            <span className="text-gray-500">CPU mode</span>
          </div>
        )}
        <div className="flex justify-between">
          <span className="text-gray-400">Knowledge Graph:</span>
          <span className={`font-mono ${health?.neo4j === "connected" ? "text-green-400" : "text-red-400"}`}>
            {health?.neo4j || "unknown"}
          </span>
        </div>
      </div>

      <div className="h-px bg-gray-700 my-4" />

      <div className="text-xs text-gray-500 mt-auto">
        Track 1 — AI Agents & Agentic Workflows
        <br />
        AMD Developer Hackathon 2026
      </div>
    </aside>
  );
}
