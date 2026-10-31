import { useState } from "react";
import Button from "@/shared/components/Button";
import Input from "@/shared/components/Input";
import { ClosedGrupo, ClosedUnion } from "../types";
import { num } from "./format";

const CORTES = "18, 25, 35, 45, 55, 65";

interface Props {
  numerica: boolean;
  originales: ClosedGrupo[];
  unir: ClosedUnion[];
  error: string;
  busy: boolean;
  onCortes: (cortes?: string) => void;
  onUnir: (unir: ClosedUnion[]) => void;
}

/** Tramos (grupo numérico) o uniones de grupos; solo valen para este análisis, no se guardan. */
export default function GroupControls({ numerica, originales, unir, error, busy, onCortes, onUnir }: Props) {
  const [cortes, setCortes] = useState(CORTES);
  const [marcados, setMarcados] = useState<string[]>([]);
  const [nombre, setNombre] = useState("");
  const usados = unir.flatMap((u) => u.valores);

  if (numerica) {
    return (
      <div className="group-controls">
        <Input label="Tramos" value={cortes} error={error} disabled={busy} onChange={(e) => setCortes(e.target.value)}
               aria-describedby={error ? "in_Tramos_err ayuda_tramos" : "ayuda_tramos"} />
        <p className="small muted" id="ayuda_tramos">Cada número inicia un tramo. Por ejemplo, 18, 25, 35 da 18–24, 25–34 y 35 o más.</p>
        <div className="group-row">
          <Button size="sm" busy={busy} onClick={() => onCortes(cortes.replace(/\s/g, ""))}>Aplicar</Button>
          <Button size="sm" variant="secondary" disabled={busy} onClick={() => { setCortes(CORTES); onCortes(undefined); }}>
            Volver a los tramos por defecto
          </Button>
        </div>
      </div>
    );
  }

  const juntar = () => {
    onUnir([...unir, { nombre: nombre.trim(), valores: marcados }]);
    setMarcados([]);
    setNombre("");
  };
  return (
    <details className="group-controls">
      <summary>Juntar grupos</summary>
      <p className="small muted">Marca dos o más grupos, ponles un nombre y júntalos. Vale solo para este análisis: no se guarda.</p>
      <fieldset className="check-list">
        <legend className="sr-only">Grupos que se pueden juntar</legend>
        {originales.map((g) => (
          <label key={g.valor}>
            <input type="checkbox" disabled={busy || usados.includes(g.valor)} checked={marcados.includes(g.valor)}
                   onChange={(e) => setMarcados(e.target.checked ? [...marcados, g.valor] : marcados.filter((v) => v !== g.valor))} />
            {g.valor} <span className="muted">({num(g.n_personas, 0)} personas)</span>
          </label>
        ))}
      </fieldset>
      <Input label="Nombre del grupo nuevo" value={nombre} error={error} onChange={(e) => setNombre(e.target.value)} />
      <div className="group-row">
        <Button size="sm" busy={busy} disabled={marcados.length < 2 || !nombre.trim()} onClick={juntar}>Juntar</Button>
      </div>
      {unir.length > 0 && (
        <ul className="unions">
          {unir.map((u, i) => (
            <li key={u.nombre}>
              <span>{u.nombre}: {u.valores.join(", ")}</span>
              <Button size="sm" variant="secondary" disabled={busy} onClick={() => onUnir(unir.filter((_, j) => j !== i))}>
                Deshacer<span className="sr-only"> la unión «{u.nombre}»</span>
              </Button>
            </li>
          ))}
          <li><Button size="sm" variant="secondary" disabled={busy} onClick={() => onUnir([])}>Quitar todas</Button></li>
        </ul>
      )}
    </details>
  );
}
