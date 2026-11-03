import { useState } from "react";
import { useAuth } from "@/features/auth/useAuth";
import { puede } from "@/features/auth/api";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import { TextArea } from "@/shared/components/Input";
import { useAsync } from "@/shared/hooks/useAsync";
import { projectsApi } from "./api";
import { useProject } from "./useProjectData";

const MAX = 5000; // el servidor es quien valida; aquí solo se informa

/** Marco teórico del proyecto (RF-41): lo lee cualquiera, lo edita un analista o administrador. */
export default function MarcoTeorico() {
  const { project, refresh } = useProject();
  const canEdit = puede(useAuth().user, "analista");
  const [editando, setEditando] = useState(false);
  const [texto, setTexto] = useState("");
  const { busy, error, setError, run } = useAsync();

  // El marco creado desde el formulario se guarda con \r\n; el textarea siempre entrega \n.
  const actual = project.marco_teorico.replace(/\r\n/g, "\n");
  const limpio = texto.trim();
  const abrir = () => { setTexto(actual); setError(""); setEditando(true); };
  const guardar = async () => {
    const r = await run(() => projectsApi.updateMarco(project.id, limpio));
    if (!r) return; // el error queda junto al editor y el texto se conserva
    refresh();
    setEditando(false);
  };

  return (
    <Card title="Marco teórico" actions={canEdit && !editando && <Button size="sm" variant="secondary" onClick={abrir}>Editar</Button>}>
      {!editando ? (
        project.marco_teorico ? (
          <p style={{ whiteSpace: "pre-wrap", margin: 0 }}>{project.marco_teorico}</p>
        ) : (
          <p className="muted" style={{ margin: 0 }}>Este proyecto no tiene marco teórico. La IA busca los temas directamente en las respuestas.</p>
        )
      ) : (
        <>
          <TextArea label="Marco teórico del proyecto" rows={8} value={texto} autoFocus
                    aria-describedby="marco_ayuda" onChange={(e) => setTexto(e.target.value)} />
          <p className="small muted" id="marco_ayuda" style={{ margin: "4px 0 10px" }}>
            {limpio.length.toLocaleString("es-CL")} de {MAX.toLocaleString("es-CL")} caracteres
          </p>
          <div className="alert alert-info">
            Lo que ya se generó (categorías, codificación e informes) no cambia. El marco nuevo se usa desde el próximo trabajo con IA y vale para todas las preguntas abiertas del proyecto. El próximo informe profundo volverá a gastar IA, porque debe rehacer sus análisis con este marco.
          </div>
          {error && <div className="alert alert-error" role="alert">{error}</div>}
          <div style={{ display: "flex", gap: 8 }}>
            <Button busy={busy} disabled={limpio === actual.trim()} onClick={guardar}>Guardar</Button>
            <Button variant="secondary" disabled={busy} onClick={() => setEditando(false)}>Cancelar</Button>
          </div>
        </>
      )}
    </Card>
  );
}
