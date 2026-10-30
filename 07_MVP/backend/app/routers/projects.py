"""Plantillas, proyectos y respuestas (movido tal cual desde main.py)."""
from __future__ import annotations

import io

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app import store, templates
from app.auth import get_current_user
from app.deps import _get_or_404, require_role
from app.models import User
from app.services.question_types import detectar

router = APIRouter()


# ---------- Plantillas de marcos teóricos ----------

@router.get("/api/framework-templates")
def framework_templates(user: User = Depends(get_current_user)):
    return templates.list_templates()


@router.post("/api/projects/{project_id}/apply-template")
def apply_template(project_id: str, template: str, user: User = Depends(require_role("analista"))):
    project = _get_or_404(project_id, user)
    tpl = templates.get_template(template)
    if not tpl:
        raise HTTPException(404, f"Plantilla '{template}' no existe")
    if not project["marco_teorico"]:
        project["marco_teorico"] = tpl["marco_teorico"]
        store.set_project_field(project_id, user.org_id, "marco_teorico", tpl["marco_teorico"])
    for c in tpl["categorias_default"]:
        cat = {
            "id": store.new_id("cat"),
            "nombre": c["nombre"],
            "definicion": c.get("definicion", ""),
            "criterios_inclusion": c.get("criterios_inclusion", ""),
            "criterios_exclusion": c.get("criterios_exclusion", ""),
            "ejemplo": c.get("ejemplo", ""),
            "origen": "plantilla",
            "status": "propuesta",  # el analista igual valida: la validación es parte del método
            "comments": [],
        }
        project["categories"].append(cat)
        store.push_category(project_id, user.org_id, cat)
    store.log_event(project, "analista", "aplicacion_plantilla", {
        "plantilla": template, "usuario": user.email,
        "n_categorias": len(tpl["categorias_default"]),
    })
    return {"marco_teorico": project["marco_teorico"], "categories": project["categories"]}


# ---------- Proyectos ----------

@router.get("/api/projects")
def list_projects(user: User = Depends(get_current_user)):
    return store.list_projects(user.org_id)


def _create_project_from_df(df: pd.DataFrame, name: str, marco_teorico: str,
                            text_column: str, template: str, user: User,
                            source_detail: dict) -> dict:
    """Camino común de creación: un DataFrame es un DataFrame, venga de un
    archivo subido, de Qualtrics o de una planilla de Google (DEC de v1.0
    que hace triviales las integraciones)."""
    if df.empty:
        raise HTTPException(400, "Los datos no contienen filas")

    columns = [str(c) for c in df.columns]
    df.columns = columns
    # Heurística: si no se indica columna de texto, usar la de mayor largo promedio
    if not text_column:
        text_column = max(columns, key=lambda c: df[c].astype(str).str.len().mean())
    if text_column not in columns:
        raise HTTPException(400, f"Columna '{text_column}' no existe. Disponibles: {columns}")

    responses = []
    for i, row in df.iterrows():
        text = str(row[text_column]).strip()
        if not text or text.lower() == "nan":
            continue
        meta = {c: ("" if pd.isna(row[c]) else str(row[c])) for c in columns if c != text_column}
        rid = meta.pop("id_respuesta", None) or f"R{i+1:04d}"
        responses.append({"id": rid, "text": text, "meta": meta})

    if not responses:
        raise HTTPException(400, f"La columna '{text_column}' no contiene textos analizables")

    # Plantilla opcional: prefija el marco teórico
    tpl = templates.get_template(template) if template else None
    if tpl and not marco_teorico:
        marco_teorico = tpl["marco_teorico"]

    project = store.create_project(user.org_id, user.id, name, marco_teorico, columns, text_column, responses)
    store.log_event(project, "analista", "creacion_proyecto", {
        **source_detail, "n_respuestas": len(responses),
        "columna_texto": text_column, "marco_teorico": marco_teorico,
        "usuario": user.email, "plantilla": template or None,
    })
    if tpl:
        for c in tpl["categorias_default"]:
            project["categories"].append({
                "id": store.new_id("cat"), "nombre": c["nombre"],
                "definicion": c.get("definicion", ""),
                "criterios_inclusion": c.get("criterios_inclusion", ""),
                "criterios_exclusion": c.get("criterios_exclusion", ""),
                "ejemplo": c.get("ejemplo", ""),
                "origen": "plantilla", "status": "propuesta", "comments": [],
            })
        store.log_event(project, "analista", "aplicacion_plantilla", {
            "plantilla": template, "usuario": user.email,
            "n_categorias": len(tpl["categorias_default"]),
        })
    store.save_project(project)
    return {"id": project["id"], "n_responses": len(responses), "text_column": text_column}


