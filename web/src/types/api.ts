export interface ChatRequest {
  query: string;
}

export interface ChatResponse {
  answer: string;
  skill_used: string | null;
  cited_doc_ids: number[];
  grounded: boolean;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
}

export interface DocumentResponse {
  document_id: number;
  doc_title: string;
  doc_type: string | null;
  parties: string[];
  jurisdiction: string | null;
  filing_date: string | null;
  source: string;
  clauses: Clause[];
}

export interface Clause {
  clause_id: number;
  clause_type: string | null;
  clause_text: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  skill_used?: string | null;
  grounded?: boolean;
  cited_doc_ids?: number[];
  timestamp: Date;
}