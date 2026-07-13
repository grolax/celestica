import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { analysisApi } from "@/features/analysis/api";
import { ProjectStats } from "@/features/analysis/types";
import Button from "@/shared/components/Button";
import Card, { StatCard } from "@/shared/components/Card";
import { useProject } from "./useProjectData";

export default function ProjectDashboard() {
  const { project } = useProject();
  const navigate = useNavigate();
  const [stats, setStats] = useState<ProjectStats | null>(null);

  useEffect(() => {
    analysisApi.summary(project.id).then(setStats).catch(() => {});
  }, [project.id, project.n_coded]);

  const validated = project.categories.filter((c) => c.status === "validada").length;
  const pctCoded = project.n_responses ? Math.round((project.n_coded / project.n_responses) * 100) : 0;

  const steps: { label: string; done: boolean; to: string; cta: string }[] = [
    { label: "Análisis léxico", done: project.has_lexical, to: "lexico", cta: "Ejecutar" },
    { label: "Libro de códigos validado", done: validated > 0, to: "codigos", cta: "Validar" },
    { label: "Corpus codificado", done: project.n_coded > 0, to: "codificacion", cta: "Codificar" },
    { label: "Informe cualitativo", done: project.has_report, to: "informe", cta: "Generar" },
  ];
  const nextStep = steps.find((s) => !s.done);

  const maxCat = stats?.by_category[0]?.count ?? 1;
  const confTotal = stats
    ? stats.confidence_distribution.alta + stats.confidence_distribution.media + stats.confidence_distribution.baja
    : 0;

  return (
    <>
      <div className="stat-grid">
        <StatCard value={project.n_responses} label="Respuestas" accent />
        <StatCard value={validated} label="Categorías validadas" />
        <StatCard value={`${pctCoded}%`} label="Corpus codificado" />
        <StatCard value={project.n_audit_events} label="Eventos de auditoría" />
      </div>

      <div className="grid-2">
        <Card title="Estado del análisis"
              actions={nextStep && (
                <Button size="sm" onClick={() => navigate(nextStep.to)}>
                  {nextStep.cta} {nextStep.label.toLowerCase().split(" ")[0]} →
                </Button>
              )}>
          {steps.map((s, i) => (
            <div key={s.label} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderBottom: i < steps.length - 1 ? "1px solid var(--border-soft)" : "none" }}>
              <span className={`pill ${s.done ? "ok" : ""}`} style={{ width: 26, textAlign: "center" }}>
                {s.done ? "✓" : i + 1}
              </span>
              <span style={{ flex: 1, fontWeight: s.done ? 400 : 600 }}>{s.label}</span>
              {!s.done && (
                <Button size="sm" variant="secondary" onClick={() => navigate(s.to)}>{s.cta}</Button>
              )}
            </div>
          ))}
          {!nextStep && (
            <div className="alert alert-success" style={{ marginTop: 12, marginBottom: 0 }}>
              Análisis completo. <a onClick={() => navigate("exportar")} style={{ cursor: "pointer" }}><strong>Exporta el reporte final →</strong></a>
            </div>
          )}
        </Card>

        <Card title="Respuestas por categoría">
          {!stats || stats.by_category.length === 0 ? (
            <p className="muted">Sin codificación aún. Los resultados aparecerán aquí.</p>
          ) : (
            stats.by_category.slice(0, 8).map((c) => (
              <div className="bar-row" key={c.category_id}>
                <span title={c.nombre}>{c.nombre}</span>
                <div className="bar" style={{ width: `${(c.count / maxCat) * 100}%` }} />
                <span className="muted">{c.count}</span>
              </div>
            ))
          )}
        </Card>
      </div>

      {stats && confTotal > 0 && (
        <Card title="Distribución de confianza de la codificación IA">
          <div style={{ display: "flex", gap: 18, flexWrap: "wrap" }}>
            <span><span className="conf-badge conf-high">Alta ≥ 0.85</span> {stats.confidence_distribution.alta} ({Math.round(stats.confidence_distribution.alta / confTotal * 100)}%)</span>
            <span><span className="conf-badge conf-mid">Media 0.60–0.84</span> {stats.confidence_distribution.media} ({Math.round(stats.confidence_distribution.media / confTotal * 100)}%)</span>
            <span><span className="conf-badge conf-low">Baja &lt; 0.60</span> {stats.confidence_distribution.baja} ({Math.round(stats.confidence_distribution.baja / confTotal * 100)}%)</span>
          </div>
          <p className="small muted" style={{ marginTop: 10, marginBottom: 0 }}>
            Las asignaciones de confianza baja son candidatas a revisión manual en la pestaña Codificación.
          </p>
        </Card>
      )}

      <Card title="Exportar" actions={<span className="pill claude">listo para acreditación</span>}>
        <p className="muted">Informe PDF/Word con tabla de trazabilidad completa, y datos en CSV/Excel.</p>
        <Button onClick={() => navigate("exportar")}>Ir a Exportar →</Button>
      </Card>
    </>
  );
}
