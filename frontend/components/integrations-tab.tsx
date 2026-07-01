"use client";

import { useState, useEffect } from "react";

const SAMPLE_CSV = `org_type,business_unit,system_name,vendor,capabilities_in_use,annual_budget_usd\nEnterprise Bank,Finance,SAP S/4HANA,SAP,"General Ledger Management,Financial Reporting",2400000\n`;

export default function IntegrationsTab({ result }: { result?: any }) {
  const [jiraUrl, setJiraUrl] = useState("");
  const [jiraEmail, setJiraEmail] = useState("");
  const [jiraToken, setJiraToken] = useState("");
  const [projectKey, setProjectKey] = useState("EAOPT");
  const [jiraLoading, setJiraLoading] = useState(false);
  const [jiraResult, setJiraResult] = useState<any>(null);

  const [snUrl, setSnUrl] = useState("");
  const [snUser, setSnUser] = useState("");
  const [snPass, setSnPass] = useState("");
  const [snLoading, setSnLoading] = useState(false);
  const [snResult, setSnResult] = useState<any>(null);

  const [adoOrg, setAdoOrg] = useState("");
  const [adoPat, setAdoPat] = useState("");
  const [adoLoading, setAdoLoading] = useState(false);
  const [adoResult, setAdoResult] = useState<any>(null);

  const [erpPreview, setErpPreview] = useState<any[]>([]);
  const [erpFile, setErpFile] = useState<File | null>(null);

  const [archimateData, setArchestrateData] = useState<any>(null);

  useEffect(() => {
    fetch("/api/backend/integrations/archimate")
      .then((r) => r.json())
      .then(setArchestrateData)
      .catch(() => {});
  }, []);

  const phases = result?.phases || [];

  const handleJiraExport = async () => {
    setJiraLoading(true);
    try {
      const res = await fetch("/api/backend/integrations/jira/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jira_url: jiraUrl, jira_email: jiraEmail, jira_api_token: jiraToken, project_key: projectKey, phases }),
      });
      setJiraResult(await res.json());
    } catch {}
    setJiraLoading(false);
  };

  const handleSnConnect = async () => {
    setSnLoading(true);
    try {
      const res = await fetch("/api/backend/integrations/itsm/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tool: "servicenow", instance_url: snUrl || "https://demo.service-now.com", credentials: { username: snUser, password: snPass } }),
      });
      setSnResult(await res.json());
    } catch {}
    setSnLoading(false);
  };

  const handleAdoConnect = async () => {
    setAdoLoading(true);
    try {
      const res = await fetch("/api/backend/integrations/itsm/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tool: "azure_devops", instance_url: adoOrg || "https://dev.azure.com/demo", credentials: { pat: adoPat } }),
      });
      setAdoResult(await res.json());
    } catch {}
    setAdoLoading(false);
  };

  const handleErpUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    setErpFile(file || null);
    if (!file) return setErpPreview([]);
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result as string;
      const lines = text.split("\n");
      const headers = lines[0].split(",");
      const rows = lines.slice(1, 4).map((line) => {
        const vals = line.match(/(".*?"|[^",\s]+)(?=\s*,|\s*$)/g) || [];
        return Object.fromEntries(headers.map((h, i) => [h.trim(), vals[i]?.replace(/"/g, "") || ""]));
      });
      setErpPreview(rows);
    };
    reader.readAsText(file);
  };

  const handleErpIngest = async () => {
    if (!erpFile) return;
    const form = new FormData();
    form.append("file", erpFile);
    const res = await fetch("/api/backend/integrations/erp/ingest", { method: "POST", body: form });
    const data = await res.json();
    alert(`Ingested ${data.rows_ingested} rows, ${data.systems_found} systems, ${data.capabilities_linked} capabilities linked.`);
  };

  const layer = (archimateData as any)?.["business"] ? "business" : (archimateData as any)?.["application"] ? "application" : "technology";
  const layerData = archimateData ? archimateData[layer] || [] : [];

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white">Platform Integrations</h2>
        <p className="text-gray-400 text-sm">Connect your EA roadmap to ITSM tools, ingest ERP/CRM system inventories, and view capabilities mapped to ArchiMate architecture layers.</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <button className="bg-blue-900/30 border border-blue-800 rounded p-3 text-left">
          <div className="text-sm font-semibold text-blue-300">Jira Cloud ✓ Live</div>
        </button>
        <button className="bg-gray-800 border border-gray-700 rounded p-3 text-left">
          <div className="text-sm font-semibold text-gray-400">ServiceNow Mock</div>
        </button>
        <button className="bg-gray-800 border border-gray-700 rounded p-3 text-left">
          <div className="text-sm font-semibold text-gray-400">Azure DevOps Mock</div>
        </button>
      </div>

      <div className="bg-[#161920] border border-gray-800 rounded-lg p-6 space-y-4">
        <h3 className="text-lg font-semibold text-white">Jira Cloud — Live Export</h3>
        <div className="grid grid-cols-2 gap-4">
          <input value={jiraUrl} onChange={(e) => setJiraUrl(e.target.value)} placeholder="Jira URL" className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white" />
          <input value={jiraEmail} onChange={(e) => setJiraEmail(e.target.value)} placeholder="Email" className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white" />
          <input value={jiraToken} onChange={(e) => setJiraToken(e.target.value)} type="password" placeholder="API Token" className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white" />
          <input value={projectKey} onChange={(e) => setProjectKey(e.target.value)} className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white" />
        </div>
        <button
          onClick={handleJiraExport}
          disabled={jiraLoading || !phases.length || !jiraUrl || !jiraEmail || !jiraToken}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white px-4 py-2 rounded text-sm"
        >
          {jiraLoading ? "Exporting…" : "Export Roadmap to Jira"}
        </button>
        {!phases.length && <p className="text-xs text-gray-500">Generate a roadmap first to enable Jira export.</p>}
        {jiraResult && (
          <div className="text-sm text-green-300">
            Created {jiraResult.created_epics || 0} Epics and {jiraResult.created_stories || 0} Stories in `{projectKey}`.
            {jiraResult.errors?.length > 0 && <p className="text-yellow-300">Warnings: {jiraResult.errors.slice(0, 2).join(", ")}</p>}
          </div>
        )}
      </div>

      <div className="bg-[#161920] border border-gray-800 rounded-lg p-6 space-y-4">
        <h3 className="text-lg font-semibold text-white">ServiceNow — Integration Preview</h3>
        <div className="grid grid-cols-3 gap-4">
          <input value={snUrl} onChange={(e) => setSnUrl(e.target.value)} placeholder="Instance URL" className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white" />
          <input value={snUser} onChange={(e) => setSnUser(e.target.value)} placeholder="Username" className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white" />
          <input value={snPass} onChange={(e) => setSnPass(e.target.value)} type="password" placeholder="Password" className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white" />
        </div>
        <button onClick={handleSnConnect} disabled={snLoading} className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm">Test Connection</button>
        {snResult && <p className="text-sm text-green-300">Connected · {snResult.sample_work_items?.length || 0} sample work items retrieved</p>}
      </div>

      <div className="bg-[#161920] border border-gray-800 rounded-lg p-6 space-y-4">
        <h3 className="text-lg font-semibold text-white">Azure DevOps — Integration Preview</h3>
        <div className="grid grid-cols-2 gap-4">
          <input value={adoOrg} onChange={(e) => setAdoOrg(e.target.value)} placeholder="Organisation URL" className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white" />
          <input value={adoPat} onChange={(e) => setAdoPat(e.target.value)} type="password" placeholder="PAT" className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white" />
        </div>
        <button onClick={handleAdoConnect} disabled={adoLoading} className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm">Test Connection</button>
        {adoResult && <p className="text-sm text-green-300">Connected · {adoResult.sample_work_items?.length || 0} sample items retrieved</p>}
      </div>

      <div className="bg-[#161920] border border-gray-800 rounded-lg p-6 space-y-4">
        <h3 className="text-lg font-semibold text-white">ERP / CRM Data Ingest</h3>
        <p className="text-sm text-gray-400">Upload a system inventory CSV to link external systems to the knowledge graph.</p>
        <textarea readOnly value={SAMPLE_CSV} className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-xs text-gray-300 h-24" />
        <input type="file" accept=".csv" onChange={handleErpUpload} className="text-sm text-gray-300" />
        {erpPreview.length > 0 && (
          <div className="text-xs text-gray-400">Preview: {erpPreview.length} rows</div>
        )}
        <button onClick={handleErpIngest} disabled={!erpFile} className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white px-4 py-2 rounded text-sm">Ingest into Knowledge Graph</button>
      </div>

      <div className="bg-[#161920] border border-gray-800 rounded-lg p-6 space-y-4">
        <h3 className="text-lg font-semibold text-white">ArchiMate Architecture Layer View</h3>
        <p className="text-sm text-gray-400">Enterprise capabilities mapped to ArchiMate 3.1 layers.</p>
        {archimateData && (
          <div className="overflow-auto max-h-96 border border-gray-800 rounded">
            <table className="w-full text-sm">
              <thead className="bg-gray-900 text-gray-400">
                <tr>
                  <th className="text-left p-2">Layer</th>
                  <th className="text-left p-2">Capability</th>
                  <th className="text-left p-2">Domain</th>
                </tr>
              </thead>
              <tbody>
                {layerData.map((item: any, i: number) => (
                  <tr key={i} className="border-t border-gray-800">
                    <td className="p-2 text-white">{layer}</td>
                    <td className="p-2 text-gray-300">{item.name}</td>
                    <td className="p-2 text-gray-400">{item.domain}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
