import { useMemo, useState } from "react";

export type TraceRow = Record<string, unknown>;

/** Estado y lógica de filtrado de la tabla de trazabilidad
 * (categoría, fuente, nivel de confianza y búsqueda de texto). */
export function useTraceabilityFilters(rows: TraceRow[]) {
  const [filterCat, setFilterCat] = useState("");
  const [filterSource, setFilterSource] = useState("");
  const [filterConf, setFilterConf] = useState("");
  const [search, setSearch] = useState("");

  const categories = useMemo(
    () => Array.from(new Set(rows.map((r) => String(r.categoria)))).sort(),
    [rows]
  );

  const filtered = useMemo(() => rows.filter((r) => {
    if (filterCat && String(r.categoria) !== filterCat) return false;
    if (filterSource && String(r.fuente) !== filterSource) return false;
    if (filterConf) {
      const conf = r.confianza != null ? Number(r.confianza) : null;
      if (conf == null) return false;
      if (filterConf === "alta" && conf < 0.85) return false;
      if (filterConf === "media" && (conf < 0.6 || conf >= 0.85)) return false;
      if (filterConf === "baja" && conf >= 0.6) return false;
    }
    if (search && !String(r.texto).toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  }), [rows, filterCat, filterSource, filterConf, search]);

  return {
    filtered, categories,
    filterCat, setFilterCat,
    filterSource, setFilterSource,
    filterConf, setFilterConf,
    search, setSearch,
  };
}
