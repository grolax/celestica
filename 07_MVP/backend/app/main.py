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
from app.routers.integrations import router as integrations_router
from app.routers.projects import router as projects_router
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
    return _download(pdf, f"informe_celestica_{_slug(project['name'])}.pdf", "application/pdf")


@app.get("/api/projects/{project_id}/export/docx")
def export_docx(project_id: str, include_details: bool = True,
                user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    docx_bytes = export_svc.generate_docx_report(project, include_details=include_details)
    return _download(
        docx_bytes, f"informe_celestica_{_slug(project['name'])}.docx",
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
