"""Plantillas, proyectos y respuestas (movido tal cual desde main.py)."""
from __future__ import annotations

import io
import json
from collections import Counter
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app import store, templates
from app.auth import get_current_user
from app.deps import _get_or_404, _get_vista, _vista_or_404, require_role
from app.models import User
from app.services.question_types import TIPOS, contexto_por_defecto, detectar

router = APIRouter()


# ---------- Plantillas de marcos teóricos ----------

@router.get("/api/framework-templates")
def framework_templates(user: User = Depends(get_current_user)):
    return templates.list_templates()


@router.post("/api/projects/{project_id}/apply-template")
def apply_template(project_id: str, template: str, pregunta: Optional[str] = None,
                   user: User = Depends(require_role("analista"))):
    vista = _get_vista(project_id, user, pregunta)
    tpl = templates.get_template(template)
    if not tpl:
        raise HTTPException(404, f"Plantilla '{template}' no existe")
    if not vista["marco_teorico"]:
        vista["marco_teorico"] = tpl["marco_teorico"]
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
        vista["categories"].append(cat)
        store.push_category(project_id, user.org_id, vista["pregunta"], cat)
    store.log_event(vista, "analista", "aplicacion_plantilla", {
        "plantilla": template, "usuario": user.email, "pregunta": vista["pregunta"],
        "n_categorias": len(tpl["categorias_default"]),
    })
    return {"marco_teorico": vista["marco_teorico"], "categories": vista["categories"]}


# ---------- Proyectos ----------

@router.get("/api/projects")
def list_projects(user: User = Depends(get_current_user)):
    return store.list_projects(user.org_id)


def _textos(s: pd.Series) -> list[Optional[str]]:
    """Valores de una columna como texto limpio; vacío o ausente = None (N/A). Un entero que Excel dejó como float no lleva '.0'."""
    if pd.api.types.is_float_dtype(s) and (s.dropna() % 1 == 0).all():
        s = s.astype("Int64")
    return [None if pd.isna(v) or v == "" else v for v in s.astype("string").str.strip()]


def _armar_preguntas(df: pd.DataFrame, columns: list[str], text_column: str, preguntas: Optional[list]) -> list[dict]:
    """Las preguntas del proyecto: las que confirmó el usuario (validadas) o, sin ellas, las que detecta T-010."""
    if preguntas is None:  # compatibilidad: todas las columnas, la de texto fuerza `abierta`
        if not text_column:  # heurística: la de mayor largo promedio
            text_column = max(columns, key=lambda c: df[c].astype(str).str.len().mean())
        if text_column not in columns:
            raise HTTPException(400, f"Columna '{text_column}' no existe. Disponibles: {columns}")
        tipos = {p["columna"]: p["tipo"] for p in detectar(df)["preguntas"]}
        preguntas = [{"titulo": c, "columnas": [c], "tipo": "abierta" if c == text_column else tipos[c]}
                     for c in columns if c != "id_respuesta"]  # id_respuesta es el id de cada persona, no una pregunta
    out, usadas = [], set()
    for i, p in enumerate(preguntas, start=1):
        if not isinstance(p, dict) or not isinstance(p.get("columnas"), list) or not p["columnas"]:
            raise HTTPException(422, "Las preguntas enviadas no tienen el formato esperado: cada una necesita título, columnas y tipo.")
        tipo = p.get("tipo")
        if tipo not in TIPOS:
            raise HTTPException(422, f"Tipo de pregunta no válido: {tipo}.")
        titulo = str(p.get("titulo") or p["columnas"][0]).strip()
        contexto = p.get("contexto_ia", contexto_por_defecto(tipo, titulo))
        if tipo == "identificador" and contexto:
            raise HTTPException(422, "Una columna de identificación no se puede enviar a la IA.")
        for c in p["columnas"]:
            if c not in columns:
                raise HTTPException(422, f"La columna «{c}» no existe en los datos.")
            if c in usadas:
                raise HTTPException(422, f"La columna «{c}» está en más de una pregunta.")
            usadas.add(c)
        out.append({"id": f"q_{i}", "titulo": titulo, "columnas": list(p["columnas"]), "tipo": tipo, "contexto_ia": bool(contexto)})
    if not any(q["tipo"] == "abierta" for q in out):
        raise HTTPException(400, "Esta encuesta no tiene preguntas abiertas. El análisis de preguntas cerradas llegará pronto.")
    return out


