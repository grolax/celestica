export interface CategoryComment {
  id: string;
  text: string;
  author: string;
  author_id?: string;
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

export interface ClaudeUsageTotals {
  calls?: number;
  input_tokens?: number;
  output_tokens?: number;
  cost_usd?: number;
}

/** Consumo acumulado de la API de Claude por proyecto (ver backend claude_log.py). */
export interface ClaudeUsage extends ClaudeUsageTotals {
  by_step?: Record<string, ClaudeUsageTotals>;
  updated_at?: string;
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

/** RF-30: GET /projects/{id}/closed-results (contrato en docs/API_CONTRATOS.md). */
export interface ClosedOpcion { valor: string; n: number; pct: number }
/** Cifras de una pregunta: las del total y las de cada grupo (RF-31) comparten forma. */
export interface ClosedMetricas {
  n_respuestas: number;
  n_na: number;
  tasa_respuesta: number;
  n_invalidas?: number;
  opciones?: ClosedOpcion[];
  nota?: string;
  escala?: {
    min: number; max: number; promedio: number; desviacion: number;
    top2?: { valores: number[]; n: number; pct: number };
    bottom2?: { valores: number[]; n: number; pct: number };
  };
  nps?: {
    valor: number;
    promotores: { n: number; pct: number };
    pasivos: { n: number; pct: number };
    detractores: { n: number; pct: number };
  };
  numerica?: { promedio: number; desviacion: number; mediana: number; min: number; max: number };
}
export interface ClosedPregunta extends ClosedMetricas {
  id: string;
  titulo: string;
  tipo: string;
  por_grupo?: (ClosedMetricas & { valor: string })[];
}
/** RF-31: grupo del cruce; `unidos` solo si viene de una unión (T-023). */
export interface ClosedGrupo { valor: string; n_personas: number; pocos_datos: boolean; unidos?: string[] }
export interface ClosedUnion { nombre: string; valores: string[] }
export interface ClosedOpciones { por: string; cortes?: string; unir?: ClosedUnion[] }
export interface ClosedResultsData {
  n_personas: number;
  preguntas: ClosedPregunta[];
  por?: { id: string; titulo: string; tipo: string };
  umbral_pocos_datos?: number;
  n_sin_grupo?: number;
  grupos?: ClosedGrupo[];
}
