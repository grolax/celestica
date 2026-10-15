import { useState } from "react";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import { useDownload } from "@/shared/hooks/useDownload";
import { useProject } from "@/features/projects/useProjectData";
import { exportApi } from "./api";
import Icon from "@/shared/components/Icon";

export default function ExportReport() {
  const { project } = useProject();
  const { busyKey, error, download } = useDownload();
  const [includeDetails, setIncludeDetails] = useState(true);

  const validated = project.categories.filter((c) => c.status === "validada").length;
  const ready = project.n_coded > 0 && validated > 0;

  const contents = [
    ["Portada", "Logo, nombre del proyecto y metadata (fechas, volúmenes, marco teórico)"],
    ["Resumen ejecutivo", "Totales y distribución de respuestas por categoría"],
    ["Informe cualitativo", project.has_report ? "Incluido (ya generado)" : "Se incluirá si lo generas en la pestaña Informe"],
    ["Análisis léxico", project.has_lexical ? "Gráfico de frecuencias, top 20 términos y sentimiento" : "Se incluirá si ejecutas el análisis léxico"],
    ["Análisis temático", "Cada categoría validada con definición, criterios y respuestas ejemplares"],
    ["Tabla de trazabilidad", "Respuesta → categoría → justificación → confianza → fuente (opcional)"],
    ["Nota metodológica", "Cómo se codificó, rol de la IA y del analista, garantías de auditoría"],
  ];

  return (
    <>
      {error && <div className="alert alert-error">{error}</div>}
      {!ready && (
        <div className="alert alert-info">
          El reporte se puede exportar en cualquier momento, pero tendrá más valor cuando el corpus esté
          codificado ({project.n_coded} respuestas codificadas, {validated} categorías validadas hasta ahora).
        </div>
      )}

      <div className="grid-2">
        <Card title="Informe completo" actions={<span className="pill claude">apto para acreditación</span>}>
          <p className="muted">
            Documento formal con todo el análisis y la tabla de trazabilidad. El PDF es el archivo final;
            el Word es editable para que tu organización agregue sus conclusiones.
          </p>
          <label className="small" style={{ display: "flex", alignItems: "center", gap: 7, margin: "10px 0 14px", cursor: "pointer" }}>
            <input type="checkbox" style={{ width: "auto" }} checked={includeDetails}
                   onChange={(e) => setIncludeDetails(e.target.checked)} />
            Incluir tabla de trazabilidad completa (una fila por asignación)
          </label>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Button busy={busyKey === "pdf"}
                    onClick={() => download("pdf", () => exportApi.downloadPdf(project.id, includeDetails))}>
              <Icon name="download" /> Descargar PDF
            </Button>
            <Button variant="secondary" busy={busyKey === "docx"}
                    onClick={() => download("docx", () => exportApi.downloadDocx(project.id, includeDetails))}>
              <Icon name="download" /> Descargar Word (.docx)
            </Button>
          </div>
        </Card>

        <Card title="Datos para análisis propio">
          <p className="muted">
            Tabla plana de trazabilidad para SPSS, R, Excel u otra herramienta:
            respuesta, categoría, justificación, confianza, fuente y estado.
          </p>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 14 }}>
            <Button variant="secondary" busy={busyKey === "csv"}
                    onClick={() => download("csv", () => exportApi.downloadCsv(project.id))}>
              <Icon name="download" /> CSV (UTF-8)
            </Button>
            <Button variant="secondary" busy={busyKey === "xlsx"}
                    onClick={() => download("xlsx", () => exportApi.downloadXlsx(project.id))}>
              <Icon name="download" /> Excel (.xlsx)
            </Button>
          </div>
        </Card>
      </div>

      <Card title="Contenido del informe">
        <table className="si">
          <tbody>
            {contents.map(([sec, desc]) => (
              <tr key={sec}>
                <td style={{ whiteSpace: "nowrap", fontWeight: 600 }}>{sec}</td>
                <td className="muted">{desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </>
  );
}
