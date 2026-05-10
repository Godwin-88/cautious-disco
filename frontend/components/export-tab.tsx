"use client";

import { useMemo, useState } from "react";
import { label, subdomainLabel, acBadge } from "@/lib/terminology";

function toJiraJson(result: any) {
  const issues: any[] = [];
  (result.phases || []).forEach((phase: any) => {
    (phase.epics || []).forEach((epic: any) => {
      issues.push({
        externalId: epic.epic_id,
        issueType: "Epic",
        summary: epic.title,
        description: epic.description,
        labels: [subdomainLabel(epic.subdomain_group || "")],
        customField_EpicName: epic.title,
        priority: phase.phase_number === 1 ? "High" : "Medium",
      });
      (epic.features || []).forEach((feat: any) => {
        (feat.user_stories || []).forEach((story: any) => {
          const role = story.role || story.as_a || "User";
          const want = story.want || story.i_want || "";
          const soThat = story.so_that || "";
          issues.push({
            externalId: `${epic.epic_id}-${feat.title?.slice(0, 10) || ""}-${role.slice(0, 5)}`,
            issueType: "Story",
            summary: `As a ${role}, I want ${want}`,
            description: `As a ${role}, I want ${want}, so that ${soThat}`,
            acceptanceCriteria: (story.acceptance_criteria || []).map((ac: string) => `- ${ac}`).join("\\n"),
            epicLink: epic.epic_id,
          });
        });
      });
    });
  });
  return JSON.stringify({ projects: [{ issues }] }, null, 2);
}

function toCsv(result: any) {
  const rows: string[] = ["Phase,Initiative ID,Title,Capability Area,Sprints,Governance,Innovation,AC Count"];
  (result.phases || []).forEach((phase: any) => {
    (phase.epics || []).forEach((epic: any) => {
      rows.push([
        `Phase ${phase.phase_number} — ${phase.phase_name}`,
        epic.epic_id,
        epic.title,
        subdomainLabel(epic.subdomain_group || ""),
        epic.estimated_sprints ?? "",
        epic.governance_reference || "",
        epic.trend_alignment || "",
        (epic.acceptance_criteria || []).length,
      ].join(","));
    });
  });
  return rows.join("\\n");
}

function toMarkdown(result: any) {
  const lines: string[] = [`# Enterprise Architecture Strategic Roadmap — ${result.org_type || ""}\\n`];
  (result.phases || []).forEach((phase: any) => {
    lines.push(`\\n## Phase ${phase.phase_number}: ${phase.phase_name}`);
    lines.push(`Duration: ${phase.duration_months || 0} months\\n`);
    (phase.epics || []).forEach((epic: any) => {
      lines.push(`### ${epic.epic_id} — ${epic.title}`);
      if (epic.subdomain_group) lines.push(`*${label("subdomain")}: ${subdomainLabel(epic.subdomain_group)}*\\n`);
      if (epic.description) lines.push(epic.description + "\\n");
      if (epic.governance_reference) lines.push(`**${label("governance_reference")}:** ${epic.governance_reference}\\n`);
      if (epic.trend_alignment) lines.push(`**${label("trend_alignment")}:** ${epic.trend_alignment}\\n`);
      lines.push(`**Delivery Sprints:** ${epic.estimated_sprints ?? "—"}\\n`);
      if (epic.acceptance_criteria?.length) {
        lines.push(`**${label("acceptance_criteria")}:**\\n`);
        epic.acceptance_criteria.forEach((ac: string) => lines.push(`- [ ] ${acBadge(ac)}`));
        lines.push("");
      }
      (epic.features || []).forEach((feat: any) => {
        lines.push(`#### ${label("feature")}: ${feat.title}`);
        (feat.user_stories || []).forEach((story: any) => {
          const role = story.role || "User";
          const want = story.want || "";
          const soThat = story.so_that || "";
          lines.push(`- **${label("user_story")}** — As a **${role}**, I want ${want}, so that ${soThat}`);
        });
      });
    });
  });
  return lines.join("\\n");
}

export default function ExportTab({ result }: { result: any }) {
  const [format, setFormat] = useState<"json" | "csv" | "md">("json");

  const content = useMemo(() => {
    if (!result) return "";
    if (format === "json") return toJiraJson(result);
    if (format === "csv") return toCsv(result);
    return toMarkdown(result);
  }, [result, format]);

  const filename = format === "json" ? "ea_roadmap_jira.json" : format === "csv" ? "ea_roadmap.csv" : "ea_roadmap.md";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Export & Handover</h2>
      </div>
      <div className="flex gap-2">
        {(["json", "csv", "md"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFormat(f)}
            className={`px-4 py-2 rounded text-sm font-medium ${format === f ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-300 hover:bg-gray-700"}`}
          >
            {f.toUpperCase()}
          </button>
        ))}
      </div>
      <a
        href={`data:text/plain;charset=utf-8,${encodeURIComponent(content)}`}
        download={filename}
        className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm"
      >
        Download {format.toUpperCase()}
      </a>
      <pre className="bg-[#161920] border border-gray-800 rounded p-4 text-xs text-gray-300 overflow-auto max-h-96">{content.slice(0, 3000)}{content.length > 3000 ? "…" : ""}</pre>
    </div>
  );
}
