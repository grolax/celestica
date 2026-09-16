import { Fragment, useEffect, useState } from "react";
import { adminApi, AdminHealth, PromptEntry, PromptsData, UsageProject } from "./api";
import { ClaudeUsageTotals } from "@/features/analysis/types";
import { projectsApi } from "@/features/projects/api";
import { useAuth } from "@/features/auth/useAuth";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import Table from "@/shared/components/Table";
import Input, { TextArea } from "@/shared/components/Input";

const PROMPT_ORDER = ["propose_categories", "codify", "interpret_lexical", "qualitative_report"];

export default function Settings() {
  const { user } = useAuth();
  const [imported, setImported] = useState<number | null>(null);
  const [error, setError] = useState("");

  async function importLegacy() {
    try {
      const r = await projectsApi.importLegacy();
      setImported(r.imported);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <>
      <h1 style={{ marginBottom: 18 }}>Configuración</h1>
      {error && <div className="alert alert-error">{error}</div>}

      <Card title="Mi cuenta">
        <p><strong>{user?.nombre || "—"}</strong> · {user?.email}</p>
        {user?.empresa && <p className="muted">{user.empresa}</p>}
      </Card>

      <Card title="Importar proyectos antiguos">
        <p className="muted">
          Si usaste la versión demo de SoftInsight (sin cuentas), puedes importar esos proyectos a tu cuenta.
        </p>
        {imported !== null ? (
          <div className="alert alert-success" style={{ marginBottom: 0 }}>
            {imported > 0 ? `${imported} proyecto(s) importado(s). Revisa "Mis proyectos".` : "No hay proyectos antiguos por importar."}
          </div>
        ) : (
          <Button variant="secondary" onClick={importLegacy}>Importar proyectos de la demo</Button>
        )}
      </Card>

      <AdminPrompts />
    </>
  );
}

/* ---- Panel de administración: prompts metodológicos (uso interno del equipo) ---- */

function AdminPrompts() {
  const [password, setPassword] = useState("");
  const [authenticated, setAuthenticated] = useState(false);
  const [prompts, setPrompts] = useState<PromptsData | null>(null);
  const [defaults, setDefaults] = useState<PromptsData | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState(false);
  const [usage, setUsage] = useState<{ projects: UsageProject[]; total: ClaudeUsageTotals; log_dir: string } | null>(null);
  const [health, setHealth] = useState<AdminHealth | null>(null);

  async function loadUsage(pwd: string) {
    try {
      const [u, h] = await Promise.all([adminApi.getUsage(pwd), adminApi.getHealth(pwd)]);
      setUsage(u);
      setHealth(h);
    } catch {
      /* el consumo es informativo: si falla no bloquea el panel */
    }
  }

  async function login() {
    if (!password) return;
    setBusy(true);
    setError("");
    try {
      const data = await adminApi.getPrompts(password);
      setPrompts(data.prompts);
      setDefaults(data.defaults);
      setAuthenticated(true);
      loadUsage(password);
    } catch {
      setError("Contraseña incorrecta.");
    } finally {
      setBusy(false);
    }
  }

  async function handleSave(key: string, system: string, instructions: string) {
    const updated = await adminApi.updatePrompt(password, key, { system, instructions });
    setPrompts((prev) => prev ? { ...prev, [key]: { ...prev[key], ...updated } } : prev);
  }

  async function handleReset(key: string) {
    if (!confirm("¿Restaurar este prompt a los valores por defecto?")) return;
    const reset = await adminApi.resetPrompt(password, key);
    setPrompts((prev) => prev ? { ...prev, [key]: { ...prev[key], ...reset } } : prev);
  }

  return (
    <Card
      title="Configuración metodológica (equipo SoftInsight)"
      actions={<Button variant="ghost" size="sm" onClick={() => setOpen(!open)}>{open ? "Ocultar" : "Abrir"}</Button>}
    >
      <p className="muted" style={{ marginBottom: open ? 12 : 0 }}>
        Prompts que definen cómo Claude analiza, categoriza e interpreta. Sección de uso interno,
        protegida por contraseña de administración.
      </p>
      {open && !authenticated && (
        <div style={{ maxWidth: 380 }}>
          {error && <div className="alert alert-error">{error}</div>}
          <Input label="Contraseña de administración" type="password" value={password}
                 onChange={(e) => setPassword(e.target.value)}
                 onKeyDown={(e) => e.key === "Enter" && login()} placeholder="••••••••••••" />
          <div style={{ marginTop: 10 }}>
            <Button onClick={login} busy={busy} disabled={!password}>Ingresar</Button>
          </div>
        </div>
      )}
      {open && authenticated && (
        <UsagePanel usage={usage} health={health} onRefresh={() => loadUsage(password)} />
      )}
      {open && authenticated && prompts && defaults && (
        <>
          <div className="alert alert-info">
            Cada prompt tiene dos partes: <strong>Rol y metodología</strong> (quién es Claude, qué tradición
            sigue) e <strong>Instrucciones de output</strong> (qué produce y cómo). Los datos del proyecto se
            inyectan automáticamente. Los cambios toman efecto de inmediato.
          </div>
          {PROMPT_ORDER.filter((k) => prompts[k]).map((key) => (
            <PromptEditor key={key} promptKey={key} entry={prompts[key]} onSave={handleSave} onReset={handleReset} />
          ))}
        </>
      )}
    </Card>
  );
}

function PromptEditor({ promptKey, entry, onSave, onReset }: {
  promptKey: string;
  entry: PromptEntry;
  onSave: (key: string, system: string, instructions: string) => Promise<void>;
  onReset: (key: string) => Promise<void>;
}) {
  const [system, setSystem] = useState(entry.system);
  const [instructions, setInstructions] = useState(entry.instructions);
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => { setSystem(entry.system); setInstructions(entry.instructions); }, [entry]);

  const isDirty = system !== entry.system || instructions !== entry.instructions;

  async function save() {
    setStatus("saving");
    setErrorMsg("");
    try {
      await onSave(promptKey, system, instructions);
      setStatus("saved");
      setTimeout(() => setStatus("idle"), 3000);
    } catch (e) {
      setStatus("error");
      setErrorMsg((e as Error).message);
    }
  }

  return (
    <div style={{ borderTop: "1px solid var(--border-soft)", paddingTop: 16, marginTop: 16 }}>
      <div className="card-title">
        <div>
          <h3 style={{ margin: 0 }}>{entry.label}</h3>
          <p className="muted small" style={{ margin: "3px 0 0" }}>{entry.description}</p>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {status === "saved" && <span className="pill ok">Guardado ✓</span>}
          {status === "error" && <span className="pill descartada">{errorMsg}</span>}
          <Button variant="danger" size="sm" onClick={() => onReset(promptKey)}>Restaurar default</Button>
          <Button size="sm" onClick={save} disabled={!isDirty} busy={status === "saving"}>Guardar</Button>
        </div>
      </div>
      <TextArea label="Rol y metodología" className="prompt-textarea" rows={6} value={system}
                onChange={(e) => setSystem(e.target.value)} spellCheck={false} />
      <TextArea label="Instrucciones de output" className="prompt-textarea" rows={10} value={instructions}
                onChange={(e) => setInstructions(e.target.value)} spellCheck={false} />
      {isDirty && <p className="small muted" style={{ marginTop: 6 }}>Cambios sin guardar.</p>}
    </div>
  );
}

