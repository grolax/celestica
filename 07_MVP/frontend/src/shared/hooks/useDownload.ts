import { useState } from "react";

/**
 * Descargas con estado por botón: `busyKey` identifica cuál botón está
 * ocupado (pdf/docx/csv/xlsx) y el error queda disponible para la página.
 */
export function useDownload() {
  const [busyKey, setBusyKey] = useState("");
  const [error, setError] = useState("");

  async function download(key: string, fn: () => Promise<void>) {
    setBusyKey(key);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusyKey("");
    }
  }

  return { busyKey, error, setError, download };
}
