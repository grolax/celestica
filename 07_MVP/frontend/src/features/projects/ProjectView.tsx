import { Link, Navigate, NavLink, Outlet, useLocation, useParams, useSearchParams } from "react-router-dom";
import { useAuth } from "@/features/auth/useAuth";
import { puede } from "@/features/auth/api";
import { ProjectContext, useProjectData } from "./useProjectData";
import { CERRADAS } from "./questionGroups";
import { ProjectAbierta } from "./types";

const TABS: [string, string][] = [
  ["", "Dashboard"],
  ["cerradas", "Preguntas cerradas"],
  ["lexico", "Análisis léxico"],
  ["codigos", "Libro de códigos"],
  ["codificacion", "Codificación"],
  ["trazabilidad", "Trazabilidad"],
  ["informe", "Informe"],
  ["exportar", "Exportar"],
  ["auditoria", "Auditoría"],
];

// Sin preguntas abiertas (RF-24) solo sirven estas pestañas.
const SOLO_CERRADAS = ["cerradas", "auditoria"];

const corto = (t: string) => (t.length > 70 ? `${t.slice(0, 70)}…` : t);

export default function ProjectView() {
  const { id } = useParams<{ id: string }>();
  const [params, setParams] = useSearchParams();
  const subruta = useLocation().pathname.split("/").filter(Boolean)[2] ?? ""; // /proyectos/<id>/<subruta>
  const urlPregunta = params.get("pregunta") ?? undefined;
  const { project, error, refresh } = useProjectData(id, urlPregunta);
  const canEdit = puede(useAuth().user, "analista");
  const search = urlPregunta ? `?pregunta=${encodeURIComponent(urlPregunta)}` : "";

  if (error) return (
    <div className="alert alert-error">
      {error} <Link to={`/proyectos/${id}`}>Volver al proyecto</Link>
    </div>
  );
  if (!project) return <p className="muted">Cargando proyecto…</p>;

  const soloCerradas = project.pregunta === null;
  if (soloCerradas && !SOLO_CERRADAS.includes(subruta)) return <Navigate to={`/proyectos/${id}/cerradas`} replace />;

  const abiertas = project.preguntas.filter((q) => q.tipo === "abierta");
  const actual = project.preguntas.find((q) => q.id === project.pregunta);
  // Las pestañas solo se muestran cuando ya cargó la pregunta pedida: así nunca mezclan dos preguntas.
  const cargando = !!urlPregunta && urlPregunta !== project.pregunta;

  // Sin abiertas solo se montan "cerradas" y "auditoría", que no usan `pregunta`.
  return (
    <ProjectContext.Provider value={{ project: project as ProjectAbierta, refresh }}>
      <div style={{ marginBottom: 4 }}>
        <h1 style={{ marginBottom: 2 }}>{project.name}{!canEdit && <> <span className="pill neutro">Solo lectura</span></>}</h1>
        <p className="muted small">
          {soloCerradas ? `${project.n_responses} personas · Solo preguntas cerradas`
            : `${project.n_responses} respuestas · Pregunta: ${actual?.titulo ?? project.text_column}`}
          {project.marco_teorico && <> · Marco: {project.marco_teorico.slice(0, 110)}{project.marco_teorico.length > 110 ? "…" : ""}</>}
        </p>
      </div>
      {abiertas.length >= 2 && (
        <div className="pregunta-selector">
          <label className="field-label" htmlFor="pregunta-select">Pregunta que estás analizando</label>
          <select id="pregunta-select" value={project.pregunta ?? ""} title={actual?.titulo}
                  onChange={(e) => setParams({ pregunta: e.target.value })}>
            {abiertas.map((q) => (
              <option key={q.id} value={q.id} title={q.titulo}>{corto(q.titulo)} · {q.n_respuestas} respuestas</option>
            ))}
          </select>
          <p className="small muted">
            Cada pregunta abierta tiene su propio libro de códigos, codificación e informe. La IA solo trabaja sobre la pregunta elegida y solo cuando tú se lo pides.
          </p>
        </div>
      )}
      <div className="project-tabs">
        {TABS.filter(([path]) => soloCerradas ? SOLO_CERRADAS.includes(path)
          : path !== "cerradas" || project.preguntas.some((q) => CERRADAS.includes(q.tipo))).map(([path, label]) => (
          <NavLink key={path} to={(path || ".") + search} end={path === ""}
                   className={({ isActive }) => `project-tab ${isActive ? "active" : ""}`}>
            {label}
          </NavLink>
        ))}
      </div>
      {cargando ? <p className="muted">Cargando pregunta…</p> : <Outlet key={project.pregunta} />}
    </ProjectContext.Provider>
  );
}
