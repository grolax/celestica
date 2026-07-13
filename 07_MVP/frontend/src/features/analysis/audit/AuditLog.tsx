import { useEffect, useState } from "react";
import { analysisApi } from "../api";
import Card from "@/shared/components/Card";
import Table from "@/shared/components/Table";
import { useProject } from "@/features/projects/useProjectData";

interface AuditEvent {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  detail: unknown;
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
    <Card
      title={`Registro de auditoría (${filtered.length} eventos)`}
      actions={
        <select value={filterActor} onChange={(e) => setFilterActor(e.target.value)} style={{ width: "auto" }}>
          <option value="">Todos los actores</option>
          <option value="analista">analista</option>
          <option value="claude">claude (IA)</option>
          <option value="sistema">sistema</option>
        </select>
      }
    >
      <p className="muted">
        Toda decisión —humana o de IA— queda registrada con timestamp y detalle. Nada es caja negra.
      </p>
      <Table headers={["Fecha/hora", "Actor", "Acción", "Detalle"]}>
        {filtered.map((e) => (
          <tr key={e.id}>
            <td className="muted" style={{ whiteSpace: "nowrap" }}>{new Date(e.timestamp).toLocaleString("es-CL")}</td>
            <td><span className={`pill ${e.actor}`}>{e.actor}</span></td>
            <td><strong>{e.action}</strong></td>
            <td className="muted small" style={{ maxWidth: 460, wordBreak: "break-word" }}>
              {JSON.stringify(e.detail).slice(0, 300)}
            </td>
          </tr>
        ))}
      </Table>
    </Card>
  );
}
