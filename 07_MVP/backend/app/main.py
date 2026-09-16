"""
SoftInsight v1.0 — API.

Flujo: signup/login → crear proyecto (upload CSV/XLSX + marco teórico, opcionalmente
desde plantilla) → análisis léxico → propuesta de categorías (Claude) → validación
humana → codificación (Claude) → revisión/re-codificación → trazabilidad →
informe cualitativo → exportación PDF/DOCX/CSV/XLSX.

Multi-tenant: cada endpoint de proyecto exige JWT y filtra por user_id.
"""
from __future__ import annotations

import io
import os
import threading
import unicodedata
from typing import Optional

import pandas as pd
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from app import store, prompt_store, templates
from app.auth import get_current_user, router as auth_router
from app.database import get_db, init_db
from app.models import User
from app.services import claude_log, lexical, thematic
from app.services import export as export_svc
from app.services.integrations import credentials, google_forms, qualtrics
from app.services.integrations.base import IntegrationError

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

# Estado de progreso de codificación y de informe por proyecto (en memoria)
_codify_progress: dict = {}
_report_progress: dict = {}

# Largo típico de un informe (~4000 tokens ≈ 12k caracteres): para estimar %.
# El progreso son caracteres realmente recibidos del stream; el % se satura en 95
# hasta que el stream termina de verdad.
_REPORT_EXPECTED_CHARS = 12000

# Contraseña del panel de administración interno (prompts metodológicos)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "softinsight2026")


def _check_admin(request: Request) -> None:
    pwd = request.headers.get("X-Admin-Password", "")
    if pwd != ADMIN_PASSWORD:
        raise HTTPException(401, "Contraseña de administrador incorrecta")


def _get_or_404(project_id: str, user: User) -> dict:
    project = store.get_project(project_id, user.id)
    if not project:
        raise HTTPException(404, "Proyecto no encontrado")
    # Las llamadas a Claude que haga este request quedan atribuidas al
    # proyecto en el log de costo. Los hilos de fondo (codificación, informe)
    # no heredan el contexto y lo fijan ellos mismos en su `run()`.
    claude_log.current_project_id.set(project_id)
    return project


def _slug(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return "".join(c if c.isalnum() else "_" for c in norm).strip("_")[:60] or "proyecto"


# ---------- Plantillas de marcos teóricos ----------

@app.get("/api/framework-templates")
def framework_templates(user: User = Depends(get_current_user)):
    return templates.list_templates()


@app.post("/api/projects/{project_id}/apply-template")
def apply_template(project_id: str, template: str, user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    tpl = templates.get_template(template)
    if not tpl:
        raise HTTPException(404, f"Plantilla '{template}' no existe")
    if not project["marco_teorico"]:
        project["marco_teorico"] = tpl["marco_teorico"]
        store.set_project_field(project_id, user.id, "marco_teorico", tpl["marco_teorico"])
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
        store.push_category(project_id, user.id, cat)
    store.log_event(project, "analista", "aplicacion_plantilla", {
        "plantilla": template, "usuario": user.email,
        "n_categorias": len(tpl["categorias_default"]),
    })
    return {"marco_teorico": project["marco_teorico"], "categories": project["categories"]}


# ---------- Proyectos ----------

@app.get("/api/projects")
def list_projects(user: User = Depends(get_current_user)):
    return store.list_projects(user.id)


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

    project = store.create_project(user.id, name, marco_teorico, columns, text_column, responses)
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


@app.post("/api/projects")
async def create_project(
    file: UploadFile = File(...),
    name: str = Form(...),
    marco_teorico: str = Form(""),
    text_column: str = Form(""),
    template: str = Form(""),
    user: User = Depends(get_current_user),
):
    raw = await file.read()
    try:
        if file.filename and file.filename.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(raw))
        else:
            df = pd.read_csv(io.BytesIO(raw))
    except Exception as e:
        raise HTTPException(400, f"No se pudo leer el archivo: {e}")

    return _create_project_from_df(df, name, marco_teorico, text_column, template, user,
                                   source_detail={"fuente": "archivo", "archivo": file.filename})


@app.get("/api/projects/{project_id}")
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


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str, user: User = Depends(get_current_user)):
    if not store.delete_project(project_id, user.id):
        raise HTTPException(404, "Proyecto no encontrado")
    return {"deleted": project_id}


