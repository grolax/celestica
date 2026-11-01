import { jsonBody, req } from "@/shared/api/client";
import {
  AuditEvent, Category, ClosedResultsData, CategoryComment, CodifyProgress, Coding,
  ClaudeUsage, ClosedOpciones, LexicalResult, ProjectStats, ReportProgress, ResponseItem,
} from "./types";

/** Parámetro `?pregunta=` que el contrato RF-23 exige en toda operación de análisis. */
export const qp = (pregunta: string) => `pregunta=${encodeURIComponent(pregunta)}`;

/** Query de "Ver por…" compartida por closed-results y export/closed-xlsx: misma codificación en ambos. */
export const closedQuery = (o?: ClosedOpciones) => o
  ? `?por=${encodeURIComponent(o.por)}`
    + (o.cortes !== undefined ? `&cortes=${encodeURIComponent(o.cortes)}` : "")
    + (o.unir?.length ? `&unir=${encodeURIComponent(JSON.stringify(o.unir))}` : "")
  : "";

export const analysisApi = {
  // Respuestas
  getResponses: (id: string, pregunta: string, offset = 0, limit = 50) =>
    req<{ total: number; items: ResponseItem[] }>(`/projects/${id}/responses?offset=${offset}&limit=${limit}&${qp(pregunta)}`),

  // Capa 1: léxico
  runLexical: (id: string, pregunta: string) => req<LexicalResult>(`/projects/${id}/lexical?${qp(pregunta)}`, { method: "POST" }),
  getLexical: (id: string, pregunta: string) => req<LexicalResult>(`/projects/${id}/lexical?${qp(pregunta)}`),

  // Capa 2: libro de códigos
  proposeCategories: (id: string, pregunta: string) =>
    req<Category[]>(`/projects/${id}/categories/propose?${qp(pregunta)}`, { method: "POST" }),
  updateCategory: (id: string, pregunta: string, catId: string, body: Partial<Category>) =>
    req<Category>(`/projects/${id}/categories/${catId}?${qp(pregunta)}`, { method: "PATCH", ...jsonBody(body) }),
  createCategory: (
    id: string,
    pregunta: string,
    body: { nombre: string; definicion: string; criterios_inclusion?: string; criterios_exclusion?: string; ejemplo?: string }
  ) => req<Category>(`/projects/${id}/categories?${qp(pregunta)}`, { method: "POST", ...jsonBody(body) }),

  // Comentarios (colaboración)
  addComment: (id: string, pregunta: string, catId: string, text: string) =>
    req<CategoryComment>(`/projects/${id}/categories/${catId}/comments?${qp(pregunta)}`, { method: "POST", ...jsonBody({ text }) }),
  deleteComment: (id: string, pregunta: string, catId: string, commentId: string) =>
    req<{ deleted: string }>(`/projects/${id}/categories/${catId}/comments/${commentId}?${qp(pregunta)}`, { method: "DELETE" }),

  // Codificación
  codify: (id: string, pregunta: string) =>
    req<{ status: string; total: number }>(`/projects/${id}/codify?${qp(pregunta)}`, { method: "POST" }),
  getCodifyProgress: (id: string, pregunta: string) =>
    req<CodifyProgress>(`/projects/${id}/codify/progress?${qp(pregunta)}`),
  recode: (id: string, pregunta: string, responseId: string, categoryIds: string[]) =>
    req<Coding[]>(`/projects/${id}/responses/${responseId}/codings?${qp(pregunta)}`, {
      method: "PUT", ...jsonBody({ category_ids: categoryIds }),
    }),

  // Resultados
  summary: (id: string, pregunta: string) => req<ProjectStats>(`/projects/${id}/summary?${qp(pregunta)}`),
  audit: (id: string) => req<AuditEvent[]>(`/projects/${id}/audit`),
  traceability: (id: string, pregunta: string) =>
    req<Record<string, unknown>[]>(`/projects/${id}/export/traceability?${qp(pregunta)}`),

  // Preguntas cerradas (RF-30): no recibe `pregunta`. RF-31: `por`, `cortes` y `unir` separan en grupos.
  getClosedResults: (id: string, o?: ClosedOpciones) =>
    req<ClosedResultsData>(`/projects/${id}/closed-results${closedQuery(o)}`),

  // Informe cualitativo
  /** forceFull: ignora el caché del análisis por respondente (Prompt 1) y
   *  vuelve a analizar todo el corpus — cuesta ~1 llamada a Claude por respondente. */
  generateReport: (id: string, pregunta: string, mode: "v1" | "v2" = "v2", forceFull = false) =>
    req<{ status: string; mode: string }>(
      `/projects/${id}/report?mode=${mode}${forceFull ? "&force_full=true" : ""}&${qp(pregunta)}`, { method: "POST" }),
  getUsage: (id: string) => req<{ project_id: string; usage: ClaudeUsage }>(`/projects/${id}/usage`),
  getReportProgress: (id: string, pregunta: string) =>
    req<ReportProgress>(`/projects/${id}/report/progress?${qp(pregunta)}`),
  getReport: (id: string, pregunta: string) => req<{ report: string }>(`/projects/${id}/report?${qp(pregunta)}`),
};
