"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useChat } from "@/lib/context";

const WELCOME =
  "Hello! I'm your **Enterprise Architecture Advisor** with live access to a knowledge graph of **capabilities across 44 domains**.\n\nI can help you:\n- Explore governance standards and compliance requirements\n- Identify the right capabilities for your organisation\n- Understand cross-domain architecture patterns\n- Generate a strategic transformation roadmap\n\nWhat would you like to explore?";

const ROADMAP_KEYWORDS = new Set([
  "roadmap", "strategy", "strategic", "plan", "planning",
  "implement", "transform", "programme", "program", "initiative",
]);

const splitThink = (text: string): [string, string] => {
  if (!text) return ["", ""];
  const start = text.indexOf("<th");
  if (start === -1) return ["", text];
  const thinkEnd = text.indexOf(">", start + 3);
  if (thinkEnd === -1) return [text.slice(start + 4).trim(), ""];
  const end = text.indexOf("</th", thinkEnd);
  if (end === -1) return [text.slice(thinkEnd + 1).trim(), ""];
  const thinkContent = text.slice(thinkEnd + 1, end).trim();
  const response = (text.slice(0, start) + text.slice(end + 5)).trim();
  return [thinkContent, response];
};

export default function ChatTab() {
  const { sessionId, setSessionId, history, setHistory, setResult, setLastChatSources, enrichInfo, setEnrichInfo, startNewSession } = useChat();
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [sessions, setSessions] = useState<any[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!history.length) {
      setHistory([{ role: "assistant" as const, content: WELCOME }]);
    }
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  const loadSessions = useCallback(async () => {
    try {
      const res = await fetch("/api/backend/chat/sessions");
      const data = await res.json();
      setSessions(Array.isArray(data) ? data : []);
    } catch {}
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleNewSession = () => {
    startNewSession();
    loadSessions();
  };

  const handleLoadSession = async (sid: string) => {
    try {
      const res = await fetch(`/api/backend/chat/sessions/${sid}/messages`);
      const data = await res.json();
      const msgs = (data.messages || []).map((m: any) => ({
        role: m.role,
        content: m.content,
        sources: m.sources || [],
      }));
      setSessionId(sid);
      setHistory(msgs);
      setLastChatSources([]);
      setEnrichInfo({ triggered: false, domains: [] });
    } catch {}
  };

  const handleDeleteSession = async (sid: string) => {
    await fetch(`/api/backend/chat/sessions/${sid}`, { method: "DELETE" });
    if (sid === sessionId) handleNewSession();
    else loadSessions();
  };

  const sendMessage = async () => {
    if (!input.trim() || streaming) return;
    const userMessage = input.trim();
    setInput("");
    setHistory((prev) => [...prev, { role: "user", content: userMessage }]);

    abortRef.current = new AbortController();

    try {
      setStreaming(true);
      const historyForApi = history
        .filter((m) => m.role === "user" || (m.role === "assistant" && !m.content.includes("Enterprise Architecture Advisor")))
        .map((m) => ({ role: m.role, content: m.content }));

      const res = await fetch(
        `/api/backend/chat/stream?message=${encodeURIComponent(userMessage)}&history=${encodeURIComponent(JSON.stringify(historyForApi))}&session_id=${sessionId}`,
        { signal: abortRef.current.signal }
      );

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let full = "";
      let assistantIndex = -1;

      setHistory((prev) => {
        const next = [...prev, { role: "assistant" as const, content: "" }];
        assistantIndex = next.length - 1;
        return next;
      });

      if (!reader) throw new Error("No stream");

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        for (const line of chunk.split("\n")) {
          if (!line.startsWith("data: ")) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.text) {
              full += event.text;
              const [think, response] = splitThink(full);
              setHistory((prev) => {
                const copy = [...prev];
                if (copy[assistantIndex]) {
                  copy[assistantIndex] = {
                    ...copy[assistantIndex],
                    content: think ? `<details style="margin-bottom:0.5rem"><summary style="cursor:pointer;color:#9ca3af;font-size:0.85rem">💭 Reasoning (click to expand / collapse)</summary>\n\n${think}\n\n</details>${response}`
                    : response || full,
                  };
                }
                return copy;
});
            }
            if (event.done) {
              setLastChatSources(event.sources || []);
              setEnrichInfo({ triggered: !!event.enrich_triggered, domains: event.enrich_domains || [] });
            }
          } catch {}
        }
      }

      const [finalThink, finalResponse] = splitThink(full);
      const cleanReply = finalResponse || (finalThink ? "" : full);
      setHistory((prev) => {
        const copy = [...prev];
        if (copy[assistantIndex]) copy[assistantIndex].content = cleanReply;
        return copy;
      });

      if (ROADMAP_KEYWORDS.has(userMessage.toLowerCase())) {
        setResult({} as any);
      }
    } catch (exc: any) {
      if (exc.name !== "AbortError") {
        // Fallback non-streaming
        const historyForApi = history.filter((m) => m.role === "user" || (m.role === "assistant" && !m.content.includes("Enterprise Architecture Advisor"))).map((m) => ({ role: m.role, content: m.content }));
        try {
          const res = await fetch("/api/backend/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userMessage, history: historyForApi, session_id: sessionId }),
          });
          const data = await res.json();
          setHistory((prev) => [...prev, { role: "assistant", content: data.reply || "Error: no reply" }]);
          setLastChatSources(data.sources || []);
          setEnrichInfo({ triggered: !!data.enrich_triggered, domains: data.enrich_domains || [] });
        } catch {
          setHistory((prev) => [...prev, { role: "assistant", content: "Error contacting EA Advisor." }]);
        }
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
      loadSessions();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">EA Advisor</h2>
        <p className="text-gray-400 text-sm">Conversational AI for enterprise architecture — Knowledge Graph RAG · 1,416 capabilities</p>
      </div>

      <div className="flex gap-6">
        <div className="flex-1">
          <div className="bg-[#161920] border border-gray-800 rounded-lg p-4 h-[600px] flex flex-col">
            <div className="flex-1 overflow-y-auto space-y-4 mb-4">
              {history.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[80%] rounded-lg px-4 py-2 text-sm whitespace-pre-wrap ${
                    msg.role === "user" ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-200"
                  }`}>
                    {msg.role === "assistant" && msg.content.includes("<think>") ? (
                      <div dangerouslySetInnerHTML={{ __html: msg.content }} />
                    ) : (
                      <div dangerouslySetInnerHTML={{ __html: msg.content.replace(/\n/g, "<br/>") }} />
                    )}
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>

            <div className="flex gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about enterprise architecture, governance, or capabilities…"
                className="flex-1 bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                rows={2}
              />
              <button
                onClick={sendMessage}
                disabled={streaming || !input.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white px-4 py-2 rounded text-sm font-medium"
              >
                {streaming ? "…" : "Send"}
              </button>
            </div>
          </div>
        </div>

        <div className="w-80 space-y-4">
          <div className="bg-[#161920] border border-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-white mb-2">Conversation History</h3>
            <button onClick={handleNewSession} className="w-full bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium py-2 rounded mb-3">
              New Conversation
            </button>
            <div className="space-y-1 max-h-[400px] overflow-y-auto">
              {sessions.length === 0 && <p className="text-xs text-gray-500">No saved conversations yet.</p>}
              {sessions.map((s) => (
                <div key={s.session_id} className="flex items-center justify-between group">
                  <button
                    onClick={() => handleLoadSession(s.session_id)}
                    className={`text-xs text-left truncate flex-1 py-1 px-2 rounded hover:bg-gray-800 ${s.session_id === sessionId ? "text-blue-400 bg-gray-800" : "text-gray-300"}`}
                  >
                    {s.title || "Untitled"}
                  </button>
                  <button
                    onClick={() => handleDeleteSession(s.session_id)}
                    className="text-xs text-gray-500 hover:text-red-400 px-1 opacity-0 group-hover:opacity-100"
                  >
                    🗑
                  </button>
                </div>
              ))}
            </div>
          </div>

          {enrichInfo.triggered && (
            <div className="bg-[#161920] border border-blue-900 rounded-lg p-3">
              <p className="text-xs text-blue-300">🧠 DRL enrichment started for: {enrichInfo.domains.join(", ")}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
