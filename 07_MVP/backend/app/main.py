"""
SoftInsight v1.0 — API.

Flujo: signup/login → crear proyecto (upload CSV/XLSX + marco teórico, opcionalmente
desde plantilla) → análisis léxico → propuesta de categorías (Claude) → validación
humana → codificación (Claude) → revisión/re-codificación → trazabilidad →
informe cualitativo → exportación PDF/DOCX/CSV/XLSX.

Multi-tenant: cada endpoint de proyecto exige JWT y filtra por org_id.
"""
from __future__ import annotations

import unicodedata
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import store
from app.auth import router as auth_router
from app.database import init_db
from app.deps import ADMIN_PASSWORD  # noqa: F401  (las pruebas lo importan desde aquí)
from app.routers.admin import router as admin_router
from app.routers.analysis import router as analysis_router
from app.routers.integrations import router as integrations_router
from app.routers.projects import router as projects_router
from app.routers.reports import router as reports_router
from app.services import claude_log

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
app.include_router(admin_router)
