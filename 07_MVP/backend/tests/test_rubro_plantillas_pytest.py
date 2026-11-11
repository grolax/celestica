"""RF-10 (T-048): el rubro de la organización ordena la lista de plantillas y desempata la sugerencia. mongomock, sin IA.

Empate real usado en las pruebas: "Cliente", "Tu compra" y "¿Nos recomiendas?" dan 2 coincidencias a
satisfaccion_clientes_nps (Estudios de Mercado: cliente, recomiend) y 2 a retail_post_compra_nps (Retail: compra, recomiend).
"""
from __future__ import annotations

import io
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

ABIERTA = {"titulo": "Comentario", "tipo": "abierta"}
EMPATE = [{"titulo": t, "tipo": "seleccion_unica"} for t in ("Cliente", "Tu compra", "¿Nos recomiendas?")] + [ABIERTA]
FRASE = " Entre plantillas parecidas, elegimos la de tu rubro."
ORDEN_DEFECTO = list(FRAMEWORK_TEMPLATES)
RETAIL = [k for k, t in FRAMEWORK_TEMPLATES.items() if t["industria"] == "Retail"]


def _org(c, email, rubro=None):
    r = c.post("/auth/signup", json={"email": email, "password": "clave12345"})
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    if rubro:
        assert c.put("/api/org/profile", headers=h, json={"nombre": "Org", "rubro": rubro, "color": None}).status_code == 200
    return h


@pytest.fixture(scope="module")
def env():
    c = TestClient(app)
    return c, {"A": _org(c, "rubro-a@x.cl", "Retail"), "B": _org(c, "rubro-b@x.cl"), "C": _org(c, "rubro-c@x.cl", "Otro")}


def _lista(env, org):
    c, heads = env
    return [t["key"] for t in c.get("/api/framework-templates", headers=heads[org]).json()]


def _sugerir(env, org, preguntas):
    c, heads = env
    r = c.post("/api/projects/suggest-template", headers=heads[org], json={"preguntas": preguntas})
    assert r.status_code == 200, r.text
    return r.json()["plantilla"]


def _reco(env, org, titulos=("Cliente", "Tu compra", "¿Nos recomiendas?")):
    c, heads = env
    h = heads[org]
    csv = "id_respuesta," + ",".join(titulos) + ",Comentario\n" + "\n".join(
        f"E{i:03d}," + ",".join("Sí" if i % 2 else "No" for _ in titulos) + f",Me gustó la compra {i}" for i in range(24))
    pid = c.post("/api/projects", headers=h, data={"name": "P"},
                 files={"file": ("e.csv", io.BytesIO(csv.encode()), "text/csv")}).json()["id"]
    return c.get(f"/api/projects/{pid}/recommendations", headers=h).json()["plantilla"]


# ---------- GET /api/framework-templates ----------

def test_lista_con_rubro_retail_pone_primero_las_4_de_retail_y_luego_las_demas_en_su_orden(env):
    assert len(RETAIL) == 4
    assert _lista(env, "A") == RETAIL + [k for k in ORDEN_DEFECTO if k not in RETAIL]


def test_lista_sin_rubro_y_con_otro_conserva_el_orden_de_hoy(env):
    assert _lista(env, "B") == ORDEN_DEFECTO
    assert _lista(env, "C") == ORDEN_DEFECTO


# ---------- desempate en suggest-template y recommendations ----------

def test_empate_sin_rubro_gana_la_primera_sin_frase(env):
    esperado = {"key": "satisfaccion_clientes_nps", "nombre": "Satisfacción de Clientes (verbatims NPS)",
                "industria": "Estudios de Mercado", "motivo": "La encuesta menciona «cliente» y «recomiend»."}
    assert _sugerir(env, "B", EMPATE) == esperado
    assert _reco(env, "B") == esperado


def test_empate_con_rubro_gana_la_del_rubro_y_el_motivo_termina_con_la_frase(env):
    esperado = {"key": "retail_post_compra_nps", "nombre": "Post-compra y NPS", "industria": "Retail",
                "motivo": "La encuesta menciona «compra» y «recomiend»." + FRASE}
    assert _sugerir(env, "A", EMPATE) == esperado
    assert _reco(env, "A") == esperado


def test_sin_empate_el_rubro_no_cambia_resultado_ni_motivo(env):
    docente = [{"titulo": t, "tipo": "seleccion_unica"} for t in ("profesor", "clase", "docente")]
    con_rubro, sin_rubro = _sugerir(env, "A", docente + EMPATE), _sugerir(env, "B", docente + EMPATE)
    assert con_rubro == sin_rubro and con_rubro["key"] == "evaluacion_docente_cna" and FRASE not in con_rubro["motivo"]
    assert _reco(env, "A", ("profesor", "clase", "docente", "Tu compra", "¿Nos recomiendas?"))["key"] == "evaluacion_docente_cna"


def test_una_sola_coincidencia_con_rubro_que_calza_sigue_null(env):
    assert _sugerir(env, "A", [{"titulo": "Tu compra", "tipo": "seleccion_unica"}, ABIERTA]) is None


def test_el_rubro_de_a_no_se_filtra_a_la_organizacion_b(env):
    # B (sin rubro) ya recibe el orden de hoy y la primera del empate aunque A tenga rubro Retail
    assert _lista(env, "B") == ORDEN_DEFECTO
    assert _sugerir(env, "B", EMPATE)["key"] == "satisfaccion_clientes_nps"
    assert _sugerir(env, "C", EMPATE)["key"] == "satisfaccion_clientes_nps"
