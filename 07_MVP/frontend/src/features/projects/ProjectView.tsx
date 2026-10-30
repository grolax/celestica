import { NavLink, Outlet, useParams } from "react-router-dom";
import { useAuth } from "@/features/auth/useAuth";
import { puede } from "@/features/auth/api";
import { ProjectContext, useProjectData } from "./useProjectData";

const TABS: [string, string][] = [
  ["", "Dashboard"],
  ["lexico", "Análisis léxico"],
  ["codigos", "Libro de códigos"],
  ["codificacion", "Codificación"],
  ["trazabilidad", "Trazabilidad"],
  ["informe", "Informe"],
  ["exportar", "Exportar"],
  ["auditoria", "Auditoría"],
];

export default function ProjectView() {
  const { id } = useParams<{ id: string }>();
  const { project, error, refresh } = useProjectData(id);
  const canEdit = puede(useAuth().user, "analista");

  if (error) return <div className="alert alert-error">{error}</div>;
  if (!project) return <p className="muted">Cargando proyecto…</p>;

  return (
    <ProjectContext.Provider value={{ project, refresh }}>
      <div style={{ marginBottom: 4 }}>
        <h1 style={{ marginBottom: 2 }}>{project.name}{!canEdit && <> <span className="pill neutro">Solo lectura</span></>}</h1>
        <p className="muted small">
          {project.n_responses} respuestas · columna de texto: <code>{project.text_column}</code>
          {project.marco_teorico && <> · Marco: {project.marco_teorico.slice(0, 110)}{project.marco_teorico.length > 110 ? "…" : ""}</>}
        </p>
      </div>
      <div className="project-tabs">
        {TABS.map(([path, label]) => (
          <NavLink key={path} to={path} end={path === ""}
                   className={({ isActive }) => `project-tab ${isActive ? "active" : ""}`}>
            {label}
          </NavLink>
        ))}
      </div>
      <Outlet />
    </ProjectContext.Provider>
  );
}
