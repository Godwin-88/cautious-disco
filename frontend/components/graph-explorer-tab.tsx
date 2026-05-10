"use client";

import { useState, useEffect, useRef } from "react";
import { domainLabel, subdomainLabel } from "@/lib/terminology";

type Node = { id: string; name: string; sector: string; drl_trained?: boolean };
type Edge = { source: string; target: string; type: string };

export default function GraphExplorerTab() {
  const networkRef = useRef<HTMLDivElement>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedDomain, setSelectedDomain] = useState("");
  const [detail, setDetail] = useState<any>(null);

  useEffect(() => {
    fetch("/api/backend/graph/network")
      .then((r) => r.json())
      .then((data) => {
        setNodes(data.nodes || []);
        setEdges((data.edges || []).filter((e: any) => e));
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedDomain || !nodes.length) return;
    fetch(`/api/backend/graph/domain-detail?domain_name=${encodeURIComponent(selectedDomain)}`)
      .then((r) => r.json())
      .then(setDetail)
      .catch(() => setDetail(null));
  }, [selectedDomain]);

  useEffect(() => {
    if (!networkRef.current || nodes.length === 0) return;

    import("vis-network").then(({ Network }) => {
      const container = networkRef.current!;
      container.innerHTML = "";
      const datasetNodes = new (window as any).vis.DataSet(
        nodes.map((n) => ({
          id: n.id,
          label: domainLabel(n.name),
          color: { background: n.drl_trained ? "#27ae60" : "#3498db", border: "#fff" },
          size: n.drl_trained ? 25 : 16,
        }))
      );
      const datasetEdges = new (window as any).vis.DataSet(
        edges.map((e, i) => ({
          id: i,
          from: e.source,
          to: e.target,
          label: e.type,
          arrows: "to",
        }))
      );
      new Network(container, { nodes: datasetNodes, edges: datasetEdges }, {
        height: "600px",
        physics: { stabilization: true },
        edges: { font: { size: 10, color: "#888" } },
      });
    }).catch(() => {
      if (networkRef.current) networkRef.current.innerHTML = `<div class="flex items-center justify-center h-full text-gray-500">vis-network unavailable</div>`;
    });
  }, [nodes, edges]);

  const friendlyNames = nodes.map((n) => domainLabel(n.name));

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Knowledge Graph Explorer</h2>
        <p className="text-gray-400 text-sm">Live network of 44 enterprise domains — nodes sized by DRL training status, colored by sector, edges show inter-domain relationships</p>
      </div>

      <div className="bg-[#161920] border border-gray-800 rounded-lg p-4">
        <div ref={networkRef} className="w-full" style={{ minHeight: "600px" }} />
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="bg-[#161920] border border-gray-800 rounded p-4 text-center">
          <div className="text-2xl font-bold text-white">{nodes.length}</div>
          <div className="text-xs text-gray-400">Domains</div>
        </div>
        <div className="bg-[#161920] border border-gray-800 rounded p-4 text-center">
          <div className="text-2xl font-bold text-white">{edges.length}</div>
          <div className="text-xs text-gray-400">Relationships</div>
        </div>
        <div className="bg-[#161920] border border-gray-800 rounded p-4 text-center">
          <div className="text-2xl font-bold text-white">{new Set(nodes.map((n) => n.sector).filter(Boolean)).size}</div>
          <div className="text-xs text-gray-400">Sectors</div>
        </div>
        <div className="bg-[#161920] border border-gray-800 rounded p-4 text-center">
          <div className="text-2xl font-bold text-green-400">{nodes.filter((n) => n.drl_trained).length}</div>
          <div className="text-xs text-gray-400">AI Trained</div>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">Select a domain to explore:</label>
        <select
          value={selectedDomain}
          onChange={(e) => setSelectedDomain(e.target.value)}
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
        >
          <option value="">— select a domain —</option>
          {friendlyNames.map((name) => (
            <option key={name} value={name}>{name}</option>
          ))}
        </select>
      </div>

      {detail && (
        <div className="bg-[#161920] border border-gray-800 rounded-lg p-6 space-y-6">
          <div className="flex items-center gap-3">
            <h3 className="text-xl font-bold text-white">{domainLabel(detail.domain?.name || selectedDomain)}</h3>
            <span className={`px-2 py-1 rounded text-xs ${detail.domain?.drl_trained ? "bg-green-900 text-green-200" : "bg-gray-700 text-gray-300"}`}>
              {detail.domain?.drl_trained ? "🟢 AI-Trained" : "⚪ Not Yet Trained"}
            </span>
            {detail.domain?.drl_final_reward != null && (
              <span className="text-xs text-gray-400">Reward: {detail.domain.drl_final_reward.toFixed(3)}</span>
            )}
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="bg-gray-900 border border-gray-800 rounded p-3">
              <div className="text-xs text-gray-500">Capability Areas</div>
              <div className="text-lg font-bold text-white">{detail.subdomain_groups?.length || 0}</div>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded p-3">
              <div className="text-xs text-gray-500">Capabilities</div>
              <div className="text-lg font-bold text-white">{detail.subdomain_groups?.reduce((s: number, g: any) => s + (g.capabilities?.length || 0), 0) || 0}</div>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded p-3">
              <div className="text-xs text-gray-500">High Complexity</div>
              <div className="text-lg font-bold text-white">
                {detail.subdomain_groups?.reduce((s: number, g: any) => s + (g.capabilities || []).filter((c: any) => (c.implementation_complexity || "").toLowerCase().includes("high")).length, 0) || 0}
              </div>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded p-3">
              <div className="text-xs text-gray-500">Est. Effort</div>
              <div className="text-lg font-bold text-white">
                {detail.subdomain_groups?.reduce((s: number, g: any) => s + (g.capabilities || []).reduce((cs: number, c: any) => cs + (Number(c.typical_duration_weeks) || 0), 0), 0) || "—"} wks
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-white">Governance Framework</h4>
              {detail.standard ? (
                <>
                  <p className="text-sm text-white">{detail.standard.name} {detail.standard.version ? `v${detail.standard.version}` : ""}</p>
                  <p className="text-xs text-gray-400">{detail.standard.publisher}</p>
                  {detail.standard.description && <p className="text-xs text-gray-300">{detail.standard.description}</p>}
                  {detail.standard.key_principles?.length > 0 && (
                    <div>
                      <p className="text-xs text-gray-500 mt-2">Key Principles:</p>
                      <ul className="text-xs text-gray-300 list-disc list-inside">{detail.standard.key_principles.slice(0, 5).map((p: string, i: number) => <li key={i}>{p}</li>)}</ul>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-xs text-gray-500">No governance framework linked yet.</p>
              )}
            </div>
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-white">Innovation Driver</h4>
              {detail.trend ? (
                <>
                  <p className="text-sm text-white">{detail.trend.name}</p>
                  <p className="text-xs text-gray-400">{[detail.trend.impact_level, detail.trend.time_horizon, detail.trend.maturity].filter(Boolean).join(" · ")}</p>
                  {detail.trend.description && <p className="text-xs text-gray-300">{detail.trend.description}</p>}
                </>
              ) : (
                <p className="text-xs text-gray-500">No innovation driver linked yet.</p>
              )}
            </div>
          </div>

          {(detail.subdomain_groups || []).map((group: any, gi: number) => {
            const caps = group.capabilities || [];
            return (
              <details key={gi} className="border border-gray-800 rounded" open>
                <summary className="p-3 text-sm font-semibold text-white cursor-pointer hover:bg-gray-800/50">
                  {subdomainLabel(group.subdomain?.name || "—")} — {caps.length} capabilities
                </summary>
                <div className="p-3 space-y-3">
                  {caps.map((cap: any, ci: number) => {
                    const complexity = cap.implementation_complexity || "";
                    const duration = cap.typical_duration_weeks;
                    return (
                      <div key={ci} className="border border-gray-800 rounded p-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <h5 className="text-sm font-medium text-white">{cap.name}</h5>
                            {cap.description && <p className="text-xs text-gray-300 mt-1">{cap.description}</p>}
                          </div>
                          <div className="text-right text-xs text-gray-400">
                            {complexity && <div className="mb-1">{complexity}</div>}
                            {duration != null && <div>⏱ {duration} weeks</div>}
                          </div>
                        </div>
                        {cap.business_outcomes?.length > 0 && (
                          <p className="text-xs text-gray-400 mt-2"><strong>Outcomes:</strong> {cap.business_outcomes.slice(0, 3).join(", ")}</p>
                        )}
                        {cap.risk_factors?.length > 0 && (
                          <p className="text-xs text-yellow-400 mt-1">⚠ {cap.risk_factors.slice(0, 2).join(", ")}</p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </details>
            );
          })}
        </div>
      )}
    </div>
  );
}
