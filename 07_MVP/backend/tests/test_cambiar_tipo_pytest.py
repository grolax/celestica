"""RF-25 (T-037): cambiar el tipo de una pregunta cerrada después de crear el proyecto.

mongomock e IA simulada que hace fallar la prueba si se llama: ninguna llamada real.
"""
from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

import mongomock
import pandas as pd
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

DF = pd.DataFrame({
    "Satisfacción": [str(i % 5 + 1) for i in range(10)],
    "Sede": ["Norte", "Sur"] * 5,
    "Texto": ["alto", "bajo"] * 5,
    "Nueve": [str(i) for i in range(9)] + ["no sé"],       # 9 de 10 son números
    "Ocho": [str(i) for i in range(8)] + ["no sé", "nada"],  # 8 de 10
    "Grande": [str(i * 3) for i in range(10)],              # hasta 27: fuera de 0-10
    "Vacia": [""] * 10,
    "Comentario": ["bien"] * 10,
    "Fecha": ["2026-01-0%d" % (i % 9 + 1) for i in range(10)],
})
COLS = {  # título -> tipo inicial
    "Satisfacción": "seleccion_unica", "Sede": "segmento", "Texto": "seleccion_unica", "Nueve": "seleccion_unica",
    "Ocho": "seleccion_unica", "Grande": "numerica", "Vacia": "seleccion_unica", "Comentario": "abierta", "Fecha": "fecha",
}
PREGUNTAS = [{"titulo": t, "columnas": [t], "tipo": tipo} for t, tipo in COLS.items()]
ID = {t: f"q_{i + 1}" for i, t in enumerate(COLS)}


@pytest.fixture(scope="module")
def env():
    ia: list[str] = []

    def no_ia(*a, **k):
        ia.append("ia")
        raise AssertionError("se llamó a la IA al cambiar el tipo de una pregunta")

    mp = pytest.MonkeyPatch()
    for f in ("propose_categories", "codify_all", "interpret_lexical", "generate_qualitative_report",
              "generate_qualitative_report_v2", "client"):
        mp.setattr(thematic, f, no_ia)

    c = TestClient(app, raise_server_exceptions=False)
    heads, orgs = {}, {}
    for who in ("a", "b"):
        r = c.post("/auth/signup", json={"email": f"tipo-{who}@x.cl", "password": "clave12345"})
        heads[who] = {"Authorization": f"Bearer {r.json()['token']}"}
        orgs[who] = r.json()["user"]["organizacion"]["id"]
    u = User(id="usr_lectortipo", email="tipo-lector@x.cl", password_hash=hash_password("clave12345"), nombre="L",
             empresa="", created_at=store.now_iso(), org_id=orgs["a"], rol="lector")
    get_db().users.insert_one(user_to_doc(u))
    yield {"c": c, "h": heads["a"], "hb": heads["b"], "hl": {"Authorization": f"Bearer {create_token(u.id)}"},
           "org": orgs["a"], "ia": ia}
    mp.undo()
    assert ia == []


@pytest.fixture()
def pid(env):
    r = env["c"].post("/api/projects", headers=env["h"], data={"name": "Tipos", "preguntas": json.dumps(PREGUNTAS)},
                      files={"file": ("e.csv", io.BytesIO(DF.to_csv(index=False).encode()), "text/csv")})
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _patch(env, pid, titulo, tipo, headers=None):
    return env["c"].patch(f"/api/projects/{pid}/preguntas/{ID[titulo]}", headers=headers or env["h"], json={"tipo": tipo})


def _acciones(env, pid):
    return [e for e in env["c"].get(f"/api/projects/{pid}/audit", headers=env["h"]).json() if e["action"] == "cambio_tipo_pregunta"]


def test_de_seleccion_unica_a_escala(env, pid):
    r = _patch(env, pid, "Satisfacción", "escala")
    assert r.status_code == 200, r.text
    assert r.json() == {"id": ID["Satisfacción"], "titulo": "Satisfacción", "columnas": ["Satisfacción"], "tipo": "escala",
                        "contexto_ia": r.json()["contexto_ia"], "n_respuestas": 10, "n_na": 0}
    q = next(q for q in env["c"].get(f"/api/projects/{pid}/closed-results", headers=env["h"]).json()["preguntas"]
             if q["id"] == ID["Satisfacción"])
    assert q["tipo"] == "escala" and "escala" in q and "opciones" in q
    assert next(p for p in env["c"].get(f"/api/projects/{pid}", headers=env["h"]).json()["preguntas"]
                if p["id"] == ID["Satisfacción"])["tipo"] == "escala"


