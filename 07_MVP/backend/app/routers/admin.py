"""Panel de administración: consumo, salud y prompts (movido tal cual desde main.py)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app import store, prompt_store
from app.deps import _check_admin
from app.services import claude_log, thematic

router = APIRouter()


@router.get("/api/admin/usage")
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


@router.get("/api/admin/health")
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


@router.get("/api/admin/prompts")
def admin_get_prompts(request: Request):
    """Devuelve prompts actuales y defaults. Requiere X-Admin-Password."""
    _check_admin(request)
    return {
        "prompts": prompt_store.get_prompts(),
        "defaults": prompt_store.get_defaults(),
    }


@router.put("/api/admin/prompts/{key}")
def admin_update_prompt(key: str, body: PromptUpdate, request: Request):
    """Actualiza system + instructions de un prompt. Toma efecto inmediatamente."""
    _check_admin(request)
    try:
        return prompt_store.save_prompt(key, body.system, body.instructions)
    except KeyError as e:
        raise HTTPException(404, str(e))


@router.post("/api/admin/prompts/{key}/reset")
def admin_reset_prompt(key: str, request: Request):
    """Restaura un prompt a su valor por defecto."""
    _check_admin(request)
    try:
        return prompt_store.reset_prompt(key)
    except KeyError as e:
        raise HTTPException(404, str(e))
