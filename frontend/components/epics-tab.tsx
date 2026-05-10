"use client";

import { subdomainLabel, label, acBadge } from "@/lib/terminology";

export default function EpicsTab({ result }: { result: any }) {
  const phases = result?.phases || [];
  if (!phases.length) {
    return <div className="bg-[#161920] border border-gray-800 rounded-lg p-6 text-gray-400 text-sm">No strategic initiatives generated yet. Generate a roadmap first.</div>;
  }

  return (
    <div className="space-y-4">
      {phases.map((phase: any) => {
        const epics = phase.epics || [];
        return (
          <details key={phase.phase_number} className="bg-[#161920] border border-gray-800 rounded-lg" open={phase.phase_number === 1}>
            <summary className="p-4 text-lg font-semibold text-white cursor-pointer hover:bg-gray-800/50 rounded-t-lg">
              Phase {phase.phase_number}: {phase.phase_name} — {epics.length} {label("epics")}
            </summary>
            <div className="px-4 pb-4 space-y-6">
              {phase.objectives?.length > 0 && (
                <div className="text-sm text-gray-300">
                  <strong>Phase Objectives:</strong>
                  <ul className="list-disc list-inside mt-1 space-y-1">
                    {phase.objectives.map((o: string, i: number) => <li key={i}>{o}</li>)}
                  </ul>
                </div>
              )}

              {epics.map((epic: any) => (
                <div key={epic.epic_id} className="border-t border-gray-800 pt-4">
                  <h3 className="text-lg font-bold text-white mb-1">{epic.epic_id} — {epic.title}</h3>
                  {epic.subdomain_group && <p className="text-xs text-gray-500 mb-2">{label("subdomain")}: {subdomainLabel(epic.subdomain_group)}</p>}

                  <div className="grid grid-cols-3 gap-4">
                    <div className="col-span-2 space-y-2">
                      {epic.description && <p className="text-sm text-gray-300">{epic.description}</p>}
                      {epic.business_value && <p className="text-sm"><span className="text-gray-400">{label("business_value")}:</span> <span className="text-white">{epic.business_value}</span></p>}
                      {epic.strategic_rationale && <p className="text-sm"><span className="text-gray-400">{label("strategic_rationale")}:</span> <span className="text-white">{epic.strategic_rationale}</span></p>}
                    </div>
                    <div className="space-y-2">
                      {epic.governance_reference && (
                        <div className="bg-blue-900/20 border border-blue-800 rounded p-3 text-sm text-blue-200">{label("governance_reference")}: {epic.governance_reference}</div>
                      )}
                      {epic.trend_alignment && (
                        <div className="bg-green-900/20 border border-green-800 rounded p-3 text-sm text-green-200">{label("trend_alignment")}: {epic.trend_alignment}</div>
                      )}
                      <div className="text-sm text-gray-400">Delivery Sprints: <span className="text-white font-mono">{epic.estimated_sprints ?? "—"}</span></div>
                    </div>
                  </div>

                  {epic.acceptance_criteria?.length > 0 && (
                    <details className="mt-3">
                      <summary className="text-sm text-gray-300 cursor-pointer">{label("acceptance_criteria")} ({epic.acceptance_criteria.length})</summary>
                      <ul className="mt-2 space-y-1">
                        {epic.acceptance_criteria.map((ac: string, i: number) => (
                          <li key={i} className="text-sm text-gray-400 flex items-start gap-2">
                            <input type="checkbox" className="mt-1" />
                            <span>{acBadge(ac)}</span>
                          </li>
                        ))}
                      </ul>
                    </details>
                  )}

                  {epic.risk_register?.length > 0 && (
                    <details className="mt-3">
                      <summary className="text-sm text-yellow-400 cursor-pointer">{label("risk_register")} ({epic.risk_register.length})</summary>
                      <ul className="mt-2 space-y-1">
                        {epic.risk_register.map((r: string, i: number) => <li key={i} className="text-sm text-yellow-200">⚠ {r}</li>)}
                      </ul>
                    </details>
                  )}

                  {epic.features?.length > 0 && (
                    <details className="mt-3">
                      <summary className="text-sm text-gray-300 cursor-pointer">{label("features")} ({epic.features.length})</summary>
                      <div className="mt-2 space-y-3">
                        {epic.features.map((feat: any, fi: number) => (
                          <div key={fi} className="border border-gray-800 rounded p-3">
                            <h4 className="text-sm font-semibold text-white">{feat.title}</h4>
                            {feat.description && <p className="text-xs text-gray-400 mt-1">{feat.description}</p>}
                            {feat.technical_notes && <p className="text-xs text-blue-300 mt-1">Technical Notes: {feat.technical_notes}</p>}
                            {(feat.user_stories || []).map((story: any, si: number) => (
                              <div key={si} className="mt-2 pl-3 border-l-2 border-gray-700">
                                <p className="text-sm text-gray-300 italic">
                                  <strong>{label("user_story")}:</strong> As a <strong>{story.role}</strong>, I want <strong>{story.want || story.i_want}</strong>, so that <strong>{story.so_that}</strong>
                                </p>
                                {story.acceptance_criteria?.length > 0 && (
                                  <ul className="mt-1 ml-4 list-disc text-xs text-gray-400">
                                    {story.acceptance_criteria.map((ac: string, aci: number) => <li key={aci}>{acBadge(ac)}</li>)}
                                  </ul>
                                )}
                                {story.tasks?.length > 0 && (
                                  <details className="mt-1">
                                    <summary className="text-xs text-gray-500 cursor-pointer">Tasks ({story.tasks.length})</summary>
                                    <ul className="mt-1 ml-4 list-disc text-xs text-gray-400">
                                      {story.tasks.map((t: any, ti: number) => (
                                        <li key={ti}>{typeof t === "string" ? t : `${t.title || t.name || `Task ${ti+1}`}${t.assignee_role ? ` (${t.assignee_role})` : ""}${t.estimated_days ? ` — ${t.estimated_days} days` : ""}`}</li>
                                      ))}
                                    </ul>
                                  </details>
                                )}
                              </div>
                            ))}
                          </div>
                        ))}
                      </div>
                    </details>
                  )}
                </div>
              ))}
            </div>
          </details>
        );
      })}
    </div>
  );
}
