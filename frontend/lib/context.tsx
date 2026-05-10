"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";
import type { ChatMessage, AnalyzeResult } from "@/lib/types";

interface ChatContextValue {
  sessionId: string;
  setSessionId: (id: string) => void;
  history: ChatMessage[];
  setHistory: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  result: AnalyzeResult | null;
  setResult: React.Dispatch<React.SetStateAction<AnalyzeResult | null>>;
  lastChatSources: any[];
  setLastChatSources: React.Dispatch<React.SetStateAction<any[]>>;
  enrichInfo: { triggered: boolean; domains: string[] };
  setEnrichInfo: React.Dispatch<React.SetStateAction<{ triggered: boolean; domains: string[] }>>;
  startNewSession: () => void;
}

const ChatContext = createContext<ChatContextValue | undefined>(undefined);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [sessionId, setSessionId] = useState<string>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("chat_session_id") || uuidv4();
    }
    return uuidv4();
  });
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [lastChatSources, setLastChatSources] = useState<any[]>([]);
  const [enrichInfo, setEnrichInfo] = useState<{ triggered: boolean; domains: string[] }>({ triggered: false, domains: [] });

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("chat_session_id", sessionId);
    }
  }, [sessionId]);

  const startNewSession = useCallback(() => {
    const newId = uuidv4();
    setSessionId(newId);
    setHistory([
      {
        role: "assistant",
        content:
          "Hello! I'm your **Enterprise Architecture Advisor**, powered by **AMD MI300X** and **Qwen-72B** with live access to a knowledge graph of **1,416 capabilities across 44 domains**.\n\nI can help you:\n- Explore governance standards and compliance requirements\n- Identify the right capabilities for your organisation\n- Understand cross-domain architecture patterns\n- Generate a strategic transformation roadmap\n\nWhat would you like to explore?",
      },
    ]);
    setLastChatSources([]);
    setEnrichInfo({ triggered: false, domains: [] });
    setResult(null);
  }, []);

  return (
    <ChatContext.Provider
      value={{
        sessionId,
        setSessionId,
        history,
        setHistory,
        result,
        setResult,
        lastChatSources,
        setLastChatSources,
        enrichInfo,
        setEnrichInfo,
        startNewSession,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be used within ChatProvider");
  return ctx;
}
