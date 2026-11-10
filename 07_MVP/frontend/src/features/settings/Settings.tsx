import { ChangeEvent, FormEvent, Fragment, useEffect, useState } from "react";
import { adminApi, AdminHealth, PromptEntry, PromptsData, UsageProject } from "./api";
import { ClaudeUsageTotals } from "@/features/analysis/types";
import { projectsApi } from "@/features/projects/api";
import { orgApi, RUBROS } from "@/features/org/api";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/features/auth/useAuth";
import { Organizacion, puede, ROL_LABEL } from "@/features/auth/api";
import { useAsync } from "@/shared/hooks/useAsync";
import Button from "@/shared/components/Button";
import PageHeader from "@/shared/components/PageHeader";
import Card from "@/shared/components/Card";
import Table from "@/shared/components/Table";
import Input, { TextArea } from "@/shared/components/Input";
import Icon from "@/shared/components/Icon";

const PROMPT_ORDER = ["propose_categories", "codify", "interpret_lexical", "qualitative_report"];

export default function Settings() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const passwordChanged = (useLocation().state as { passwordChanged?: boolean } | null)?.passwordChanged;
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
      <PageHeader title="Configuración" help="Los datos de tu organización, tu cuenta y los ajustes del equipo." />
      {error && <div className="alert alert-error">{error}</div>}
      {passwordChanged && <div className="alert alert-success">Tu contraseña se cambió.</div>}

      <Card title="Mi cuenta">
        <p><strong>{user?.nombre || "—"}</strong> · {user?.email}</p>
        {user && <p className="muted">Rol: {ROL_LABEL[user.rol] ?? user.rol}</p>}
        <Button variant="secondary" onClick={() => navigate("/cambiar-contrasena")}>Cambiar contraseña</Button>
      </Card>

      {user?.organizacion && (
        <Card title="Organización">
          {puede(user, "admin") ? <OrgForm org={user.organizacion} /> : <OrgReadOnly org={user.organizacion} />}
        </Card>
      )}

      {puede(user, "analista") && <Card title="Importar proyectos antiguos">
        <p className="muted">
          Si usaste la versión demo de Celestica (sin cuentas), puedes importar esos proyectos a tu cuenta.
        </p>
        {imported !== null ? (
          <div className="alert alert-success" style={{ marginBottom: 0 }}>
            {imported > 0 ? `${imported} proyecto(s) importado(s). Revisa "Mis proyectos".` : "No hay proyectos antiguos por importar."}
          </div>
        ) : (
          <Button variant="secondary" onClick={importLegacy}>Importar proyectos de la demo</Button>
        )}
      </Card>}

      <AdminPrompts />
    </>
  );
}

/* ---- Organización (RF-10): nombre, rubro, color y logo ---- */

const HEX = /^#[0-9a-f]{6}$/i;
const LOGO_MAX_BYTES = 512_000;

function OrgReadOnly({ org }: { org: Organizacion }) {
  const { logo } = useAuth();
  return (
    <>
      {logo && <img src={logo} alt={`Logo de ${org.nombre}`} className="org-logo-preview" />}
      <p><strong>{org.nombre}</strong></p>
      <p className="muted">Rubro: {org.rubro ?? "Sin rubro"}</p>
      <p className="muted">
        Color: {org.color ? <><span className="org-dot" style={{ background: org.color }} aria-hidden="true" />{org.color}</> : "Sin color"}
      </p>
      <p className="muted small">Solo un administrador puede cambiar estos datos.</p>
    </>
  );
}