def test_audita_antes_despues_y_usuario_y_solo_crece(env, pid):
    antes = len(env["c"].get(f"/api/projects/{pid}/audit", headers=env["h"]).json())
    _patch(env, pid, "Satisfacción", "escala")
    _patch(env, pid, "Satisfacción", "numerica")
    ev = _acciones(env, pid)
    assert [e["detail"] for e in ev] == [
        {"pregunta": ID["Satisfacción"], "titulo": "Satisfacción", "antes": "seleccion_unica", "despues": "escala", "usuario": "tipo-a@x.cl"},
        {"pregunta": ID["Satisfacción"], "titulo": "Satisfacción", "antes": "escala", "despues": "numerica", "usuario": "tipo-a@x.cl"}]
    assert ev[0]["actor"] == "analista"
    assert len(env["c"].get(f"/api/projects/{pid}/audit", headers=env["h"]).json()) == antes + 2
    assert get_db().audit_events.count_documents({"project_id": pid, "action": "cambio_tipo_pregunta"}) == 2


def test_mismo_tipo_no_escribe_ni_audita(env, pid):
    antes = get_db().projects.find_one({"_id": pid})
    r = _patch(env, pid, "Sede", "segmento")
    assert r.status_code == 200 and r.json()["tipo"] == "segmento"
    assert get_db().projects.find_one({"_id": pid}) == antes and _acciones(env, pid) == []


def test_tipo_invalido(env, pid):
    r = _patch(env, pid, "Sede", "inventado")
    assert r.status_code == 400 and r.json()["detail"] == "«inventado» no es un tipo de pregunta válido."
    assert _acciones(env, pid) == []


@pytest.mark.parametrize("titulo,tipo", [("Comentario", "escala"), ("Sede", "abierta"), ("Sede", "fecha"), ("Fecha", "escala"),
                                         ("Comentario", "abierta")])
def test_solo_entre_cerradas(env, pid, titulo, tipo):
    r = _patch(env, pid, titulo, tipo)
    assert r.status_code == 400 and r.json()["detail"] == "Solo se puede cambiar el tipo entre preguntas cerradas."
    assert _acciones(env, pid) == []
    assert next(p for p in env["c"].get(f"/api/projects/{pid}", headers=env["h"]).json()["preguntas"]
                if p["id"] == ID[titulo])["tipo"] == COLS[titulo]


@pytest.mark.parametrize("tipo,etiqueta", [("escala", "Escala"), ("nps", "NPS"), ("numerica", "Numérica")])
def test_texto_no_pasa_a_tipos_numericos(env, pid, tipo, etiqueta):
    r = _patch(env, pid, "Texto", tipo)
    assert r.status_code == 400
    assert r.json()["detail"] == f"Las respuestas de esta pregunta no son números, así que no puede ser «{etiqueta}»."
    assert _acciones(env, pid) == []


def test_borde_del_90_por_ciento(env, pid):
    assert _patch(env, pid, "Nueve", "escala").status_code == 200  # 9 de 10
    r = _patch(env, pid, "Ocho", "escala")  # 8 de 10
    assert r.status_code == 400 and "no son números" in r.json()["detail"]
    assert len(_acciones(env, pid)) == 1


def test_nps_exige_0_a_10(env, pid):
    r = _patch(env, pid, "Grande", "nps")
    assert r.status_code == 400 and r.json()["detail"] == "Para ser NPS, las respuestas deben ser números del 0 al 10."
    assert _patch(env, pid, "Satisfacción", "nps").status_code == 200  # 1 a 5
    assert len(_acciones(env, pid)) == 1


def test_pregunta_sin_respuestas_pasa(env, pid):
    assert _patch(env, pid, "Vacia", "escala").status_code == 200  # nada que contradiga


def test_pregunta_inexistente(env, pid):
    r = env["c"].patch(f"/api/projects/{pid}/preguntas/q_99", headers=env["h"], json={"tipo": "escala"})
    assert r.status_code == 404 and r.json()["detail"] == "Pregunta no encontrada"


def test_lector_recibe_403_y_no_cambia(env, pid):
    r = _patch(env, pid, "Satisfacción", "escala", env["hl"])
    assert r.status_code == 403 and _acciones(env, pid) == []
    assert get_db().projects.find_one({"_id": pid})["preguntas"][0]["tipo"] == "seleccion_unica"


def test_otra_organizacion_404_y_no_cambia(env, pid):
    antes = get_db().projects.find_one({"_id": pid})
    r = _patch(env, pid, "Satisfacción", "escala", env["hb"])
    assert r.status_code == 404 and r.json()["detail"] == "Proyecto no encontrado"
    assert get_db().projects.find_one({"_id": pid}) == antes


def test_la_escritura_filtra_por_org_en_el_store(env, pid):
    assert store.set_pregunta_tipo(pid, "org_ajena", ID["Sede"], "si_no") is False
    assert store.set_pregunta_tipo(pid, "", ID["Sede"], "si_no") is False
    assert get_db().projects.find_one({"_id": pid})["preguntas"][1]["tipo"] == "segmento"
    assert store.set_pregunta_tipo(pid, env["org"], ID["Sede"], "si_no") is True
