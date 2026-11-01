"""RF-17 (T-031): estructura de todas las plantillas de marco teórico y las de Retail y Municipal.

Sin IA ni internet; mongomock.
"""
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

from app.main import app  # noqa: E402
from app.templates import FRAMEWORK_TEMPLATES  # noqa: E402

NUEVAS = {"Retail": 4, "Municipal": 3}
CAMPOS_CAT = ("nombre", "definicion", "criterios_inclusion", "criterios_exclusion")


@pytest.mark.parametrize("key", FRAMEWORK_TEMPLATES)
def test_estructura_de_cada_plantilla(key):
    t = FRAMEWORK_TEMPLATES[key]
    assert all(str(t.get(k, "")).strip() for k in ("nombre", "industria", "descripcion", "marco_teorico"))
    cats = t["categorias_default"]
    assert 4 <= len(cats) <= 6
    for c in cats:
        assert all(str(c.get(k, "")).strip() for k in CAMPOS_CAT), (key, c.get("nombre"))
    nombres = [c["nombre"] for c in cats]
    assert len(set(nombres)) == len(nombres)


@pytest.mark.parametrize("key", [k for k, t in FRAMEWORK_TEMPLATES.items() if t["industria"] in NUEVAS])
def test_plantillas_nuevas_clave_y_exclusion_con_vecina(key):
    assert key == key.lower() and " " not in key
    cats = FRAMEWORK_TEMPLATES[key]["categorias_default"]
    for c in cats:
        otras = [o["nombre"] for o in cats if o is not c]
        assert any(o in c["criterios_exclusion"] for o in otras), (key, c["nombre"])


def test_listado_incluye_retail_y_municipal():
    c = TestClient(app)
    r = c.post("/auth/signup", json={"email": "tpl@x.cl", "password": "clave12345"})
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    lista = c.get("/api/framework-templates", headers=h).json()
    for industria, n in NUEVAS.items():
        assert sum(1 for t in lista if t["industria"] == industria) == n


def test_aplicar_plantilla_nueva_crea_categorias_propuestas():
    c = TestClient(app)
    r = c.post("/auth/signup", json={"email": "tpl2@x.cl", "password": "clave12345"})
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    csv = "id_respuesta,respuesta\n" + "\n".join(f"E{i},Me atendieron bien ({i})" for i in range(5))
    p = c.post("/api/projects", headers=h, data={"name": "Tienda"},
               files={"file": ("e.csv", csv.encode(), "text/csv")})
    assert p.status_code == 200, p.text
    r = c.post(f"/api/projects/{p.json()['id']}/apply-template", params={"template": "retail_experiencia_tienda"}, headers=h)
    assert r.status_code == 200, r.text
    cats = r.json()["categories"]
    assert len(cats) == len(FRAMEWORK_TEMPLATES["retail_experiencia_tienda"]["categorias_default"])
    assert all(x["status"] == "propuesta" and x["origen"] == "plantilla" for x in cats)
    assert r.json()["marco_teorico"] == FRAMEWORK_TEMPLATES["retail_experiencia_tienda"]["marco_teorico"]
