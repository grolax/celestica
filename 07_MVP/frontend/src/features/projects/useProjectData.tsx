import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { projectsApi } from "./api";
import { Project } from "./types";

/**
 * Carga y refresco del proyecto activo + contexto para las pestañas.
 * `useProjectData(id, pregunta)` hace el fetch de esa pregunta (sin ella, la primera abierta); `useProject()` lo consume desde
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

export function useProjectData(id: string | undefined, pregunta?: string) {
  const [project, setProject] = useState<Project | null>(null);
  const [error, setError] = useState("");
  const latest = useRef(pregunta);
  latest.current = pregunta;

  const refresh = useCallback(() => {
    if (!id) return;
    setError("");
    projectsApi.getProject(id, pregunta).then((p) => {
      // Si el usuario ya cambió de pregunta, esta respuesta es vieja: no se mezcla.
      if (latest.current === pregunta) setProject(p);
    }).catch((e) => { if (latest.current === pregunta) setError(e.message); });
  }, [id, pregunta]);
  useEffect(refresh, [refresh]);

  return { project, error, refresh };
}
