import { useEffect, useState } from "react";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import Table, { ConfBadge } from "@/shared/components/Table";
import { exportApi } from "@/features/export/api";
import { useProject } from "@/features/projects/useProjectData";
import { analysisApi } from "../api";
import { ProjectStats } from "../types";
import CategoryBars from "./CategoryBars";
import ConfidenceInfo from "./ConfidenceInfo";
import { TraceRow, useTraceabilityFilters } from "./useTraceabilityFilters";

export default function Traceability() {
  const { project } = useProject();
  const [rows, setRows] = useState<TraceRow[]>([]);
  const [stats, setStats] = useState<ProjectStats | null>(null);
  const [error, setError] = useState("");
  const {
    filtered, categories,
    filterCat, setFilterCat,
    filterSource, setFilterSource,
    filterConf, setFilterConf,
    search, setSearch,
  } = useTraceabilityFilters(rows);

  useEffect(() => {
    analysisApi.traceability(project.id).then(setRows).catch((e) => setError(e.message));
    analysisApi.summary(project.id).then(setStats).catch(() => {});
  }, [project.id]);

  return (
    <>
      {error && <div className="alert alert-error">{error}</div>}

      {stats && <CategoryBars stats={stats} />}

      <ConfidenceInfo />

      <Card
        title={`Tabla de trazabilidad (${filtered.length}${filtered.length !== rows.length ? ` de ${rows.length}` : ""} filas)`}
        actions={
          <>
            <Button variant="secondary" size="sm" onClick={() => exportApi.downloadCsv(project.id).catch((e) => setError(e.message))}>⬇ CSV</Button>
            <Button variant="secondary" size="sm" onClick={() => exportApi.downloadXlsx(project.id).catch((e) => setError(e.message))}>⬇ Excel</Button>
          </>
        }
      >
        <p className="muted">
          Cada fila documenta: qué respuesta fue asignada a qué categoría, con qué justificación, por quién
          (IA o analista) y en qué estado. Esta tabla es el insumo de auditoría (p. ej. acreditación CNA/CNE).
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: 10, marginBottom: 12 }}>
          <input placeholder="Buscar en el texto…" value={search} onChange={(e) => setSearch(e.target.value)} />
          <select value={filterCat} onChange={(e) => setFilterCat(e.target.value)}>
            <option value="">Todas las categorías</option>
            {categories.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select value={filterSource} onChange={(e) => setFilterSource(e.target.value)}>
            <option value="">Toda fuente</option>
            <option value="claude">claude (IA)</option>
            <option value="analista">analista</option>
          </select>
          <select value={filterConf} onChange={(e) => setFilterConf(e.target.value)}>
            <option value="">Toda confianza</option>
            <option value="alta">Alta (≥ 0.85)</option>
            <option value="media">Media (0.60–0.84)</option>
            <option value="baja">Baja (&lt; 0.60)</option>
          </select>
        </div>
        <div style={{ maxHeight: 500, overflow: "auto" }}>
          <Table headers={["ID", "Texto", "Categoría", "Justificación", "Conf.", "Fuente"]}>
            {filtered.slice(0, 300).map((r, i) => {
              const conf = r.confianza != null ? Number(r.confianza) : null;
              return (
                <tr key={i}>
                  <td className="muted">{String(r.id_respuesta)}</td>
                  <td style={{ maxWidth: 260 }}>{String(r.texto)}</td>
                  <td><strong>{String(r.categoria)}</strong></td>
                  <td className="muted small" style={{ maxWidth: 220 }}>{String(r.justificacion ?? "")}</td>
                  <td><ConfBadge value={conf} /></td>
                  <td>{r.fuente ? <span className={`pill ${r.fuente}`}>{String(r.fuente)}</span> : null}</td>
                </tr>
              );
            })}
          </Table>
          {filtered.length > 300 && <p className="muted small">Mostrando 300 de {filtered.length} filas. El CSV/Excel incluye todo.</p>}
        </div>
      </Card>
    </>
  );
}
