"""Análisis léxico, categorías, codificación, resumen y auditoría (movido tal cual desde main.py)."""
from __future__ import annotations

import threading
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app import store
from app.auth import get_current_user
from app.deps import _codify_progress, _get_or_404
from app.models import User
from app.services import claude_log, lexical, thematic

router = APIRouter()


# ---------- Capa 1: análisis léxico ----------

@router.post("/api/projects/{project_id}/lexical")
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


@router.get("/api/projects/{project_id}/lexical")
def get_lexical(project_id: str, user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    if not project["lexical"]:
        raise HTTPException(404, "Análisis léxico no ejecutado aún")
    return {k: v for k, v in project["lexical"].items() if k != "sentiment_by_response"}


# ---------- Capa 2: análisis temático ----------

@router.post("/api/projects/{project_id}/categories/propose")
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


@router.patch("/api/projects/{project_id}/categories/{category_id}")
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


@router.post("/api/projects/{project_id}/categories")
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


@router.post("/api/projects/{project_id}/categories/{category_id}/comments")
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


@router.delete("/api/projects/{project_id}/categories/{category_id}/comments/{comment_id}")
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

@router.post("/api/projects/{project_id}/codify")
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


@router.get("/api/projects/{project_id}/codify/progress")
def codify_progress(project_id: str, user: User = Depends(get_current_user)):
    _get_or_404(project_id, user)
    return _codify_progress.get(project_id, {"status": "idle"})


class RecodeBody(BaseModel):
    category_ids: list[str]
    rationale: str = "Re-codificación manual del analista"


@router.put("/api/projects/{project_id}/responses/{response_id}/codings")
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

@router.get("/api/projects/{project_id}/summary")
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


@router.get("/api/projects/{project_id}/audit")
def audit(project_id: str, user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    return project["audit_log"]
