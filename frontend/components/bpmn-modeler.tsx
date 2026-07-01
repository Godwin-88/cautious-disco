"use client";

// Import bpmn-js CSS - must be imported here for proper bundling
import "bpmn-js/dist/assets/diagram-js.css";
import "bpmn-js/dist/assets/bpmn-js.css";

import { useEffect, useRef, useState, useCallback } from "react";

type BpmnModelerProps = {
  xml: string;
  onChange: (xml: string) => void;
  onSave: (xml: string) => void;
  model: { id: string; name: string } | null;
  theme?: "dark" | "light";
};

export default function BpmnModeler({ xml, onChange, onSave, model, theme = "dark" }: BpmnModelerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const modelerRef = useRef<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  const initModeler = useCallback(async () => {
    if (!containerRef.current) return null;
    try {
      const BpmnJS = (await import("bpmn-js/lib/Modeler")).default;
      const modeler = new BpmnJS({
        container: containerRef.current,
      });
      return modeler;
    } catch (err) {
      console.error("Failed to create modeler:", err);
      return null;
    }
  }, []);

  const destroyModeler = useCallback(() => {
    if (modelerRef.current) {
      try {
        modelerRef.current.destroy();
      } catch {
        // ignore destroy errors
      }
      modelerRef.current = null;
    }
  }, []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    destroyModeler();

    initModeler().then(async (mdl) => {
      if (!active) return;
      if (!mdl || !containerRef.current) {
        setLoading(false);
        return;
      }
      try {
        modelerRef.current = mdl;
        const { warnings } = await mdl.importXML(xml);
        if (warnings?.length) {
          console.warn("BPMN import warnings:", warnings);
        }

        // Fit the diagram to the viewport - use requestAnimationFrame to ensure
        // the container has rendered dimensions before zooming
        requestAnimationFrame(() => {
          try {
            const canvas = mdl.get("canvas");
            canvas.zoom("fit-viewport");
          } catch (zoomErr) {
            console.warn("BPMN zoom fit failed (non-critical):", zoomErr);
          }
        });

        // Listen for changes
        mdl.on("commandStack.changed", async () => {
          try {
            const { xml: newXml } = await mdl.saveXML({ format: true });
            onChange(newXml);
          } catch {
            // ignore save errors during editing
          }
        });

        setLoading(false);
      } catch (err: any) {
        const msg = err?.message || err?.toString() || "Unknown error";
        console.error("Failed to load BPMN:", err);
        // Extract meaningful error from bpmn-js import errors
        const detail = err?.warnings?.length
          ? err.warnings.map((w: any) => w.message || w).join("; ")
          : msg;
        setError(`Failed to load BPMN diagram: ${detail}`);
        setLoading(false);
      }
    });

    return () => {
      active = false;
      destroyModeler();
    };
    // We intentionally only re-init when xml changes and is a new model
  }, [xml, initModeler, destroyModeler, onChange]);

  const handleSave = async () => {
    if (!modelerRef.current) return;
    setSaving(true);
    try {
      const { xml: savedXml } = await modelerRef.current.saveXML({ format: true });
      onSave(savedXml);
    } catch {
      setError("Failed to save BPMN");
    } finally {
      setSaving(false);
    }
  };

  const handleDownload = async (format: "bpmn" | "svg") => {
    if (!xml) return;
    if (format === "bpmn") {
      const blob = new Blob([xml], { type: "application/xml" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${model?.name || "diagram"}.bpmn`;
      a.click();
      URL.revokeObjectURL(url);
    } else if (format === "svg" && modelerRef.current) {
      try {
        const { svg } = await modelerRef.current.saveSVG();
        const blob = new Blob([svg], { type: "image/svg+xml" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${model?.name || "diagram"}.svg`;
        a.click();
        URL.revokeObjectURL(url);
      } catch {
        setError("SVG export failed");
      }
    }
  };

  const handleUndo = () => {
    try {
      modelerRef.current?.get("commandStack").undo();
    } catch {
      // ignore
    }
  };
  const handleRedo = () => {
    try {
      modelerRef.current?.get("commandStack").redo();
    } catch {
      // ignore
    }
  };

  const bg = theme === "dark" ? "#1a1d27" : "#ffffff";
  const border = theme === "dark" ? "#374151" : "#d1d5e7";
  const textColor = theme === "dark" ? "#e5e7eb" : "#111827";

  return (
    <div className="flex flex-col h-full rounded-lg overflow-hidden" style={{ backgroundColor: bg, border: `1px solid ${border}` }}>
      {/* Toolbar */}
      <div className="flex justify-between items-center p-3 flex-wrap gap-2" style={{ borderBottom: `1px solid ${border}`, backgroundColor: bg }}>
        <div className="text-sm font-medium truncate" style={{ color: textColor }}>
          {model?.name || "Untitled Model"}
        </div>
        <div className="flex gap-2 flex-wrap">
          <button onClick={handleUndo}
            className="px-3 py-1.5 rounded text-xs font-medium transition-colors"
            style={{ backgroundColor: theme === "dark" ? "#374151" : "#e5e7eb", color: textColor }}
            title="Undo (Ctrl+Z)">Undo</button>
          <button onClick={handleRedo}
            className="px-3 py-1.5 rounded text-xs font-medium transition-colors"
            style={{ backgroundColor: theme === "dark" ? "#374151" : "#e5e7eb", color: textColor }}
            title="Redo (Ctrl+Shift+Z)">Redo</button>
          <button onClick={() => handleDownload("bpmn")}
            className="px-3 py-1.5 rounded text-xs font-medium transition-colors"
            style={{ backgroundColor: theme === "dark" ? "#374151" : "#e5e7eb", color: textColor }}>
            BPMN</button>
          <button onClick={() => handleDownload("svg")}
            className="px-3 py-1.5 rounded text-xs font-medium transition-colors"
            style={{ backgroundColor: theme === "dark" ? "#374151" : "#e5e7eb", color: textColor }}>
            SVG</button>
          <button onClick={handleSave} disabled={saving}
            className="px-4 py-1.5 rounded text-xs font-medium text-white transition-colors disabled:opacity-50"
            style={{ backgroundColor: saving ? "#6b7280" : "#3b82f6" }}>
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="px-3 py-2 text-xs" style={{ backgroundColor: "#7f1d1d", color: "#fca5a5" }}>
          {error}
          <button onClick={() => setError(null)} className="ml-2 font-bold">✕</button>
        </div>
      )}

      {/* Modeler container - always visible so bpmn-js can measure dimensions */}
      <div className="flex-1 relative" style={{ minHeight: "500px", height: "100%" }}>
        {/* Loading overlay */}
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center z-10" style={{ backgroundColor: theme === "dark" ? "#111" : "#f9fafb" }}>
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: theme === "dark" ? "#374151" : "#d1d5e7", borderTopColor: "#3b82f6" }} />
              <span className="text-xs" style={{ color: theme === "dark" ? "#9ca3af" : "#6b7280" }}>Loading BPMN editor...</span>
            </div>
          </div>
        )}
        <div ref={containerRef} className="w-full h-full" style={{
          backgroundColor: theme === "dark" ? "#111827" : "#ffffff",
        }} />
      </div>

      {/* Empty state fallback */}
      {!loading && !error && !model && (
        <div className="flex items-center justify-center flex-1" style={{ minHeight: "500px", backgroundColor: theme === "dark" ? "#111827" : "#ffffff" }}>
          <p className="text-sm" style={{ color: theme === "dark" ? "#9ca3af" : "#6b7280" }}>
            No model loaded. Create or select a model from the sidebar.
          </p>
        </div>
      )}
    </div>
  );
}