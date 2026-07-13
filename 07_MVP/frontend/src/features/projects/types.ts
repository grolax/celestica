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
}

export interface FrameworkTemplate {
  key: string;
  nombre: string;
  descripcion: string;
  n_categorias: number;
  marco_teorico: string;
  industria?: string;
}