/* ---- Consumo de la API de Claude por proyecto + estado del backend ---- */

const fmtInt = (n?: number) => (n ?? 0).toLocaleString("es-CL");
const fmtUsd = (n?: number) => `US$ ${(n ?? 0).toFixed(2)}`;

function UsagePanel({ usage, health, onRefresh }: {
  usage: { projects: UsageProject[]; total: ClaudeUsageTotals; log_dir: string } | null;
  health: AdminHealth | null;
  onRefresh: () => void;
}) {
  const [expanded, setExpanded] = useState<string | null>(null);
  return (
    <div style={{ borderBottom: "1px solid var(--border-soft)", paddingBottom: 16, marginBottom: 16 }}>
      <div className="card-title">
        <div>
          <h3 style={{ margin: 0 }}>Consumo de la API de Claude</h3>
          <p className="muted small" style={{ margin: "3px 0 0" }}>
            Tokens y costo estimado por proyecto (precios configurables en el backend; es una estimación, no la factura).
            {health && <> Backend: <code>thematic {health.thematic_version}</code> · modelo informe <code>{health.model_report_v2}</code></>}
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={onRefresh}>Actualizar</Button>
      </div>
      {!usage ? (
        <p className="muted small">Sin datos de consumo todavía.</p>
      ) : (
        <>
          <p className="small" style={{ margin: "8px 0" }}>
            Total: <strong>{fmtUsd(usage.total.cost_usd)}</strong> · {fmtInt(usage.total.calls)} llamadas ·{" "}
            {fmtInt(usage.total.input_tokens)} tokens de entrada · {fmtInt(usage.total.output_tokens)} de salida.
            {" "}Detalle por llamada en <code>{usage.log_dir}/claude_calls.jsonl</code>.
          </p>
          <Table headers={["Proyecto", "Respuestas", "Llamadas", "Entrada", "Salida", "Costo est.", ""]}>
            {usage.projects.map((p) => {
              const u = p.claude_usage || {};
              const steps = Object.entries(u.by_step || {}).sort((a, b) => (b[1].cost_usd ?? 0) - (a[1].cost_usd ?? 0));
              return (
                <Fragment key={p.id}>
                  <tr>
                    <td>{p.name}<br /><span className="muted small">{p.id}</span></td>
                    <td>{fmtInt(p.n_responses)}</td>
                    <td>{fmtInt(u.calls)}</td>
                    <td>{fmtInt(u.input_tokens)}</td>
                    <td>{fmtInt(u.output_tokens)}</td>
                    <td><strong>{fmtUsd(u.cost_usd)}</strong></td>
                    <td>
                      <Button variant="ghost" size="sm" onClick={() => setExpanded(expanded === p.id ? null : p.id)}>
                        {expanded === p.id ? "Ocultar" : "Por paso"}
                      </Button>
                    </td>
                  </tr>
                  {expanded === p.id && steps.map(([step, t]) => (
                    <tr key={p.id + step} className="muted small">
                      <td style={{ paddingLeft: 24 }}>↳ {step.replace(/_/g, " ")}</td>
                      <td></td>
                      <td>{fmtInt(t.calls)}</td>
                      <td>{fmtInt(t.input_tokens)}</td>
                      <td>{fmtInt(t.output_tokens)}</td>
                      <td>{fmtUsd(t.cost_usd)}</td>
                      <td></td>
                    </tr>
                  ))}
                </Fragment>
              );
            })}
          </Table>
          {usage.projects.length === 0 && <p className="muted small">Ningún proyecto ha usado Claude desde que se activó el registro.</p>}
        </>
      )}
    </div>
  );
}
