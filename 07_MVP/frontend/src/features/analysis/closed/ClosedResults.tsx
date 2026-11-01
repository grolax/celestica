import { useEffect, useRef, useState } from "react";
import { analysisApi } from "../api";
import { ClosedGrupo, ClosedOpcion, ClosedPregunta, ClosedResultsData, ClosedUnion } from "../types";
import GroupControls from "./GroupControls";
import GroupTable from "./GroupTable";
import { conN, num, pct, valores } from "./format";
import Button from "@/shared/components/Button";
import Card, { StatCard } from "@/shared/components/Card";
import Icon from "@/shared/components/Icon";
import { useDownload } from "@/shared/hooks/useDownload";
import { exportApi } from "@/features/export/api";
import PageHeader from "@/shared/components/PageHeader";
import { useProject } from "@/features/projects/useProjectData";
import { TIPOS } from "@/features/projects/questionGroups";

const MAX_VISIBLES = 10;
const TIPOS_GRUPO = ["segmento", "seleccion_unica", "si_no", "numerica"];
const recortar = (t: string) => (t.length > 70 ? `${t.slice(0, 70)}…` : t);

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

function Pregunta({ q, grupos }: { q: ClosedPregunta; grupos?: ClosedGrupo[] }) {
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

      {grupos && q.por_grupo
        ? <GroupTable q={q} grupos={grupos} />
        : q.opciones && <Opciones opciones={q.opciones} />}
      {q.nota && <p className="small muted" style={{ marginBottom: 0 }}>{q.nota}</p>}
    </Card>
  );
}

export default function ClosedResults() {
  const { project } = useProject();
  const [data, setData] = useState<ClosedResultsData | null>(null);
  const [error, setError] = useState("");
  const [errorControl, setErrorControl] = useState(""); // 400 de tramos o uniones: se muestra junto al campo
  const [busy, setBusy] = useState(false);
  const [por, setPor] = useState("");
  const [cortes, setCortes] = useState<string | undefined>(); // tramos aplicados (lo que se ve), para el Excel
  const [unir, setUnir] = useState<ClosedUnion[]>([]);
  const descarga = useDownload();
  const [originales, setOriginales] = useState<ClosedGrupo[]>([]); // grupos sin unir, para las casillas
  const ultima = useRef(0);

  /** Pide los resultados; si falla, no cambia nada de lo que se ve y deja el error a quien llama. */
  const cargar = async (p: string, c?: string, u: ClosedUnion[] = []) => {
    const n = ++ultima.current;
    setBusy(true);
    try {
      const d = await analysisApi.getClosedResults(project.id, p ? { por: p, cortes: c, unir: u } : undefined);
      if (n !== ultima.current) return;
      setData(d); setPor(p); setCortes(c); setUnir(u); setError(""); setErrorControl("");
      if (!u.length) setOriginales(d.grupos ?? []);
    } finally {
      if (n === ultima.current) setBusy(false);
    }
  };

  useEffect(() => {
    setData(null);
    cargar("").catch((e) => setError(e.message));
  }, [project.id]);

  const cambiarPor = (p: string) => { setError(""); cargar(p).catch((e) => setError(e.message)); };
  const cambiarControl = (c: string | undefined, u: ClosedUnion[]) =>
    cargar(por, c, u).then(() => true, (e) => { setErrorControl(e.message); return false; }); // true = se aplicó
  const separables = project.preguntas.filter((q) => TIPOS_GRUPO.includes(q.tipo));
  const pocos = data?.grupos?.some((g) => g.pocos_datos);

  return (
    <>
      <PageHeader level={2} title="Preguntas cerradas"
        help="Estos números los calcula la plataforma directamente desde las respuestas, sin IA. Los porcentajes son sobre quienes respondieron cada pregunta; quienes no respondieron aparecen como N/A.">
        <Button variant="secondary" busy={descarga.busyKey === "closed-xlsx"} disabled={!data || busy}
                onClick={() => descarga.download("closed-xlsx", () =>
                  exportApi.downloadClosedXlsx(project.id, por ? { por, cortes, unir } : undefined))}>
          <Icon name="download" /> Descargar Excel
        </Button>
      </PageHeader>
      {(error || descarga.error) && <div className="alert alert-error">{error || descarga.error}</div>}
      {!data && !error && <p className="muted">Calculando resultados…</p>}
      {data && (
        <>
          <p className="muted">{num(data.n_personas, 0)} personas respondieron la encuesta</p>
          {separables.length > 0 && (
            <div className="pregunta-selector">
              <label className="field-label" htmlFor="ver_por">Ver por…</label>
              <select id="ver_por" value={por} onChange={(e) => cambiarPor(e.target.value)}>
                <option value="">Todas las personas (sin separar)</option>
                {separables.map((q) => <option key={q.id} value={q.id} title={q.titulo}>{recortar(q.titulo)}</option>)}
              </select>
            </div>
          )}
          {data.por && data.grupos && (
            <>
              <p className="muted">
                Separado por: {data.por.titulo}{/[.?!]$/.test(data.por.titulo) ? "" : "."} {num(data.grupos.length, 0)} grupos.
                {data.n_sin_grupo ? ` ${num(data.n_sin_grupo, 0)} personas no respondieron esta pregunta y no aparecen en ningún grupo.` : ""}
              </p>
              {pocos && (
                <p className="muted">
                  Los grupos marcados con «Pocos datos» tienen menos de {data.umbral_pocos_datos} personas: tómalos con cautela.
                </p>
              )}
              <GroupControls key={por} numerica={data.por.tipo === "numerica"} originales={originales} unir={unir}
                             error={errorControl} busy={busy}
                             onCortes={(c) => cambiarControl(c, [])} onUnir={(u) => cambiarControl(undefined, u)} />
            </>
          )}
          {data.preguntas.length === 0
            ? <p className="muted">Este proyecto no tiene preguntas cerradas.</p>
            : data.preguntas.map((q) => <Pregunta key={q.id} q={q} grupos={data.grupos} />)}
        </>
      )}
    </>
  );
}
