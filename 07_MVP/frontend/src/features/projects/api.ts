import { jsonBody, req } from "@/shared/api/client";
import { qp } from "@/features/analysis/api";
import { Category } from "@/features/analysis/types";
import { FrameworkTemplate, Project, ProjectSummary, VistaPrevia } from "./types";

export const projectsApi = {
  listProjects: () => req<ProjectSummary[]>("/projects"),
  createProject: (form: FormData) => req<{ id: string }>("/projects", { method: "POST", body: form }),
  // Vista previa (solo lectura): detecta el tipo de cada columna sin crear nada
  preview: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return req<VistaPrevia>("/projects/preview", { method: "POST", body: form });
  },
  previewQualtrics: (survey_id: string) =>
    req<VistaPrevia>("/projects/preview/qualtrics", { method: "POST", ...jsonBody({ survey_id }) }),
  previewGoogleForms: (sheet_url: string) =>
    req<VistaPrevia>("/projects/preview/google-forms", { method: "POST", ...jsonBody({ sheet_url }) }),
  // Sin `pregunta`, el backend devuelve la primera pregunta abierta.
  getProject: (id: string, pregunta?: string) =>
    req<Project>(`/projects/${id}${pregunta ? `?${qp(pregunta)}` : ""}`),
  deleteProject: (id: string) => req<{ deleted: string }>(`/projects/${id}`, { method: "DELETE" }),
  importLegacy: () => req<{ imported: number }>("/projects/import-legacy", { method: "POST" }),

  // Plantillas de marcos teóricos
  listTemplates: () => req<FrameworkTemplate[]>("/framework-templates"),
  applyTemplate: (id: string, pregunta: string, template: string) =>
    req<{ marco_teorico: string; categories: Category[] }>(
      `/projects/${id}/apply-template?template=${encodeURIComponent(template)}&${qp(pregunta)}`, { method: "POST" }),
};

export { jsonBody };
