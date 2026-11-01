"""Análisis léxico, categorías, codificación, resumen y auditoría (movido tal cual desde main.py)."""
from __future__ import annotations

import threading
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app import store
from app.auth import get_current_user
from app.deps import (_analisis_en_curso, _codify_progress, _get_or_404, _get_vista, _progress_lock, require_role,
                      una_sola_vez)
from app.models import User
from app.services import claude_log, lexical, thematic

router = APIRouter()


# ---------- Capa 1: análisis léxico ----------

@router.post("/api/projects/{project_id}/lexical")
def run_lexical(project_id: str, pregunta: Optional[str] = None, user: User = Depends(require_role("analista"))):
    vista = _get_vista(project_id, user, pregunta)
    with una_sola_vez((project_id, vista["pregunta"], "lexical"),
                      "El análisis léxico ya está en curso para esta pregunta. Espera a que termine."):
        result = lexical.analyze(vista["responses"])

        try:
            interpretation = thematic.interpret_lexical(vista["marco_teorico"], result)
        except Exception:
            interpretation = ""
        result["interpretation"] = interpretation

        store.set_project_field(project_id, user.org_id, "lexical", result, vista["pregunta"])
        store.set_project_field(project_id, user.org_id, "lexical_interpretation", interpretation, vista["pregunta"])
        store.log_event(vista, "sistema", "analisis_lexico", {
            "n_respuestas": result["n_responses"], "metodo": result["method_note"], "pregunta": vista["pregunta"],
        })
        return {k: v for k, v in result.items() if k != "sentiment_by_response"}


@router.get("/api/projects/{project_id}/lexical")
def get_lexical(project_id: str, pregunta: Optional[str] = None, user: User = Depends(get_current_user)):
    vista = _get_vista(project_id, user, pregunta)
    if not vista["lexical"]:
        raise HTTPException(404, "Análisis léxico no ejecutado aún")
    return {k: v for k, v in vista["lexical"].items() if k != "sentiment_by_response"}


# ---------- Capa 2: análisis temático ----------

@router.post("/api/projects/{project_id}/categories/propose")
def propose_categories(project_id: str, pregunta: Optional[str] = None, user: User = Depends(require_role("analista"))):
    vista = _get_vista(project_id, user, pregunta)
    with una_sola_vez((project_id, vista["pregunta"], "propose"),
                      "Claude ya está proponiendo categorías para esta pregunta. Espera a que termine."):
        sample = [r["text"] for r in vista["responses"][:60]]
        try:
            proposals = thematic.propose_categories(vista["marco_teorico"], sample)
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
            vista["categories"].append(cat)
            store.push_category(project_id, user.org_id, vista["pregunta"], cat)
            store.log_event(vista, "claude", "propuesta_categoria", {"categoria": cat, "pregunta": vista["pregunta"]})
        return vista["categories"]


class CategoryUpdate(BaseModel):
    nombre: Optional[str] = None
    definicion: Optional[str] = None
    criterios_inclusion: Optional[str] = None
    criterios_exclusion: Optional[str] = None
    ejemplo: Optional[str] = None
    status: Optional[str] = None  # validada | descartada | propuesta


