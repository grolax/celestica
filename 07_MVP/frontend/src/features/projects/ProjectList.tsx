import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { projectsApi } from "./api";
import { ProjectSummary } from "./types";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import Table from "@/shared/components/Table";

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
      <div className="card-title" style={{ marginBottom: 18 }}>
        <h1>Mis proyectos</h1>
        <Button onClick={() => navigate("/proyectos/nuevo")}>+ Nuevo proyecto</Button>
      </div>
      {error && <div className="alert alert-error">{error}</div>}

      {projects && projects.length === 0 && (
        <Card>
          <div className="empty-state">
            <div className="icon">📊</div>
            <h3>Aún no tienes proyectos</h3>
            <p>Crea tu primer proyecto subiendo un CSV o XLSX con respuestas abiertas.</p>
            <Button onClick={() => navigate("/proyectos/nuevo")}>Crear primer proyecto</Button>
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
                  <span className={`pill ${p.has_lexical ? "ok" : ""}`}>Léxico {p.has_lexical ? "✓" : "—"}</span>{" "}
                  <span className={`pill ${p.n_coded > 0 ? "ok" : ""}`}>
                    {p.n_coded > 0 ? `${p.n_coded} codificadas` : "sin codificar"}
                  </span>
                </td>
                <td>
                  {p.n_categories} categorías
                  {p.has_report && <span className="pill claude" style={{ marginLeft: 6 }}>informe ✓</span>}
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
