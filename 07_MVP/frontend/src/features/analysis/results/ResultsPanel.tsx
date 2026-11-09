import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { projectsApi } from "@/features/projects/api";
import { Recomendaciones } from "@/features/projects/types";
import { useProject } from "@/features/projects/useProjectData";
import Button from "@/shared/components/Button";
import Card, { StatCard } from "@/shared/components/Card";
import PageHeader from "@/shared/components/PageHeader";
import { analysisApi } from "../api";
import { ClosedPregunta, ClosedResultsData, TemasDePregunta, TemasPrincipalesData } from "../types";
import GroupTable from "../closed/GroupTable";
import { num, pct, valores } from "../closed/format";

const MAX_ESCALAS = 6;
const MAX_SEGMENTOS = 3;
const personas = (x: { n: number; pct: number }) => `${pct(x.pct)} · ${num(x.n, 0)} personas`;
// En una tarjeta de cifra el % va grande y las personas en la etiqueta.
const cifra = (x: { n: number; pct: number }, label: string) => ({ value: pct(x.pct), label: `${label} · ${num(x.n, 0)} personas` });

/** Todas las NPS y las primeras 6 escalas o sí/no, en el orden que entrega la API. */
const elegirMetricas = (qs: ClosedPregunta[]) => {
  let otras = 0;
  return qs.filter((q) => q.tipo === "nps" || ((q.tipo === "escala" || q.tipo === "si_no") && ++otras <= MAX_ESCALAS));
};

function Metrica({ q, sep }: { q: ClosedPregunta; sep?: ClosedResultsData }) {
  const { escala, nps } = q;
  return (
    <Card title={<h4 style={{ margin: 0 }}>{q.titulo}</h4>}>
      <p className="muted small" style={{ marginTop: -4 }}>{num(q.n_respuestas, 0)} personas respondieron esta pregunta</p>
      {sep?.grupos && q.por_grupo ? <GroupTable q={q} grupos={sep.grupos} /> : (
        <>
          {q.tipo === "nps" && nps && (
            <>
              <div className="stat-grid">
                <StatCard accent value={(nps.valor > 0 ? "+" : "") + num(nps.valor)} label="NPS" />
                <StatCard {...cifra(nps.promotores, "Promotores: recomiendan (9–10)")} />
                <StatCard {...cifra(nps.pasivos, "Pasivos: neutrales (7–8)")} />
                <StatCard {...cifra(nps.detractores, "Detractores: no recomiendan (0–6)")} />
              </div>
              <p className="small muted" style={{ marginBottom: 0 }}>El NPS va de −100 a +100: mientras más alto, más personas recomiendan.</p>
            </>
          )}
          {q.tipo === "escala" && escala && (
            <div className="stat-grid" style={{ marginBottom: 0 }}>
              <StatCard accent value={`${num(escala.promedio)} de ${num(escala.max, 0)}`} label="Promedio" />
              {escala.top2 && <StatCard {...cifra(escala.top2, `Notas altas (${valores(escala.top2.valores)})`)} />}
            </div>
          )}
          {q.tipo === "si_no" && q.opciones?.map((o) => (
            <div className="bar-row closed" key={o.valor}>
              <span>{o.valor}</span>
              <div className="bar" aria-hidden="true" style={{ width: `${o.pct}%` }} />
              <span>{personas(o)}</span>
            </div>
          ))}
        </>
      )}
    </Card>
  );
}

function Temas({ q }: { q: TemasDePregunta }) {
  return (
    <Card title={<h4 style={{ margin: 0 }}>{q.titulo}</h4>}>
      {q.temas.length === 0 && <p className="muted">Esta pregunta todavía no tiene temas listos para mostrar.</p>}
      {q.temas.map((t) => (
        <div className="tema" key={t.category_id}>
          <div className="tema-head">
            <strong>{t.nombre}</strong>
            <span>{num(t.personas, 0)} personas · {pct(t.porcentaje)}</span>
          </div>
          <div className="bar" aria-hidden="true" style={{ width: `${t.porcentaje}%` }} />
          <p className="small muted">{t.definicion}</p>
          {t.citas.map((c, i) => <blockquote key={i}>{c}</blockquote>)}
        </div>
      ))}
      <p className="small muted" style={{ marginBottom: 0 }}>
        {q.temas.length > 0 && `Porcentajes sobre ${num(q.n_codificadas, 0)} respuestas analizadas. Una persona puede mencionar más de un tema.`}
        {q.n_codificadas < q.n_respuestas && ` Se han analizado ${num(q.n_codificadas, 0)} de ${num(q.n_respuestas, 0)} respuestas.`}
        {q.n_temas > q.temas.length && ` Se muestran los ${q.temas.length} temas más mencionados de ${q.n_temas}.`}
      </p>
    </Card>
  );
}

