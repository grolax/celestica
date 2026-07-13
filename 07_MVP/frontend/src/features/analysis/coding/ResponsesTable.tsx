import Table, { ConfBadge } from "@/shared/components/Table";
import { Category, Coding as CodingT, ResponseItem } from "../types";

/** Tabla de respuestas con sus codificaciones y selector de re-codificación. */
export default function ResponsesTable({ items, categories, validated, onRecode }: {
  items: ResponseItem[];
  categories: Category[];
  validated: Category[];
  onRecode: (responseId: string, categoryId: string) => void;
}) {
  const catName = (cid: string) =>
    cid === "SIN_CATEGORIA" ? "Sin categoría" : categories.find((c) => c.id === cid)?.nombre ?? cid;

  return (
    <Table headers={["ID", "Respuesta", "Sentimiento", "Codificación", "Re-codificar"]}>
      {items.map((r) => (
        <tr key={r.id}>
          <td className="muted">{r.id}</td>
          <td style={{ maxWidth: 340 }}>{r.text}</td>
          <td>{r.sentiment ? <span className={`pill ${r.sentiment.label}`}>{r.sentiment.label}</span> : <span className="muted">—</span>}</td>
          <td>
            {r.codings.length === 0 && <span className="muted">no codificada</span>}
            {r.codings.map((c: CodingT, i: number) => (
              <div key={i} style={{ marginBottom: 6 }}>
                <strong>{catName(c.category_id)}</strong>{" "}
                <span className={`pill ${c.source}`}>{c.source}</span>
                <ConfBadge value={c.confidence} />
                <br />
                <span className="small muted">{c.rationale}</span>
              </div>
            ))}
          </td>
          <td>
            <select defaultValue="" onChange={(e) => e.target.value && onRecode(r.id, e.target.value)}>
              <option value="">— elegir —</option>
              {validated.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
          </td>
        </tr>
      ))}
    </Table>
  );
}
