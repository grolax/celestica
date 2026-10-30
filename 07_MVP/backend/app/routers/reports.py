"""Trazabilidad, exportaciones e informe cualitativo (movido tal cual desde main.py)."""
from __future__ import annotations

import threading
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app import store
from app.auth import get_current_user
from app.deps import _REPORT_EXPECTED_CHARS, _get_or_404, _report_progress, _slug, require_role
from app.models import User
from app.services import claude_log, thematic
from app.services import export as export_svc

router = APIRouter()


@router.get("/api/projects/{project_id}/export/traceability")
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


@router.get("/api/projects/{project_id}/export/pdf")
def export_pdf(project_id: str, include_details: bool = True,
               user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    pdf = export_svc.generate_pdf_report(project, include_details=include_details)
    return _download(pdf, f"informe_celestica_{_slug(project['name'])}.pdf", "application/pdf")


@router.get("/api/projects/{project_id}/export/docx")
def export_docx(project_id: str, include_details: bool = True,
                user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    docx_bytes = export_svc.generate_docx_report(project, include_details=include_details)
    return _download(
        docx_bytes, f"informe_celestica_{_slug(project['name'])}.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/api/projects/{project_id}/export/csv")
def export_csv(project_id: str, user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    return _download(export_svc.generate_csv_export(project),
                     f"trazabilidad_{_slug(project['name'])}.csv", "text/csv; charset=utf-8")


@router.get("/api/projects/{project_id}/export/xlsx")
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


@router.post("/api/projects/{project_id}/report")
def generate_report(project_id: str, mode: str = "v2", force_full: bool = False,
                    user: User = Depends(require_role("analista"))):
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
    org_id = user.org_id

    def run():
        claude_log.current_project_id.set(project_id)  # hilo nuevo: sin contexto heredado
        try:
            proj = store.get_project(project_id, org_id)
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
                        project_id, org_id, "v2_analyses_cache",
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
            store.set_project_field(project_id, org_id, "qualitative_report", report)  # $set puntual
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


@router.get("/api/projects/{project_id}/report/progress")
def report_progress(project_id: str, user: User = Depends(get_current_user)):
    _get_or_404(project_id, user)
    return _report_progress.get(project_id, {"status": "idle"})


@router.get("/api/projects/{project_id}/report")
def get_report(project_id: str, user: User = Depends(get_current_user)):
    project = _get_or_404(project_id, user)
    if not project.get("qualitative_report"):
        raise HTTPException(404, "Informe no generado aún")
    return {"report": project["qualitative_report"]}
