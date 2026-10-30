"""
Almacenamiento multi-tenant sobre MongoDB.

Mantiene la interfaz documental del MVP original (el proyecto viaja como dict),
pero cada proyecto pertenece a una organización y TODA lectura/escritura filtra
por org_id — el aislamiento entre organizaciones vive aquí, no en los routers.
(`user_id` del proyecto solo significa "creado por".)

v1.1: además del ciclo clásico get_project → mutar → save_project (que
reescribe el documento y sigue siendo correcto para operaciones masivas como
la codificación), hay helpers de actualización parcial ($set/$push/$pull)
para operaciones puntuales: agregar un coding, un comentario o un evento de
auditoría ya no reescribe las cientos de respuestas del proyecto.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pymongo.errors import OperationFailure

from app.database import get_db

# Carpeta del antiguo store JSON (para importar proyectos pre-auth)
LEGACY_DIR = Path(__file__).resolve().parent.parent / "data_store"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _empty_project(name: str, marco_teorico: str, columns: list[str],
                   text_column: str, responses: list[dict]) -> dict:
    return {
        "id": new_id("proj"),
        "name": name,
        "marco_teorico": marco_teorico,
        "created_at": now_iso(),
        "columns": columns,
        "text_column": text_column,
        "responses": responses,          # [{id, text, meta:{...}}]
        "lexical": None,
        "categories": [],                # [{id, nombre, definicion, status, origen, comments:[...]}]
        "codings": {},                   # response_id -> [{category_id, rationale, confidence, source, status}]
        "audit_log": [],
        "lexical_interpretation": None,
        "qualitative_report": None,
    }


def _tenant_filter(project_id: str, org_id: str) -> dict:
    """Filtro base de TODO acceso a un proyecto: id + organización dueña."""
    return {"_id": project_id, "org_id": org_id}


def create_project(org_id: str, created_by: str, name: str, marco_teorico: str, columns: list[str],
                   text_column: str, responses: list[dict]) -> dict:
    project = _empty_project(name, marco_teorico, columns, text_column, responses)
    project["org_id"] = org_id
    project["user_id"] = created_by  # "creado por", no aislamiento
    save_project(project)
    return project


def save_project(project: dict) -> None:
    """Guarda el documento completo (upsert). Para operaciones masivas
    (creación, análisis léxico, codificación del corpus). Para cambios
    puntuales usar los helpers parciales de más abajo."""
    doc = dict(project)
    doc["_id"] = project["id"]
    get_db().projects.replace_one({"_id": project["id"]}, doc, upsert=True)


def get_project(project_id: str, org_id: str) -> Optional[dict]:
    doc = get_db().projects.find_one(_tenant_filter(project_id, org_id))
    if doc is None:
        return None  # no existe O no es suyo → la API responde 404 sin distinguir
    doc.pop("_id", None)
    return doc


def delete_project(project_id: str, org_id: str) -> bool:
    result = get_db().projects.delete_one(_tenant_filter(project_id, org_id))
    if result.deleted_count == 0:
        return False
    get_db().audit_events.delete_many({"project_id": project_id})
    return True


def list_projects(org_id: str) -> list[dict]:
    """Resumen de proyectos de la organización, calculado en el servidor de Mongo
    (no viaja el documento completo con sus cientos de respuestas)."""
    pipeline = [
        {"$match": {"org_id": org_id}},
        {"$project": {
            "_id": 0,
            "id": 1, "name": 1, "created_at": 1,
            "n_responses": {"$size": {"$ifNull": ["$responses", []]}},
            "has_lexical": {"$ne": [{"$ifNull": ["$lexical", None]}, None]},
            "n_categories": {"$size": {"$ifNull": ["$categories", []]}},
            "n_coded": {"$size": {"$objectToArray": {"$ifNull": ["$codings", {}]}}},
            "report": {"$ifNull": ["$qualitative_report", ""]},
        }},
        {"$sort": {"created_at": -1}},
    ]
    out = []
    for d in get_db().projects.aggregate(pipeline):
        d["has_report"] = bool(d.pop("report", ""))
        out.append(d)
    return out


# ---------- Actualizaciones parciales (v1.1: aprovechar Mongo de verdad) ----------

def update_category_fields(project_id: str, org_id: str, category_id: str,
                           changes: dict) -> bool:
    """$set sobre los campos de UNA categoría (operador posicional)."""
    if not changes:
        return True
    result = get_db().projects.update_one(
        {**_tenant_filter(project_id, org_id), "categories.id": category_id},
        {"$set": {f"categories.$.{k}": v for k, v in changes.items()}},
    )
    return result.matched_count > 0


def push_category(project_id: str, org_id: str, category: dict) -> bool:
    result = get_db().projects.update_one(
        _tenant_filter(project_id, org_id),
        {"$push": {"categories": category}},
    )
    return result.matched_count > 0


def _set_categories_array(project_id: str, org_id: str, mutate) -> bool:
    """Fallback parcial: lee SOLO el array categories, lo muta en memoria y
    lo re-escribe con $set (sin tocar responses/codings). Se usa cuando el
    servidor no soporta el operador posicional con $push/$pull (ej: mocks)."""
    doc = get_db().projects.find_one(_tenant_filter(project_id, org_id), {"categories": 1})
    if doc is None:
        return False
    categories = doc.get("categories", [])
    if not mutate(categories):
        return False
    get_db().projects.update_one(_tenant_filter(project_id, org_id),
                                 {"$set": {"categories": categories}})
    return True


def push_comment(project_id: str, org_id: str, category_id: str, comment: dict) -> bool:
    try:
        result = get_db().projects.update_one(
            {**_tenant_filter(project_id, org_id), "categories.id": category_id},
            {"$push": {"categories.$.comments": comment}},
        )
        return result.matched_count > 0
    except OperationFailure:
        def mutate(categories: list) -> bool:
            for c in categories:
                if c["id"] == category_id:
                    c.setdefault("comments", []).append(comment)
                    return True
            return False
        return _set_categories_array(project_id, org_id, mutate)


def pull_comment(project_id: str, org_id: str, category_id: str, comment_id: str) -> bool:
    """Devuelve True solo si el comentario existía y fue eliminado."""
    try:
        result = get_db().projects.update_one(
            {**_tenant_filter(project_id, org_id), "categories.id": category_id},
            {"$pull": {"categories.$.comments": {"id": comment_id}}},
        )
        return result.modified_count > 0
    except OperationFailure:
        def mutate(categories: list) -> bool:
            for c in categories:
                if c["id"] == category_id:
                    n = len(c.get("comments", []))
                    c["comments"] = [x for x in c.get("comments", []) if x["id"] != comment_id]
                    return len(c["comments"]) < n
            return False
        return _set_categories_array(project_id, org_id, mutate)


def set_codings_for_response(project_id: str, org_id: str, response_id: str,
                             assignments: list[dict]) -> bool:
    """$set de las asignaciones de UNA respuesta (re-codificación manual):
    no reescribe el resto del corpus."""
    result = get_db().projects.update_one(
        _tenant_filter(project_id, org_id),
        {"$set": {f"codings.{response_id}": assignments}},
    )
    return result.matched_count > 0


def set_codings_bulk(project_id: str, org_id: str, codings: dict) -> bool:
    """$set de las asignaciones de muchas respuestas en una sola operación
    (resultado de la codificación del corpus). No toca responses, categories
    ni comentarios agregados mientras corría el hilo."""
    if not codings:
        return True
    result = get_db().projects.update_one(
        _tenant_filter(project_id, org_id),
        {"$set": {f"codings.{rid}": assignments for rid, assignments in codings.items()}},
    )
    return result.matched_count > 0


def set_project_field(project_id: str, org_id: str, field: str, value: Any) -> bool:
    """$set de un campo de primer nivel (ej: qualitative_report, marco_teorico)."""
    result = get_db().projects.update_one(
        _tenant_filter(project_id, org_id),
        {"$set": {field: value}},
    )
    return result.matched_count > 0


# ---------- Consumo de API Claude por proyecto (observabilidad de costo) ----------

def inc_project_usage(project_id: str, step: str, input_tokens: int,
                      output_tokens: int, cost_usd: float) -> bool:
    """Acumula con $inc el consumo de Claude en `claude_usage` del proyecto.

    Se filtra solo por id de proyecto (sin org_id) a propósito: lo llama el
    sink de claude_log desde hilos de fondo que solo conocen el proyecto, y es
    una escritura del sistema (contabilidad), no una acción de usuario. Los
    endpoints que LEEN este campo sí pasan por el filtro multi-tenant.

    Por qué $inc y no leer-sumar-guardar: el flujo V2 hace decenas de llamadas
    en paralelo; $inc es atómico y no pisa lo que sumó otro hilo.
    """
    step_key = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in step)[:60] or "otro"
    inc = {
        "claude_usage.calls": 1,
        "claude_usage.input_tokens": int(input_tokens),
        "claude_usage.output_tokens": int(output_tokens),
        "claude_usage.cost_usd": float(cost_usd),
        f"claude_usage.by_step.{step_key}.calls": 1,
        f"claude_usage.by_step.{step_key}.input_tokens": int(input_tokens),
        f"claude_usage.by_step.{step_key}.output_tokens": int(output_tokens),
        f"claude_usage.by_step.{step_key}.cost_usd": float(cost_usd),
    }
    result = get_db().projects.update_one(
        {"id": project_id},
        {"$inc": inc, "$set": {"claude_usage.updated_at": now_iso()}},
    )
    return result.matched_count > 0


def list_usage_all_projects() -> list[dict]:
    """Panel admin: consumo de Claude de TODOS los proyectos (todos los usuarios).
    Solo campos de resumen: nunca viaja el documento completo."""
    pipeline = [
        {"$match": {"claude_usage": {"$exists": True}}},
        {"$project": {
            "_id": 0, "id": 1, "name": 1, "user_id": 1, "created_at": 1,
            "n_responses": {"$size": {"$ifNull": ["$responses", []]}},
            "claude_usage": 1,
        }},
        {"$sort": {"claude_usage.cost_usd": -1}},
    ]
    return list(get_db().projects.aggregate(pipeline))


# ---------- Auditoría ----------

def log_event(project: dict, actor: str, action: str, detail: dict[str, Any]) -> None:
    """Trazabilidad: toda decisión (humana o IA) queda auditada.

    Triple registro coherente:
    1. En memoria (project["audit_log"]) — para que un save_project posterior
       del mismo request lo conserve.
    2. $push al documento persistido — para endpoints que solo hacen
       actualizaciones parciales y nunca llaman save_project.
    3. Colección audit_events — copia plana consultable por proyecto/actor.
    (1 y 2 no se duplican: save_project es replace, no push.)
    """
    event = {
        "id": new_id("evt"),
        "timestamp": now_iso(),
        "actor": actor,        # "analista" | "claude" | "sistema"
        "action": action,
        "detail": detail,
    }
    project.setdefault("audit_log", []).append(event)
    try:
        db = get_db()
        db.projects.update_one(
            _tenant_filter(project["id"], project.get("org_id", "")),
            {"$push": {"audit_log": event}},
        )
        db.audit_events.insert_one({
            "_id": event["id"],
            "project_id": project["id"],
            "org_id": project.get("org_id", ""),
            "user_id": project.get("user_id", ""),
            "actor": actor,
            "action": action,
            "timestamp": event["timestamp"],
            "detail": detail,
        })
    except Exception:
        pass  # el registro canónico vive en el documento del proyecto


# ---------- Importación de proyectos antiguos ----------

def import_legacy_projects(org_id: str, created_by: str) -> int:
    """Importa proyectos del antiguo store JSON (pre-auth) a la organización indicada.
    Cada archivo importado se renombra a .imported para no duplicar."""
    if not LEGACY_DIR.exists():
        return 0
    n = 0
    for f in sorted(LEGACY_DIR.glob("proj_*.json")):
        try:
            project = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        project["org_id"] = org_id
        project["user_id"] = created_by
        save_project(project)
        f.rename(f.with_suffix(".json.imported"))
        n += 1
    return n
