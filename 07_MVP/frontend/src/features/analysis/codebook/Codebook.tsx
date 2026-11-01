import { useEffect, useState } from "react";
import { useAuth } from "@/features/auth/useAuth";
import { puede } from "@/features/auth/api";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import PageHeader from "@/shared/components/PageHeader";
import { ApiError } from "@/shared/api/client";
import { usePolling } from "@/shared/hooks/usePolling";
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
  const canEdit = puede(useAuth().user, "analista");
  const [templates, setTemplates] = useState<FrameworkTemplate[]>([]);
  const [waiting, setWaiting] = useState(false); // el servidor sigue proponiendo (otra visita a la pestaña o 409)
  const { start, stop } = usePolling(2000);

  // Al entrar o cambiar de pregunta: retoma una propuesta que siga en curso.
  useEffect(() => {
    let off = false;
    analysisApi.getAnalysisStatus(project.id, project.pregunta)
      .then((s) => { if (!off && s.propose === "running") setWaiting(true); }).catch(() => {});
    return () => { off = true; setWaiting(false); };
  }, [project.id, project.pregunta]);

  // Mientras espera, consulta cada 2 s; al quedar libre trae las categorías nuevas sin recargar la página.
  useEffect(() => {
    if (!waiting) return;
    let off = false;
    start(async () => {
      try {
        const s = await analysisApi.getAnalysisStatus(project.id, project.pregunta);
        if (off || s.propose !== "idle") return;
        off = true;
        stop();
        setWaiting(false);
        refresh();
      } catch { /* se reintenta en el próximo ciclo */ }
    });
    return () => { off = true; stop(); };
  }, [waiting, project.id, project.pregunta]);

  useEffect(() => {
    if (canEdit && project.categories.length === 0) {
      projectsApi.listTemplates().then(setTemplates).catch(() => {});
    }
  }, [canEdit, project.categories.length]);

  async function propose() {
    const ok = await run(async () => {
      try {
        return await analysisApi.proposeCategories(project.id, project.pregunta);
      } catch (e) {
        if (!(e instanceof ApiError && e.status === 409)) throw e;
        setWaiting(true); // ya se está proponiendo: no es un error, se espera
        return null;
      }
    });
    if (ok) refresh();
  }

  async function applyTemplate(key: string) {
    const ok = await run(() => projectsApi.applyTemplate(project.id, project.pregunta, key));
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
      <PageHeader level={2} title="Libro de códigos" help="Los temas para clasificar las respuestas. La IA los propone y tu equipo los revisa y valida.">
        <span className="pill ok">{nValidated} validadas</span>
      </PageHeader>
      {error && <div className="alert alert-error">{error}</div>}
      {canEdit && <Card>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <Button onClick={propose} busy={busy || waiting}>
            {busy || waiting ? "Claude está analizando la muestra…" : "Proponer categorías con IA"}
          </Button>
          {templates.length > 0 && (
            <select style={{ width: "auto" }} disabled={busy || waiting} value=""
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
      </Card>}

      <div className="cat-grid">
        {project.categories.map((c) => (
          <CategoryCard key={c.id} category={c} projectId={project.id} onChange={refresh} onError={setError} />
        ))}
      </div>

      {canEdit && <ManualCategoryForm projectId={project.id} onChange={refresh} onError={setError} />}
      {!canEdit && project.categories.length === 0 && <p className="muted">Aún no hay categorías. Un analista de tu organización las propondrá y validará.</p>}
    </>
  );
}
