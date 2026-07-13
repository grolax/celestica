import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { projectsApi } from "./api";
import { Project } from "./types";

/**
 * Carga y refresco del proyecto activo + contexto para las pestañas.
 * `useProjectData(id)` hace el fetch; `useProject()` lo consume desde
 * cualquier página hija de ProjectView.
 */

interface ProjectCtx {
  project: Project;
  refresh: () => void;
}

export const ProjectContext = createContext<ProjectCtx | null>(null);

export function useProject(): ProjectCtx {
  const ctx = useContext(ProjectContext);
  if (!ctx) throw new Error("useProject debe usarse dentro de <ProjectView>");
  return ctx;
}

export function useProjectData(id: string | undefined) {
  const [project, setProject] = useState<Project | null>(null);
  const [error, setError] = useState("");

  const refresh = useCallback(() => {
    if (!id) return;
    projectsApi.getProject(id).then(setProject).catch((e) => setError(e.message));
  }, [id]);
  useEffect(refresh, [refresh]);

  return { project, error, refresh };
}
