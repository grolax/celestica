"""
SoftInsight v1.0 — API.

Flujo: signup/login → crear proyecto (upload CSV/XLSX + marco teórico, opcionalmente
desde plantilla) → análisis léxico → propuesta de categorías (Claude) → validación
humana → codificación (Claude) → revisión/re-codificación → trazabilidad →
informe cualitativo → exportación PDF/DOCX/CSV/XLSX.

Multi-tenant: cada endpoint de proyecto exige JWT y filtra por user_id.
"""
from __future__ import annotations

import threading
import unicodedata
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from app import store, prompt_store
from app.auth import get_current_user, router as auth_router
from app.database import init_db
from app.deps import (  # noqa: F401  (ADMIN_PASSWORD: las pruebas lo importan desde aquí)
    ADMIN_PASSWORD, _REPORT_EXPECTED_CHARS, _check_admin, _codify_progress,
    _get_or_404, _report_progress, _slug,
)
from app.models import User
from app.routers.analysis import router as analysis_router
from app.routers.integrations import router as integrations_router
from app.routers.projects import router as projects_router
from app.routers.reports import router as reports_router
from app.services import claude_log, lexical, thematic
from app.services import export as export_svc

app = FastAPI(title="SoftInsight", version="1.1.0")
try:
    init_db()
except Exception as e:
    raise RuntimeError(
        "No se pudo conectar a MongoDB. ¿Está corriendo? "
        "En macOS: `brew services start mongodb-community`. "
        f"URI usada: revisa MONGODB_URI en .env. Error original: {e}"
    ) from e


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Modo desarrollo: expone el error real en la UI en vez de un 500 mudo."""
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}"},
    )

# ---------- Observabilidad de costo de Claude ----------
# Cada llamada a Claude (ver services/claude_log.py) pasa por este sink y se
# acumula en Mongo en `claude_usage` del proyecto activo, agrupada por paso.
# Así el costo de un informe se ve en el panel admin ANTES de que un reintento
# a ciegas lo multiplique (incidente de septiembre 2026: >US$10 sin aviso).

def _usage_step(label: str) -> str:
    """'síntesis de clusters — tanda 3/10 (13 resp.)' → 'síntesis de clusters'."""
    base = label.split(" — ")[0].split(" (")[0].strip()
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode().lower()
    # 'análisis del respondente R0181' → 'analisis del respondente'
    return " ".join(w for w in base.split() if not any(ch.isdigit() for ch in w))


def _usage_sink(project_id: Optional[str], rec: dict) -> None:
    if not project_id:
        return
    store.inc_project_usage(
        project_id, _usage_step(rec.get("label", "")),
        rec.get("input_tokens", 0), rec.get("output_tokens", 0), rec.get("cost_usd", 0.0),
    )


claude_log.set_usage_sink(_usage_sink)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(integrations_router)
app.include_router(analysis_router)
app.include_router(reports_router)


@app.get("/api/admin/usage")
def admin_usage(request: Request):
    """Panel admin: consumo de todos los proyectos, ordenado por costo."""
    _check_admin(request)
    projects = store.list_usage_all_projects()
    total = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
    for p in projects:
        u = p.get("claude_usage") or {}
        for k in total:
            total[k] += u.get(k, 0) or 0
    total["cost_usd"] = round(total["cost_usd"], 4)
    return {"projects": projects, "total": total, "log_dir": str(claude_log.LOG_DIR)}


@app.get("/api/admin/health")
def admin_health(request: Request):
    """Qué código y configuración está corriendo REALMENTE este proceso.
    Sirve para confirmar que uvicorn recargó thematic.py tras un cambio."""
    _check_admin(request)
    return {
        "thematic_version": thematic.THEMATIC_VERSION,
        "model": thematic.MODEL,
        "model_report_v2": thematic.MODEL_V2,
        "model_max_output_tokens": thematic._model_output_limits or None,
        "synthesis_batch_input_tokens": thematic.SYNTHESIS_BATCH_INPUT_TOKENS,
        "merge_input_tokens": thematic.MERGE_INPUT_TOKENS,
        "large_output_tokens": thematic.LARGE_OUTPUT_TOKENS,
        "v2_max_workers": thematic.V2_MAX_WORKERS,
        "log_dir": str(claude_log.LOG_DIR),
    }


# ---------- Panel de administración: gestión de prompts ----------

class PromptUpdate(BaseModel):
    system: str
    instructions: str


@app.get("/api/admin/prompts")
def admin_get_prompts(request: Request):
    """Devuelve prompts actuales y defaults. Requiere X-Admin-Password."""
    _check_admin(request)
    return {
        "prompts": prompt_store.get_prompts(),
        "defaults": prompt_store.get_defaults(),
    }


@app.put("/api/admin/prompts/{key}")
def admin_update_prompt(key: str, body: PromptUpdate, request: Request):
    """Actualiza system + instructions de un prompt. Toma efecto inmediatamente."""
    _check_admin(request)
    try:
        return prompt_store.save_prompt(key, body.system, body.instructions)
    except KeyError as e:
        raise HTTPException(404, str(e))


@app.post("/api/admin/prompts/{key}/reset")
def admin_reset_prompt(key: str, request: Request):
    """Restaura un prompt a su valor por defecto."""
    _check_admin(request)
    try:
        return prompt_store.reset_prompt(key)
    except KeyError as e:
        raise HTTPException(404, str(e))
