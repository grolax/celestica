import { useCallback, useState } from "react";

/**
 * Patrón busy/error que se repetía inline en todas las páginas.
 * `run` ejecuta la operación, marca busy, captura el mensaje de error
 * y devuelve el resultado (o undefined si falló).
 */
export function useAsync() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const run = useCallback(async <T>(fn: () => Promise<T>): Promise<T | undefined> => {
    setBusy(true);
    setError("");
    try {
      return await fn();
    } catch (e) {
      setError((e as Error).message);
      return undefined;
    } finally {
      setBusy(false);
    }
  }, []);

  return { busy, error, setError, run };
}
