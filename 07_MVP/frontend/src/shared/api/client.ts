/**
 * Cliente HTTP compartido: ÚNICO punto de contacto con el backend.
 * Adjunta el token JWT, traduce errores y maneja el 401 (sesión expirada).
 * Cada feature define su propio slice de API sobre `req`/`jsonBody`/`downloadFile`.
 */

const BASE = "/api";

// ---------- Token en memoria + localStorage ----------

const TOKEN_KEY = "softinsight_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

/** Se registra desde useAuth para redirigir a /login en 401. */
let onUnauthorized: ((detail: string) => void) | null = null;
export function setUnauthorizedHandler(fn: (detail: string) => void) {
  onUnauthorized = fn;
}

/** Error de `req` con el código HTTP, para distinguir casos como el 409 sin leer el texto. */
export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

export async function req<T>(path: string, init?: RequestInit, base = BASE): Promise<T> {
  const token = getToken();
  const r = await fetch(`${base}${path}`, {
    ...init,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (!r.ok) {
    let detail = r.statusText;
    try {
      const data = await r.json();
      detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail ?? detail);
    } catch {}
    if (r.status === 401 && onUnauthorized && !path.startsWith("/login") && !path.startsWith("/signup")) {
      onUnauthorized(detail);
    }
    throw new ApiError(detail, r.status);
  }
  return r.json();
}

export function jsonBody(body: unknown): RequestInit {
  return { headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

/** Descarga un archivo autenticado (blob → link temporal). */
export async function downloadFile(path: string): Promise<void> {
  const token = getToken();
  const r = await fetch(`${BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!r.ok) {
    let detail = r.statusText;
    try { detail = (await r.json()).detail ?? detail; } catch {}
    throw new Error(detail);
  }
  const disposition = r.headers.get("Content-Disposition") ?? "";
  const match = /filename="?([^";]+)"?/.exec(disposition);
  const blob = await r.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = match?.[1] ?? "softinsight_export";
  a.click();
  URL.revokeObjectURL(a.href);
}
