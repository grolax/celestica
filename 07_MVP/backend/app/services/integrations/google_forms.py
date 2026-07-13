"""
Integración Google Forms — la vía simple y honesta.

Google Forms guarda sus respuestas en una planilla de Google Sheets. En vez
de implementar OAuth completo de Google (flujo de consentimiento, refresh
tokens, verificación de app — desproporcionado para importación puntual),
importamos desde esa planilla: el usuario comparte la planilla como
"Cualquiera con el enlace puede ver" y pega la URL.

DECISIÓN DOCUMENTADA: OAuth de Google queda para una iteración futura si
los clientes lo piden; esta vía cubre el caso de uso (crear el proyecto sin
exportar CSV a mano) sin fricción de configuración.
"""
from __future__ import annotations

import io
import re

import pandas as pd
import requests

from app.services.integrations.base import IntegrationError

_TIMEOUT = 30


def _to_csv_url(sheet_url: str) -> str:
    """Convierte una URL de Google Sheets en su URL de exportación CSV.
    Acepta también una URL que ya es de export CSV."""
    url = (sheet_url or "").strip()
    if not url:
        raise IntegrationError("Pega la URL de la planilla de respuestas de Google Sheets.")
    if "output=csv" in url or "/export" in url and "format=csv" in url:
        return url
    m = re.search(r"docs\.google\.com/spreadsheets/d/(?:e/)?([\w-]+)", url)
    if not m:
        raise IntegrationError(
            "La URL no parece de Google Sheets. Debe verse como "
            "https://docs.google.com/spreadsheets/d/…"
        )
    sheet_id = m.group(1)
    gid = "0"
    g = re.search(r"[#?&]gid=(\d+)", url)
    if g:
        gid = g.group(1)
    if "/d/e/" in url:  # planillas publicadas ("publish to web")
        return f"https://docs.google.com/spreadsheets/d/e/{sheet_id}/pub?output=csv&gid={gid}"
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


def fetch_responses(config: dict) -> pd.DataFrame:
    """config: {sheet_url} → DataFrame con las respuestas del formulario."""
    csv_url = _to_csv_url(config.get("sheet_url", ""))
    try:
        r = requests.get(csv_url, timeout=_TIMEOUT, allow_redirects=True)
    except requests.RequestException as e:
        raise IntegrationError(f"No se pudo descargar la planilla: {e}")

    if r.status_code in (401, 403):
        raise IntegrationError(
            "La planilla no es pública. En Google Sheets: Compartir → "
            "\"Cualquiera con el enlace\" → Lector, y vuelve a intentarlo."
        )
    if r.status_code == 404:
        raise IntegrationError("Planilla no encontrada. Revisa la URL.")
    if not r.ok:
        raise IntegrationError(f"Google Sheets respondió {r.status_code}.")
    # Google redirige a la página de login si la planilla es privada
    ctype = r.headers.get("Content-Type", "")
    if "text/html" in ctype:
        raise IntegrationError(
            "La planilla no es pública (Google pidió iniciar sesión). "
            "Compártela como \"Cualquiera con el enlace puede ver\" e intenta de nuevo."
        )

    try:
        df = pd.read_csv(io.BytesIO(r.content))
    except Exception as e:
        raise IntegrationError(f"No se pudo leer el CSV de la planilla: {e}")

    if df.empty:
        raise IntegrationError("La planilla no tiene respuestas todavía.")
    return df
