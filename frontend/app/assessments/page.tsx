"use client";

import { useState, useEffect } from "react";

export default function AssessmentsPage() {
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
    <div className="p-8 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Assessments Dashboard</h2>
        <p className="text-gray-400 text-sm">All past and in-progress capability assessments</p>
      </div>

      {loading && <p className="text-gray-400">Loading assessments...</p>}

      {!loading && assessments.length === 0 && (
        <div className="bg-[#161920] border border-gray-800 rounded-lg p-6 text-center">
          <p className="text-gray-500">No assessments yet. Create your first assessment in Canvas.</p>
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}