"""RF-41 (T-039): editar el marco teórico después de crear el proyecto.

mongomock e IA simulada que hace fallar la prueba si se llama: ninguna llamada real.
"""
from __future__ import annotations

import io
import json
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

from app import store  # noqa: E402
from app.auth import create_token, hash_password  # noqa: E402
from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User, user_to_doc  # noqa: E402
from app.services import thematic  # noqa: E402

CSV = "id_respuesta,respuesta\n" + "\n".join(f"E{i:03d},El curso fue bueno ({i})" for i in range(1, 6))
CERRADAS = "Sede\nNorte\nSur\nNorte\n"
E400_LARGO = "El marco teórico no puede superar los 5.000 caracteres."
E400_SIN_ABIERTAS = "Este proyecto no tiene preguntas abiertas, así que no usa marco teórico."


@pytest.fixture(scope="module")
def env():
    ia: list[str] = []
    fingerprint = thematic._v2_analyses_fingerprint  # la función real: no es una llamada a la IA

    def no_ia(*a, **k):
        ia.append("ia")
        raise AssertionError("se llamó a la IA al editar el marco")

    mp = pytest.MonkeyPatch()
    for f in ("propose_categories", "codify_all", "interpret_lexical", "generate_qualitative_report",
              "generate_qualitative_report_v2", "client"):
        mp.setattr(thematic, f, no_ia)

    c = TestClient(app, raise_server_exceptions=False)
    heads, orgs = {}, {}
    for who in ("a", "b"):
        r = c.post("/auth/signup", json={"email": f"marco-{who}@x.cl", "password": "clave12345"})
        heads[who] = {"Authorization": f"Bearer {r.json()['token']}"}
        orgs[who] = r.json()["user"]["organizacion"]["id"]
    u = User(id="usr_lectormarco", email="marco-lector@x.cl", password_hash=hash_password("clave12345"), nombre="L",
             empresa="", created_at=store.now_iso(), org_id=orgs["a"], rol="lector")
    get_db().users.insert_one(user_to_doc(u))
    yield {"c": c, "h": heads["a"], "hb": heads["b"], "hl": {"Authorization": f"Bearer {create_token(u.id)}"},
           "org": orgs["a"], "ia": ia, "fp": fingerprint}
    mp.undo()
    assert ia == []


def _crear(env, csv=CSV, **extra):
    r = env["c"].post("/api/projects", headers=env["h"], data={"name": "Marco", **extra},
                      files={"file": ("e.csv", io.BytesIO(csv.encode()), "text/csv")})
    assert r.status_code == 200, r.text
    return r.json()["id"]


@pytest.fixture()
def pid(env):
    return _crear(env, marco_teorico="Marco original")


def _patch(env, pid, texto, headers=None):
    return env["c"].patch(f"/api/projects/{pid}", headers=headers or env["h"], json={"marco_teorico": texto})


def _eventos(env, pid):
    return [e for e in env["c"].get(f"/api/projects/{pid}/audit", headers=env["h"]).json()
            if e["action"] == "cambio_marco_teorico"]


def test_cambia_el_marco_sin_espacios_en_los_extremos(env, pid):
    r = _patch(env, pid, "  Marco nuevo \n")
    assert r.status_code == 200 and r.json() == {"marco_teorico": "Marco nuevo"}
    assert env["c"].get(f"/api/projects/{pid}", headers=env["h"]).json()["marco_teorico"] == "Marco nuevo"


def test_el_marco_puede_quedar_vacio(env, pid):
    r = _patch(env, pid, "   ")
    assert r.status_code == 200 and r.json() == {"marco_teorico": ""}
    assert env["c"].get(f"/api/projects/{pid}", headers=env["h"]).json()["marco_teorico"] == ""


@pytest.mark.parametrize("texto", ["Marco original", "  Marco original  "])
def test_mismo_texto_no_escribe_ni_audita(env, pid, texto):
    antes = get_db().projects.find_one({"_id": pid})
    r = _patch(env, pid, texto)
    assert r.status_code == 200 and r.json() == {"marco_teorico": "Marco original"}
    assert get_db().projects.find_one({"_id": pid}) == antes and _eventos(env, pid) == []


