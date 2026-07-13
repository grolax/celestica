import { useEffect, useState } from "react";
import { adminApi, PromptEntry, PromptsData } from "./api";
import { projectsApi } from "@/features/projects/api";
import { useAuth } from "@/features/auth/useAuth";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
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

  async function login() {
    if (!password) return;
    setBusy(true);
    setError("");
    try {
      const data = await adminApi.getPrompts(password);
      setPrompts(data.prompts);
      setDefaults(data.defaults);
      setAuthenticated(true);
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
