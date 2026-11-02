import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
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
import { CERRADAS, TIPOS } from "@/features/projects/questionGroups";
import Recommendations from "@/features/projects/Recommendations";

const MAX_VISIBLES = 10;
const TIPOS_GRUPO = ["segmento", "seleccion_unica", "si_no", "numerica"];
const recortar = (t: string) => (t.length > 70 ? `${t.slice(0, 70)}…` : t);
const TODAS = "todas"; // valor del selector "Pregunta"; un id de pregunta nunca se llama así

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
        {q.n_na * 2 > q.n_respuestas + q.n_na && (
          <>
            {" "}
            <span className="pill propuesta" title="Más de la mitad de las personas no respondió esta pregunta">Poco respondida</span>
          </>
        )}
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
  const [ver, setVer] = useState(""); // "" = sin elegir, TODAS o el id de la pregunta (lo aplicado, no lo pendiente)
  const [cortes, setCortes] = useState<string | undefined>(); // tramos aplicados (lo que se ve), para el Excel
  const [unir, setUnir] = useState<ClosedUnion[]>([]);
  const descarga = useDownload();
  const [originales, setOriginales] = useState<ClosedGrupo[]>([]); // grupos sin unir, para las casillas
  const ultima = useRef(0);
  // Grupo pedido en la dirección: solo vale para el proyecto con que se montó la pantalla (y sobrevive al doble efecto de StrictMode).
  const [params] = useSearchParams();
  const porUrl = useRef({ id: project.id, por: params.get("por") ?? "", ver: params.get("ver") ?? "" });
  const cerradas = project.preguntas.filter((q) => CERRADAS.includes(q.tipo));

  /** Pide los resultados; si falla, no cambia nada de lo que se ve y deja el error a quien llama. */
  const cargar = async (p: string, v: string, c?: string, u: ClosedUnion[] = []) => {
    const n = ++ultima.current;
    setBusy(true);
    try {
      // Sin pregunta elegida solo hacen falta los grupos (para tramos y uniones): se pide una sola pregunta, que no se muestra.
      const pedida = v === TODAS ? undefined : v || cerradas.find((q) => q.id !== p)?.id;
      const d = await analysisApi.getClosedResults(project.id, p ? { por: p, ver: pedida, cortes: c, unir: u } : undefined);
      if (n !== ultima.current) return;
      setData(d); setPor(p); setVer(p ? v : ""); setCortes(c); setUnir(u); setError(""); setErrorControl("");
      if (!u.length) setOriginales(d.grupos ?? []);
    } finally {
      if (n === ultima.current) setBusy(false);
    }
  };

  useEffect(() => {
    setData(null);
    const { id, por: pedido, ver: pedidoVer } = porUrl.current;
    const inicial = id === project.id && TIPOS_GRUPO.includes(project.preguntas.find((q) => q.id === pedido)?.tipo ?? "") ? pedido : "";
    const verInicial = inicial && pedidoVer !== inicial && cerradas.some((q) => q.id === pedidoVer) ? pedidoVer : "";
    cargar(inicial, verInicial).catch((e) => setError(e.message));
  }, [project.id]);

  const aplicar = (p: string, v = "") => { setError(""); cargar(p, v).catch((e) => setError(e.message)); };
  // Cambiar solo la pregunta conserva los tramos y los grupos unidos que ya se ven (y que lleva el Excel).
  const cambiarPregunta = (v: string) => { setError(""); cargar(por, v, cortes, unir).catch((e) => setError(e.message)); };
  const cambiarControl = (c: string | undefined, u: ClosedUnion[]) =>
    cargar(por, ver, c, u).then(() => true, (e) => { setErrorControl(e.message); return false; }); // true = se aplicó
  const separables = project.preguntas.filter((q) => TIPOS_GRUPO.includes(q.tipo));
  const pocos = data?.grupos?.some((g) => g.pocos_datos);
  const sinElegir = !!por && !ver; // con "Ver por…" falta elegir la pregunta

  return (
    <>
      <PageHeader level={2} title="Preguntas cerradas"
        help="Estos números los calcula la plataforma directamente desde las respuestas, sin IA. Los porcentajes son sobre quienes respondieron cada pregunta; quienes no respondieron aparecen como N/A.">
        <Button variant="secondary" busy={descarga.busyKey === "closed-xlsx"} disabled={!data || busy || sinElegir}
                title={sinElegir ? "Elige una pregunta para descargar" : undefined}
                onClick={() => descarga.download("closed-xlsx", () =>
                  exportApi.downloadClosedXlsx(project.id, por ? { por, ver: ver === TODAS ? undefined : ver, cortes, unir } : undefined))}>
          <Icon name="download" /> Descargar Excel
        </Button>
      </PageHeader>
      {(error || descarga.error) && <div className="alert alert-error">{error || descarga.error}</div>}
      {!data && !error && <p className="muted">Calculando resultados…</p>}
      {data && (
        <>
          <p className="muted">{num(data.n_personas, 0)} personas respondieron la encuesta</p>
          {project.pregunta == null && <Recommendations onVerPor={aplicar} />}
          {separables.length > 0 && (
            <div className="pregunta-selector">
              <label className="field-label" htmlFor="ver_por">Ver por…</label>
              <select id="ver_por" value={por} onChange={(e) => aplicar(e.target.value)}>
                <option value="">Todas las personas (sin separar)</option>
                {separables.map((q) => <option key={q.id} value={q.id} title={q.titulo}>{recortar(q.titulo)}</option>)}
              </select>
            </div>
          )}
          {por && (
            <div className="pregunta-selector">
              <label className="field-label" htmlFor="ver_pregunta">Pregunta</label>
              <select id="ver_pregunta" value={ver} disabled={busy} onChange={(e) => cambiarPregunta(e.target.value)}>
                <option value="">Elige una pregunta…</option>
                <option value={TODAS}>Todas las preguntas</option>
                {cerradas.filter((q) => q.id !== por).map((q) => <option key={q.id} value={q.id} title={q.titulo}>{recortar(q.titulo)}</option>)}
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
          {sinElegir
            ? <p className="muted">Elige qué pregunta quieres ver separada por «{data.por?.titulo}», o «Todas las preguntas».</p>
            : data.preguntas.length === 0
            ? <p className="muted">Este proyecto no tiene preguntas cerradas.</p>
            : data.preguntas.map((q) => <Pregunta key={q.id} q={q} grupos={data.grupos} />)}
        </>
      )}
    </>
  );
}
