import { PreguntaDetectada, PreguntaProyecto, TipoPregunta, VistaPrevia } from "./types";

export const TIPOS: [TipoPregunta, string][] = [
  ["abierta", "Abierta"], ["escala", "Escala"], ["nps", "NPS"], ["si_no", "Sí / No"],
  ["seleccion_unica", "Selección única"], ["seleccion_multiple", "Selección múltiple"],
  ["numerica", "Numérica"], ["fecha", "Fecha"], ["identificador", "Identificador"],
  ["segmento", "Segmento"], ["constante", "Constante"], ["sin_datos", "Sin datos"],
];

/** Fila editable del paso "Revisa las preguntas": una columna detectada o varias unidas. */
export interface Fila extends Omit<PreguntaDetectada, "columna" | "n_vacias" | "valores_distintos" | "escala"> {
  titulo: string;
  columnas: string[];
  n_na: number;
  incluir: boolean;
  contexto: boolean;
  origen?: Fila[]; // filas originales de una unión, para "Deshacer"
}

const SIN_INCLUIR: TipoPregunta[] = ["constante", "sin_datos"];
export const SIN_CONTEXTO: TipoPregunta[] = ["identificador", "abierta", "fecha", "constante", "sin_datos"];

const sinTildes = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

// Mismo criterio que el backend (question_types.py): género, sexo o edad en el título.
export const contextoPorDefecto = (titulo: string, tipo: TipoPregunta) =>
  ["segmento", "numerica", "seleccion_unica"].includes(tipo) && /\b(genero|sexo|edad)\b/.test(sinTildes(titulo));

export const incluirPorDefecto = (tipo: TipoPregunta) => !SIN_INCLUIR.includes(tipo);

export const filasIniciales = (vp: VistaPrevia): Fila[] =>
  vp.preguntas.map(({ columna, n_vacias, valores_distintos: _v, escala: _e, ...p }) => {
    const titulo = columna.trim();
    return { ...p, titulo, columnas: [columna], n_na: n_vacias,
             incluir: incluirPorDefecto(p.tipo), contexto: contextoPorDefecto(titulo, p.tipo) };
  });

/** Título sin espacios finales ni el número final de las columnas ramificadas ("… 2"). */
export const baseTitulo = (t: string) => t.trim().replace(/\s+\d+$/, "").trim();

/** Títulos base que aparecen en 2 o más columnas aún sin unir, con su cantidad. */
export function gruposPendientes(filas: Fila[]): [string, number][] {
  const cuenta = new Map<string, number>();
  for (const f of filas) if (f.columnas.length === 1) cuenta.set(baseTitulo(f.titulo), (cuenta.get(baseTitulo(f.titulo)) ?? 0) + 1);
  return [...cuenta].filter(([, n]) => n > 1);
}

export function unir(filas: Fila[], base: string, nFilas: number): Fila[] {
  const grupo = filas.filter((f) => f.columnas.length === 1 && baseTitulo(f.titulo) === base);
  const votos = new Map<string, number>();
  for (const g of grupo) votos.set(g.tipo, (votos.get(g.tipo) ?? 0) + 1);
  const tipo = [...votos].sort((a, b) => b[1] - a[1])[0][0] as TipoPregunta; // empate: gana el primero
  const opciones = new Map<string, number>();
  for (const o of grupo.flatMap((g) => g.opciones ?? [])) opciones.set(o.valor, (opciones.get(o.valor) ?? 0) + o.n);
  const n_respuestas = grupo.reduce((s, g) => s + g.n_respuestas, 0);
  const unida: Fila = {
    titulo: base, columnas: grupo.flatMap((g) => g.columnas), tipo,
    motivo: grupo.find((g) => g.tipo === tipo)!.motivo,
    n_respuestas, n_na: Math.max(0, nFilas - n_respuestas), // cada persona responde en una sola columna
    ejemplos: grupo.flatMap((g) => g.ejemplos).slice(0, 3),
    opciones: opciones.size ? [...opciones].map(([valor, n]) => ({ valor, n })).sort((a, b) => b.n - a.n) : undefined,
    incluir: incluirPorDefecto(tipo), contexto: contextoPorDefecto(base, tipo), origen: grupo,
  };
  return filas.flatMap((f) => (f === grupo[0] ? [unida] : grupo.includes(f) ? [] : [f]));
}

export const deshacer = (filas: Fila[], unida: Fila): Fila[] =>
  filas.flatMap((f) => (f === unida ? unida.origen! : [f]));

export const hayAbierta = (filas: Fila[]) => filas.some((f) => f.incluir && f.tipo === "abierta");

export const aPreguntas = (filas: Fila[]): PreguntaProyecto[] =>
  filas.filter((f) => f.incluir).map((f) => ({
    titulo: f.titulo.trim() || f.columnas[0].trim(), columnas: f.columnas, tipo: f.tipo,
    contexto_ia: f.contexto && !SIN_CONTEXTO.includes(f.tipo),
  }));
