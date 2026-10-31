"""RF-24 (T-025): proyectos con solo preguntas cerradas.

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
from app.services.integrations import google_forms, qualtrics  # noqa: E402

N = 6
DF = pd.DataFrame({
    "Satisfacción": ["1", "2", "3", "4", "5", "5"],
    "Sede": ["Norte", "Sur"] * 3,
    "Fecha": ["2026-01-0%d" % i for i in range(1, 7)],
    "Comentario": ["", "bien", "mal", "", "ok", "ok"],
})
ESCALA = {"titulo": "Satisfacción", "columnas": ["Satisfacción"], "tipo": "escala"}
SEDE = {"titulo": "Sede", "columnas": ["Sede"], "tipo": "segmento"}
FECHA = {"titulo": "Fecha", "columnas": ["Fecha"], "tipo": "fecha"}
ABIERTA = {"titulo": "Comentario", "columnas": ["Comentario"], "tipo": "abierta"}
SOLO_CERRADAS = [ESCALA, SEDE, FECHA]
MENSAJE = "Esta encuesta no tiene preguntas que se puedan analizar: marca al menos una pregunta abierta o cerrada."


@pytest.fixture(scope="module")
def env():
    ia: list[str] = []

    def no_ia(*a, **k):
        ia.append("ia")
        raise AssertionError("se llamó a la IA en un proyecto sin abiertas")

    mp = pytest.MonkeyPatch()
    for f in ("propose_categories", "codify_all", "interpret_lexical", "generate_qualitative_report",
              "generate_qualitative_report_v2", "client"):
        mp.setattr(thematic, f, no_ia)

    c = TestClient(app, raise_server_exceptions=False)
    heads, orgs = {}, {}
    for who in ("a", "b"):
        r = c.post("/auth/signup", json={"email": f"cerr-{who}@x.cl", "password": "clave12345"})
        heads[who] = {"Authorization": f"Bearer {r.json()['token']}"}
        orgs[who] = r.json()["user"]["organizacion"]["id"]
    u = User(id="usr_lectorcerr", email="cerr-lector@x.cl", password_hash=hash_password("clave12345"), nombre="L",
             empresa="", created_at=store.now_iso(), org_id=orgs["a"], rol="lector")
    get_db().users.insert_one(user_to_doc(u))
    yield {"c": c, "h": heads["a"], "hb": heads["b"], "hl": {"Authorization": f"Bearer {create_token(u.id)}"}, "ia": ia}
    mp.undo()


def _crear(env, preguntas, name="Solo cerradas", **extra):
    return env["c"].post("/api/projects", headers=env["h"], data={"name": name, "preguntas": json.dumps(preguntas), **extra},
                         files={"file": ("e.csv", io.BytesIO(DF.to_csv(index=False).encode()), "text/csv")})


@pytest.fixture(scope="module")
def pid(env):
    r = _crear(env, SOLO_CERRADAS)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_crear_sin_abiertas_responde_la_forma_del_contrato_y_audita(env):
    r = _crear(env, SOLO_CERRADAS)
    assert r.status_code == 200 and set(r.json()) == {"id", "n_responses", "text_column", "preguntas_abiertas"}
    assert (r.json()["n_responses"], r.json()["text_column"], r.json()["preguntas_abiertas"]) == (N, "", [])
    ev = [e for e in env["c"].get(f"/api/projects/{r.json()['id']}/audit", headers=env["h"]).json()
          if e["action"] == "creacion_proyecto"][0]["detail"]
    assert ev["n_respuestas"] == N and ev["columna_texto"] is None
    assert get_db().projects.find_one({"_id": r.json()["id"]})["analisis"] == {}


def test_con_plantilla_guarda_el_marco_pero_no_agrega_categorias(env):
    r = _crear(env, SOLO_CERRADAS, template="evaluacion_docente_cna")
    assert r.status_code == 200, r.text
    g = env["c"].get(f"/api/projects/{r.json()['id']}", headers=env["h"]).json()
    assert g["marco_teorico"] and g["categories"] == []
    acciones = [e["action"] for e in env["c"].get(f"/api/projects/{r.json()['id']}/audit", headers=env["h"]).json()]
    assert "aplicacion_plantilla" not in acciones


def test_sin_abiertas_ni_cerradas_es_400_y_no_guarda(env):
    antes = get_db().projects.count_documents({})
    r = _crear(env, [{"titulo": "Id", "columnas": ["Sede"], "tipo": "identificador"}, FECHA])
    assert r.status_code == 400 and r.json()["detail"] == MENSAJE
    assert get_db().projects.count_documents({}) == antes


def test_get_proyecto_sin_abiertas(env, pid):
    g = env["c"].get(f"/api/projects/{pid}", headers=env["h"])
    assert g.status_code == 200
    g = g.json()
    assert (g["pregunta"], g["text_column"], g["categories"], g["n_responses"]) == (None, "", [], N)
    assert (g["has_lexical"], g["n_coded"], g["has_report"], g["n_audit_events"]) == (False, 0, False, 1)
    assert [p["titulo"] for p in g["preguntas"]] == ["Satisfacción", "Sede", "Fecha"] and g["columns"]
    assert env["c"].get(f"/api/projects/{pid}?pregunta=q_1", headers=env["h"]).status_code == 404


def test_listado_n_abiertas_y_n_responses(env, pid):
    cero = pid
    una = _crear(env, [ESCALA, ABIERTA], name="Una").json()["id"]
    dos = _crear(env, [ESCALA, ABIERTA, {**ABIERTA, "titulo": "Otro", "columnas": ["Sede"]}], name="Dos").json()["id"]
    por_id = {p["id"]: p for p in env["c"].get("/api/projects", headers=env["h"]).json()}
    assert [por_id[i]["n_abiertas"] for i in (cero, una, dos)] == [0, 1, 2]
    p0 = por_id[cero]
    assert (p0["n_responses"], p0["has_lexical"], p0["n_categories"], p0["n_coded"], p0["has_report"]) == (N, False, 0, 0, False)
    assert por_id[una]["n_responses"] == 4  # personas con texto, como hoy


def test_operaciones_de_analisis_dan_404_sin_llamar_a_la_ia(env, pid):
    c, h, base = env["c"], env["h"], f"/api/projects/{pid}"
    ops = [("POST", "/lexical"), ("GET", "/lexical"), ("POST", "/categories/propose"), ("POST", "/categories"),
           ("POST", "/codify"), ("GET", "/codify/progress"), ("GET", "/summary"), ("GET", "/responses"),
           ("POST", "/report"), ("GET", "/report"), ("GET", "/export/pdf"), ("GET", "/export/csv"),
           ("GET", "/export/xlsx"), ("POST", "/apply-template?template=evaluacion_docente_cna")]
    for met, ruta in ops:
        for sufijo in ("", ("&" if "?" in ruta else "?") + "pregunta=q_1"):
            r = c.request(met, base + ruta + sufijo, headers=h, json={"nombre": "X"} if ruta == "/categories" else None)
            assert r.status_code == 404 and r.json()["detail"] == "Pregunta no encontrada", (met, ruta, sufijo, r.text)
    assert env["ia"] == []


def test_closed_results_lector_y_otra_organizacion(env, pid):
    c, base = env["c"], f"/api/projects/{pid}/closed-results"
    assert c.get(base, headers=env["h"]).json()["n_personas"] == N
    por = c.get(base + "?por=q_2", headers=env["h"])
    assert por.status_code == 200 and por.json()["grupos"]
    assert c.get(base, headers=env["hl"]).status_code == 200
    assert c.get(f"/api/projects/{pid}", headers=env["hl"]).status_code == 200
    assert c.get(base, headers=env["hb"]).status_code == 404
    assert c.get(f"/api/projects/{pid}", headers=env["hb"]).status_code == 404


def test_google_forms_y_qualtrics_heredan_el_cambio(env, monkeypatch):
    monkeypatch.setattr(google_forms, "fetch_responses", lambda cfg: DF.copy())
    r = env["c"].post("/api/projects/from-google-forms", headers=env["h"],
                      json={"name": "GF", "sheet_url": "https://docs.google.com/spreadsheets/d/X/edit", "preguntas": SOLO_CERRADAS})
    assert r.status_code == 200 and r.json()["n_responses"] == N and r.json()["preguntas_abiertas"] == []

    monkeypatch.setattr(qualtrics, "fetch_responses", lambda cfg: DF.copy())
    monkeypatch.setattr("app.routers.integrations._qualtrics_config", lambda user: {"api_token": "t", "datacenter": "d"})
    r = env["c"].post("/api/projects/from-qualtrics", headers=env["h"],
                      json={"name": "QX", "survey_id": "SV_1", "preguntas": SOLO_CERRADAS})
    assert r.status_code == 200 and r.json()["n_responses"] == N and r.json()["text_column"] == ""
    ev = [e for e in env["c"].get(f"/api/projects/{r.json()['id']}/audit", headers=env["h"]).json()
          if e["action"] == "creacion_proyecto"][0]["detail"]
    assert ev["n_respuestas"] == N and ev["columna_texto"] is None
