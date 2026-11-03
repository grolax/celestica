import { useEffect, useState } from "react";
import { analysisApi } from "../api";
import Card from "@/shared/components/Card";
import PageHeader from "@/shared/components/PageHeader";
import Table from "@/shared/components/Table";
import { useProject } from "@/features/projects/useProjectData";

interface AuditEvent {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  detail: unknown;
}

interface CambioMarcoDetail { antes: string; despues: string; usuario: string }

// Texto completo y con saltos de línea: es lo que permite ver qué cambió.
function CambioMarco({ d }: { d: CambioMarcoDetail }) {
  return (
    <>
      {([["Antes", d.antes], ["Después", d.despues], ["Por", d.usuario]] as const).map(([k, v]) => (
        <div key={k} style={{ whiteSpace: "pre-wrap" }}><strong>{k}:</strong> {v || "(vacío)"}</div>
      ))}
    </>
  );
}

export default function AuditLog() {
  const { project } = useProject();
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [filterActor, setFilterActor] = useState("");

  useEffect(() => {
    analysisApi.audit(project.id).then(setEvents).catch(() => {});
  }, [project.id]);

  const filtered = [...events].reverse().filter((e) => !filterActor || e.actor === filterActor);

  return (
    <>
    <PageHeader level={2} title="Auditoría" help="Registro de cada acción, de personas y de la IA. No se puede editar ni borrar." />
    <Card
      title={`${filtered.length} eventos`}
      actions={
        <select value={filterActor} onChange={(e) => setFilterActor(e.target.value)} style={{ width: "auto" }}>
          <option value="">Todos los actores</option>
          <option value="analista">analista</option>
          <option value="claude">claude (IA)</option>
          <option value="sistema">sistema</option>
        </select>
      }
    >
      <Table headers={["Fecha/hora", "Actor", "Acción", "Detalle"]}>
        {filtered.map((e) => (
          <tr key={e.id}>
            <td className="muted" style={{ whiteSpace: "nowrap" }}>{new Date(e.timestamp).toLocaleString("es-CL")}</td>
            <td><span className={`pill ${e.actor}`}>{e.actor}</span></td>
            <td><strong>{e.action}</strong></td>
            <td className="muted small" style={{ maxWidth: 460, wordBreak: "break-word" }}>
              {e.action === "cambio_marco_teorico" ? <CambioMarco d={e.detail as CambioMarcoDetail} /> : JSON.stringify(e.detail).slice(0, 300)}
            </td>
          </tr>
        ))}
      </Table>
    </Card>
    </>
  );
}
