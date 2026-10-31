import { ReactNode, useState } from "react";
import Button from "@/shared/components/Button";
import Table from "@/shared/components/Table";
import { ClosedGrupo, ClosedMetricas, ClosedPregunta } from "../types";
import { conN, num, pct, valores } from "./format";

const MAX_COLUMNAS = 6;
const SIN_DATO = "—";

/** Tabla de una pregunta con una fila por grupo (RF-31). Todas las cifras vienen del backend. */
export default function GroupTable({ q, grupos }: { q: ClosedPregunta; grupos: ClosedGrupo[] }) {
  const [todas, setTodas] = useState(false);
  const opciones = q.opciones ?? [];
  const categorica = q.tipo !== "escala" && q.tipo !== "nps" && q.tipo !== "numerica";
  const opcionesVisibles = todas ? opciones : opciones.slice(0, MAX_COLUMNAS);

  let cabeceras: string[] = [];
  let celdas: (m: ClosedMetricas) => ReactNode[] = () => [];
  if (q.tipo === "escala") {
    cabeceras = ["Promedio", `Notas altas (${valores(q.escala?.top2?.valores ?? [])})`, `Notas bajas (${valores(q.escala?.bottom2?.valores ?? [])})`];
    celdas = (m) => [m.escala && num(m.escala.promedio), m.escala?.top2 && pct(m.escala.top2.pct), m.escala?.bottom2 && pct(m.escala.bottom2.pct)];
  } else if (q.tipo === "nps") {
    cabeceras = ["NPS", "Promotores", "Detractores"];
    celdas = (m) => [m.nps && (m.nps.valor > 0 ? "+" : "") + num(m.nps.valor), m.nps && conN(m.nps.promotores), m.nps && conN(m.nps.detractores)];
  } else if (q.tipo === "numerica") {
    cabeceras = ["Promedio", "Mediana", "Mínimo", "Máximo"];
    celdas = (m) => [m.numerica && num(m.numerica.promedio), m.numerica && num(m.numerica.mediana), m.numerica && num(m.numerica.min), m.numerica && num(m.numerica.max)];
  } else {
    cabeceras = opcionesVisibles.map((o) => o.valor);
    celdas = (m) => opcionesVisibles.map((o) => { const x = m.opciones?.find((y) => y.valor === o.valor); return x && conN(x); });
  }

  const fila = (nombre: ReactNode, m: ClosedMetricas, key: string) => (
    <tr key={key}>
      <td>{nombre}</td>
      <td>{num(m.n_respuestas, 0)}</td>
      {celdas(m).map((c, i) => <td key={i}>{m.n_respuestas === 0 || c == null ? SIN_DATO : c}</td>)}
    </tr>
  );

  return (
    <div className="group-table">
      <Table headers={["Grupo", "Respondieron", ...cabeceras]}>
        {fila(<strong>Todas las personas</strong>, q, "total")}
        {grupos.map((g, i) => fila(
          <>
            <span title={g.unidos?.join(", ")}>{g.valor}</span>{" "}
            {g.pocos_datos && <span className="pill propuesta">Pocos datos</span>}
            {g.unidos && <div className="small muted">Junta: {g.unidos.join(", ")}</div>}
          </>,
          q.por_grupo?.[i] ?? { n_respuestas: 0, n_na: 0, tasa_respuesta: 0 }, g.valor))}
      </Table>
      {categorica && opciones.length > MAX_COLUMNAS && (
        <Button size="sm" variant="secondary" onClick={() => setTodas(!todas)}>
          {todas ? "Ver menos" : `Ver todas las opciones (${opciones.length})`}
        </Button>
      )}
    </div>
  );
}
