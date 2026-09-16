import { jsonBody, req } from "@/shared/api/client";
import {
  AuditEvent, Category, CategoryComment, CodifyProgress, Coding,
  ClaudeUsage, LexicalResult, ProjectStats, ReportProgress, ResponseItem,
} from "./types";

export const analysisApi = {
  // Respuestas
  getResponses: (id: string, offset = 0, limit = 50) =>
    req<{ total: number; items: ResponseItem[] }>(`/projects/${id}/responses?offset=${offset}&limit=${limit}`),

  // Capa 1: léxico
  runLexical: (id: string) => req<LexicalResult>(`/projects/${id}/lexical`, { method: "POST" }),
  getLexical: (id: string) => req<LexicalResult>(`/projects/${id}/lexical`),

  // Capa 2: libro de códigos
  proposeCategories: (id: string) => req<Category[]>(`/projects/${id}/categories/propose`, { method: "POST" }),
  updateCategory: (id: string, catId: string, body: Partial<Category>) =>
    req<Category>(`/projects/${id}/categories/${catId}`, { method: "PATCH", ...jsonBody(body) }),
  createCategory: (
    id: string,
    body: { nombre: string; definicion: string; criterios_inclusion?: string; criterios_exclusion?: string; ejemplo?: string }
  ) => req<Category>(`/projects/${id}/categories`, { method: "POST", ...jsonBody(body) }),

  // Comentarios (colaboración)
  addComment: (id: string, catId: string, text: string) =>
    req<CategoryComment>(`/projects/${id}/categories/${catId}/comments`, { method: "POST", ...jsonBody({ text }) }),
  deleteComment: (id: string, catId: string, commentId: string) =>
    req<{ deleted: string }>(`/projects/${id}/categories/${catId}/comments/${commentId}`, { method: "DELETE" }),

  // Codificación
  codify: (id: string) => req<{ status: string; total: number }>(`/projects/${id}/codify`, { method: "POST" }),
  getCodifyProgress: (id: string) => req<CodifyProgress>(`/projects/${id}/codify/progress`),
  recode: (id: string, responseId: string, categoryIds: string[]) =>
    req<Coding[]>(`/projects/${id}/responses/${responseId}/codings`, {
      method: "PUT", ...jsonBody({ category_ids: categoryIds }),
    }),

  // Resultados
  summary: (id: string) => req<ProjectStats>(`/projects/${id}/summary`),
  audit: (id: string) => req<AuditEvent[]>(`/projects/${id}/audit`),
  traceability: (id: string) => req<Record<string, unknown>[]>(`/projects/${id}/export/traceability`),

  // Informe cualitativo
  /** forceFull: ignora el caché del análisis por respondente (Prompt 1) y
   *  vuelve a analizar todo el corpus — cuesta ~1 llamada a Claude por respondente. */
  generateReport: (id: string, mode: "v1" | "v2" = "v2", forceFull = false) =>
    req<{ status: string; mode: string }>(
      `/projects/${id}/report?mode=${mode}${forceFull ? "&force_full=true" : ""}`, { method: "POST" }),
  getUsage: (id: string) => req<{ project_id: string; usage: ClaudeUsage }>(`/projects/${id}/usage`),
  getReportProgress: (id: string) => req<ReportProgress>(`/projects/${id}/report/progress`),
  getReport: (id: string) => req<{ report: string }>(`/projects/${id}/report`),
};
