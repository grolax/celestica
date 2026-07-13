import { useState } from "react";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";

/** Explicación metodológica del indicador de confianza (colapsable). */
export default function ConfidenceInfo() {
  const [open, setOpen] = useState(false);

  return (
    <Card title="Sobre el indicador de confianza"
          actions={<Button variant="ghost" size="sm" onClick={() => setOpen(!open)}>
            {open ? "Ocultar" : "Ver explicación"}
          </Button>}>
      {open ? (
        <>
          <p className="muted">
            <strong>¿Qué mide?</strong> La confianza (0.0–1.0) es la estimación del modelo sobre qué tan
            bien encaja una respuesta en la categoría asignada. Es un indicador orientativo basado en
            alineación semántica y léxica, no un p-valor estadístico.
          </p>
          <p className="muted">
            <strong>¿Cómo se calcula?</strong> El modelo lee la definición de la categoría, sus criterios de
            inclusión y exclusión, y evalúa cuántas señales del texto coinciden. Bajo 0.6 sugiere ambigüedad
            o solapamiento con otra categoría.
          </p>
          <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
            <span><span className="conf-badge conf-high">≥ 0.85 Alta</span> <span className="muted small">vocabulario muy alineado</span></span>
            <span><span className="conf-badge conf-mid">0.60–0.84 Media</span> <span className="muted small">alineación parcial</span></span>
            <span><span className="conf-badge conf-low">&lt; 0.60 Baja</span> <span className="muted small">se recomienda revisión manual</span></span>
          </div>
          <p className="small muted" style={{ marginTop: 8, fontStyle: "italic" }}>
            Nota metodológica: la confianza sirve para priorizar la revisión manual, no para excluir datos
            automáticamente. Toda re-codificación queda en el registro de auditoría.
          </p>
        </>
      ) : (
        <p className="muted" style={{ margin: 0 }}>Indicador orientativo para priorizar revisión manual.</p>
      )}
    </Card>
  );
}
