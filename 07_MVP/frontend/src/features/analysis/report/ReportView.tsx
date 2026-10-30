import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/features/auth/useAuth";
import { puede } from "@/features/auth/api";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import PageHeader from "@/shared/components/PageHeader";
import { usePolling } from "@/shared/hooks/usePolling";
import { useProject } from "@/features/projects/useProjectData";
import { analysisApi } from "../api";
import { ReportProgress } from "../types";
import ReportBody from "./ReportBody";
import Icon from "@/shared/components/Icon";

export default function ReportView() {
  const { project, refresh } = useProject();
  const navigate = useNavigate();
  const canEdit = puede(useAuth().user, "analista");
  const [report, setReport] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState<ReportProgress | null>(null);
  const [mode, setMode] = useState<"v1" | "v2">("v2");
  // Confirmación inline para "regenerar desde cero": vuelve a pagar el análisis
  // por respondente (Prompt 1) aunque el caché siga vigente.
  const [confirmFull, setConfirmFull] = useState(false);
  const { start: startPolling, stop: stopPolling } = usePolling(2000);

  useEffect(() => {
    if (project.has_report) {
      analysisApi.getReport(project.id).then((r) => setReport(r.report)).catch(() => {});
    }
  }, [project.id, project.has_report]);

  async function generate(forceFull = false) {
    setBusy(true);
    setError("");
    setProgress(null);
    setConfirmFull(false);
    try {
      await analysisApi.generateReport(project.id, mode, forceFull);
      startPolling(async () => {
        try {
          const prog = await analysisApi.getReportProgress(project.id);
          setProgress(prog);
          if (prog.status === "done") {
            stopPolling();
            const r = await analysisApi.getReport(project.id);
            setReport(r.report);
            setBusy(false);
            setProgress(null);
            refresh();
          } else if (prog.status === "error") {
            stopPolling();
            setBusy(false);
            setProgress(null);
            setError(prog.error ?? "Error desconocido al generar el informe");
          }
        } catch {}
      });
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }

  const progressPct = progress && progress.total
    ? Math.round(((progress.done ?? 0) / progress.total) * 100)
    : 0;

  const progressBar = busy && (
    <div style={{ marginTop: 16, maxWidth: 560, marginLeft: "auto", marginRight: "auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 13 }}>
        <span>
          {progress?.section
            ? (mode === "v2"
              ? <><strong>{progress.section}</strong>…</>
              : <>Redactando: <strong>{progress.section}</strong>…</>)
            : "Generando el informe…"}
        </span>
        <span className="muted">{progressPct}%</span>
      </div>
      <div className="progress-track">
        <div className="progress-bar" style={{ width: `${progressPct}%` }} />
      </div>
      <p className="small muted" style={{ marginTop: 6 }}>
        {mode === "v2"
          ? "Progreso real por etapa: análisis por respondente, síntesis y redacción. No cierres esta ventana."
          : "Progreso real del texto que Claude va escribiendo (streaming). No cierres esta ventana."}
      </p>
    </div>
  );

  const modeSelector = (
    <div style={{ margin: "12px 0 4px", fontSize: 13 }}>
      <label style={{ marginRight: 16, cursor: "pointer" }}>
        <input
          type="radio"
          name="report-mode"
          checked={mode === "v2"}
          onChange={() => setMode("v2")}
          disabled={busy}
          style={{ marginRight: 6 }}
        />
        <strong>Análisis profundo</strong>{" "}
        <span className="muted">— por respondente, con contexto (más lento)</span>
      </label>
      <label style={{ cursor: "pointer" }}>
        <input
          type="radio"
          name="report-mode"
          checked={mode === "v1"}
          onChange={() => setMode("v1")}
          disabled={busy}
          style={{ marginRight: 6 }}
        />
        <strong>Modo rápido</strong>{" "}
        <span className="muted">— análisis agregado en una pasada</span>
      </label>
    </div>
  );

  const canGenerate = project.n_coded > 0;

  return (
    <>
      <PageHeader level={2} title="Informe" help="Genera el informe con los hallazgos y las citas textuales que los respaldan." />
      {error && <div className="alert alert-error">{error}</div>}
      {!report ? (
        <Card>
          <div className="empty-state">
            <div className="icon"><Icon name="file" size={40} /></div>
            <p style={{ maxWidth: 560, margin: "0 auto 8px" }}>
              Lectura interpretativa profunda generada por un investigador cualitativo IA. No es un resumen
              de frecuencias: es análisis sustantivo con hipótesis, tensiones y preguntas para profundizar,
              anclado al marco teórico del proyecto.
            </p>
            {!canEdit ? (
              <p className="muted">Aún no se genera el informe. Un analista de tu organización puede hacerlo.</p>
            ) : (
              <>
                {!canGenerate && (
                  <p className="muted">Primero completa la codificación para habilitar el informe.</p>
                )}
                {canGenerate && modeSelector}
                <Button size="lg" onClick={() => generate(false)} busy={busy} disabled={!canGenerate}>
                  {busy ? "Claude está redactando el informe…" : "Generar informe cualitativo"}
                </Button>
                {progressBar}
              </>
            )}
          </div>
        </Card>
      ) : (
        <>
          <Card
            title={<p className="muted small" style={{ margin: 0 }}>Análisis cualitativo asistido por IA · Celestica</p>}
            actions={
              <>
                <Button variant="secondary" size="sm" onClick={() => navigate("../exportar")}><Icon name="download" size={16} /> Exportar PDF/Word</Button>
                {canEdit && (
                  <Button variant="ghost" size="sm" onClick={() => generate(false)} busy={busy}>
                    {busy ? "Regenerando…" : "Regenerar"}
                  </Button>
                )}
                {canEdit && mode === "v2" && !busy && (
                  <Button variant="ghost" size="sm" onClick={() => setConfirmFull(true)} title="Ignora el caché del análisis por respondente">
                    Regenerar desde cero
                  </Button>
                )}
              </>
            }
          >
            {confirmFull && !busy && (
              <div className="alert alert-info" style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                <span>
                  <strong>Regenerar desde cero</strong> vuelve a analizar cada uno de los {project.n_responses} respondentes
                  con Claude (≈{project.n_responses} llamadas) en vez de reutilizar el análisis ya calculado.
                  Úsalo solo si cambiaste el prompt de análisis o desconfías del resultado anterior.
                </span>
                <span style={{ display: "flex", gap: 8 }}>
                  <Button size="sm" onClick={() => generate(true)}>Sí, regenerar todo</Button>
                  <Button variant="secondary" size="sm" onClick={() => setConfirmFull(false)}>Cancelar</Button>
                </span>
              </div>
            )}
            {progressBar}
            <ReportBody text={report} />
          </Card>
          <Card>
            <p className="small muted" style={{ margin: 0 }}>
              <strong>Nota metodológica:</strong> Este informe es un insumo interpretativo generado por IA sobre
              la base de la codificación validada por el analista. Las hipótesis y lecturas son orientaciones
              para el investigador, no conclusiones definitivas. Toda la codificación subyacente es auditable
              en la pestaña Trazabilidad.
            </p>
          </Card>
        </>
      )}
    </>
  );
}
