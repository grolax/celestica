import { jsonBody, req } from "@/shared/api/client";
import { Category } from "@/features/analysis/types";
import { FrameworkTemplate, Project, ProjectSummary } from "./types";

export const projectsApi = {
  listProjects: () => req<ProjectSummary[]>("/projects"),
  createProject: (form: FormData) => req<{ id: string }>("/projects", { method: "POST", body: form }),
  getProject: (id: string) => req<Project>(`/projects/${id}`),
  deleteProject: (id: string) => req<{ deleted: string }>(`/projects/${id}`, { method: "DELETE" }),
  importLegacy: () => req<{ imported: number }>("/projects/import-legacy", { method: "POST" }),

  // Plantillas de marcos teóricos
  listTemplates: () => req<FrameworkTemplate[]>("/framework-templates"),
  applyTemplate: (id: string, template: string) =>
    req<{ marco_teorico: string; categories: Category[] }>(
      `/projects/${id}/apply-template?template=${encodeURIComponent(template)}`, { method: "POST" }),
};

export { jsonBody };