@router.patch("/api/projects/{project_id}/categories/{category_id}")
def update_category(project_id: str, category_id: str, update: CategoryUpdate, pregunta: Optional[str] = None,
                    user: User = Depends(require_role("analista"))):
    vista = _get_vista(project_id, user, pregunta)
    cat = next((c for c in vista["categories"] if c["id"] == category_id), None)
    if not cat:
        raise HTTPException(404, "Categoría no encontrada")
    changes = {k: v for k, v in update.model_dump().items() if v is not None}
    before = {k: cat[k] for k in changes if k in cat}
    cat.update(changes)
    store.update_category_fields(project_id, user.org_id, vista["pregunta"], category_id, changes)  # $set puntual
    store.log_event(vista, "analista", "validacion_categoria", {
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
def create_category(project_id: str, body: CategoryCreate, pregunta: Optional[str] = None,
                    user: User = Depends(require_role("analista"))):
    vista = _get_vista(project_id, user, pregunta)
    cat = {
        "id": store.new_id("cat"),
        **body.model_dump(),
        "origen": "analista",
        "status": "validada",
        "comments": [],
    }
    vista["categories"].append(cat)
    store.push_category(project_id, user.org_id, vista["pregunta"], cat)  # $push puntual
    store.log_event(vista, "analista", "creacion_categoria_manual",
                    {"categoria": cat, "usuario": user.email})
    return cat


# ---------- Comentarios en categorías (colaboración básica) ----------

class CommentCreate(BaseModel):
    text: str


@router.post("/api/projects/{project_id}/categories/{category_id}/comments")
def add_comment(project_id: str, category_id: str, body: CommentCreate, pregunta: Optional[str] = None,
                user: User = Depends(get_current_user)):
    vista = _get_vista(project_id, user, pregunta)
    cat = next((c for c in vista["categories"] if c["id"] == category_id), None)
    if not cat:
        raise HTTPException(404, "Categoría no encontrada")
    comment = {
        "id": store.new_id("com"),
        "text": body.text.strip(),
        "author": user.nombre or user.email,
        "author_id": user.id,
        "timestamp": store.now_iso(),
    }
    cat.setdefault("comments", []).append(comment)
    store.push_comment(project_id, user.org_id, vista["pregunta"], category_id, comment)  # $push puntual
    store.log_event(vista, "analista", "comentario_categoria", {
        "categoria_id": category_id, "comentario": comment["text"], "usuario": user.email,
    })
    return comment


@router.delete("/api/projects/{project_id}/categories/{category_id}/comments/{comment_id}")
def delete_comment(project_id: str, category_id: str, comment_id: str, pregunta: Optional[str] = None,
                   user: User = Depends(get_current_user)):
    vista = _get_vista(project_id, user, pregunta)
    cat = next((c for c in vista["categories"] if c["id"] == category_id), None)
    if not cat:
        raise HTTPException(404, "Categoría no encontrada")
    # El lector solo borra los suyos; los comentarios antiguos sin author_id no cuentan como suyos.
    com = next((c for c in cat.get("comments", []) if c["id"] == comment_id), None)
    if com and user.rol not in ("analista", "admin") and com.get("author_id") != user.id:
        raise HTTPException(403, "Solo puedes borrar tus propios comentarios.")
    if not store.pull_comment(project_id, user.org_id, vista["pregunta"], category_id, comment_id):  # $pull puntual
        raise HTTPException(404, "Comentario no encontrado")
    store.log_event(vista, "analista", "eliminacion_comentario", {
        "categoria_id": category_id, "comentario_id": comment_id, "usuario": user.email,
    })
    return {"deleted": comment_id}


# ---------- Codificación con seguimiento de progreso ----------

@router.post("/api/projects/{project_id}/codify")
def codify(project_id: str, pregunta: Optional[str] = None, user: User = Depends(require_role("analista"))):
    vista = _get_vista(project_id, user, pregunta)
    validated = [c for c in vista["categories"] if c["status"] == "validada"]
    if not validated:
        raise HTTPException(400, "No hay categorías validadas. Valida el libro de códigos antes de codificar.")

    total = len(vista["responses"])
    qid = vista["pregunta"]  # el hilo captura la pregunta: el progreso es por (proyecto, pregunta)
    key = (project_id, qid)
    with _progress_lock:
        en_curso = _codify_progress.get(key, {})
        if en_curso.get("status") == "running":
            return {"status": "already_running", "total": en_curso.get("total", total)}
        _codify_progress[key] = {"done": 0, "total": total, "status": "running"}
    org_id = user.org_id

    def run():
        claude_log.current_project_id.set(project_id)  # hilo nuevo: sin contexto heredado
        try:
            proj = store.get_project(project_id, org_id)
            v = store.vista_pregunta(proj, qid) if proj else None
            if not v:
                _codify_progress[key] = {"status": "error", "error": "Proyecto no encontrado", "done": 0, "total": 0}
                return

            def progress_cb(done: int, total: int):
                _codify_progress[key] = {"done": done, "total": total, "status": "running"}

            results = thematic.codify_all(
                v["marco_teorico"], validated, v["responses"], progress_cb=progress_cb
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
            store.set_codings_bulk(project_id, org_id, qid, new_codings)
            v["codings"].update(new_codings)
            store.log_event(v, "claude", "codificacion_corpus", {
                "n_respuestas": len(results), "n_asignaciones": n_assigned, "pregunta": qid,
                "categorias_usadas": [c["nombre"] for c in validated],
            })
            _codify_progress[key] = {
                "done": total, "total": total, "status": "done",
                "coded": len(results), "assignments": n_assigned,
            }
        except Exception as e:
            _codify_progress[key] = {
                "status": "error", "error": str(e), "done": 0, "total": total,
            }

    threading.Thread(target=run, daemon=True).start()
    return {"status": "started", "total": total}


@router.get("/api/projects/{project_id}/analysis-status")
def analysis_status(project_id: str, pregunta: Optional[str] = None, user: User = Depends(get_current_user)):
    vista = _get_vista(project_id, user, pregunta)
    return {op: "running" if (project_id, vista["pregunta"], op) in _analisis_en_curso else "idle"
            for op in ("lexical", "propose")}


@router.get("/api/projects/{project_id}/codify/progress")
def codify_progress(project_id: str, pregunta: Optional[str] = None, user: User = Depends(get_current_user)):
    vista = _get_vista(project_id, user, pregunta)
    return _codify_progress.get((project_id, vista["pregunta"]), {"status": "idle"})


class RecodeBody(BaseModel):
    category_ids: list[str]
    rationale: str = "Re-codificación manual del analista"


@router.put("/api/projects/{project_id}/responses/{response_id}/codings")
def recode(project_id: str, response_id: str, body: RecodeBody, pregunta: Optional[str] = None,
           user: User = Depends(require_role("analista"))):
    vista = _get_vista(project_id, user, pregunta)
    before = vista["codings"].get(response_id, [])
    vista["codings"][response_id] = [
        {"category_id": cid, "rationale": body.rationale, "confidence": 1.0,
         "source": "analista", "status": "validada"}
        for cid in body.category_ids
    ]
    # $set de UNA respuesta: no reescribe el resto del corpus codificado
    store.set_codings_for_response(project_id, user.org_id, vista["pregunta"], response_id, vista["codings"][response_id])
    store.log_event(vista, "analista", "recodificacion_manual", {
        "response_id": response_id, "antes": before,
        "despues": vista["codings"][response_id], "usuario": user.email,
    })
    return vista["codings"][response_id]


# ---------- Resultados, trazabilidad e informe ----------

@router.get("/api/projects/{project_id}/summary")
def summary(project_id: str, pregunta: Optional[str] = None, user: User = Depends(get_current_user)):
    vista = _get_vista(project_id, user, pregunta)
    cat_names = {c["id"]: c["nombre"] for c in vista["categories"]}
    cat_names["SIN_CATEGORIA"] = "Sin categoría"
    counts: dict[str, int] = {}
    conf_dist = {"alta": 0, "media": 0, "baja": 0}
    for assignments in vista["codings"].values():
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
        "sentiment_distribution": (vista["lexical"] or {}).get("sentiment_distribution", {}),
        "confidence_distribution": conf_dist,
        "n_responses": len(vista["responses"]),
        "n_coded": len(vista["codings"]),
        "n_categories_validated": len([c for c in vista["categories"] if c["status"] == "validada"]),
        "has_lexical": vista["lexical"] is not None,
        "has_report": bool(vista.get("qualitative_report")),
    }


@router.get("/api/projects/{project_id}/audit")
def audit(project_id: str, user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    return project["audit_log"]
