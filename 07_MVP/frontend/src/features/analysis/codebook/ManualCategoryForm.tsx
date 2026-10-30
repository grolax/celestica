import { useState } from "react";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import Input, { TextArea } from "@/shared/components/Input";
import { useProject } from "@/features/projects/useProjectData";
import { analysisApi } from "../api";

/** Alta manual de categorías (entran validadas: las escribió un humano). */
export default function ManualCategoryForm({ projectId, onChange, onError }: {
  projectId: string;
  onChange: () => void;
  onError: (msg: string) => void;
}) {
  const { pregunta } = useProject().project;
  const empty = { nombre: "", definicion: "", criterios_inclusion: "", criterios_exclusion: "", ejemplo: "" };
  const [form, setForm] = useState(empty);
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  async function add() {
    if (!form.nombre.trim()) return;
    try {
      await analysisApi.createCategory(projectId, pregunta, form);
      setForm(empty);
      onChange();
    } catch (e) {
      onError((e as Error).message);
    }
  }

  return (
    <Card title="Agregar categoría manual">
      <div className="grid-2">
        <div>
          <Input label="Nombre" value={form.nombre} onChange={set("nombre")} placeholder="Ej: Carga académica" />
          <TextArea label="Definición general" rows={2} value={form.definicion} onChange={set("definicion")}
                    placeholder="¿Qué fenómeno captura esta categoría?" />
          <TextArea label="Ejemplo ilustrativo" rows={2} value={form.ejemplo} onChange={set("ejemplo")}
                    placeholder="Cita una respuesta real o construye un ejemplo." />
        </div>
        <div>
          <TextArea label="Incluye (criterios de inclusión)" rows={3} value={form.criterios_inclusion}
                    onChange={set("criterios_inclusion")}
                    placeholder="¿Cuándo SÍ aplica? Palabras clave, situaciones o patrones que la activan." />
          <TextArea label="Excluye (criterios de exclusión)" rows={3} value={form.criterios_exclusion}
                    onChange={set("criterios_exclusion")}
                    placeholder="¿Cuándo NO aplica? Distingue de categorías similares." />
        </div>
      </div>
      <div style={{ marginTop: 10 }}>
        <Button variant="secondary" onClick={add} disabled={!form.nombre.trim()}>Agregar (queda validada)</Button>
      </div>
    </Card>
  );
}