/** Pantalla "Resultados" para lectores (RF-43): cifras clave, temas con citas y alertas, imprimible. Solo lectura y sin IA. */
export default function ResultsPanel() {
  const { project } = useProject();
  const pregunta = useSearchParams()[0].get("pregunta");
  const [base, setBase] = useState<ClosedResultsData | null>(null); // sin separar: manda el conteo y qué preguntas se muestran
  const [sep, setSep] = useState<ClosedResultsData>();
  const [por, setPor] = useState("");
  const [busy, setBusy] = useState(false);
  const [errCerradas, setErrCerradas] = useState("");
  const [temas, setTemas] = useState<TemasPrincipalesData | null>(null);
  const [errTemas, setErrTemas] = useState("");
  const [rec, setRec] = useState<Recomendaciones | null>(null);
  const ultima = useRef(0);

  useEffect(() => {
    let vigente = true;
    ultima.current++; // una respuesta lenta del proyecto anterior no pisa a este
    setBase(null); setSep(undefined); setPor(""); setBusy(false); setTemas(null); setRec(null); setErrCerradas(""); setErrTemas("");
    analysisApi.getClosedResults(project.id).then((d) => vigente && setBase(d)).catch((e) => vigente && setErrCerradas(e.message));
    analysisApi.getTemasPrincipales(project.id).then((d) => vigente && setTemas(d)).catch((e) => vigente && setErrTemas(e.message));
    projectsApi.getRecommendations(project.id).then((d) => vigente && setRec(d)).catch(() => {}); // sin alertas ni "Ver por…", sin mensaje
    return () => { vigente = false; };
  }, [project.id]);

  const elegir = (p: string) => {
    const n = ++ultima.current;
    setErrCerradas("");
    if (!p) { setPor(""); setSep(undefined); setBusy(false); return; }
    setBusy(true);
    analysisApi.getClosedResults(project.id, { por: p })
      .then((d) => { if (n === ultima.current) { setSep(d); setPor(p); } })
      .catch((e) => { if (n === ultima.current) setErrCerradas(e.message); })
      .finally(() => { if (n === ultima.current) setBusy(false); });
  };

  const metricas = base ? elegirMetricas(base.preguntas) : [];
  const ids = new Set(metricas.map((q) => q.id));
  const visibles = (sep ?? base)?.preguntas.filter((q) => ids.has(q.id)) ?? [];
  const otras = base ? base.preguntas.length - metricas.length : 0;
  const segmentos = rec?.segmentos.slice(0, MAX_SEGMENTOS) ?? [];
  const generales = rec?.alertas.filter((a) => a.pregunta_id == null) ?? [];
  const pocos = sep?.grupos?.some((g) => g.pocos_datos);

  return (
    <>
      <PageHeader level={2} title="Resultados"
        help="Un resumen de lo que respondieron las personas: cifras clave, los temas más mencionados y avisos sobre la encuesta.">
        <Button className="no-print" variant="secondary" onClick={() => window.print()}>Imprimir</Button>
      </PageHeader>
      {errCerradas && <div className="alert alert-error">{errCerradas}</div>}
      {errTemas && <div className="alert alert-error">{errTemas}</div>}
      {((!base && !errCerradas) || (!temas && !errTemas)) && <p className="muted">Cargando resultados…</p>}
      {base && <p className="muted">{num(base.n_personas, 0)} personas respondieron la encuesta</p>}
      {generales.map((a) => (
        <div key={a.id + a.mensaje} className={`alert ${a.nivel === "importante" ? "alert-error" : "alert-warning"}`}>{a.mensaje}</div>
      ))}

      {metricas.length > 0 && (
        <section className="results-panel">
          <h3>Cifras clave</h3>
          {segmentos.length > 0 && (
            <div className="pregunta-selector no-print">
              <label className="field-label" htmlFor="resultados_ver_por">Ver por…</label>
              <select id="resultados_ver_por" value={por} onChange={(e) => elegir(e.target.value)}>
                <option value="">Todas las personas (sin separar)</option>
                {segmentos.map((s) => <option key={s.pregunta_id} value={s.pregunta_id}>{s.titulo}</option>)}
              </select>
              {busy && <p className="small muted" role="status">Calculando…</p>}
            </div>
          )}
          {sep?.por && sep.grupos && (
            <p className="muted">
              Separado por: {sep.por.titulo}{/[.?!]$/.test(sep.por.titulo) ? "" : "."}
              {pocos && ` Los grupos marcados con «Pocos datos» tienen menos de ${sep.umbral_pocos_datos} personas: tómalos con cautela.`}
              {!!sep.n_sin_grupo && ` ${num(sep.n_sin_grupo, 0)} personas no respondieron esta pregunta y no aparecen en ningún grupo.`}
            </p>
          )}
          {visibles.map((q) => <Metrica key={q.id} q={q} sep={sep} />)}
          {otras > 0 && (
            <p className="no-print">
              <Link to={`/proyectos/${project.id}/cerradas${pregunta ? `?pregunta=${encodeURIComponent(pregunta)}` : ""}`}>
                Ver las otras {otras} preguntas
              </Link>
            </p>
          )}
        </section>
      )}

      {temas && temas.preguntas.length > 0 && (
        <section>
          <h3>Temas principales</h3>
          <p className="small muted">
            Temas revisados y validados por tu equipo. La IA ayudó a clasificar las respuestas; las cifras las calcula la plataforma.
          </p>
          {temas.preguntas.map((q) => <Temas key={q.pregunta_id} q={q} />)}
        </section>
      )}
    </>
  );
}