def _create_project_from_df(df: pd.DataFrame, name: str, marco_teorico: str,
                            text_column: str, template: str, user: User,
                            source_detail: dict, preguntas: Optional[list] = None) -> dict:
    """Camino común de creación: un DataFrame es un DataFrame, venga de un
    archivo subido, de Qualtrics o de una planilla de Google (DEC de v1.0
    que hace triviales las integraciones). `preguntas`: lo que el usuario confirmó
    en la vista previa; sin ello se detectan (T-010)."""
    if df.empty:
        raise HTTPException(400, "Los datos no contienen filas")

    columns = [str(c) for c in df.columns]
    df.columns = columns
    preguntas = _armar_preguntas(df, columns, text_column, preguntas)

    # Una sola fila por persona; la unión de columnas ramificadas toma el primer valor no vacío.
    textos = {c: _textos(df[c]) for q in preguntas for c in q["columnas"]}
    ids = _textos(df["id_respuesta"]) if "id_respuesta" in columns else [None] * len(df)
    respondentes = [
        {"id": ids[i] or f"R{i+1:04d}",
         "valores": {q["id"]: next((v for c in q["columnas"] if (v := textos[c][i]) is not None), None)
                     for q in preguntas}}
        for i in range(len(df))
    ]
    abiertas = [q for q in preguntas if q["tipo"] == "abierta"]
    n_por_abierta = {q["id"]: sum(1 for r in respondentes if r["valores"][q["id"]] is not None) for q in abiertas}
    por_defecto = abiertas[0]
    if not n_por_abierta[por_defecto["id"]]:
        raise HTTPException(400, f"La columna '{por_defecto['titulo']}' no contiene textos analizables")
    text_column = por_defecto["titulo"]

    # Plantilla opcional: prefija el marco teórico
    tpl = templates.get_template(template) if template else None
    if tpl and not marco_teorico:
        marco_teorico = tpl["marco_teorico"]

    project = store.create_project(user.org_id, user.id, name, marco_teorico, columns, text_column,
                                   preguntas, respondentes)
    store.log_event(project, "analista", "creacion_proyecto", {
        **source_detail, "n_respuestas": n_por_abierta[por_defecto["id"]],
        "columna_texto": text_column, "marco_teorico": marco_teorico,
        "usuario": user.email, "plantilla": template or None,
        "preguntas_por_tipo": dict(Counter(q["tipo"] for q in preguntas)),  # solo conteos, nunca valores
    })
    if tpl:
        for c in tpl["categorias_default"]:
            project["analisis"][por_defecto["id"]]["categories"].append({
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
    return {"id": project["id"], "n_responses": n_por_abierta[por_defecto["id"]], "text_column": text_column,
            "preguntas_abiertas": [{"id": q["id"], "titulo": q["titulo"], "n_respuestas": n_por_abierta[q["id"]]}
                                   for q in abiertas]}


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
    preguntas: str = Form(""),  # JSON con las preguntas confirmadas en la vista previa (opcional)
    user: User = Depends(require_role("analista")),
):
    df = _leer_archivo(await file.read(), file.filename)
    try:
        lista = json.loads(preguntas) if preguntas.strip() else None
    except ValueError:
        raise HTTPException(422, "Las preguntas enviadas no son un JSON válido.")
    if lista is not None and not isinstance(lista, list):
        raise HTTPException(422, "Las preguntas enviadas deben ser una lista.")
    return _create_project_from_df(df, name, marco_teorico, text_column, template, user,
                                   source_detail={"fuente": "archivo", "archivo": file.filename}, preguntas=lista)


@router.get("/api/projects/{project_id}")
def get_project(project_id: str, pregunta: Optional[str] = None, user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    vista = _vista_or_404(project, pregunta)
    return {
        **{k: vista[k] for k in ["id", "name", "marco_teorico", "created_at", "columns", "text_column", "categories"]},
        "n_responses": len(vista["responses"]),
        "has_lexical": vista["lexical"] is not None,
        "n_coded": len(vista["codings"]),
        "has_report": bool(vista.get("qualitative_report")),
        "n_audit_events": len(project.get("audit_log", [])),
        "preguntas": store.preguntas_publicas(project),
        "pregunta": vista["pregunta"],
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
def get_responses(project_id: str, offset: int = 0, limit: int = 50, pregunta: Optional[str] = None,
                  user: User = Depends(get_current_user)):
    vista = _get_vista(project_id, user, pregunta)
    items = []
    for r in vista["responses"][offset:offset + limit]:
        sentiment = (vista["lexical"] or {}).get("sentiment_by_response", {}).get(r["id"])
        items.append({**r, "sentiment": sentiment, "codings": vista["codings"].get(r["id"], [])})
    return {"total": len(vista["responses"]), "offset": offset, "items": items}



# ---------- Consumo de API Claude (observabilidad de costo) ----------

@router.get("/api/projects/{project_id}/usage")
def project_usage(project_id: str, user: User = Depends(get_current_user)):
    """Tokens y costo estimado acumulados por el proyecto, por paso."""
    project = _get_or_404(project_id, user)
    return {"project_id": project_id, "usage": project.get("claude_usage") or {}}
