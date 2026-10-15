import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { projectsApi } from "./api";
import { FrameworkTemplate } from "./types";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import Input, { TextArea } from "@/shared/components/Input";
import { integrationsApi } from "@/features/integrations/api";
import QualtricsSection from "@/features/integrations/QualtricsSection";

type Origin = "file" | "qualtrics" | "gforms";

const ORIGINS: [Origin, string][] = [
  ["file", "Subir archivo"],
  ["qualtrics", "Qualtrics"],
  ["gforms", "Google Forms"],
];

export default function NewProject() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [marco, setMarco] = useState("");
  const [origin, setOrigin] = useState<Origin>("file");
  const [file, setFile] = useState<File | null>(null);
  const [surveyId, setSurveyId] = useState("");
  const [surveyName, setSurveyName] = useState("");
  const [sheetUrl, setSheetUrl] = useState("");
  const [templates, setTemplates] = useState<FrameworkTemplate[]>([]);
  const [templateKey, setTemplateKey] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    projectsApi.listTemplates().then(setTemplates).catch(() => {});
  }, []);

  function pickTemplate(key: string) {
    if (templateKey === key) {
      setTemplateKey("");
      return;
    }
    setTemplateKey(key);
    const tpl = templates.find((t) => t.key === key);
    if (tpl && !marco) setMarco(tpl.marco_teorico);
  }

  // Agrupar plantillas por industria preservando el orden del backend
  const industries: [string, FrameworkTemplate[]][] = [];
  for (const t of templates) {
    const ind = t.industria ?? "General";
    const entry = industries.find(([name]) => name === ind);
    if (entry) entry[1].push(t);
    else industries.push([ind, [t]]);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      setError("Falta el nombre del proyecto.");
      return;
    }
    if (origin === "file" && !file) {
      setError("Falta el archivo de datos.");
      return;
    }
    if (origin === "qualtrics" && !surveyId) {
      setError("Elige una encuesta de Qualtrics para importar.");
      return;
    }
    if (origin === "gforms" && !sheetUrl.trim()) {
      setError("Pega la URL de la planilla de respuestas de Google Sheets.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const common = { name: name.trim(), marco_teorico: marco, template: templateKey };
      let id: string;
      if (origin === "qualtrics") {
        ({ id } = await integrationsApi.createFromQualtrics({ ...common, survey_id: surveyId, survey_name: surveyName }));
      } else if (origin === "gforms") {
        ({ id } = await integrationsApi.createFromGoogleForms({ ...common, sheet_url: sheetUrl.trim() }));
      } else {
        const form = new FormData();
        form.append("file", file!);
        form.append("name", common.name);
        form.append("marco_teorico", common.marco_teorico);
        if (templateKey) form.append("template", templateKey);
        ({ id } = await projectsApi.createProject(form));
      }
      navigate(`/proyectos/${id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} style={{ maxWidth: 760 }}>
      <h1 style={{ marginBottom: 18 }}>Nuevo proyecto de análisis</h1>
      {error && <div className="alert alert-error">{error}</div>}

      <Card title="1 · Datos del proyecto">
        <Input label="Nombre del proyecto" value={name} onChange={(e) => setName(e.target.value)}
               placeholder="Ej: Evaluación Docente 2026-1" required autoFocus />

        <label className="field-label">Origen de los datos</label>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
          {ORIGINS.map(([key, label]) => (
            <Button key={key} type="button" size="sm"
                    variant={origin === key ? "primary" : "secondary"}
                    onClick={() => { setOrigin(key); setError(""); }}>
              {label}
            </Button>
          ))}
        </div>

        {origin === "file" && (
          <>
            <label className="field-label">Datos (CSV o XLSX con una columna de respuestas abiertas)</label>
            <input type="file" accept=".csv,.xlsx,.xls"
                   onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </>
        )}

        {origin === "qualtrics" && (
          <QualtricsSection surveyId={surveyId}
                            onSelect={(id, n) => { setSurveyId(id); setSurveyName(n); }}
                            onError={setError} />
        )}

        {origin === "gforms" && (
          <div style={{ maxWidth: 560 }}>
            <Input label="URL de la planilla de respuestas (Google Sheets)" value={sheetUrl}
                   onChange={(e) => setSheetUrl(e.target.value)}
                   placeholder="https://docs.google.com/spreadsheets/d/…" />
            <p className="small muted" style={{ marginTop: 6 }}>
              En tu Google Form: Respuestas → Vincular con Hojas de cálculo. Luego comparte esa planilla
              como <strong>"Cualquiera con el enlace puede ver"</strong> y pega aquí su URL.
              Importación puntual: para actualizar datos después, crea un nuevo proyecto.
            </p>
          </div>
        )}

        <p className="small muted" style={{ marginTop: 6 }}>
          Si los datos tienen varias columnas, Celestica detecta automáticamente la columna de texto
          (la de mayor largo promedio).
        </p>
      </Card>

      <Card title="2 · Marco teórico"
            actions={<span className="pill claude">ancla el análisis temático</span>}>
        {templates.length > 0 && (
          <>
            <p className="small muted">Parte de una plantilla (opcional) — crea el marco y categorías base que tu equipo valida después:</p>
            {industries.map(([industria, group]) => (
              <div key={industria} style={{ marginBottom: 14 }}>
                <p className="small" style={{ fontWeight: 600, margin: "0 0 8px", textTransform: "uppercase", letterSpacing: "0.04em", color: "var(--primary)" }}>
                  {industria}
                </p>
                <div style={{ display: "grid", gap: 10 }}>
                  {group.map((t) => (
                    <div key={t.key}
                         className={`template-option ${templateKey === t.key ? "selected" : ""}`}
                         onClick={() => pickTemplate(t.key)}>
                      <strong>{t.nombre}</strong>{" "}
                      <span className="pill">{t.n_categorias} categorías</span>
                      <p className="small muted" style={{ margin: "4px 0 0" }}>{t.descripcion}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </>
        )}
        <TextArea label="Marco teórico del proyecto" rows={4} value={marco}
                  onChange={(e) => setMarco(e.target.value)}
                  placeholder="Ej: Modelo de competencias docentes — dominio disciplinar, metodología, evaluación de aprendizajes, relación pedagógica. Las categorías propuestas por la IA se anclarán a este marco." />
      </Card>

      <div style={{ display: "flex", gap: 10 }}>
        <Button type="submit" busy={busy} size="lg">Crear proyecto</Button>
        <Button type="button" variant="secondary" size="lg" onClick={() => navigate("/")}>Cancelar</Button>
      </div>
    </form>
  );
}
