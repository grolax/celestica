import { useEffect, useState } from "react";
import { analysisApi } from "../api";
import { LexicalResult } from "../types";
import { useAuth } from "@/features/auth/useAuth";
import { puede } from "@/features/auth/api";
import Button from "@/shared/components/Button";
import Card from "@/shared/components/Card";
import PageHeader from "@/shared/components/PageHeader";
import { useProject } from "@/features/projects/useProjectData";

export default function LexicalAnalysis() {
  const { project, refresh } = useProject();
  const canEdit = puede(useAuth().user, "analista");
  const [result, setResult] = useState<LexicalResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    analysisApi.getLexical(project.id, project.pregunta).then(setResult).catch(() => {});
  }, [project.id, project.pregunta]);

  async function run() {
    setBusy(true);
    setError("");
    try {
      setResult(await analysisApi.runLexical(project.id, project.pregunta));
      refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const maxCount = result?.top_terms[0]?.count ?? 1;
  const sentTotal = result ? Object.values(result.sentiment_distribution).reduce((a, b) => a + b, 0) : 0;

  return (
    <>
      <PageHeader level={2} title="Análisis léxico" help="Las palabras y frases que más se repiten y el tono de las respuestas, calculados sin IA." />
      {error && <div className="alert alert-error">{error}</div>}
      {!result && (
        <Card>
          <p className="muted">
            Frecuencias, bigramas, co-ocurrencias y sentimiento por lexicón. Al finalizar, la IA genera
            una breve interpretación de los patrones. El análisis numérico es determinístico y se ejecuta en segundos.
          </p>
          {canEdit
            ? <Button onClick={run} busy={busy}>{busy ? "Analizando e interpretando…" : "Ejecutar análisis léxico"}</Button>
            : <p className="small muted">Aún no se ejecuta. Un analista de tu organización puede hacerlo.</p>}
        </Card>
      )}
      {result && (
        <>
          {result.interpretation && (
            <Card title="Interpretación léxica" actions={<span className="pill claude">generada por IA</span>}>
              <p>{result.interpretation}</p>
            </Card>
          )}
          <div className="grid-2">
            <Card title="Términos más frecuentes">
              {result.top_terms.slice(0, 15).map((t) => (
                <div className="bar-row" key={t.term}>
                  <span>{t.term}</span>
                  <div className="bar" style={{ width: `${(t.count / maxCount) * 100}%` }} />
                  <span className="muted">{t.count}</span>
                </div>
              ))}
            </Card>
            <div>
              <Card title="Distribución de sentimiento">
                {Object.entries(result.sentiment_distribution).map(([label, n]) => (
                  <div className="bar-row" key={label}>
                    <span className={`pill ${label}`}>{label}</span>
                    <div className="bar" style={{ width: `${(n / sentTotal) * 100}%` }} />
                    <span className="muted">{n}</span>
                  </div>
                ))}
              </Card>
              <Card title="Bigramas frecuentes">
                <div className="term-cloud">
                  {result.top_bigrams.slice(0, 12).map((b) => (
                    <span key={b.bigram} style={{ fontSize: 12 + b.count / 2 }}>{b.bigram}</span>
                  ))}
                </div>
              </Card>
            </div>
          </div>
          <Card title="Co-ocurrencias (mismo texto)">
            <div className="term-cloud">
              {result.top_cooccurrences.map((c) => (
                <span key={c.pair} className="muted">{c.pair} ({c.count})</span>
              ))}
            </div>
            <p className="small muted" style={{ marginTop: 12 }}><strong>Método:</strong> {result.method_note}</p>
            {canEdit && <Button variant="secondary" size="sm" onClick={run} busy={busy}>Re-ejecutar</Button>}
          </Card>
        </>
      )}
    </>
  );
}
