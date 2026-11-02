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

type Alerta = Recomendaciones["alertas"][number];

const RESUMEN: Record<string, (k: number) => string> = {
  muchas_vacias: (k) => `${k} preguntas tienen más de la mitad sin responder.`,
  abierta_repetida: (k) => `${k} preguntas abiertas tienen respuestas muy repetidas: quizás son cerradas.`,
  abierta_corta: (k) => `${k} preguntas abiertas tienen respuestas muy cortas: el análisis de temas tendrá poco material.`,
  cerrada_dispersa: (k) => `${k} preguntas cerradas tienen casi tantas opciones como respuestas: quizás son abiertas.`,
};

const clase = (g: Alerta[]) => (g.some((a) => a.nivel === "importante") ? "alert-error" : "alert-warning");

/** Agrupa por `id` las alertas por pregunta; las generales y las desconocidas quedan una por una. */
function alertasAgrupadas(alertas: Alerta[]): Alerta[][] {
  const grupos: Alerta[][] = [];
  const porId: Record<string, Alerta[]> = {};
  for (const a of alertas) {
    if (!RESUMEN[a.id]) grupos.push([a]);
    else if (porId[a.id]) porId[a.id].push(a);
    else grupos.push((porId[a.id] = [a]));
  }
  return grupos;
}

function AlertaGrupo({ alertas }: { alertas: Alerta[] }) {
  const [abierto, setAbierto] = useState(false);
  return (
    <div className={`alert ${clase(alertas)}`}>
      {RESUMEN[alertas[0].id](alertas.length)}{" "}
      <button type="button" className="qr-link" style={{ color: "inherit", fontWeight: 700 }} aria-expanded={abierto} onClick={() => setAbierto(!abierto)}>
        {abierto ? "Ocultar" : `Ver cuáles (${alertas.length})`}
      </button>
      {abierto && (
        <ul style={{ margin: "6px 0 0", paddingLeft: 20 }}>
          {alertas.map((a) => (
            <li key={a.pregunta_id ?? a.mensaje}>{a.mensaje}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

/** Alertas, cruces y plantilla sugeridos (RF-41). No se muestra si está vacía o si la consulta falla.
 *  `onVerPor`: si la pantalla que la contiene ya muestra las preguntas cerradas, separa ahí en vez de navegar. */
export default function Recommendations({ onVerPor }: { onVerPor?: (por: string, ver?: string) => void }) {
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
  if (!rec.alertas.length && !rec.cruces.length && !rec.segmentos.length && !plantilla) return null;

  const verPor = (por: string, ver?: string) => {
    if (onVerPor) return onVerPor(por, ver);
    const p = new URLSearchParams(search);
    p.set("por", por);
    if (ver) p.set("ver", ver); else p.delete("ver");
    navigate(`cerradas?${p}`);
  };

  return (
    <Card title="Recomendaciones">
      <p className="small muted" style={{ marginTop: -4 }}>
        Sugerencias automáticas según tus respuestas, calculadas con reglas fijas (sin IA).
      </p>
      {alertasAgrupadas(rec.alertas).map((g) =>
        g.length > 1 ? (
          <AlertaGrupo key={g[0].id} alertas={g} />
        ) : (
          <div key={g[0].id + (g[0].pregunta_id ?? "")} className={`alert ${clase(g)}`}>
            {g[0].mensaje}
          </div>
        ),
      )}

      {(rec.cruces.length > 0 || rec.segmentos.length > 0) && (
        <>
          <h4 style={{ marginTop: 14 }}>Cruces sugeridos</h4>
          {/* Sin pares (no hay escalas ni NPS) se sugieren solo los grupos, como antes. */}
          {(rec.cruces.length > 0
            ? rec.cruces.map((c) => ({
                key: `${c.por}|${c.ver}`, motivo: c.motivo, boton: "Ver este cruce", abrir: () => verPor(c.por, c.ver),
                titulo: <><strong title={c.por_titulo}>{recortar(c.por_titulo)}</strong> × <strong title={c.ver_titulo}>{recortar(c.ver_titulo)}</strong></>,
              }))
            : rec.segmentos.map((s) => ({
                key: s.pregunta_id, motivo: s.motivo, boton: "Ver por este grupo", abrir: () => verPor(s.pregunta_id),
                titulo: <strong title={s.titulo}>{recortar(s.titulo)}</strong>,
              }))
          ).map((f) => (
            <div key={f.key} style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", padding: "8px 0", borderBottom: "1px solid var(--border-soft)" }}>
              <div style={{ flex: 1, minWidth: 200 }}>
                {f.titulo}
                <div className="small muted">{f.motivo}</div>
              </div>
              <Button size="sm" variant="secondary" onClick={f.abrir}>
                {f.boton} <Icon name="arrowRight" size={16} />
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
