import { useEffect, useState } from "react";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import { useAsync } from "@/shared/hooks/useAsync";
import { projectsApi } from "@/features/projects/api";
import { FrameworkTemplate } from "@/features/projects/types";
import { useProject } from "@/features/projects/useProjectData";
import { analysisApi } from "../api";
import CategoryCard from "./CategoryCard";
import ManualCategoryForm from "./ManualCategoryForm";

export default function Codebook() {
  const { project, refresh } = useProject();
  const { busy, error, setError, run } = useAsync();
  const [templates, setTemplates] = useState<FrameworkTemplate[]>([]);

  useEffect(() => {
    if (project.categories.length === 0) {
      projectsApi.listTemplates().then(setTemplates).catch(() => {});
    }
  }, [project.categories.length]);

  async function propose() {
    const ok = await run(() => analysisApi.proposeCategories(project.id));
    if (ok) refresh();
  }

  async function applyTemplate(key: string) {
    const ok = await run(() => projectsApi.applyTemplate(project.id, key));
    if (ok) refresh();
  }

  const nValidated = project.categories.filter((c) => c.status === "validada").length;

  // Plantillas agrupadas por industria (mismo criterio que en Nuevo Proyecto)
  const industries: [string, FrameworkTemplate[]][] = [];
  for (const t of templates) {
    const ind = t.industria ?? "General";
    const entry = industries.find(([name]) => name === ind);
    if (entry) entry[1].push(t);
    else industries.push([ind, [t]]);
  }

  return (
    <>
      {error && <div className="alert alert-error">{error}</div>}
      <Card title="Capa 2 · Libro de códigos"
            actions={<span className="pill ok">{nValidated} validadas</span>}>
        <p className="muted">
          Claude propone categorías ancladas al marco teórico; <strong>tu equipo decide</strong> cuáles
          forman el libro de códigos. Cada decisión queda en el registro de auditoría.
        </p>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <Button onClick={propose} busy={busy}>
            {busy ? "Claude está analizando la muestra…" : "Proponer categorías con IA"}
          </Button>
          {templates.length > 0 && (
            <select style={{ width: "auto" }} disabled={busy} value=""
                    onChange={(e) => e.target.value && applyTemplate(e.target.value)}>
              <option value="">Aplicar plantilla…</option>
              {industries.map(([industria, group]) => (
                <optgroup key={industria} label={industria}>
                  {group.map((t) => (
                    <option key={t.key} value={t.key} title={t.descripcion}>
                      {t.nombre} ({t.n_categorias} categorías)
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          )}
        </div>
      </Card>

      <div className="cat-grid">
        {project.categories.map((c) => (
          <CategoryCard key={c.id} category={c} projectId={project.id} onChange={refresh} onError={setError} />
        ))}
      </div>

      <ManualCategoryForm projectId={project.id} onChange={refresh} onError={setError} />
    </>
  );
}
