import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import { usePolling } from "@/shared/hooks/usePolling";
import { useProject } from "@/features/projects/useProjectData";
import { analysisApi } from "../api";
import { ReportProgress } from "../types";
import ReportBody from "./ReportBody";

export default function ReportView() {
  const { project, refresh } = useProject();
  const navigate = useNavigate();
  const [report, setReport] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState<ReportProgress | null>(null);
  const { start: startPolling, stop: stopPolling } = usePolling(2000);

  useEffect(() => {
    if (project.has_report) {
      analysisApi.getReport(project.id).then((r) => setReport(r.report)).catch(() => {});
    }
  }, [project.id, project.has_report]);

  async function generate() {
    setBusy(true);
    setError("");
    setProgress(null);
    try {
      await analysisApi.generateReport(project.id);
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
          {progress?.section ? <>Redactando: <strong>{progress.section}</strong>…</> : "Redactando el informe…"}
        </span>
        <span className="muted">{progressPct}%</span>
      </div>
      <div className="progress-track">
        <div className="progress-bar" style={{ width: `${progressPct}%` }} />
      </div>
      <p className="small muted" style={{ marginTop: 6 }}>
        Progreso real del texto que Claude va escribiendo (streaming). No cierres esta ventana.
      </p>
    </div>
  );

  const canGenerate = project.n_coded > 0;

  return (
    <>
      {error && <div className="alert alert-error">{error}</div>}
      {!report ? (
        <Card>
          <div className="empty-state">
            <div className="icon">★</div>
            <h2>Informe de resultados</h2>
            <p style={{ maxWidth: 560, margin: "0 auto 8px" }}>
              Lectura interpretativa profunda generada por un investigador cualitativo IA. No es un resumen
              de frecuencias: es análisis sustantivo con hipótesis, tensiones y preguntas para profundizar,
              anclado al marco teórico del proyecto.
            </p>
            {!canGenerate && (
              <p className="muted">Primero completa la codificación para habilitar el informe.</p>
            )}
            <Button size="lg" onClick={generate} busy={busy} disabled={!canGenerate}>
              {busy ? "Claude está redactando el informe…" : "Generar informe cualitativo"}
            </Button>
            {progressBar}
          </div>
        </Card>
      ) : (
        <>
          <Card
            title={<div><h2 style={{ margin: 0 }}>Informe de resultados — {project.name}</h2>
              <p className="muted small" style={{ margin: "3px 0 0" }}>Análisis cualitativo asistido por IA · SoftInsight</p></div>}
            actions={
              <>
                <Button variant="secondary" size="sm" onClick={() => navigate("../exportar")}>⬇ Exportar PDF/Word</Button>
                <Button variant="ghost" size="sm" onClick={generate} busy={busy}>
                  {busy ? "Regenerando…" : "Regenerar"}
                </Button>
              </>
            }
          >
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
