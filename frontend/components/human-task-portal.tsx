"use client";

import { useState, useEffect, useCallback } from "react";

type Task = {
  task_id: string;
  assessment_id: string;
  title: string;
  description: string;
  status: string;
  assigned_to?: string;
  due_date?: string;
  priority?: string;
};

type AssessmentDetail = {
  gap_analysis?: string[];
  maturity_scores?: Record<string, number>;
  drl_ranking?: Array<{ capability: string; score: number }>;
  roadmap?: any[];
};

export default function HumanTaskPortal() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [assessmentDetail, setAssessmentDetail] = useState<AssessmentDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [overrideScores, setOverrideScores] = useState<Record<string, number>>({});
  const [comment, setComment] = useState("");

  const fetchTasks = useCallback(async () => {
    try {
      const res = await fetch("/api/backend/uipath/tasks");
      const data = await res.json();
      setTasks(data || []);
    } catch {
      setTasks([]);
    }
  }, []);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const fetchAssessmentDetail = async (task_id: string, assessment_id: string) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/backend/uipath/assessment/${assessment_id}`);
      const data = await res.json();
      setAssessmentDetail(data);
    } catch {
      setAssessmentDetail(null);
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (decision: "approve" | "reject" | "escalate") => {
    if (!selectedTask) return;

    await fetch("/api/backend/uipath/task-complete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        task_id: selectedTask.task_id,
        assessment_id: selectedTask.assessment_id,
        decision,
        override_scores: decision === "approve" && Object.keys(overrideScores).length ? overrideScores : undefined,
        comment,
      }),
    });

    setTasks(tasks.filter((t) => t.task_id !== selectedTask.task_id));
    setSelectedTask(null);
    setAssessmentDetail(null);
    setOverrideScores({});
    setComment("");
  };

  const handleOverride = async () => {
    if (!selectedTask || !comment) return;
    await handleDecision("approve");
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Human Task Portal</h2>
        <p className="text-gray-400 text-sm">Review and approve capability assessments with human oversight</p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-[#161920] border border-gray-800 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-4">Pending Tasks</h3>
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {tasks.length === 0 && <p className="text-gray-500 text-sm">No pending tasks</p>}
            {tasks.map((task) => (
              <button
                key={task.task_id}
                onClick={() => {
                  setSelectedTask(task);
                  fetchAssessmentDetail(task.task_id, task.assessment_id);
                }}
                className={`w-full text-left p-3 rounded border transition-colors ${
                  selectedTask?.task_id === task.task_id
                    ? "border-blue-500 bg-blue-900/20"
                    : "border-gray-700 hover:bg-gray-800/50"
                }`}
              >
                <div className="font-medium text-white">{task.title}</div>
                <div className="text-xs text-gray-400 mt-1">{task.description}</div>
                <div className="flex gap-2 mt-2">
                  <span className="text-xs px-2 py-1 rounded bg-gray-700 text-gray-300">
                    {task.priority || "medium"}
                  </span>
                  {task.due_date && (
                    <span className="text-xs text-gray-500">Due: {task.due_date}</span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="bg-[#161920] border border-gray-800 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-4">Assessment Detail</h3>
          {loading && <p className="text-gray-400">Loading...</p>}
          {!loading && selectedTask && assessmentDetail && (
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-semibold text-white mb-2">Gap Analysis</h4>
                <ul className="text-xs text-gray-300 list-disc list-inside">
                  {(assessmentDetail.gap_analysis || []).map((gap, i) => (
                    <li key={i}>{gap}</li>
                  ))}
                </ul>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-white mb-2">Maturity Scores</h4>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(assessmentDetail.maturity_scores || {}).map(([domain, score]) => (
                    <div key={domain} className="flex justify-between text-xs">
                      <span className="text-gray-400">{domain}</span>
                      <span className="text-white font-mono">{score}/100</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-white mb-2">DRL Prioritisation</h4>
                <div className="space-y-1 max-h-[150px] overflow-y-auto">
                  {(assessmentDetail.drl_ranking || []).slice(0, 5).map((r, i) => (
                    <div key={i} className="flex justify-between text-xs">
                      <span className="text-gray-400 truncate">{r.capability}</span>
                      <span className="text-white font-mono">{r.score.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border-t border-gray-700 pt-4 space-y-3">
                <h4 className="text-sm font-semibold text-white">Decision Panel</h4>

                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Add comment for override (required)..."
                  className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-xs text-white placeholder-gray-500"
                  rows={2}
                />

                <div className="flex gap-2">
                  <button
                    onClick={() => handleDecision("approve")}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 rounded text-xs font-medium"
                  >
                    Approve
                  </button>
                  <button
                    onClick={handleOverride}
                    disabled={!comment}
                    className="flex-1 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-700 text-white py-2 rounded text-xs font-medium"
                  >
                    Override
                  </button>
                  <button
                    onClick={() => handleDecision("reject")}
                    className="flex-1 bg-red-600 hover:bg-red-700 text-white py-2 rounded text-xs font-medium"
                  >
                    Reject
                  </button>
                  <button
                    onClick={() => handleDecision("escalate")}
                    className="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-2 rounded text-xs font-medium"
                  >
                    Escalate
                  </button>
                </div>
              </div>
            </div>
          )}
          {!loading && !selectedTask && <p className="text-gray-500 text-sm">Select a task to review</p>}
        </div>
      </div>
    </div>
  );
}