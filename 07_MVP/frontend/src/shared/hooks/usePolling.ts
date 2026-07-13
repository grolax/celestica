import { useCallback, useEffect, useRef } from "react";

/**
 * Polling con intervalo fijo y limpieza automática al desmontar.
 * Lo usan la barra de progreso de codificación y la del informe.
 */
export function usePolling(intervalMs = 2000) {
  const ref = useRef<ReturnType<typeof setInterval> | null>(null);

  const stop = useCallback(() => {
    if (ref.current) {
      clearInterval(ref.current);
      ref.current = null;
    }
  }, []);

  const start = useCallback((tick: () => void | Promise<void>) => {
    stop();
    ref.current = setInterval(tick, intervalMs);
  }, [intervalMs, stop]);

  useEffect(() => stop, [stop]);

  return { start, stop };
}
