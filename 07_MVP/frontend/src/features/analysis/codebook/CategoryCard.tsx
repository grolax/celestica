import { useState } from "react";
import { useAuth } from "@/features/auth/useAuth";
import { puede } from "@/features/auth/api";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import { TextArea } from "@/shared/components/Input";
import { useProject } from "@/features/projects/useProjectData";
import { analysisApi } from "../api";
import { Category } from "../types";
import CommentThread from "./CommentThread";
import Icon from "@/shared/components/Icon";

/** Tarjeta de una categoría: estado, edición inline y comentarios del equipo. */
export default function CategoryCard({ category: c, projectId, onChange, onError }: {
  category: Category;
  projectId: string;
  onChange: () => void;
  onError: (msg: string) => void;
}) {
  const canEdit = puede(useAuth().user, "analista");
  const { pregunta } = useProject().project;
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    nombre: c.nombre, definicion: c.definicion,
    criterios_inclusion: c.criterios_inclusion, criterios_exclusion: c.criterios_exclusion,
    ejemplo: c.ejemplo,
  });
  const [showComments, setShowComments] = useState(false);
  const comments = c.comments ?? [];

  async function setStatus(status: Category["status"]) {
    try {
      await analysisApi.updateCategory(projectId, pregunta, c.id, { status });
      onChange();
    } catch (e) {
      onError((e as Error).message);
    }
  }

  async function saveEdit() {
    try {
      await analysisApi.updateCategory(projectId, pregunta, c.id, form);
      setEditing(false);
      onChange();
    } catch (e) {
      onError((e as Error).message);
    }
  }

  const set = (k: keyof typeof form) => (e: { target: { value: string } }) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  return (
    <Card
      title={editing
        ? <input value={form.nombre} onChange={set("nombre")} style={{ fontWeight: 700 }} />
        : <h3 style={{ margin: 0 }}>{c.nombre}</h3>}
      actions={canEdit && (
        <Button size="sm" variant="ghost" onClick={() => setEditing(!editing)}>
          {editing ? "Cancelar" : <><Icon name="edit" size={16} /> Editar</>}
        </Button>
      )}
    >
      <p style={{ marginTop: -4 }}>
        <span className={`pill ${c.status}`}>{c.status}</span>{" "}
        <span className={`pill ${c.origen}`}>origen: {c.origen}</span>
      </p>

      {editing ? (
        <>
          <TextArea label="Definición" rows={2} value={form.definicion} onChange={set("definicion")} />
          <TextArea label="Incluye" rows={2} value={form.criterios_inclusion} onChange={set("criterios_inclusion")} />
          <TextArea label="Excluye" rows={2} value={form.criterios_exclusion} onChange={set("criterios_exclusion")} />
          <TextArea label="Ejemplo" rows={2} value={form.ejemplo} onChange={set("ejemplo")} />
          <div style={{ marginTop: 10 }}>
            <Button size="sm" onClick={saveEdit}>Guardar cambios</Button>
          </div>
        </>
      ) : (
        <>
          <p className="muted">{c.definicion}</p>
          {c.criterios_inclusion && <p className="small muted"><strong>Incluye:</strong> {c.criterios_inclusion}</p>}
          {c.criterios_exclusion && <p className="small muted"><strong>Excluye:</strong> {c.criterios_exclusion}</p>}
          {c.ejemplo && <p className="small muted"><strong>Ejemplo:</strong> "{c.ejemplo}"</p>}
        </>
      )}

      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 8 }}>
        {canEdit && c.status !== "validada" && <Button size="sm" variant="success" onClick={() => setStatus("validada")}>Validar</Button>}
        {canEdit && c.status !== "descartada" && <Button size="sm" variant="danger" onClick={() => setStatus("descartada")}>Descartar</Button>}
        {canEdit && c.status !== "propuesta" && <Button size="sm" variant="ghost" onClick={() => setStatus("propuesta")}>Revertir</Button>}
        <Button size="sm" variant="ghost" onClick={() => setShowComments(!showComments)}>
          <Icon name="comment" size={16} /> {comments.length > 0 ? comments.length : ""}
        </Button>
      </div>

      {showComments && (
        <CommentThread projectId={projectId} categoryId={c.id} comments={comments}
                       onChange={onChange} onError={onError} />
      )}
    </Card>
  );
}
