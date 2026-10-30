"""Piezas que comparten los routers (movidas tal cual desde main.py)."""
from __future__ import annotations

import os
import unicodedata

from fastapi import Depends, HTTPException, Request

from app import store
from app.auth import get_current_user
from app.models import User
from app.services import claude_log


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
        raise HTTPException(403, "Contraseña de administrador incorrecta")


# Única tabla de roles (RF-03): nivel de menor a mayor y etiqueta en español.
# Un rol desconocido en la base se trata como lector, nunca como admin.
ROL_NIVEL = {"lector": 0, "analista": 1, "admin": 2}
ROL_ETIQUETA = {"lector": "Lector", "analista": "Analista", "admin": "Administrador"}


def require_role(minimo: str):
    """Dependencia como get_current_user (401) que además exige rol >= `minimo` (403)."""
    def dep(user: User = Depends(get_current_user)) -> User:
        if ROL_NIVEL.get(user.rol, 0) < ROL_NIVEL[minimo]:
            raise HTTPException(403, f"Tu rol ({ROL_ETIQUETA.get(user.rol, 'Lector')}) no permite esta acción.")
        return user
    return dep


def _get_or_404(project_id: str, user: User) -> dict:
    project = store.get_project(project_id, user.org_id)
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
