import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { projectsApi } from "./api";
import { FrameworkTemplate, Recomendaciones, VistaPrevia } from "./types";
import QuestionReview from "./QuestionReview";
import { aPreguntas, Fila, filasIniciales, CERRADAS, hayAbierta, hayCerrada, SIN_CONTEXTO } from "./questionGroups";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import PageHeader from "@/shared/components/PageHeader";
import Input, { TextArea } from "@/shared/components/Input";
import { integrationsApi } from "@/features/integrations/api";
import QualtricsSection from "@/features/integrations/QualtricsSection";

type Origin = "file" | "qualtrics" | "gforms";

const STEPS = ["Sube tu encuesta", "Revisa las preguntas", "Elige una plantilla", "Datos del proyecto"];
const AYUDA = [
  "Sube el archivo de tu encuesta o impórtala desde Qualtrics o Google Forms.",
  "Revisa qué detectamos en cada pregunta y corrige lo que no calce.",
  "Una plantilla trae un enfoque de análisis y categorías de partida, que tu equipo revisa antes de usarlas.",
  "Ponle nombre a tu proyecto y confirma qué se va a analizar.",
];

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
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [sugerida, setSugerida] = useState<Recomendaciones["plantilla"]>(null);
  const [verOtras, setVerOtras] = useState(false);
  const [preview, setPreview] = useState<VistaPrevia | null>(null);
  const [filas, setFilas] = useState<Fila[]>([]);
  const [reviewedKey, setReviewedKey] = useState("");

  useEffect(() => {
    projectsApi.listTemplates().then(setTemplates).catch(() => {});
  }, []);

  // key "" = sin plantilla. El marco cambia solo si está vacío o sigue igual al de la plantilla anterior.
  function elegir(key: string) {
    const marcoDe = (k: string) => templates.find((t) => t.key === k)?.marco_teorico ?? "";
    if (!marco || marco === marcoDe(templateKey)) setMarco(marcoDe(key));
    setTemplateKey(key);
  }

  // Agrupar las demás plantillas por industria preservando el orden del backend
  const industries: [string, FrameworkTemplate[]][] = [];
  for (const t of templates.filter((t) => t.key !== sugerida?.key)) {
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

  async function continuar() {
    setError("");
    if (!hayAbierta(filas)) return setStep(4);
    setBusy(true);
    let p: Recomendaciones["plantilla"] = null;
    try {
      p = (await projectsApi.suggestTemplate(aPreguntas(filas).map(({ titulo, tipo }) => ({ titulo, tipo })))).plantilla;
    } catch {
      // Sin sugerencia: la persona sigue igual y elige de la lista.
    }
    setSugerida(p);
    setVerOtras(templateKey !== "" && templateKey !== p?.key); // que la plantilla ya elegida no quede escondida
    setBusy(false);
    setStep(3);
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
  const errorDePreguntas = step === 4 && /pregunta|columna|identificaci/i.test(error);

  // Revisadas las preguntas y sin abiertas, no hay plantilla que elegir: el paso 3 se salta.
  const sinPlantilla = step > 1 && !hayAbierta(filas);
  const pasos = STEPS.map((label, i) => ({ label, n: i + 1 })).filter((p) => !(sinPlantilla && p.n === 3));
  const otrasAbiertas = !sugerida || verOtras;

  return (
    <form onSubmit={(e) => { e.preventDefault(); if (step === 4) crear(); else if (step === 1) revisar(); }}
          style={{ maxWidth: step === 2 ? 1000 : 760 }}>
      <PageHeader title="Nuevo proyecto de análisis" help={AYUDA[step - 1]} />
      <ol className="steps" aria-label="Pasos para crear el proyecto">
        {pasos.map(({ label, n }, i) => (
          <li key={label} aria-current={step === n ? "step" : undefined}
              className={step > n ? "done" : ""}>
            <span className="steps-n" aria-hidden="true">{step > n ? "✓" : i + 1}</span>
            {label}
            {step === n && <span className="sr-only"> (paso actual)</span>}
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
            <Button type="button" size="lg" busy={busy} disabled={!hayAbierta(filas) && !hayCerrada(filas)} onClick={continuar}>
              Continuar →
            </Button>
          </div>
        </Card>
      )}

      {step === 3 && (
      <>
      {sugerida && (
        <Card title="Te sugerimos esta plantilla">
          {(() => {
            const t = templates.find((x) => x.key === sugerida.key);
            return (
              <>
                <strong>{sugerida.nombre}</strong>{" "}
                <span className="pill">{sugerida.industria}</span>{t && <> <span className="pill">{t.n_categorias} categorías</span></>}
                <p className="small muted" style={{ margin: "6px 0 0" }}>{sugerida.motivo}</p>
                {t && <p className="small muted" style={{ margin: "4px 0 0" }}>{t.descripcion}</p>}
              </>
            );
          })()}
          <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            {templateKey === sugerida.key ? (
              <>
                <span className="small" style={{ color: "var(--success)", fontWeight: 600 }}>✓ Plantilla elegida</span>
                <Button type="button" size="sm" variant="secondary" onClick={() => elegir("")}>Quitar plantilla</Button>
              </>
            ) : (
              <Button type="button" size="sm" onClick={() => elegir(sugerida.key)}>Usar esta plantilla</Button>
            )}
          </div>
        </Card>
      )}

      <Card title="Marco teórico"
            actions={<span className="pill claude">ancla el análisis temático</span>}>
        {!sugerida && (
          <p className="small muted">
            No encontramos una plantilla que calce claramente con tu encuesta. Puedes elegir una de la lista o continuar sin plantilla.
          </p>
        )}
        {sugerida && industries.length > 0 && (
          <Button type="button" size="sm" variant="secondary" aria-expanded={otrasAbiertas}
                  onClick={() => setVerOtras(!verOtras)}>
            Ver otras plantillas
          </Button>
        )}
        {otrasAbiertas && industries.map(([industria, group]) => (
          <div key={industria} style={{ margin: "10px 0 14px" }}>
            <p className="small" style={{ fontWeight: 600, margin: "0 0 8px", textTransform: "uppercase", letterSpacing: "0.04em", color: "var(--primary)" }}>
              {industria}
            </p>
            <div style={{ display: "grid", gap: 10 }}>
              {group.map((t) => (
                <button key={t.key} type="button" aria-pressed={templateKey === t.key}
                        className={`template-option ${templateKey === t.key ? "selected" : ""}`}
                        onClick={() => elegir(templateKey === t.key ? "" : t.key)}>
                  <strong>{t.nombre}</strong>{" "}
                  <span className="pill">{t.n_categorias} categorías</span>
                  <span className="small muted" style={{ display: "block", margin: "4px 0 0" }}>{t.descripcion}</span>
                </button>
              ))}
            </div>
          </div>
        ))}
        <TextArea label="Marco teórico del proyecto" rows={4} value={marco}
                  onChange={(e) => setMarco(e.target.value)}
                  placeholder="Ej: Modelo de competencias docentes — dominio disciplinar, metodología, evaluación de aprendizajes, relación pedagógica. Las categorías propuestas por la IA se anclarán a este marco." />
        <p className="small muted" style={{ marginTop: 6 }}>Elegir otra plantilla cambia este texto, salvo que lo hayas editado.</p>
      </Card>

      <div className="qr-nav">
        <Button type="button" variant="secondary" size="lg" onClick={() => setStep(2)}>← Volver</Button>
        <Button type="button" size="lg" onClick={() => { setError(""); setStep(4); }}>Continuar →</Button>
        <Button type="button" variant="ghost" size="lg" onClick={() => navigate("/proyectos")}>Cancelar</Button>
      </div>
      </>
      )}

      {step === 4 && (
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

      <div className="qr-nav">
        <Button type="button" variant="secondary" size="lg" onClick={() => setStep(hayAbierta(filas) ? 3 : 2)}>← Volver</Button>
        <Button type="submit" busy={busy} size="lg">Crear proyecto</Button>
        <Button type="button" variant="ghost" size="lg" onClick={() => navigate("/proyectos")}>Cancelar</Button>
      </div>
      </>
      )}
      {step === 1 && (
        <div style={{ marginTop: 12 }}>
          <Button type="button" variant="ghost" onClick={() => navigate("/proyectos")}>Cancelar</Button>
        </div>
      )}
    </form>
  );
}
