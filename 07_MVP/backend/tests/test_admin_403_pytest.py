"""T-009 RNF-13: el panel interno responde 403 (no 401) con X-Admin-Password ausente o incorrecta."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import mongomock
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")

from app import database  # noqa: E402

database._client = mongomock.MongoClient()

from fastapi.testclient import TestClient  # noqa: E402

from app.main import ADMIN_PASSWORD, app  # noqa: E402

MSG = "Contraseña de administrador incorrecta"
BODY = {"system": "s", "instructions": "i"}
# Con la contraseña correcta, PUT/reset usan una clave inexistente: llegan al 404 sin escribir prompts.json.
ENDPOINTS = [
    ("GET", "/api/admin/usage", None, 200),
    ("GET", "/api/admin/health", None, 200),
    ("GET", "/api/admin/prompts", None, 200),
    ("PUT", "/api/admin/prompts/no_existe", BODY, 404),
    ("POST", "/api/admin/prompts/no_existe/reset", None, 404),
]
c = TestClient(app)


@pytest.mark.parametrize("headers", [{}, {"X-Admin-Password": "mala"}])
@pytest.mark.parametrize("metodo,ruta,body,_", ENDPOINTS)
def test_contrasena_incorrecta_o_ausente_es_403(metodo, ruta, body, _, headers):
    r = c.request(metodo, ruta, json=body, headers=headers)
    assert r.status_code == 403
    assert r.json()["detail"] == MSG


@pytest.mark.parametrize("metodo,ruta,body,esperado", ENDPOINTS)
def test_contrasena_correcta_pasa(metodo, ruta, body, esperado):
    r = c.request(metodo, ruta, json=body, headers={"X-Admin-Password": ADMIN_PASSWORD})
    assert r.status_code == esperado
