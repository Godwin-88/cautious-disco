"use client";

import HumanTaskPortal from "@/components/human-task-portal";

export default function ReviewPage() {
  return (
    <div className="p-8 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Review Portal</h2>
        <p className="text-gray-400 text-sm">Human-in-the-loop review and approval of AI-generated roadmaps</p>
      </div>
      <HumanTaskPortal />
    </div>
  );
}