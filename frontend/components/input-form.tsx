"use client";

import { useState, useEffect } from "react";

export default function InputForm({ onSubmit }: { onSubmit: (payload: any) => void }) {
  const [allDomains, setAllDomains] = useState<any[]>([]);
  const [selectedDomainNames, setSelectedDomainNames] = useState<string[]>([]);
  const [subdomains, setSubdomains] = useState<any[]>([]);
  const [selectedSubdomainIds, setSelectedSubdomainIds] = useState<string[]>([]);
  const [capabilities, setCapabilities] = useState<any[]>([]);
  const [selectedCapIds, setSelectedCapIds] = useState<string[]>([]);
  const [orgType, setOrgType] = useState("");
  const [budgetTier, setBudgetTier] = useState("medium");
  const [riskTolerance, setRiskTolerance] = useState("medium");
  const [timelineMonths, setTimelineMonths] = useState(18);
  const [goalsText, setGoalsText] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/backend/domains")
      .then((r) => r.json())
      .then(setAllDomains)
      .catch(() => setAllDomains([]));
  }, []);

  useEffect(() => {
    if (selectedDomainNames.length === 0) {
      setSubdomains([]);
      setSelectedSubdomainIds([]);
      setCapabilities([]);
      setSelectedCapIds([]);
      return;
    }
    const params = new URLSearchParams();
    selectedDomainNames.forEach((name) => params.append("domain_names", name));
    fetch(`/api/backend/subdomains?${params}`)
      .then((r) => r.json())
      .then((data) => {
        setSubdomains(Array.isArray(data) ? data : []);
        setSelectedSubdomainIds((data as any[]).map((d: any) => d.id));
      })
      .catch(() => { setSubdomains([]); setSelectedSubdomainIds([]); });
  }, [selectedDomainNames]);

  useEffect(() => {
    if (selectedSubdomainIds.length === 0) {
      setCapabilities([]);
      setSelectedCapIds([]);
      return;
    }
    const params = new URLSearchParams();
    selectedSubdomainIds.forEach((id) => params.append("subdomain_ids", id));
    fetch(`/api/backend/subdomain-capabilities?${params}`)
      .then((r) => r.json())
      .then((data) => {
        setCapabilities(Array.isArray(data) ? data : []);
        setSelectedCapIds((data as any[]).map((c: any) => c.id));
      })
      .catch(() => { setCapabilities([]); setSelectedCapIds([]); });
  }, [selectedSubdomainIds]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!orgType.trim()) {
      setError("Please enter your Organisation Type.");
      return;
    }
    if (selectedDomainNames.length === 0 && selectedCapIds.length === 0) {
      setError("Please select at least one Strategic Domain in Step 1.");
      return;
    }
    const extraGoals = goalsText.split(",").map((g) => g.trim()).filter(Boolean);
    const goals = extraGoals.length ? extraGoals : [`Transform ${orgType} digital capabilities`];

    onSubmit({
      org_type: orgType.trim(),
      goals,
      budget_tier: budgetTier,
      timeline_months: timelineMonths,
      risk_tolerance: riskTolerance,
      sector_focus: selectedDomainNames,
      selected_capability_ids: selectedCapIds,
      selected_subdomain_ids: selectedSubdomainIds,
    });
  };

  const complexityCounts = capabilities.reduce(
    (acc: any, c: any) => {
      const cx = (c.complexity || "").toLowerCase();
      if (cx === "high" || cx === "very_high") acc.high++;
      else if (cx === "medium") acc.med++;
      else if (cx === "low") acc.low++;
      return acc;
    },
    { high: 0, med: 0, low: 0 }
  );

  return (
    <div className="bg-[#161920] border border-gray-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-1">Assessment Intake</h2>
      <p className="text-gray-400 text-sm mb-6">Configure your organisation profile and let the AI generate a digital capability roadmap.</p>

      {error && <div className="bg-red-900/30 border border-red-800 text-red-300 text-sm p-3 rounded mb-4">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Step 1 — Select Strategic Domains</label>
          <div className="max-h-[200px] overflow-y-auto border border-gray-700 rounded bg-gray-900 p-2">
            <div className="grid grid-cols-2 gap-2">
              {allDomains.map((d) => {
                const dn = d.name || d.id;
                return (
                  <label key={d.id} className="flex items-center gap-2 cursor-pointer hover:bg-gray-800 p-2 rounded">
                    <input
                      type="checkbox"
                      checked={selectedDomainNames.includes(dn)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedDomainNames([...selectedDomainNames, dn]);
                        } else {
                          setSelectedDomainNames(selectedDomainNames.filter(x => x !== dn));
                        }
                      }}
                      className="w-4 h-4 text-blue-600 bg-gray-800 border-gray-600 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-white">{dn.replace("Manage ", "")}</span>
                  </label>
                );
              })}
            </div>
          </div>
          {allDomains.length > 0 && (
            <p className="text-xs text-gray-500 mt-1">Click to select multiple domains</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Step 2 — Capability Areas (from selected domains)</label>
          <div className="max-h-[150px] overflow-y-auto border border-gray-700 rounded bg-gray-900 p-2">
            {subdomains.length > 0 ? (
              <div className="grid grid-cols-2 gap-2">
                {subdomains.map((sd: any) => (
                  <label key={sd.id} className="flex items-center gap-2 cursor-pointer hover:bg-gray-800 p-2 rounded">
                    <input
                      type="checkbox"
                      checked={selectedSubdomainIds.includes(sd.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedSubdomainIds([...selectedSubdomainIds, sd.id]);
                        } else {
                          setSelectedSubdomainIds(selectedSubdomainIds.filter(x => x !== sd.id));
                        }
                      }}
                      className="w-4 h-4 text-blue-600 bg-gray-800 border-gray-600 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-white truncate">{sd.name?.replace(/Manage |Digital /g, "") || sd.id}</span>
                  </label>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-500 p-2">Select domains above to see capability areas</p>
            )}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Step 3 — Select Strategic Capabilities</label>
          <div className="max-h-[150px] overflow-y-auto border border-gray-700 rounded bg-gray-900 p-2">
            {capabilities.length > 0 ? (
              <div className="grid grid-cols-2 gap-2">
                {capabilities.map((c: any) => (
                  <label key={c.id} className="flex items-center gap-2 cursor-pointer hover:bg-gray-800 p-2 rounded">
                    <input
                      type="checkbox"
                      checked={selectedCapIds.includes(c.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedCapIds([...selectedCapIds, c.id]);
                        } else {
                          setSelectedCapIds(selectedCapIds.filter(x => x !== c.id));
                        }
                      }}
                      className="w-4 h-4 text-blue-600 bg-gray-800 border-gray-600 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-white truncate">{c.name}</span>
                  </label>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-500 p-2">Select capability areas to see specific capabilities</p>
            )}
          </div>
          {capabilities.length > 0 && (
            <p className="text-xs text-gray-500 mt-1">
              Selected: {capabilities.length} capabilities &middot; 
              🔴 {complexityCounts.high} high &middot; 🟡 {complexityCounts.med} medium &middot; 🟢 {complexityCounts.low} low
            </p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Organisation Type</label>
            <input
              type="text"
              value={orgType}
              onChange={(e) => setOrgType(e.target.value)}
              placeholder="e.g. Commercial Bank, Healthcare Provider"
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Budget Tier</label>
            <select value={budgetTier} onChange={(e) => setBudgetTier(e.target.value)} className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Risk Tolerance</label>
            <select value={riskTolerance} onChange={(e) => setRiskTolerance(e.target.value)} className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Timeline (months)</label>
            <input type="number" value={timelineMonths} onChange={(e) => setTimelineMonths(Number(e.target.value))} min={6} max={36} step={3} className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Additional Strategic Goals (optional)</label>
          <textarea
            value={goalsText}
            onChange={(e) => setGoalsText(e.target.value)}
            placeholder="e.g. Achieve ISO 27001 certification, Deploy AI-driven fraud detection"
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 h-24"
          />
        </div>

        <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded text-sm">
          Run Assessment
        </button>
      </form>
    </div>
  );
}