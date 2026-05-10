"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { domainLabel } from "@/lib/terminology";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export default function TrainingTab() {
  const [coverage, setCoverage] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any[]>([]);
  const [episodes, setEpisodes] = useState(50);
  const [domainFilter, setDomainFilter] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    fetch("/api/backend/training/coverage").then((r) => r.json()).then(setCoverage).catch(() => {});
    fetch("/api/backend/training/metrics").then((r) => r.json()).then(setMetrics).catch(() => {});
  }, []);

  const handleRun = async () => {
    setRunning(true);
    setResult(null);
    try {
      const res = await fetch("/api/backend/training/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ episodes_per_domain: Number(episodes), domain: domainFilter || null }),
      });
      setResult(await res.json());
    } catch {}
    setRunning(false);
  };

  const trained = coverage.filter((d) => d.drl_trained).length;
  const stdEnriched = coverage.filter((d) => d.standard_enriched).length;
  const trendEnriched = coverage.filter((d) => d.trend_enriched).length;
  const rewards = metrics.filter((m) => m.final_reward != null).map((m) => Number(m.final_reward));
  const avg = rewards.length ? (rewards.reduce((a, b) => a + b, 0) / rewards.length).toFixed(4) : null;

  const heatZ = coverage.map((d) => [d.standard_enriched ? 1 : 0, d.trend_enriched ? 1 : 0, d.drl_trained ? 1 : 0]);
  const heatY = coverage.map((d) => domainLabel(d.domain));
  const heatX = ["Governance Framework", "Innovation Driver", "AI Trained"];

  const lineX = metrics.map((_, i) => i);
  const lineY = metrics.map((m) => m.final_reward);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white">AI Learning Engine</h2>
        <p className="text-gray-400 text-sm max-w-4xl">
          The AI Prioritisation Engine trains on every strategic domain in the knowledge graph. Each learning session is recorded as a node in Neo4j — the graph continuously improves itself.
        </p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="bg-[#161920] border border-gray-800 rounded p-4 text-center">
          <div className="text-2xl font-bold text-white">{trained} / {coverage.length}</div>
          <div className="text-xs text-gray-400">Strategic Domains Trained</div>
        </div>
        <div className="bg-[#161920] border border-gray-800 rounded p-4 text-center">
          <div className="text-2xl font-bold text-white">{stdEnriched} / {coverage.length}</div>
          <div className="text-xs text-gray-400">Governance Frameworks Enriched</div>
        </div>
        <div className="bg-[#161920] border border-gray-800 rounded p-4 text-center">
          <div className="text-2xl font-bold text-white">{trendEnriched} / {coverage.length}</div>
          <div className="text-xs text-gray-400">Innovation Drivers Enriched</div>
        </div>
        <div className="bg-[#161920] border border-gray-800 rounded p-4 text-center">
          <div className="text-2xl font-bold text-white">{avg ?? "—"}</div>
          <div className="text-xs text-gray-400">Avg Prioritisation Reward</div>
        </div>
      </div>

      {coverage.length > 0 && (
        <div className="bg-[#161920] border border-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Knowledge Graph Enrichment Coverage</h3>
          <Plot
            data={[
              {
                type: "heatmap",
                z: heatZ,
                x: heatX,
                y: heatY,
                colorscale: [[0, "#e74c3c"], [0.5, "#f39c12"], [1, "#27ae60"]],
                zmin: 0,
                zmax: 1,
                showscale: false,
                xgap: 2,
                ygap: 1,
              },
            ]}
            layout={{
              height: Math.max(400, heatY.length * 14),
              margin: { l: 200, r: 20, t: 20, b: 20 },
              paper_bgcolor: "rgba(0,0,0,0)",
              plot_bgcolor: "rgba(0,0,0,0)",
              font: { color: "#ccc" },
              yaxis: { tickfont: { size: 10 } },
            }}
            config={{ responsive: true, displayModeBar: false }}
            className="w-full"
          />
        </div>
      )}

      {metrics.length > 0 && (
        <div className="bg-[#161920] border border-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">AI Prioritisation Reward Progression</h3>
          <Plot
            data={[
              {
                type: "scatter",
                mode: "markers",
                x: lineX,
                y: lineY,
                name: "Final Reward",
                marker: { color: metrics.map((m: any) => m.sector) },
              },
              {
                type: "scatter",
                mode: "lines",
                x: lineX,
                y: metrics.map((_, i) => {
                  const window = metrics.slice(Math.max(0, i - 4), i + 1).map((m: any) => m.final_reward);
                  const avg = window.reduce((a: number, b: number) => a + b, 0) / window.length;
                  return avg;
                }),
                name: "5-run avg",
                line: { color: "white", width: 2, dash: "dash" },
              },
            ]}
            layout={{
              height: 350,
              margin: { t: 20, b: 20 },
              paper_bgcolor: "rgba(0,0,0,0)",
              plot_bgcolor: "rgba(0,0,0,0)",
              font: { color: "#ccc" },
              xaxis: { title: "Training Run #", color: "#888" },
              yaxis: { title: "Final Reward", color: "#888" },
            }}
            config={{ responsive: true, displayModeBar: false }}
            className="w-full"
          />
        </div>
      )}

      <div className="bg-[#161920] border border-gray-800 rounded-lg p-6 space-y-4">
        <h3 className="text-lg font-semibold text-white">Run AI Learning Session</h3>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Learning episodes per domain</label>
            <input type="number" value={episodes} onChange={(e) => setEpisodes(Number(e.target.value))} min={10} max={500} step={10} className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Specific domain (blank = all)</label>
            <input value={domainFilter} onChange={(e) => setDomainFilter(e.target.value)} placeholder="e.g. Healthcare Provider" className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white" />
          </div>
          <div className="flex items-end">
            <button onClick={handleRun} disabled={running} className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white px-4 py-2 rounded text-sm">
              {running ? "Running…" : "Run AI Learning Session"}
            </button>
          </div>
        </div>
        {result && (
          <div className={`text-sm ${result.status === "started" ? "text-green-300" : "text-red-300"}`}>
            {result.status === "started"
              ? `Training started (run_id: ${result.run_id}). Metrics appear as each domain completes.`
              : `Failed: ${result.message || result}`}
          </div>
        )}
      </div>

      {metrics.length > 0 && (
        <div className="bg-[#161920] border border-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-2">Latest AI Learning Sessions</h3>
          <div className="overflow-auto">
            <table className="w-full text-sm">
              <thead className="text-gray-500 text-xs border-b border-gray-800">
                <tr>
                  <th className="text-left py-2">Domain</th>
                  <th className="text-left py-2">Sector</th>
                  <th className="text-left py-2">Episodes</th>
                  <th className="text-left py-2">Reward</th>
                  <th className="text-left py-2">Device</th>
                  <th className="text-left py-2">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {metrics.slice(0, 20).map((m: any, i: number) => (
                  <tr key={i} className="border-b border-gray-800">
                    <td className="py-2 text-white">{domainLabel(m.domain_name)}</td>
                    <td className="py-2 text-gray-400">{m.sector}</td>
                    <td className="py-2 text-gray-400">{m.episodes}</td>
                    <td className="py-2 text-white font-mono">{m.final_reward?.toFixed(4)}</td>
                    <td className="py-2 text-gray-400">{m.device}</td>
                    <td className="py-2 text-gray-500">{(m.ts || "").slice(0, 19)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
