import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/features/auth/useAuth";
import { puede } from "@/features/auth/api";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import PageHeader from "@/shared/components/PageHeader";
import { usePolling } from "@/shared/hooks/usePolling";
import { useProject } from "@/features/projects/useProjectData";
import { analysisApi } from "../api";
import { CodifyProgress, ResponseItem } from "../types";
import ResponsesTable from "./ResponsesTable";
import Icon from "@/shared/components/Icon";

const PAGE_SIZE = 25;

export default function Coding() {
  const { project, refresh } = useProject();
  const canEdit = puede(useAuth().user, "analista");
  const [items, setItems] = useState<ResponseItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState<CodifyProgress | null>(null);
  const [filterLow, setFilterLow] = useState(false);
  const { start: startPolling, stop: stopPolling } = usePolling(2000);

  const validated = project.categories.filter((c) => c.status === "validada");

  const load = useCallback(() => {
    analysisApi.getResponses(project.id, project.pregunta, offset, PAGE_SIZE).then((r) => {
      setItems(r.items);
      setTotal(r.total);
    }).catch((e) => setError(e.message));
  }, [project.id, project.pregunta, offset]);
  useEffect(load, [load]);

  async function poll() {
    try {
      const prog = await analysisApi.getCodifyProgress(project.id, project.pregunta);
      setProgress(prog);
      if (prog.status === "done") {
        stopPolling();
        setBusy(false);
        load();
        refresh();
      } else if (prog.status === "error") {
        stopPolling();
        setBusy(false);
        setError(prog.error ?? "Error desconocido en la codificación");
      }
    } catch {}
  }

  // Retoma una codificación en curso (otra pestaña o otra pregunta) para no pagar la IA dos veces.
  useEffect(() => {
    let off = false;
    analysisApi.getCodifyProgress(project.id, project.pregunta).then((prog) => {
      if (off || prog.status !== "running") return;
      setBusy(true);
      setProgress(prog);
      startPolling(poll);
    }).catch(() => {});
    return () => { off = true; stopPolling(); setBusy(false); setProgress(null); };
  }, [project.id, project.pregunta]);

  async function runCodify() {
    setBusy(true);
    setError("");
    setProgress(null);
    try {
      await analysisApi.codify(project.id, project.pregunta);
      startPolling(poll);
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }

  async function recode(rid: string, categoryId: string) {
    try {
      await analysisApi.recode(project.id, project.pregunta, rid, categoryId ? [categoryId] : []);
      load();
      refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const progressPct = progress && progress.total ? Math.round((progress.done! / progress.total) * 100) : 0;
  const visible = filterLow
    ? items.filter((r) => r.codings.some((c) => typeof c.confidence === "number" && c.confidence < 0.6))
    : items;

  return (
    <>
      <PageHeader level={2} title="Codificación" help="La IA asigna a cada respuesta sus temas validados, con el motivo y su nivel de confianza. Puedes corregir cualquier asignación.">
        <span className="pill ok">{validated.length} categorías validadas</span>
      </PageHeader>
      {error && <div className="alert alert-error">{error}</div>}
      <Card>
        <p className="muted">
          Cada asignación incluye justificación y nivel de confianza
          (<span className="conf-badge conf-high">alta</span>
          <span className="conf-badge conf-mid">media</span>
          <span className="conf-badge conf-low">baja</span>).
          Puedes re-codificar manualmente cualquier respuesta; todo queda auditado.
        </p>
        {canEdit && (
          <Button onClick={runCodify} busy={busy} disabled={validated.length === 0}>
            {busy ? "Codificando…" : "Codificar corpus con IA"}
          </Button>
        )}
        {canEdit && validated.length === 0 && (
          <p className="small muted" style={{ marginTop: 8 }}>Primero valida categorías en el Libro de códigos.</p>
        )}

        {busy && progress?.status === "running" && (
          <div style={{ marginTop: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 13 }}>
              <span>Procesando respuestas con IA…</span>
              <span className="muted">{progress.done} de {progress.total} ({progressPct}%)</span>
            </div>
            <div className="progress-track">
              <div className="progress-bar" style={{ width: `${progressPct}%` }} />
            </div>
            <p className="small muted" style={{ marginTop: 6 }}>
              Claude codifica el corpus por lotes (~20 s por lote). No cierres esta ventana.
            </p>
          </div>
        )}

        {progress?.status === "done" && (
          <div className="alert alert-success" style={{ marginTop: 12, marginBottom: 0 }}>
            Codificación completa: {progress.coded} respuestas, {progress.assignments} asignaciones.
            Revisa y corrige donde sea necesario.
          </div>
        )}
      </Card>

      <Card
        title={`Respuestas (${total})`}
        actions={
          <label className="small muted" style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
            <input type="checkbox" style={{ width: "auto" }} checked={filterLow}
                   onChange={(e) => setFilterLow(e.target.checked)} />
            solo confianza baja (en esta página)
          </label>
        }
      >
        <ResponsesTable items={visible} categories={project.categories}
                        validated={validated} onRecode={canEdit ? recode : undefined} />
        <div style={{ display: "flex", gap: 8, marginTop: 12, alignItems: "center" }}>
          <Button variant="secondary" size="sm" disabled={offset === 0}
                  onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}><Icon name="arrowLeft" size={16} /> Anterior</Button>
          <span className="muted small">{offset + 1}–{Math.min(offset + PAGE_SIZE, total)} de {total}</span>
          <Button variant="secondary" size="sm" disabled={offset + PAGE_SIZE >= total}
                  onClick={() => setOffset(offset + PAGE_SIZE)}>Siguiente <Icon name="arrowRight" size={16} /></Button>
        </div>
      </Card>
    </>
  );
}