@app.post("/api/projects/import-legacy")
def import_legacy(user: User = Depends(get_current_user)):
    """Importa a esta cuenta los proyectos del antiguo store JSON (pre-auth)."""
    n = store.import_legacy_projects(user.id)
    return {"imported": n}


@app.get("/api/projects/{project_id}/responses")
def get_responses(project_id: str, offset: int = 0, limit: int = 50,
                  user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    items = []
    for r in project["responses"][offset:offset + limit]:
        sentiment = (project["lexical"] or {}).get("sentiment_by_response", {}).get(r["id"])
        items.append({**r, "sentiment": sentiment, "codings": project["codings"].get(r["id"], [])})
    return {"total": len(project["responses"]), "offset": offset, "items": items}


# ---------- Integraciones: Qualtrics y Google Forms ----------
# Arquitectura: app/services/integrations/* — cada fuente entrega un DataFrame
# y desemboca en _create_project_from_df (el mismo camino que subir un archivo).

class QualtricsCredentials(BaseModel):
    api_token: str
    datacenter: str


class QualtricsImportBody(BaseModel):
    name: str
    survey_id: str
    survey_name: str = ""
    marco_teorico: str = ""
    text_column: str = ""
    template: str = ""


class GoogleFormsImportBody(BaseModel):
    name: str
    sheet_url: str
    marco_teorico: str = ""
    text_column: str = ""
    template: str = ""


def _qualtrics_config(user: User) -> dict:
    cfg = (user.integrations or {}).get("qualtrics")
    if not cfg or not cfg.get("token_enc"):
        raise HTTPException(400, "No hay credenciales de Qualtrics configuradas. Ingrésalas primero.")
    try:
        token = credentials.decrypt(cfg["token_enc"])
    except IntegrationError as e:
        raise HTTPException(400, str(e))
    return {"api_token": token, "datacenter": cfg.get("datacenter", "")}


@app.get("/api/integrations/qualtrics/credentials")
def qualtrics_credentials_status(user: User = Depends(get_current_user)):
    """La UI solo sabe si hay credenciales y el datacenter; el token jamás sale del backend."""
    cfg = (user.integrations or {}).get("qualtrics") or {}
    return {"configured": bool(cfg.get("token_enc")), "datacenter": cfg.get("datacenter", "")}


@app.put("/api/integrations/qualtrics/credentials")
def qualtrics_save_credentials(body: QualtricsCredentials, user: User = Depends(get_current_user)):
    if not body.api_token.strip() or not body.datacenter.strip():
        raise HTTPException(400, "API Token y Datacenter ID son obligatorios.")
    get_db().users.update_one({"_id": user.id}, {"$set": {"integrations.qualtrics": {
        "token_enc": credentials.encrypt(body.api_token.strip()),
        "datacenter": body.datacenter.strip(),
    }}})
    return {"configured": True, "datacenter": body.datacenter.strip()}


@app.delete("/api/integrations/qualtrics/credentials")
def qualtrics_delete_credentials(user: User = Depends(get_current_user)):
    get_db().users.update_one({"_id": user.id}, {"$unset": {"integrations.qualtrics": ""}})
    return {"configured": False}


@app.get("/api/integrations/qualtrics/surveys")
def qualtrics_surveys(user: User = Depends(get_current_user)):
    cfg = _qualtrics_config(user)
    try:
        return qualtrics.list_surveys(cfg["api_token"], cfg["datacenter"])
    except IntegrationError as e:
        raise HTTPException(400, str(e))


@app.post("/api/projects/from-qualtrics")
def create_project_from_qualtrics(body: QualtricsImportBody, user: User = Depends(get_current_user)):
    cfg = _qualtrics_config(user)
    try:
        df = qualtrics.fetch_responses({**cfg, "survey_id": body.survey_id})
    except IntegrationError as e:
        raise HTTPException(400, str(e))
    result = _create_project_from_df(
        df, body.name, body.marco_teorico, body.text_column, body.template, user,
        source_detail={"fuente": "qualtrics", "encuesta_id": body.survey_id,
                       "encuesta": body.survey_name or body.survey_id},
    )
    project = store.get_project(result["id"], user.id)
    store.log_event(project, "sistema", "importacion_qualtrics", {
        "encuesta_id": body.survey_id, "encuesta": body.survey_name or body.survey_id,
        "n_respuestas": result["n_responses"], "usuario": user.email,
    })
    return result


@app.post("/api/projects/from-google-forms")
def create_project_from_google_forms(body: GoogleFormsImportBody, user: User = Depends(get_current_user)):
    try:
        df = google_forms.fetch_responses({"sheet_url": body.sheet_url})
    except IntegrationError as e:
        raise HTTPException(400, str(e))
    result = _create_project_from_df(
        df, body.name, body.marco_teorico, body.text_column, body.template, user,
        source_detail={"fuente": "google_forms", "planilla": body.sheet_url},
    )
    project = store.get_project(result["id"], user.id)
    store.log_event(project, "sistema", "importacion_google_forms", {
        "planilla": body.sheet_url, "n_respuestas": result["n_responses"], "usuario": user.email,
    })
    return result


# ---------- Capa 1: análisis léxico ----------

@app.post("/api/projects/{project_id}/lexical")
def run_lexical(project_id: str, user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    result = lexical.analyze(project["responses"])

    try:
        interpretation = thematic.interpret_lexical(project["marco_teorico"], result)
    except Exception:
        interpretation = ""
    result["interpretation"] = interpretation

    project["lexical"] = result
    project["lexical_interpretation"] = interpretation
    store.set_project_field(project_id, user.id, "lexical", result)
    store.set_project_field(project_id, user.id, "lexical_interpretation", interpretation)
    store.log_event(project, "sistema", "analisis_lexico", {
        "n_respuestas": result["n_responses"], "metodo": result["method_note"],
    })
    return {k: v for k, v in result.items() if k != "sentiment_by_response"}


@app.get("/api/projects/{project_id}/lexical")
def get_lexical(project_id: str, user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    if not project["lexical"]:
        raise HTTPException(404, "Análisis léxico no ejecutado aún")
    return {k: v for k, v in project["lexical"].items() if k != "sentiment_by_response"}


# ---------- Capa 2: análisis temático ----------

@app.post("/api/projects/{project_id}/categories/propose")
def propose_categories(project_id: str, user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    sample = [r["text"] for r in project["responses"][:60]]
    try:
        proposals = thematic.propose_categories(project["marco_teorico"], sample)
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    for p in proposals:
        cat = {
            "id": store.new_id("cat"),
            "nombre": p.get("nombre", "Sin nombre"),
            "definicion": p.get("definicion", ""),
            "criterios_inclusion": p.get("criterios_inclusion", ""),
            "criterios_exclusion": p.get("criterios_exclusion", ""),
            "ejemplo": p.get("ejemplo", ""),
            "origen": "claude",
            "status": "propuesta",  # propuesta | validada | descartada
            "comments": [],
        }
        project["categories"].append(cat)
        store.push_category(project_id, user.id, cat)
        store.log_event(project, "claude", "propuesta_categoria", {"categoria": cat})
    return project["categories"]


class CategoryUpdate(BaseModel):
    nombre: Optional[str] = None
    definicion: Optional[str] = None
    criterios_inclusion: Optional[str] = None
    criterios_exclusion: Optional[str] = None
    ejemplo: Optional[str] = None
    status: Optional[str] = None  # validada | descartada | propuesta


@app.patch("/api/projects/{project_id}/categories/{category_id}")
def update_category(project_id: str, category_id: str, update: CategoryUpdate,
                    user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    cat = next((c for c in project["categories"] if c["id"] == category_id), None)
    if not cat:
        raise HTTPException(404, "Categoría no encontrada")
    changes = {k: v for k, v in update.model_dump().items() if v is not None}
    before = {k: cat[k] for k in changes if k in cat}
    cat.update(changes)
    store.update_category_fields(project_id, user.id, category_id, changes)  # $set puntual
    store.log_event(project, "analista", "validacion_categoria", {
        "categoria_id": category_id, "antes": before, "despues": changes, "usuario": user.email,
    })
    return cat


class CategoryCreate(BaseModel):
    nombre: str
    definicion: str = ""
    criterios_inclusion: str = ""
    criterios_exclusion: str = ""
    ejemplo: str = ""


@app.post("/api/projects/{project_id}/categories")
def create_category(project_id: str, body: CategoryCreate,
                    user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    cat = {
        "id": store.new_id("cat"),
        **body.model_dump(),
        "origen": "analista",
        "status": "validada",
        "comments": [],
    }
    project["categories"].append(cat)
    store.push_category(project_id, user.id, cat)  # $push puntual
    store.log_event(project, "analista", "creacion_categoria_manual",
                    {"categoria": cat, "usuario": user.email})
    return cat


# ---------- Comentarios en categorías (colaboración básica) ----------

class CommentCreate(BaseModel):
    text: str


@app.post("/api/projects/{project_id}/categories/{category_id}/comments")
def add_comment(project_id: str, category_id: str, body: CommentCreate,
                user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    cat = next((c for c in project["categories"] if c["id"] == category_id), None)
    if not cat:
        raise HTTPException(404, "Categoría no encontrada")
    comment = {
        "id": store.new_id("com"),
        "text": body.text.strip(),
        "author": user.nombre or user.email,
        "timestamp": store.now_iso(),
    }
    cat.setdefault("comments", []).append(comment)
    store.push_comment(project_id, user.id, category_id, comment)  # $push puntual
    store.log_event(project, "analista", "comentario_categoria", {
        "categoria_id": category_id, "comentario": comment["text"], "usuario": user.email,
    })
    return comment


@app.delete("/api/projects/{project_id}/categories/{category_id}/comments/{comment_id}")
def delete_comment(project_id: str, category_id: str, comment_id: str,
                   user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    cat = next((c for c in project["categories"] if c["id"] == category_id), None)
    if not cat:
        raise HTTPException(404, "Categoría no encontrada")
    if not store.pull_comment(project_id, user.id, category_id, comment_id):  # $pull puntual
        raise HTTPException(404, "Comentario no encontrado")
    store.log_event(project, "analista", "eliminacion_comentario", {
        "categoria_id": category_id, "comentario_id": comment_id, "usuario": user.email,
    })
    return {"deleted": comment_id}


# ---------- Codificación con seguimiento de progreso ----------

@app.post("/api/projects/{project_id}/codify")
def codify(project_id: str, user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    validated = [c for c in project["categories"] if c["status"] == "validada"]
    if not validated:
        raise HTTPException(400, "No hay categorías validadas. Valida el libro de códigos antes de codificar.")

    total = len(project["responses"])
    _codify_progress[project_id] = {"done": 0, "total": total, "status": "running"}
    user_id = user.id

    def run():
        claude_log.current_project_id.set(project_id)  # hilo nuevo: sin contexto heredado
        try:
            proj = store.get_project(project_id, user_id)
            if not proj:
                _codify_progress[project_id] = {"status": "error", "error": "Proyecto no encontrado", "done": 0, "total": 0}
                return

            def progress_cb(done: int, total: int):
                _codify_progress[project_id] = {"done": done, "total": total, "status": "running"}

            results = thematic.codify_all(
                proj["marco_teorico"], validated, proj["responses"], progress_cb=progress_cb
            )

            valid_ids = {c["id"] for c in validated} | {"SIN_CATEGORIA"}
            n_assigned = 0
            new_codings: dict = {}
            for item in results:
                rid = item.get("response_id")
                assignments = [
                    {**a, "source": "claude", "status": "propuesta"}
                    for a in item.get("assignments", []) if a.get("category_id") in valid_ids
                ]
                if rid:
                    new_codings[rid] = assignments
                    n_assigned += len(assignments)

            # $set masivo de codings: no pisa comentarios/categorías agregados
            # por el analista mientras corría la codificación
            store.set_codings_bulk(project_id, user_id, new_codings)
            proj["codings"].update(new_codings)
            store.log_event(proj, "claude", "codificacion_corpus", {
                "n_respuestas": len(results), "n_asignaciones": n_assigned,
                "categorias_usadas": [c["nombre"] for c in validated],
            })
            _codify_progress[project_id] = {
                "done": total, "total": total, "status": "done",
                "coded": len(results), "assignments": n_assigned,
            }
        except Exception as e:
            _codify_progress[project_id] = {
                "status": "error", "error": str(e), "done": 0, "total": total,
            }

    threading.Thread(target=run, daemon=True).start()
    return {"status": "started", "total": total}


@app.get("/api/projects/{project_id}/codify/progress")
def codify_progress(project_id: str, user: User = Depends(get_current_user)):
    _get_or_404(project_id, user)
    return _codify_progress.get(project_id, {"status": "idle"})


class RecodeBody(BaseModel):
    category_ids: list[str]
    rationale: str = "Re-codificación manual del analista"


@app.put("/api/projects/{project_id}/responses/{response_id}/codings")
def recode(project_id: str, response_id: str, body: RecodeBody,
           user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    before = project["codings"].get(response_id, [])
    project["codings"][response_id] = [
        {"category_id": cid, "rationale": body.rationale, "confidence": 1.0,
         "source": "analista", "status": "validada"}
        for cid in body.category_ids
    ]
    # $set de UNA respuesta: no reescribe el resto del corpus codificado
    store.set_codings_for_response(project_id, user.id, response_id, project["codings"][response_id])
    store.log_event(project, "analista", "recodificacion_manual", {
        "response_id": response_id, "antes": before,
        "despues": project["codings"][response_id], "usuario": user.email,
    })
    return project["codings"][response_id]


# ---------- Resultados, trazabilidad e informe ----------

@app.get("/api/projects/{project_id}/summary")
def summary(project_id: str, user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    cat_names = {c["id"]: c["nombre"] for c in project["categories"]}
    cat_names["SIN_CATEGORIA"] = "Sin categoría"
    counts: dict[str, int] = {}
    conf_dist = {"alta": 0, "media": 0, "baja": 0}
    for assignments in project["codings"].values():
        for a in assignments:
            counts[a["category_id"]] = counts.get(a["category_id"], 0) + 1
            conf = a.get("confidence")
            if isinstance(conf, (int, float)):
                conf_dist["alta" if conf >= 0.85 else "media" if conf >= 0.6 else "baja"] += 1
    return {
        "by_category": sorted(
            [{"category_id": cid, "nombre": cat_names.get(cid, cid), "count": n} for cid, n in counts.items()],
            key=lambda x: -x["count"],
        ),
        "sentiment_distribution": (project["lexical"] or {}).get("sentiment_distribution", {}),
        "confidence_distribution": conf_dist,
        "n_responses": len(project["responses"]),
        "n_coded": len(project["codings"]),
        "n_categories_validated": len([c for c in project["categories"] if c["status"] == "validada"]),
        "has_lexical": project["lexical"] is not None,
        "has_report": bool(project.get("qualitative_report")),
    }


@app.get("/api/projects/{project_id}/audit")
def audit(project_id: str, user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    return project["audit_log"]


@app.get("/api/projects/{project_id}/export/traceability")
def export_traceability(project_id: str, user: User = Depends(get_current_user)):
    """Tabla plana de trazabilidad: respuesta → categoría → criterio → fuente."""
    project = _get_or_404(project_id, user)
    rows = export_svc.traceability_rows(project)
    # Compatibilidad con el frontend previo
    for r in rows:
        r["calculo_confianza"] = {
            "Alta": "Alta — el texto usa vocabulario muy alineado con la definición",
            "Media": "Media — hay alineación parcial o la categoría compite con otra",
            "Baja": "Baja — asignación incierta; se recomienda revisión manual",
        }.get(r.pop("nivel_confianza", ""), "")
    return rows


# ---------- Exportación de reportes (PDF / DOCX / CSV / XLSX) ----------

def _download(content: bytes, filename: str, media_type: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/projects/{project_id}/export/pdf")
def export_pdf(project_id: str, include_details: bool = True,
               user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    pdf = export_svc.generate_pdf_report(project, include_details=include_details)
    return _download(pdf, f"informe_softinsight_{_slug(project['name'])}.pdf", "application/pdf")


@app.get("/api/projects/{project_id}/export/docx")
def export_docx(project_id: str, include_details: bool = True,
                user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    docx_bytes = export_svc.generate_docx_report(project, include_details=include_details)
    return _download(
        docx_bytes, f"informe_softinsight_{_slug(project['name'])}.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.get("/api/projects/{project_id}/export/csv")
def export_csv(project_id: str, user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    return _download(export_svc.generate_csv_export(project),
                     f"trazabilidad_{_slug(project['name'])}.csv", "text/csv; charset=utf-8")


@app.get("/api/projects/{project_id}/export/xlsx")
def export_xlsx(project_id: str, user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    return _download(
        export_svc.generate_xlsx_export(project),
        f"trazabilidad_{_slug(project['name'])}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ---------- Fase 2: informe cualitativo ----------

def _report_section(text: str) -> Optional[str]:
    """Última sección detectada en el texto recibido (líneas cortas en mayúsculas,
    el mismo criterio que usa el frontend para renderizar títulos)."""
    section = None
    for line in text.splitlines():
        t = line.strip()
        if t and len(t) < 80 and t == t.upper() and any(ch.isalpha() for ch in t):
            section = t.title()
    return section


@app.post("/api/projects/{project_id}/report")
def generate_report(project_id: str, mode: str = "v2", force_full: bool = False,
                    user: User = Depends(get_current_user)):
    """Genera el informe en un hilo.

    mode="v2" (default): flujo multi-prompt — análisis contextual por
    respondente (paralelo) → síntesis de clusters → redacción. El progreso
    reportado es por etapa/respondente.
    mode="v1": modo rápido — un solo prompt monolítico con streaming real.
    force_full=true (solo v2): ignora el caché del Prompt 1 y vuelve a analizar
    cada respondente aunque los datos no hayan cambiado. Cuesta ~1 llamada por
    respondente: es una decisión explícita del analista, no el camino por defecto.
    """
    if mode not in ("v1", "v2"):
        raise HTTPException(400, f"Modo '{mode}' no válido. Usa 'v1' o 'v2'.")
    project = _get_or_404(project_id, user)
    validated = [c for c in project["categories"] if c["status"] == "validada"]
    if not validated:
        raise HTTPException(400, "No hay categorías validadas. Completa la codificación antes de generar el informe.")
    if not project["codings"]:
        raise HTTPException(400, "No hay respuestas codificadas. Ejecuta la codificación antes de generar el informe.")

    if _report_progress.get(project_id, {}).get("status") == "running":
        return {"status": "already_running"}

    _report_progress[project_id] = {"status": "running", "done": 0, "total": _REPORT_EXPECTED_CHARS, "section": None}
    user_id = user.id

    def run():
        claude_log.current_project_id.set(project_id)  # hilo nuevo: sin contexto heredado
        try:
            proj = store.get_project(project_id, user_id)
            if not proj:
                _report_progress[project_id] = {"status": "error", "error": "Proyecto no encontrado"}
                return

            if mode == "v2":
                store.log_event(proj, "claude", "informe_v2_inicio", {
                    "n_respondentes": len(proj["responses"]),
                    "regeneracion_completa": force_full,
                    "usa_cache_prompt1": (not force_full) and bool(proj.get("v2_analyses_cache")),
                })

                def progress_cb_v2(stage: str, done: int, total: int):
                    _report_progress[project_id] = {
                        "status": "running", "done": done, "total": total,
                        "section": stage,
                    }

                # Caché del Prompt 1 (análisis por respondente) entre reintentos:
                # es ~1 llamada a Claude POR RESPONDENTE: si un reintento vuelve a
                # dispararlas todas solo porque síntesis/redacción fallaron después,
                # el costo se multiplica sin necesidad. Se reutiliza mientras las
                # respuestas y el marco teórico no cambien (ver fingerprint).
                def save_v2_analyses_cb(fingerprint: str, analyses: list) -> None:
                    store.set_project_field(
                        project_id, user_id, "v2_analyses_cache",
                        {"fingerprint": fingerprint, "analyses": analyses},
                    )

                report = thematic.generate_qualitative_report_v2(
                    survey_id=proj["id"],
                    marco_teorico=proj["marco_teorico"],
                    categories=validated,
                    codings=proj["codings"],
                    responses=proj["responses"],
                    columns=proj["columns"],
                    text_column=proj["text_column"],
                    lexical_data=proj.get("lexical"),
                    progress_cb=progress_cb_v2,
                    cached_analyses=proj.get("v2_analyses_cache"),
                    save_analyses_cb=save_v2_analyses_cb,
                    force_full=force_full,
                )
                total_steps = len(proj["responses"]) + 2
                done_progress = {"status": "done", "done": total_steps, "total": total_steps}
            else:
                def progress_cb(text: str):
                    _report_progress[project_id] = {
                        "status": "running",
                        "done": min(len(text), int(_REPORT_EXPECTED_CHARS * 0.95)),
                        "total": _REPORT_EXPECTED_CHARS,
                        "section": _report_section(text),
                    }

                report = thematic.generate_qualitative_report(
                    marco_teorico=proj["marco_teorico"],
                    categories=validated,
                    codings=proj["codings"],
                    responses=proj["responses"],
                    lexical_data=proj.get("lexical"),
                    progress_cb=progress_cb,
                )
                done_progress = {
                    "status": "done", "done": _REPORT_EXPECTED_CHARS, "total": _REPORT_EXPECTED_CHARS,
                }

            proj["qualitative_report"] = report
            store.set_project_field(project_id, user_id, "qualitative_report", report)  # $set puntual
            store.log_event(proj, "claude", "generacion_informe_cualitativo", {
                "n_categorias": len(validated), "n_codificadas": len(proj["codings"]),
                "modo": mode,
            })
            _report_progress[project_id] = done_progress
        except Exception as e:
            claude_log.log_warning(f"informe {mode} del proyecto {project_id} falló: {type(e).__name__}: {e}")
            _report_progress[project_id] = {"status": "error", "error": str(e)}

    threading.Thread(target=run, daemon=True).start()
    return {"status": "started", "mode": mode, "force_full": force_full}


@app.get("/api/projects/{project_id}/report/progress")
def report_progress(project_id: str, user: User = Depends(get_current_user)):
    _get_or_404(project_id, user)
    return _report_progress.get(project_id, {"status": "idle"})


@app.get("/api/projects/{project_id}/report")
def get_report(project_id: str, user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    if not project.get("qualitative_report"):
        raise HTTPException(404, "Informe no generado aún")
    return {"report": project["qualitative_report"]}


# ---------- Consumo de API Claude (observabilidad de costo) ----------

@app.get("/api/projects/{project_id}/usage")
def project_usage(project_id: str, user: User = Depends(get_current_user)):
    """Tokens y costo estimado acumulados por el proyecto, por paso."""
    project = _get_or_404(project_id, user)
    return {"project_id": project_id, "usage": project.get("claude_usage") or {}}


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
