import { useEffect, useState } from "react";
import Button from "@/shared/components/Button";
import Input from "@/shared/components/Input";
import { useAsync } from "@/shared/hooks/useAsync";
import { integrationsApi, QualtricsStatus, QualtricsSurvey } from "./api";

/**
 * Origen Qualtrics en "Nuevo proyecto": configurar credenciales (una vez,
 * quedan cifradas en el backend) → listar encuestas → elegir una.
 */
export default function QualtricsSection({ surveyId, onSelect, onError }: {
  surveyId: string;
  onSelect: (id: string, name: string) => void;
  onError: (msg: string) => void;
}) {
  const [status, setStatus] = useState<QualtricsStatus | null>(null);
  const [token, setToken] = useState("");
  const [datacenter, setDatacenter] = useState("");
  const [surveys, setSurveys] = useState<QualtricsSurvey[] | null>(null);
  const { busy, error, run } = useAsync();

  useEffect(() => {
    integrationsApi.qualtricsStatus().then(setStatus).catch(() => setStatus({ configured: false, datacenter: "" }));
  }, []);

  useEffect(() => { if (error) onError(error); }, [error, onError]);

  async function saveCredentials() {
    const s = await run(() => integrationsApi.qualtricsSaveCredentials(token.trim(), datacenter.trim()));
    if (s) {
      setStatus(s);
      setToken("");
      loadSurveys();
    }
  }

  async function loadSurveys() {
    const list = await run(() => integrationsApi.qualtricsSurveys());
    if (list) {
      setSurveys(list);
      if (list.length === 0) onError("Tu cuenta de Qualtrics no tiene encuestas visibles con este token.");
    }
  }

  async function removeCredentials() {
    const s = await run(() => integrationsApi.qualtricsDeleteCredentials());
    if (s) {
      setStatus(s);
      setSurveys(null);
      onSelect("", "");
    }
  }

  if (!status) return <p className="muted small">Verificando credenciales de Qualtrics…</p>;

  if (!status.configured) {
    return (
      <div style={{ maxWidth: 460 }}>
        <p className="small muted">
          Conecta tu cuenta con un <strong>API Token</strong> (Qualtrics → Account Settings → Qualtrics IDs)
          y el <strong>Datacenter ID</strong> (ej: <code>ca1</code>, <code>fra1</code>). Se guardan cifrados
          en el servidor; nunca en tu navegador.
        </p>
        <Input label="API Token" type="password" value={token} onChange={(e) => setToken(e.target.value)}
               placeholder="••••••••••••••••" />
        <Input label="Datacenter ID" value={datacenter} onChange={(e) => setDatacenter(e.target.value)}
               placeholder="ej: ca1" />
        <div style={{ marginTop: 10 }}>
          <Button type="button" onClick={saveCredentials} busy={busy}
                  disabled={!token.trim() || !datacenter.trim()}>
            Guardar credenciales
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <p className="small muted" style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <span className="pill ok">Qualtrics conectado · datacenter {status.datacenter}</span>
        <Button type="button" variant="ghost" size="sm" onClick={removeCredentials}>Quitar credenciales</Button>
      </p>
      {!surveys ? (
        <Button type="button" variant="secondary" onClick={loadSurveys} busy={busy}>
          Listar mis encuestas
        </Button>
      ) : (
        <>
          <label className="field-label">Encuesta a importar ({surveys.length} disponibles)</label>
          <select value={surveyId}
                  onChange={(e) => {
                    const s = surveys.find((x) => x.id === e.target.value);
                    onSelect(e.target.value, s?.name ?? e.target.value);
                  }}>
            <option value="">— elegir encuesta —</option>
            {surveys.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
          <p className="small muted" style={{ marginTop: 6 }}>
            Se importarán todas las respuestas registradas al momento de crear el proyecto
            (importación puntual, no sincronización continua).
          </p>
        </>
      )}
    </div>
  );
}
