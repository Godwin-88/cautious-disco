"use client";

import TrainingTab from "@/components/training-tab";

export default function AnalyticsPage() {
  return (
    <div className="p-8 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Analytics</h2>
        <p className="text-gray-400 text-sm">Platform metrics and assessment analytics</p>
      </div>
      <TrainingTab />
    </div>
  );
}