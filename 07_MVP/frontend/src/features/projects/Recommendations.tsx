import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { puede } from "@/features/auth/api";
import { useAuth } from "@/features/auth/useAuth";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import Icon from "@/shared/components/Icon";
import { projectsApi } from "./api";
import { Recomendaciones } from "./types";
import { useProject } from "./useProjectData";

const recortar = (t: string) => (t.length > 60 ? `${t.slice(0, 60)}…` : t);

/** Alertas, cruces y plantilla sugeridos (RF-41). No se muestra si está vacía o si la consulta falla. */
export default function Recommendations() {
  const { project } = useProject();
  const navigate = useNavigate();
  const { search } = useLocation();
  const canEdit = puede(useAuth().user, "analista");
  const [rec, setRec] = useState<Recomendaciones | null>(null);

  useEffect(() => {
    setRec(null);
    projectsApi.getRecommendations(project.id).then(setRec).catch(() => {});
  }, [project.id]);

  if (!rec) return null;
  const plantilla = canEdit ? rec.plantilla : null;
  if (!rec.alertas.length && !rec.segmentos.length && !plantilla) return null;

  const verPor = (id: string) => {
    const p = new URLSearchParams(search);
    p.set("por", id);
    navigate(`cerradas?${p}`);
  };

  return (
    <Card title="Recomendaciones">
      <p className="small muted" style={{ marginTop: -4 }}>
        Sugerencias automáticas según tus respuestas, calculadas con reglas fijas (sin IA).
      </p>
      {rec.alertas.map((a) => (
        <div key={a.id + (a.pregunta_id ?? "")} className={`alert ${a.nivel === "importante" ? "alert-error" : "alert-warning"}`}>
          {a.mensaje}
        </div>
      ))}

      {rec.segmentos.length > 0 && (
        <>
          <h4 style={{ marginTop: 14 }}>Cruces sugeridos</h4>
          {rec.segmentos.map((s) => (
            <div key={s.pregunta_id} style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", padding: "8px 0", borderBottom: "1px solid var(--border-soft)" }}>
              <div style={{ flex: 1, minWidth: 200 }}>
                <strong title={s.titulo}>{recortar(s.titulo)}</strong>
                <div className="small muted">{s.motivo}</div>
              </div>
              <Button size="sm" variant="secondary" onClick={() => verPor(s.pregunta_id)}>
                Ver por este grupo <Icon name="arrowRight" size={16} />
              </Button>
            </div>
          ))}
        </>
      )}

      {plantilla && (
        <>
          <h4 style={{ marginTop: 14 }}>Plantilla sugerida</h4>
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 200 }}>
              <strong>{plantilla.nombre}</strong> <span className="pill">{plantilla.industria}</span>
              <div className="small muted">{plantilla.motivo}</div>
              <div className="small muted">Puedes aplicarla en «Libro de códigos» y luego modificar sus categorías.</div>
            </div>
            <Button size="sm" variant="secondary" onClick={() => navigate(`codigos${search}`)}>
              Ir a Libro de códigos <Icon name="arrowRight" size={16} />
            </Button>
          </div>
        </>
      )}
    </Card>
  );
}
