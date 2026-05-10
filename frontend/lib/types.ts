export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: any[];
}

export interface AnalyzeResult {
  request_id: string;
  org_type: string;
  phases: any[];
  compliance_summary?: any;
  amd_metrics?: any;
  drl_trace?: any;
}
