import { useEffect, useState } from "react";
import { analysisApi } from "../api";
import { ClosedOpcion, ClosedPregunta, ClosedResultsData } from "../types";
import Button from "@/shared/components/Button";
import Card, { StatCard } from "@/shared/components/Card";
import PageHeader from "@/shared/components/PageHeader";
import { useProject } from "@/features/projects/useProjectData";
import { TIPOS } from "@/features/projects/questionGroups";

const MAX_VISIBLES = 10;
const num = (n: number, max = 2) => n.toLocaleString("es-CL", { maximumFractionDigits: max }).replace("-", "−");
const pct = (n: number) => `${n.toLocaleString("es-CL", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} %`;
const conN = (x: { n: number; pct: number }) => `${pct(x.pct)} (${num(x.n, 0)})`;
const valores = (v: number[]) => v.join(" y ");

function Opciones({ opciones }: { opciones: ClosedOpcion[] }) {
  const [todas, setTodas] = useState(false);
  const visibles = todas ? opciones : opciones.slice(0, MAX_VISIBLES);
  return (
    <>
      {visibles.map((o) => (
        <div className="bar-row closed" key={o.valor}>
          <span title={o.valor}>{o.valor}</span>
          <div className="bar" aria-hidden="true" style={{ width: `${o.pct}%` }} />
          <span>{conN(o)}</span>
        </div>
      ))}
      {opciones.length > MAX_VISIBLES && (
        <Button size="sm" variant="secondary" onClick={() => setTodas(!todas)}>
          {todas ? "Ver menos" : `Ver todas (${opciones.length})`}
        </Button>
      )}
    </>
  );
}

function Pregunta({ q }: { q: ClosedPregunta }) {
  const { escala, nps, numerica } = q;
  const tipo = TIPOS.find(([t]) => t === q.tipo)?.[1] ?? q.tipo;
  return (
    <Card title={q.titulo}>
      <p className="muted small" style={{ marginTop: -4 }}>
        {tipo} · {num(q.n_respuestas, 0)} respondieron · {num(q.n_na, 0)} N/A ({pct(q.tasa_respuesta)} de respuesta)
      </p>
      {q.n_invalidas ? (
        <p className="small muted">{num(q.n_invalidas, 0)} respuestas no se pudieron leer como número y no se cuentan.</p>
      ) : null}

      {q.tipo === "escala" && escala && (
        <>
          <div className="stat-grid">
            <StatCard accent value={`${num(escala.promedio)} de ${num(escala.max, 0)}`} label="Promedio" />
            {escala.top2 && <StatCard value={pct(escala.top2.pct)} label={`Notas altas (${valores(escala.top2.valores)})`} />}
            {escala.bottom2 && <StatCard value={pct(escala.bottom2.pct)} label={`Notas bajas (${valores(escala.bottom2.valores)})`} />}
          </div>
          <p className="small muted">Desviación: {num(escala.desviacion)}</p>
        </>
      )}

      {q.tipo === "nps" && nps && (
        <>
          <div className="stat-grid">
            <StatCard accent value={(nps.valor > 0 ? "+" : "") + num(nps.valor)} label="NPS" />
            <StatCard value={conN(nps.promotores)} label="Promotores (9–10)" />
            <StatCard value={conN(nps.pasivos)} label="Pasivos (7–8)" />
            <StatCard value={conN(nps.detractores)} label="Detractores (0–6)" />
          </div>
          <p className="small muted">NPS = % de promotores − % de detractores. Va de −100 a +100.</p>
        </>
      )}

      {q.tipo === "numerica" && numerica && (
        <>
          <div className="stat-grid">
            <StatCard accent value={num(numerica.promedio)} label="Promedio" />
            <StatCard value={num(numerica.mediana)} label="Mediana" />
            <StatCard value={num(numerica.min)} label="Mínimo" />
            <StatCard value={num(numerica.max)} label="Máximo" />
          </div>
          <p className="small muted">Desviación: {num(numerica.desviacion)}</p>
        </>
      )}

      {q.opciones && <Opciones opciones={q.opciones} />}
      {q.nota && <p className="small muted" style={{ marginBottom: 0 }}>{q.nota}</p>}
    </Card>
  );
}

export default function ClosedResults() {
  const { project } = useProject();
  const [data, setData] = useState<ClosedResultsData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setData(null);
    setError("");
    analysisApi.getClosedResults(project.id).then(setData).catch((e) => setError(e.message));
  }, [project.id]);

  return (
    <>
      <PageHeader level={2} title="Preguntas cerradas"
        help="Estos números los calcula la plataforma directamente desde las respuestas, sin IA. Los porcentajes son sobre quienes respondieron cada pregunta; quienes no respondieron aparecen como N/A." />
      {error && <div className="alert alert-error">{error}</div>}
      {!data && !error && <p className="muted">Calculando resultados…</p>}
      {data && (
        <>
          <p className="muted">{num(data.n_personas, 0)} personas respondieron la encuesta</p>
          {data.preguntas.length === 0
            ? <p className="muted">Este proyecto no tiene preguntas cerradas.</p>
            : data.preguntas.map((q) => <Pregunta key={q.id} q={q} />)}
        </>
      )}
    </>
  );
}