function OrgForm({ org }: { org: Organizacion }) {
  const { logo, setOrganizacion } = useAuth();
  const inicial = { nombre: org.nombre, rubro: org.rubro ?? "", color: org.color ?? "" };
  const [form, setForm] = useState(inicial);
  const [saved, setSaved] = useState(false);
  const guardar = useAsync();
  const logoOp = useAsync();

  useEffect(() => setForm({ nombre: org.nombre, rubro: org.rubro ?? "", color: org.color ?? "" }), [org]);

  const dirty = form.nombre !== inicial.nombre || form.rubro !== inicial.rubro || form.color !== inicial.color;
  const set = (k: keyof typeof form) => (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [k]: e.target.value });

  async function save(e: FormEvent) {
    e.preventDefault();
    setSaved(false);
    if (!form.nombre.trim()) { guardar.setError("Escribe el nombre de la organización."); return; }
    const updated = await guardar.run(() =>
      orgApi.updateProfile({ nombre: form.nombre.trim(), rubro: form.rubro || null, color: form.color || null }));
    if (updated) { setOrganizacion(updated); setSaved(true); }
  }

  async function subirLogo(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = ""; // permite volver a elegir el mismo archivo tras un error
    if (!file) return;
    if (file.size > LOGO_MAX_BYTES) { logoOp.setError("El logo pesa más de 500 KB. Usa una imagen más liviana."); return; }
    const updated = await logoOp.run(() => orgApi.uploadLogo(file));
    if (updated) setOrganizacion(updated, true);
  }

  async function quitarLogo() {
    if (!confirm("¿Quitar el logo de la organización?")) return;
    const updated = await logoOp.run(() => orgApi.deleteLogo());
    if (updated) setOrganizacion(updated, true);
  }

  return (
    <>
      <form onSubmit={save} style={{ maxWidth: 440 }}>
        {guardar.error && <div className="alert alert-error">{guardar.error}</div>}
        {saved && <div className="alert alert-success">Los datos de la organización se guardaron.</div>}
        <Input label="Nombre de la organización" required maxLength={100} value={form.nombre} onChange={set("nombre")} />
        <div>
          <label className="field-label" htmlFor="org_rubro">Rubro</label>
          <select id="org_rubro" value={form.rubro} onChange={set("rubro")}>
            <option value="">Sin rubro</option>
            {RUBROS.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
          <p className="muted small" style={{ margin: "4px 0 0" }}>El rubro ordena las plantillas que te sugerimos.</p>
        </div>
        <div>
          <label className="field-label" htmlFor="org_color">Color de la organización</label>
          <div className="org-color-row">
            <label htmlFor="org_color_pick" className="sr-only">Elegir color</label>
            <input type="color" id="org_color_pick" value={HEX.test(form.color) ? form.color : "#ffffff"} onChange={set("color")} />
            <input type="text" id="org_color" value={form.color} placeholder="#1F6FEB" maxLength={7} onChange={set("color")} />
            <Button type="button" variant="ghost" size="sm" disabled={!form.color} onClick={() => setForm({ ...form, color: "" })}>
              Sin color
            </Button>
          </div>
          <p className="muted small" style={{ margin: "4px 0 0" }}>
            Se usa como acento junto al logo y, más adelante, en los informes. No cambia los colores de la plataforma.
          </p>
        </div>
        <div style={{ marginTop: 14 }}><Button type="submit" busy={guardar.busy} disabled={!dirty}>Guardar</Button></div>
      </form>

      <div style={{ borderTop: "1px solid var(--border-soft)", marginTop: 16, paddingTop: 12, maxWidth: 440 }}>
        {logoOp.error && <div className="alert alert-error">{logoOp.error}</div>}
        {logo && <img src={logo} alt={`Logo de ${org.nombre}`} className="org-logo-preview" />}
        <label className="field-label" htmlFor="org_logo" style={{ marginTop: 0 }}>{org.tiene_logo ? "Reemplazar logo" : "Subir logo"}</label>
        <input type="file" id="org_logo" accept="image/png,image/jpeg" disabled={logoOp.busy} onChange={subirLogo} />
        <p className="muted small" style={{ margin: "4px 0 8px" }}>PNG o JPG de hasta 500 KB.</p>
        {org.tiene_logo && (
          <Button type="button" variant="danger" size="sm" disabled={logoOp.busy} onClick={quitarLogo}>Quitar logo</Button>
        )}
      </div>
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
      title="Configuración metodológica (equipo Celestica)"
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
          {status === "saved" && <span className="pill ok">Guardado <Icon name="check" size={12} /></span>}
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
                      <td style={{ paddingLeft: 24 }}>{step.replace(/_/g, " ")}</td>
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
