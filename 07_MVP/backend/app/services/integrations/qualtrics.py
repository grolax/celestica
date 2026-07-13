"""
Integración Qualtrics: importación puntual de respuestas de una encuesta.

Usa la API v3 de exportación de respuestas (el flujo oficial):
1. POST  /surveys/{id}/export-responses         → inicia la exportación (CSV)
2. GET   /surveys/{id}/export-responses/{pid}   → poll hasta 'complete'
3. GET   .../{fileId}/file                      → descarga ZIP con el CSV

Credenciales: API Token + Datacenter ID del usuario (ej: 'ca1', 'fra1').
Se guardan cifradas en el documento del usuario y NUNCA viajan al navegador.
"""
from __future__ import annotations

import io
import time
import zipfile

import pandas as pd
import requests

from app.services.integrations.base import IntegrationError

_TIMEOUT = 30
_EXPORT_WAIT_SECONDS = 120


def _base_url(datacenter: str) -> str:
    dc = (datacenter or "").strip().rstrip(".")
    if not dc:
        raise IntegrationError("Falta el Datacenter ID de Qualtrics (ej: 'ca1', 'fra1').")
    return f"https://{dc}.qualtrics.com/API/v3"


def _headers(api_token: str) -> dict:
    return {"X-API-TOKEN": (api_token or "").strip()}


def _check_auth(r: requests.Response) -> None:
    if r.status_code == 401:
        raise IntegrationError("Token de Qualtrics inválido o expirado. Revisa tus credenciales.")
    if r.status_code == 403:
        raise IntegrationError("El token de Qualtrics no tiene permisos suficientes para esta operación.")
    if r.status_code == 404:
        raise IntegrationError("Recurso no encontrado en Qualtrics. ¿El Datacenter ID es correcto?")
    if not r.ok:
        raise IntegrationError(f"Qualtrics respondió {r.status_code}: {r.text[:200]}")


def list_surveys(api_token: str, datacenter: str) -> list:
    """Lista las encuestas visibles para el token: [{id, name}]."""
    url = _base_url(datacenter) + "/surveys"
    surveys = []
    try:
        while url:
            r = requests.get(url, headers=_headers(api_token), timeout=_TIMEOUT)
            _check_auth(r)
            result = r.json().get("result", {})
            surveys.extend(
                {"id": s["id"], "name": s.get("name", s["id"])}
                for s in result.get("elements", [])
            )
            url = result.get("nextPage")
    except requests.RequestException as e:
        raise IntegrationError(f"No se pudo conectar con Qualtrics: {e}")
    return surveys


def fetch_responses(config: dict) -> pd.DataFrame:
    """Descarga las respuestas de una encuesta como DataFrame.

    config: {api_token, datacenter, survey_id}
    Qualtrics exporta un CSV con 3 filas de encabezado (nombre de campo,
    texto de la pregunta, metadata de import). Usamos el texto de la pregunta
    como nombre de columna y descartamos la fila de metadata.
    """
    api_token = config.get("api_token", "")
    datacenter = config.get("datacenter", "")
    survey_id = config.get("survey_id", "")
    if not survey_id:
        raise IntegrationError("Falta el ID de la encuesta de Qualtrics.")

    base = _base_url(datacenter) + f"/surveys/{survey_id}/export-responses"
    headers = _headers(api_token)

    try:
        # 1. iniciar exportación
        r = requests.post(base, headers={**headers, "Content-Type": "application/json"},
                          json={"format": "csv"}, timeout=_TIMEOUT)
        _check_auth(r)
        progress_id = r.json()["result"]["progressId"]

        # 2. poll hasta completar
        file_id = None
        deadline = time.time() + _EXPORT_WAIT_SECONDS
        while time.time() < deadline:
            r = requests.get(f"{base}/{progress_id}", headers=headers, timeout=_TIMEOUT)
            _check_auth(r)
            result = r.json()["result"]
            status = result.get("status")
            if status == "complete":
                file_id = result.get("fileId")
                break
            if status == "failed":
                raise IntegrationError("Qualtrics no pudo exportar la encuesta (export 'failed').")
            time.sleep(1.0)
        if not file_id:
            raise IntegrationError("La exportación de Qualtrics tardó demasiado. Intenta de nuevo.")

        # 3. descargar ZIP y leer el CSV
        r = requests.get(f"{base}/{file_id}/file", headers=headers, timeout=_TIMEOUT)
        _check_auth(r)
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not names:
                raise IntegrationError("La exportación de Qualtrics no contiene un CSV.")
            raw = zf.read(names[0])
    except requests.RequestException as e:
        raise IntegrationError(f"No se pudo conectar con Qualtrics: {e}")

    # Encabezado triple de Qualtrics: fila 0 = id de campo, fila 1 = texto de
    # la pregunta (la usamos como nombre), fila 2 = metadata {"ImportId":...}
    df = pd.read_csv(io.BytesIO(raw), header=1)
    df = df[~df.iloc[:, 0].astype(str).str.startswith('{"ImportId"')].reset_index(drop=True)

    if df.empty:
        raise IntegrationError("La encuesta no tiene respuestas registradas todavía.")
    return df
