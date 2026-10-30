import { Category } from "@/features/analysis/types";

export interface ProjectSummary {
  id: string;
  name: string;
  created_at: string;
  n_responses: number;
  has_lexical: boolean;
  n_categories: number;
  n_coded: number;
  has_report: boolean;
}

export interface Project {
  id: string;
  name: string;
  marco_teorico: string;
  created_at: string;
  columns: string[];
  text_column: string;
  categories: Category[];
  n_responses: number;
  has_lexical: boolean;
  n_coded: number;
  has_report: boolean;
  n_audit_events: number;
  preguntas: Pregunta[];
  /** Id de la pregunta que se está mostrando. */
  pregunta: string;
}

export interface FrameworkTemplate {
  key: string;
  nombre: string;
  descripcion: string;
  n_categorias: number;
  marco_teorico: string;
  industria?: string;
}

export type TipoPregunta =
  | "abierta" | "escala" | "nps" | "si_no" | "seleccion_unica" | "seleccion_multiple"
  | "numerica" | "fecha" | "identificador" | "segmento" | "constante" | "sin_datos";

export interface PreguntaDetectada {
  columna: string;
  tipo: TipoPregunta;
  motivo: string;
  n_respuestas: number;
  n_vacias: number;
  valores_distintos: number;
  ejemplos: string[];
  escala?: { min: number; max: number };
  opciones?: { valor: string; n: number }[];
}

export interface VistaPrevia {
  n_filas: number;
  preguntas: PreguntaDetectada[];
  advertencias: string[];
}

/** Lo que el usuario confirmó en la vista previa y se envía al crear el proyecto. */
export interface PreguntaProyecto {
  titulo: string;
  columnas: string[];
  tipo: TipoPregunta;
  contexto_ia: boolean;
}

/** Pregunta guardada en el proyecto (RF-23, T-011a). */
export interface Pregunta extends PreguntaProyecto {
  id: string;
  n_respuestas: number;
  n_na: number;
}
