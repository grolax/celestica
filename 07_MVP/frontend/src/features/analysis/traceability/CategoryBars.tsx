import Card from "@/shared/components/Card";
import { ProjectStats } from "../types";

/** Distribución de respuestas por categoría (barras horizontales). */
export default function CategoryBars({ stats }: { stats: ProjectStats }) {
  if (stats.by_category.length === 0) return null;
  const maxCat = stats.by_category[0]?.count ?? 1;

  return (
    <Card title="Respuestas por categoría">
      {stats.by_category.map((c) => (
        <div className="bar-row" key={c.category_id}>
          <span title={c.nombre}>{c.nombre}</span>
          <div className="bar" style={{ width: `${(c.count / maxCat) * 100}%` }} />
          <span className="muted">{c.count}</span>
        </div>
      ))}
    </Card>
  );
}
