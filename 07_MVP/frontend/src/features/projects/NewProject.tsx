import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { projectsApi } from "./api";
import { FrameworkTemplate, VistaPrevia } from "./types";
import QuestionReview from "./QuestionReview";
import { aPreguntas, Fila, filasIniciales, CERRADAS, hayAbierta, hayCerrada, SIN_CONTEXTO } from "./questionGroups";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import PageHeader from "@/shared/components/PageHeader";
import Input, { TextArea } from "@/shared/components/Input";
import { integrationsApi } from "@/features/integrations/api";
import QualtricsSection from "@/features/integrations/QualtricsSection";

type Origin = "file" | "qualtrics" | "gforms";

const STEPS = ["Sube tu encuesta", "Revisa las preguntas", "Datos del proyecto"];

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
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [preview, setPreview] = useState<VistaPrevia | null>(null);
  const [filas, setFilas] = useState<Fila[]>([]);
  const [reviewedKey, setReviewedKey] = useState("");

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

  const previewKey = origin === "file" ? (file ? `f:${file.name}:${file.size}:${file.lastModified}` : "")
    : origin === "qualtrics" ? `q:${surveyId}` : `g:${sheetUrl.trim()}`;

  async function revisar() {
    if (origin === "file" && !file) return setError("Falta el archivo de datos.");
    if (origin === "qualtrics" && !surveyId) return setError("Elige una encuesta de Qualtrics para importar.");
    if (origin === "gforms" && !sheetUrl.trim()) return setError("Pega la URL de la planilla de respuestas de Google Sheets.");
    setError("");
    if (previewKey === reviewedKey) return setStep(2); // mismos datos: se conservan los cambios hechos
    setBusy(true);
    try {
      const vp = origin === "qualtrics" ? await projectsApi.previewQualtrics(surveyId)
        : origin === "gforms" ? await projectsApi.previewGoogleForms(sheetUrl.trim())
        : await projectsApi.preview(file!);
      setPreview(vp);
      setFilas(filasIniciales(vp));
      setReviewedKey(previewKey);
      setStep(2);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function crear() {
    if (!name.trim()) {
      setError("Falta el nombre del proyecto.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const preguntas = aPreguntas(filas);
      // Sin abiertas no hay análisis con IA: el marco teórico y la plantilla no se envían.
      const ia = hayAbierta(filas);
      const common = { name: name.trim(), marco_teorico: ia ? marco : "", template: ia ? templateKey : "", preguntas };
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
        form.append("preguntas", JSON.stringify(preguntas));
        if (common.template) form.append("template", common.template);
        ({ id } = await projectsApi.createProject(form));
      }
      navigate(`/proyectos/${id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const incluidas = filas.filter((f) => f.incluir);
  const nAbiertas = incluidas.filter((f) => f.tipo === "abierta").length;
  const nCerradas = incluidas.filter((f) => CERRADAS.includes(f.tipo)).length;
  const cuenta = (n: number, uno: string, varias: string) => (n === 1 ? `1 ${uno}` : `${n} ${varias}`);
  const contexto = incluidas.filter((f) => f.contexto && !SIN_CONTEXTO.includes(f.tipo)).map((f) => `«${f.titulo}»`);
  const errorDePreguntas = step === 3 && /pregunta|columna|identificaci/i.test(error);

  return (
    <form onSubmit={(e) => { e.preventDefault(); if (step === 3) crear(); else if (step === 1) revisar(); }}
          style={{ maxWidth: step === 2 ? 1000 : 760 }}>
      <PageHeader title="Nuevo proyecto de análisis"
                  help="Sube tu encuesta, revisa las preguntas que detectamos y ponle nombre a tu proyecto." />
      <ol className="steps" aria-label="Pasos para crear el proyecto">
        {STEPS.map((label, i) => (
          <li key={label} aria-current={step === i + 1 ? "step" : undefined}
              className={step > i + 1 ? "done" : ""}>
            <span className="steps-n" aria-hidden="true">{step > i + 1 ? "✓" : i + 1}</span>
            {label}
            {step === i + 1 && <span className="sr-only"> (paso actual)</span>}
          </li>
        ))}
      </ol>
      {error && (
        <div className="alert alert-error" role="alert">
          {error}
          {errorDePreguntas && (
            <> <Button type="button" size="sm" variant="secondary" onClick={() => { setError(""); setStep(2); }}>
              Volver a revisar las preguntas
            </Button></>
          )}
        </div>
      )}

      {step === 1 && (
      <Card title="Sube tu encuesta">
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
            <label className="field-label" htmlFor="archivo">Archivo de datos (CSV o XLSX)</label>
            <input id="archivo" type="file" accept=".csv,.xlsx,.xls"
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
            <Input label="URL de la planilla de respuestas (Google Sheets)" type="text" value={sheetUrl}
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
          En el siguiente paso verás qué detectamos en cada columna y podrás corregirlo.
        </p>
        <div style={{ marginTop: 14 }}>
          <Button type="button" size="lg" busy={busy} onClick={revisar}>Revisar preguntas →</Button>
        </div>
      </Card>
      )}

      {step === 2 && preview && (
        <Card>
          <QuestionReview filas={filas} setFilas={setFilas} nFilas={preview.n_filas}
                          nColumnas={preview.preguntas.length} advertencias={preview.advertencias} />
          <div className="qr-nav">
            <Button type="button" variant="secondary" size="lg" onClick={() => setStep(1)}>← Volver</Button>
            <Button type="button" size="lg" disabled={!hayAbierta(filas) && !hayCerrada(filas)} onClick={() => { setError(""); setStep(3); }}>
              Continuar →
            </Button>
          </div>
        </Card>
      )}

      {step === 3 && (
      <>
      <Card title="Datos del proyecto">
        <Input label="Nombre del proyecto" type="text" value={name} onChange={(e) => setName(e.target.value)}
               placeholder="Ej: Evaluación Docente 2026-1" required autoFocus />
        <p className="small muted" style={{ marginTop: 10 }}>
          {nAbiertas + nCerradas === 1 ? "Se analizará " : "Se analizarán "}
          {[nAbiertas > 0 && cuenta(nAbiertas, "pregunta abierta", "preguntas abiertas"),
            nCerradas > 0 && cuenta(nCerradas, "pregunta cerrada", "preguntas cerradas")].filter(Boolean).join(" y ")}
          {nAbiertas === 0 ? ", sin IA." : <>;{" "}
            {contexto.length === 0 ? "ninguna pregunta irá como contexto a la IA."
              : `${contexto.length === 1 ? "1 pregunta irá" : `${contexto.length} preguntas irán`} como contexto a la IA: ${contexto.join(", ")}.`}</>}
        </p>
      </Card>

      {nAbiertas > 0 && (
      <Card title="Marco teórico"
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
      )}

      <div className="qr-nav">
        <Button type="button" variant="secondary" size="lg" onClick={() => setStep(2)}>← Volver</Button>
        <Button type="submit" busy={busy} size="lg">Crear proyecto</Button>
        <Button type="button" variant="ghost" size="lg" onClick={() => navigate("/proyectos")}>Cancelar</Button>
      </div>
      </>
      )}
      {step !== 3 && step !== 2 && (
        <div style={{ marginTop: 12 }}>
          <Button type="button" variant="ghost" onClick={() => navigate("/proyectos")}>Cancelar</Button>
        </div>
      )}
    </form>
  );
}
