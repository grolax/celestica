export interface CategoryComment {
  id: string;
  text: string;
  author: string;
  timestamp: string;
}

export interface Category {
  id: string;
  nombre: string;
  definicion: string;
  criterios_inclusion: string;
  criterios_exclusion: string;
  ejemplo: string;
  origen: string;
  status: "propuesta" | "validada" | "descartada";
  comments?: CategoryComment[];
}

export interface Coding {
  category_id: string;
  rationale: string;
  confidence: number;
  source: string;
  status: string;
}

export interface ResponseItem {
  id: string;
  text: string;
  meta: Record<string, string>;
  sentiment: { score: number; label: string; evidencia_positiva: string[]; evidencia_negativa: string[] } | null;
  codings: Coding[];
}

export interface LexicalResult {
  n_responses: number;
  top_terms: { term: string; count: number }[];
  top_bigrams: { bigram: string; count: number }[];
  top_cooccurrences: { pair: string; count: number }[];
  sentiment_distribution: Record<string, number>;
  method_note: string;
  interpretation?: string;
}

export interface CodifyProgress {
  status: "idle" | "running" | "done" | "error";
  done?: number;
  total?: number;
  coded?: number;
  assignments?: number;
  error?: string;
}

export interface ReportProgress {
  status: "idle" | "running" | "done" | "error";
  done?: number;
  total?: number;
  section?: string;
  error?: string;
}

export interface ProjectStats {
  by_category: { category_id: string; nombre: string; count: number }[];
  sentiment_distribution: Record<string, number>;
  confidence_distribution: { alta: number; media: number; baja: number };
  n_responses: number;
  n_coded: number;
  n_categories_validated: number;
  has_lexical: boolean;
  has_report: boolean;
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  detail: unknown;
}
