import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { projectsApi } from "./api";
import { ProjectSummary } from "./types";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import Table from "@/shared/components/Table";
import Icon from "@/shared/components/Icon";
import PageHeader from "@/shared/components/PageHeader";

export default function ProjectList() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectSummary[] | null>(null);
  const [error, setError] = useState("");

  const refresh = useCallback(() => {
    projectsApi.listProjects().then(setProjects).catch((e) => setError(e.message));
  }, []);
  useEffect(refresh, [refresh]);

  async function remove(p: ProjectSummary) {
    if (!confirm(`¿Eliminar el proyecto "${p.name}"? Esta acción no se puede deshacer.`)) return;
    try {
      await projectsApi.deleteProject(p.id);
      refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <>
      <PageHeader title="Mis proyectos" help="Aquí están tus encuestas en análisis. Abre una para continuar o crea un proyecto nuevo.">
        <Button onClick={() => navigate("/proyectos/nuevo")}>+ Nuevo proyecto</Button>
      </PageHeader>
      {error && <div className="alert alert-error">{error}</div>}

      {projects && projects.length === 0 && (
        <Card>
          <div className="empty-state">
            <div className="icon"><Icon name="chart" size={40} /></div>
            <p>Todavía no tienes proyectos. Crea el primero subiendo tu encuesta.</p>
            <Button onClick={() => navigate("/proyectos/nuevo")}>Crear proyecto</Button>
          </div>
        </Card>
      )}

      {projects && projects.length > 0 && (
        <Card>
          <Table headers={["Proyecto", "Respuestas", "Análisis", "Estado", ""]}>
            {projects.map((p) => (
              <tr key={p.id} style={{ cursor: "pointer" }} onClick={() => navigate(`/proyectos/${p.id}`)}>
                <td>
                  <strong>{p.name}</strong>
                  <br />
                  <span className="muted small">{new Date(p.created_at).toLocaleDateString("es-CL", { day: "numeric", month: "long", year: "numeric" })}</span>
                </td>
                <td>{p.n_responses}</td>
                <td>
                  <span className={`pill ${p.has_lexical ? "ok" : ""}`}>Léxico {p.has_lexical ? <><Icon name="check" size={12} /><span className="sr-only">listo</span></> : "—"}</span>{" "}
                  <span className={`pill ${p.n_coded > 0 ? "ok" : ""}`}>
                    {p.n_coded > 0 ? `${p.n_coded} codificadas` : "sin codificar"}
                  </span>
                </td>
                <td>
                  {p.n_categories} categorías
                  {p.has_report && <span className="pill claude" style={{ marginLeft: 6 }}>informe <Icon name="check" size={12} /><span className="sr-only">listo</span></span>}
                </td>
                <td onClick={(e) => e.stopPropagation()}>
                  <div style={{ display: "flex", gap: 6 }}>
                    <Button size="sm" variant="secondary" onClick={() => navigate(`/proyectos/${p.id}`)}>Abrir</Button>
                    <Button size="sm" variant="danger" onClick={() => remove(p)}>Eliminar</Button>
                  </div>
                </td>
              </tr>
            ))}
          </Table>
        </Card>
      )}
    </>
  );
}
