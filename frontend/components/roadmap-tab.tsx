"use client";

import { useMemo } from "react";
import dynamic from "next/dynamic";
import { domainLabel, subdomainLabel, label } from "@/lib/terminology";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

const PHASE_COLORS = ["#00C5E3", "#FF5733", "#27AE60"];

function AmdMetrics({ metrics }: { metrics: any }) {
  if (!metrics) return null;
  return (
    <div className="grid grid-cols-4 gap-4 mb-6">
      <div className="bg-[#161920] border border-gray-800 rounded p-4">
        <div className="text-xs text-gray-500">{label("gpu_device")}</div>
        <div className="text-lg font-bold text-white">{metrics.gpu_device || "CPU"}</div>
      </div>
      <div className="bg-[#161920] border border-gray-800 rounded p-4">
        <div className="text-xs text-gray-500">{label("rocm_version")}</div>
        <div className="text-lg font-bold text-white">{metrics.rocm_version || "N/A"}</div>
      </div>
      <div className="bg-[#161920] border border-gray-800 rounded p-4">
        <div className="text-xs text-gray-500">{label("processing_time")}</div>
        <div className="text-lg font-bold text-white">{metrics.processing_time_seconds} s</div>
      </div>
      <div className="bg-[#161920] border border-gray-800 rounded p-4">
        <div className="text-xs text-gray-500">{label("capabilities_retrieved")}</div>
        <div className="text-lg font-bold text-white">{metrics.capabilities_retrieved ?? 0}</div>
      </div>
    </div>
  );
}

function DrlTrace({ drlTrace }: { drlTrace: any }) {
  if (!drlTrace) return null;
  const scores = drlTrace.capability_scores || [];
  if (!scores.length) return null;
  const x = scores.map((s: any) => s.score);
  const y = scores.map((s: any) => s.capability_name);
  return (
    <div className="bg-[#161920] border border-gray-800 rounded-lg p-4 mt-6">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">{label("drl_trace")}</h3>
      <Plot
        data={[
          {
            type: "bar",
            x,
            y,
            orientation: "h",
            marker: { color: x, colorscale: "Blues" },
          },
        ]}
        layout={{
          height: 350,
          margin: { l: 200, r: 20, t: 20, b: 40 },
          paper_bgcolor: "rgba(0,0,0,0)",
          plot_bgcolor: "rgba(0,0,0,0)",
          font: { color: "#ccc" },
          xaxis: { title: "Priority Score", color: "#888" },
          yaxis: { color: "#888" },
          title: { text: "AI Capability Prioritisation Scores", font: { size: 14, color: "#ccc" } },
        }}
        config={{ responsive: true, displayModeBar: false }}
        className="w-full"
      />
    </div>
  );
}

export default function RoadmapTab({ result }: { result: any }) {
  const phases = result?.phases || [];
  const totalInitiatives = phases.reduce((sum: number, p: any) => sum + (p.epics?.length || 0), 0);
  const compliance = result?.compliance_summary;

  const ganttData = useMemo(() => {
    const rows: any[] = [];
    let startMonth = 0;
    phases.forEach((phase: any) => {
      const epics = (phase.epics || []).slice(0, 6);
      epics.forEach((epic: any) => {
        const duration = (epic.estimated_sprints || 4) * 2;
        rows.push({
          Phase: `Phase ${phase.phase_number}`,
          Initiative: subdomainLabel(epic.title || "").slice(0, 45),
          Start: startMonth,
          End: startMonth + duration,
          "Capability Area": domainLabel(epic.subdomain_group || ""),
        });
      });
      startMonth += phase.duration_months || 3;
    });
    return rows;
  }, [phases]);

  return (
    <div className="space-y-6">
      <AmdMetrics metrics={result?.amd_metrics} />

      <div>
        <h2 className="text-2xl font-bold text-white">
          Strategic Roadmap — {phases.length} Phases · {totalInitiatives} {label("epics")}
        </h2>
      </div>

      {ganttData.length > 0 && (
        <div className="bg-[#161920] border border-gray-800 rounded-lg p-4">
          <Plot
            data={[
              {
                type: "bar",
                x: ganttData.map((d) => d.Start),
                y: ganttData.map((d) => d.Initiative),
                orientation: "h",
                marker: { color: ganttData.map((d) => {
                  const num = parseInt(d.Phase.match(/Phase (\d)/)?.[1] || "1");
                  return PHASE_COLORS[(num - 1) % PHASE_COLORS.length];
                }) },
              },
            ]}
            layout={{
              height: Math.max(400, ganttData.length * 25),
              margin: { l: 200, r: 20, t: 20, b: 40 },
              paper_bgcolor: "rgba(0,0,0,0)",
              plot_bgcolor: "rgba(0,0,0,0)",
              font: { color: "#ccc" },
              xaxis: { title: "Month", color: "#888" },
              yaxis: { color: "#888", autorange: "reversed" },
              title: { text: "Strategic Roadmap Timeline", font: { size: 14, color: "#ccc" } },
            }}
            config={{ responsive: true, displayModeBar: false }}
            className="w-full"
          />
        </div>
      )}

      {compliance && (
        <div className="bg-[#161920] border border-gray-800 rounded-lg p-4">
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-400">{label("compliance_score")}:</div>
            <div className={`text-2xl font-bold ${compliance.score >= 70 ? "text-green-400" : compliance.score >= 50 ? "text-yellow-400" : "text-red-400"}`}>
              {compliance.score} / 100
            </div>
            {compliance.standards_covered?.length > 0 && (
              <div className="text-xs text-gray-500">{label("standards_covered")}: {compliance.standards_covered.slice(0, 5).join(", ")}</div>
            )}
          </div>
        </div>
      )}

      <DrlTrace drlTrace={result?.drl_trace} />
    </div>
  );
}