def test_limite_de_5000_caracteres(env, pid):
    assert _patch(env, pid, "x" * 5000).status_code == 200
    assert _patch(env, pid, f"  {'y' * 5000}  ").status_code == 200  # el límite cuenta sin los espacios de los extremos
    r = _patch(env, pid, "z" * 5001)
    assert r.status_code == 400 and r.json()["detail"] == E400_LARGO
    assert env["c"].get(f"/api/projects/{pid}", headers=env["h"]).json()["marco_teorico"] == "y" * 5000
    assert len(_eventos(env, pid)) == 2


def test_proyecto_sin_abiertas_400_y_no_cambia(env):
    pid = _crear(env, CERRADAS, marco_teorico="Marco original",
                 preguntas=json.dumps([{"titulo": "Sede", "columnas": ["Sede"], "tipo": "seleccion_unica"}]))
    antes = get_db().projects.find_one({"_id": pid})
    r = _patch(env, pid, "Otro")
    assert r.status_code == 400 and r.json()["detail"] == E400_SIN_ABIERTAS
    assert get_db().projects.find_one({"_id": pid}) == antes


def test_audita_antes_despues_y_usuario_y_solo_crece(env, pid):
    total = len(env["c"].get(f"/api/projects/{pid}/audit", headers=env["h"]).json())
    _patch(env, pid, "Segundo")
    _patch(env, pid, "Tercero")
    ev = _eventos(env, pid)
    assert [e["detail"] for e in ev] == [
        {"antes": "Marco original", "despues": "Segundo", "usuario": "marco-a@x.cl"},
        {"antes": "Segundo", "despues": "Tercero", "usuario": "marco-a@x.cl"}]
    assert ev[0]["actor"] == "analista"
    assert len(env["c"].get(f"/api/projects/{pid}/audit", headers=env["h"]).json()) == total + 2
    assert get_db().audit_events.count_documents({"project_id": pid, "action": "cambio_marco_teorico"}) == 2


def test_no_toca_lo_generado_ni_llama_a_la_ia(env, pid):
    c, h = env["c"], env["h"]
    cid = c.post(f"/api/projects/{pid}/categories", headers=h, json={"nombre": "Docencia"}).json()["id"]
    c.put(f"/api/projects/{pid}/responses/E001/codings", headers=h, json={"category_ids": [cid]})
    store.set_project_field(pid, env["org"], "lexical", {"top_words": ["curso"]}, "q_1")
    store.set_project_field(pid, env["org"], "qualitative_report", "# Informe", "q_1")
    antes = get_db().projects.find_one({"_id": pid})

    assert _patch(env, pid, "Marco distinto").status_code == 200

    despues = get_db().projects.find_one({"_id": pid})
    for d in (antes, despues):  # lo único que cambia es el marco y la auditoría
        d.pop("marco_teorico"), d.pop("audit_log")
    assert despues == antes
    assert despues["analisis"]["q_1"]["codings"] and despues["analisis"]["q_1"]["lexical"]
    assert despues["analisis"]["q_1"]["qualitative_report"] == "# Informe"
    assert env["ia"] == []


def test_la_huella_del_informe_profundo_cambia_con_el_marco(env):
    respuestas = [{"id": "E001", "text": "bien", "meta": {}}]
    assert env["fp"]("Marco A", respuestas) != env["fp"]("Marco B", respuestas)
    assert env["fp"]("Marco A", respuestas) == env["fp"]("Marco A", respuestas)


def test_lector_recibe_403_y_no_cambia(env, pid):
    r = _patch(env, pid, "Intruso", env["hl"])
    assert r.status_code == 403 and _eventos(env, pid) == []
    assert get_db().projects.find_one({"_id": pid})["marco_teorico"] == "Marco original"


def test_otra_organizacion_404_y_no_cambia(env, pid):
    antes = get_db().projects.find_one({"_id": pid})
    r = _patch(env, pid, "Ajeno", env["hb"])
    assert r.status_code == 404 and r.json()["detail"] == "Proyecto no encontrado"
    assert get_db().projects.find_one({"_id": pid}) == antes
