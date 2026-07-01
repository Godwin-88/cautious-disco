"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";

const NetworkGraph = dynamic(() => import("@/components/enables-network-graph"), { ssr: false });

export default function CanvasPage() {
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
    <div className="p-8 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Canvas Explorer</h2>
        <p className="text-gray-400 text-sm">44-domain capability hierarchy — click domains to expand</p>
      </div>

      <div className="flex items-center gap-2 text-xs text-gray-500">
        <span>Canvas</span>
        <span>/</span>
        <span>Domains</span>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-white mb-3">Domain Hierarchy Navigator</h3>
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
          <div className="grid grid-cols-3 md:grid-cols-5 gap-3 max-h-[400px] overflow-y-auto">
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
    </div>
  );
}
