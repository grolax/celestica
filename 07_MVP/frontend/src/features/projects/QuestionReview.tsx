import { useId } from "react";
import Button from "@/shared/components/Button";
import Table from "@/shared/components/Table";
import { TipoPregunta } from "./types";
import {
  baseTitulo, contextoPorDefecto, deshacer, Fila, gruposPendientes, hayAbierta,
  incluirPorDefecto, SIN_CONTEXTO, TIPOS, unir,
} from "./questionGroups";

const CON_OPCIONES: TipoPregunta[] = ["seleccion_unica", "seleccion_multiple", "segmento", "si_no"];
const HEADERS = ["Incluir", "Pregunta", "Tipo", "Respuestas", "Contexto para la IA"];

function FilaPregunta({ f, onChange, onUndo }: {
  f: Fila; onChange: (parche: Partial<Fila>) => void; onUndo: () => void;
}) {
  const id = useId();
  const sinContexto = SIN_CONTEXTO.includes(f.tipo);
  const unicas = f.opciones?.filter((o) => o.n === 1).length ?? 0;
  return (
    <tr>
      <td>
        <input type="checkbox" checked={f.incluir} aria-label={`Incluir «${f.titulo}»`}
               onChange={(e) => onChange({ incluir: e.target.checked })} />
      </td>
      <td>
        {f.origen ? (
          <>
            <input type="text" value={f.titulo} aria-label={`Título de la pregunta unida «${f.titulo}»`}
                   onChange={(e) => onChange({ titulo: e.target.value })} />
            <p className="small muted qr-help">
              Unida desde {f.columnas.length} columnas.{" "}
              <button type="button" className="qr-link" onClick={onUndo}>Deshacer</button>
            </p>
          </>
        ) : <div className="qr-title" title={f.titulo}>{f.titulo}</div>}
        {f.tipo === "abierta" && f.ejemplos.length > 0 && (
          <ul className="qr-ejemplos small muted">
            {f.ejemplos.slice(0, 3).map((e, i) => <li key={i} title={e}>“{e}”</li>)}
          </ul>
        )}
        {CON_OPCIONES.includes(f.tipo) && !!f.opciones?.length && (
          <details className="small">
            <summary>Ver opciones</summary>
            <ul className="qr-ejemplos">
              {f.opciones.filter((o) => o.n > 1).map((o) => <li key={o.valor}>{o.valor} · {o.n}</li>)}
              {unicas > 0 && <li>Otras respuestas ({unicas})</li>}
            </ul>
          </details>
        )}
      </td>
      <td>
        <select value={f.tipo} aria-label={`Tipo de «${f.titulo}»`} aria-describedby={`${id}m`}
                onChange={(e) => {
                  const tipo = e.target.value as TipoPregunta;
                  onChange({ tipo, incluir: incluirPorDefecto(tipo), contexto: contextoPorDefecto(f.titulo, tipo) });
                }}>
          {TIPOS.map(([k, label]) => <option key={k} value={k}>{label}</option>)}
        </select>
        <p className="small muted qr-help" id={`${id}m`}>{f.motivo}</p>
      </td>
      <td>
        {f.n_respuestas}
        {f.n_na > 0 && <div className="small muted">N/A {f.n_na}</div>}
      </td>
      <td>
        <input type="checkbox" checked={f.contexto && !sinContexto} disabled={sinContexto}
               aria-label={`Contexto para la IA: «${f.titulo}»${sinContexto ? " (no se envía a la IA)" : ""}`}
               onChange={(e) => onChange({ contexto: e.target.checked })} />
        {sinContexto && <div className="small muted">No se envía a la IA</div>}
      </td>
    </tr>
  );
}

export default function QuestionReview({ filas, setFilas, nFilas, nColumnas, advertencias }: {
  filas: Fila[]; setFilas: (fn: (fs: Fila[]) => Fila[]) => void;
  nFilas: number; nColumnas: number; advertencias: string[];
}) {
  const pendientes = gruposPendientes(filas);
  // Las columnas ramificadas ya tienen su aviso de unión: no repetir su advertencia de "vacías".
  const ramificadas = new Set(filas.filter((f) => f.columnas.length > 1 || pendientes.some(([b]) => b === baseTitulo(f.titulo))).flatMap((f) => f.columnas));
  const avisos = advertencias.filter((a) => ![...ramificadas].some((c) => a.includes(`«${c}»`)));
  const cambiar = (f: Fila) => (parche: Partial<Fila>) => setFilas((fs) => fs.map((x) => (x === f ? { ...x, ...parche } : x)));
  const seccion = (titulo: string, sub: string | null, lista: Fila[]) => lista.length > 0 && (
    <div style={{ marginTop: 18 }}>
      <h3 style={{ margin: 0 }}>{titulo}</h3>
      {sub && <p className="small muted" style={{ margin: "2px 0 8px" }}>{sub}</p>}
      <Table headers={HEADERS}>
        {lista.map((f) => (
          <FilaPregunta key={f.columnas.join("|")} f={f} onChange={cambiar(f)}
                        onUndo={() => setFilas((fs) => deshacer(fs, f))} />
        ))}
      </Table>
    </div>
  );

  return (
    <div>
      <h2 style={{ marginBottom: 4 }}>Revisa las preguntas detectadas</h2>
      <p className="muted">
        Encontramos {nFilas} respuestas y {nColumnas} columnas. Revisa el tipo de cada una; puedes cambiarlo si no corresponde.
      </p>
      {avisos.map((a) => <div key={a} className="alert alert-info">{a}</div>)}
      {pendientes.map(([base, n]) => (
        <div key={base} className="alert alert-warning qr-aviso">
          <span>«{base}» aparece en {n} columnas. Si las unes, cada persona queda con su respuesta en una sola pregunta.</span>
          <Button type="button" size="sm" variant="secondary" onClick={() => setFilas((fs) => unir(fs, base, nFilas))}>
            Unir en una
          </Button>
        </div>
      ))}
      {!hayAbierta(filas) && (
        <div className="alert alert-warning" role="status">
          Necesitas al menos una pregunta abierta para analizar. El análisis de preguntas cerradas llegará pronto.
        </div>
      )}
      {seccion("Preguntas abiertas", "Se analizan con IA, una por una, cuando tú lo pidas.", filas.filter((f) => f.tipo === "abierta"))}
      {seccion("Otras preguntas", null, filas.filter((f) => f.tipo !== "abierta"))}
      <p className="small muted" style={{ marginTop: 14 }}>
        <strong>Contexto para la IA:</strong> la IA solo recibe el texto de la pregunta abierta y lo que marques aquí.
        Los datos de identificación (nombre, RUT, email) nunca se envían.
      </p>
    </div>
  );
}