MAX_ARCHIVO = 20 * 1024 * 1024


def _leer_archivo(raw: bytes, filename: str | None) -> pd.DataFrame:
    """Lectura común de CSV/XLSX para crear proyectos y para la vista previa."""
    if len(raw) > MAX_ARCHIVO:
        raise HTTPException(413, "El archivo supera el máximo de 20 MB.")
    try:
        if filename and filename.lower().endswith((".xlsx", ".xls")):
            return pd.read_excel(io.BytesIO(raw))
        return pd.read_csv(io.BytesIO(raw))
    except Exception as e:
        raise HTTPException(400, f"No se pudo leer el archivo: {e}")


def preview_df(df: pd.DataFrame) -> dict:
    """Vista previa de tipos de pregunta (T-010): solo lectura, no guarda nada."""
    if df.empty:
        raise HTTPException(400, "Los datos no contienen filas")
    return detectar(df)


@router.post("/api/projects/preview")
async def preview_file(file: UploadFile = File(...), user: User = Depends(require_role("analista"))):
    return preview_df(_leer_archivo(await file.read(), file.filename))


@router.post("/api/projects")
async def create_project(
    file: UploadFile = File(...),
    name: str = Form(...),
    marco_teorico: str = Form(""),
    text_column: str = Form(""),
    template: str = Form(""),
    user: User = Depends(require_role("analista")),
):
    df = _leer_archivo(await file.read(), file.filename)

    return _create_project_from_df(df, name, marco_teorico, text_column, template, user,
                                   source_detail={"fuente": "archivo", "archivo": file.filename})


@router.get("/api/projects/{project_id}")
def get_project(project_id: str, user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    return {
        **{k: project[k] for k in ["id", "name", "marco_teorico", "created_at", "columns", "text_column", "categories"]},
        "n_responses": len(project["responses"]),
        "has_lexical": project["lexical"] is not None,
        "n_coded": len(project["codings"]),
        "has_report": bool(project.get("qualitative_report")),
        "n_audit_events": len(project.get("audit_log", [])),
    }


@router.delete("/api/projects/{project_id}")
def delete_project(project_id: str, user: User = Depends(require_role("analista"))):
    if not store.delete_project(project_id, user.org_id):
        raise HTTPException(404, "Proyecto no encontrado")
    return {"deleted": project_id}


@router.post("/api/projects/import-legacy")
def import_legacy(user: User = Depends(require_role("analista"))):
    """Importa a esta cuenta los proyectos del antiguo store JSON (pre-auth)."""
    n = store.import_legacy_projects(user.org_id, user.id)
    return {"imported": n}


@router.get("/api/projects/{project_id}/responses")
def get_responses(project_id: str, offset: int = 0, limit: int = 50,
                  user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    items = []
    for r in project["responses"][offset:offset + limit]:
        sentiment = (project["lexical"] or {}).get("sentiment_by_response", {}).get(r["id"])
        items.append({**r, "sentiment": sentiment, "codings": project["codings"].get(r["id"], [])})
    return {"total": len(project["responses"]), "offset": offset, "items": items}



# ---------- Consumo de API Claude (observabilidad de costo) ----------

@router.get("/api/projects/{project_id}/usage")
def project_usage(project_id: str, user: User = Depends(get_current_user)):
    """Tokens y costo estimado acumulados por el proyecto, por paso."""
    project = _get_or_404(project_id, user)
    return {"project_id": project_id, "usage": project.get("claude_usage") or {}}
