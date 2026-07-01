"use client";

import { useEffect, useRef, useState } from "react";

type Edge = { source: string; target: string };

function getSector(domainName: string): string {
  const lower = domainName.toLowerCase();
  if (lower.includes("digital it") || lower.includes("security") || lower.includes("intelligence")) return "IT";
  if (lower.includes("healthcare") || lower.includes("health")) return "Healthcare";
  if (lower.includes("banking") || lower.includes("financial") || lower.includes("capital")) return "Finance";
  if (lower.includes("government") || lower.includes("court") || lower.includes("justice")) return "Government";
  if (lower.includes("oil") || lower.includes("energy") || lower.includes("electricity")) return "Energy";
  if (lower.includes("logistics") || lower.includes("transport") || lower.includes("airport")) return "Logistics";
  return "Other";
}

function getSectorColor(sector: string): string {
  const colors: Record<string, string> = {
    IT: "#3b82f6", Healthcare: "#22c55e", Finance: "#f59e0b",
    Government: "#a855f7", Energy: "#f97316", Logistics: "#ef4444", Other: "#6b7280"
  };
  return colors[sector] || "#6b7280";
}

export default function EnablesNetworkGraph() {
  const networkRef = useRef<HTMLDivElement>(null);
  const [nodes, setNodes] = useState<any[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  useEffect(() => {
    fetch("/api/backend/graph/enables")
      .then((r) => r.json())
      .then((data) => {
        const edgeList = data as Edge[];
        setEdges(edgeList);
        
        const nodeList = Array.from(new Set(edgeList.flatMap(e => [e.source, e.target]))).map((name, idx) => ({
          id: idx,
          label: name.replace("Manage ", ""),
          sector: getSector(name),
          enables_count: edgeList.filter((e) => e.source === name).length,
        }));
        setNodes(nodeList);
      })
      .catch(() => setNodes([]));
  }, []);

  useEffect(() => {
    if (!networkRef.current || nodes.length === 0) return;

    let network: any;
    import("vis-network").then(({ DataSet, Network }) => {
      const container = networkRef.current!;
      container.innerHTML = "";
      
      const dataSetNodes = new DataSet(
        nodes.map((n) => ({
          id: n.id,
          label: n.label,
          color: { background: getSectorColor(n.sector), border: "#fff" },
          size: 15 + (n.enables_count || 0) * 2,
        }))
      );
      const dataSetEdges = new DataSet(
        edges.map((e, idx) => ({
          id: `edge-${idx}`,
          from: nodes.find((n) => e.source.includes(n.label) || n.label.includes(e.source.replace("Manage ", "")))?.id ?? 0,
          to: nodes.find((n) => e.target.includes(n.label) || n.label.includes(e.target.replace("Manage ", "")))?.id ?? 0,
          arrows: "to",
          color: { color: "#f39c12", highlight: "#f59e0b" },
        }))
      );

      network = new Network(container, { nodes: dataSetNodes, edges: dataSetEdges }, {
        height: "500px",
        physics: { stabilization: true, repulsion: { nodeDistance: 150 } },
      });
    }).catch(() => {
      if (networkRef.current) {
        networkRef.current.innerHTML = '<div class="flex items-center justify-center h-full text-gray-500">vis-network unavailable</div>';
      }
    });

    return () => {
      if (network) network.destroy();
    };
  }, [nodes, edges]);

  return (
    <div className="bg-[#161920] border border-gray-800 rounded-lg p-4">
      <div ref={networkRef} className="w-full" style={{ minHeight: "500px", background: "#111" }} />
    </div>
  );
}
