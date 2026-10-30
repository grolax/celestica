"""RF-22 / RF-25 (T-010): detección determinística de tipos de pregunta y vista previa.

Sin IA ni internet: `requests` de las integraciones se simula como en test_fase5.py.
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
import zipfile
from pathlib import Path

import mongomock
import numpy as np
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
from app.services.question_types import detectar  # noqa: E402

DEMO = Path(__file__).resolve().parents[2] / "data" / "dataset_demo_evaluacion_docente.csv"
N = 40
ABIERTAS = [f"El profesor explica muy bien el tema número {i} de la clase" for i in range(N)]


def tipo(columna: str, valores, **otras) -> dict:
    """Detecta una columna dentro de una encuesta que además tiene una abierta (sin advertencias de más)."""
    df = pd.DataFrame({columna: valores, "comentario": ABIERTAS[:len(valores)], **otras})
    return next(p for p in detectar(df)["preguntas"] if p["columna"] == columna)


# ---------- unitarias: los 12 tipos ----------

def test_sin_datos():
    assert tipo("p1", [None] * N)["tipo"] == "sin_datos"


def test_constante():
    p = tipo("pregunta", ["¿Cómo estuvo el curso?"] * N)
    assert p["tipo"] == "constante" and p["valores_distintos"] == 1 and p["ejemplos"] == ["¿Cómo estuvo el curso?"]


@pytest.mark.parametrize("titulo,valores", [
    ("id_respuesta", [f"R{i:04d}" for i in range(N)]),
    ("Correo electrónico", ["a@x.cl", "b@x.cl"] * (N // 2)),  # el título manda aunque se repita
    ("ResponseId", ["R_1", "R_2"] * (N // 2)),
    ("codigo", [f"X{i:05d}" for i in range(N)]),  # solo por valores
    ("numero", list(range(1000, 1000 + N))),
])
def test_identificador(titulo, valores):
    assert tipo(titulo, valores)["tipo"] == "identificador"


def test_fecha():
    p = tipo("Marca temporal", [f"2026-07-{1 + i % 28:02d}" for i in range(N)])
    assert p["tipo"] == "fecha"
    assert tipo("fecha", [f"{1 + i % 28:02d}/07/2026" for i in range(N)])["tipo"] == "fecha"


def test_nps_con_palabra_clave_y_sin_ella():
    valores = [i % 11 for i in range(N)]
    p = tipo("P5_recomendaria", valores)
    assert p["tipo"] == "nps" and p["escala"] == {"min": 0, "max": 10}
    p = tipo("P5", valores)  # sin palabra clave: no es NPS
    assert p["tipo"] == "escala" and p["escala"] == {"min": 0, "max": 10}


def test_si_no_con_mayusculas_y_tildes():
    p = tipo("¿Volvería?", ["Sí", "NO", "si", "No", "SÍ", "no"] * 6)
    assert p["tipo"] == "si_no" and {o["valor"] for o in p["opciones"]} == {"Sí", "NO", "si", "No", "SÍ", "no"}
    assert tipo("flag", ["1", "0"] * (N // 2))["tipo"] == "si_no"
    assert tipo("ok", ["yes", "no", "TRUE"] * 10)["tipo"] != "si_no"  # tres respuestas distintas: no es un par


def test_escala_y_ambiguos():
    p = tipo("satisfaccion", [1 + i % 5 for i in range(N)])
    assert p["tipo"] == "escala" and p["escala"] == {"min": 1, "max": 5}
    assert tipo("p2", [1 + i % 7 for i in range(N)])["escala"] == {"min": 1, "max": 7}
    # mismos números 1-5, pero el título dice año cursado: es un grupo, no una escala
    assert tipo("anio_cursado", [1 + i % 5 for i in range(N)])["tipo"] == "segmento"
    # una pregunta larga que menciona "el curso" sigue siendo escala
    assert tipo("¿Cómo evalúa el curso en general?", [1 + i % 5 for i in range(N)])["tipo"] == "escala"


def test_numerica():
    assert tipo("monto", [round(1000 + i * 3.7, 1) for i in range(N)])["tipo"] == "numerica"
    assert tipo("edad", [18 + i % 30 for i in range(N)])["tipo"] == "numerica"  # edad con muchos valores distintos
    assert tipo("pct", [f"{i % 90},5" for i in range(N)])["tipo"] == "numerica"  # coma decimal


def test_seleccion_multiple():
    p = tipo("canales", ["Web;App", "Web", "App;Tienda", "Tienda;Web;App"] * 10)
    assert p["tipo"] == "seleccion_multiple"
    assert {o["valor"]: o["n"] for o in p["opciones"]} == {"Web": 30, "App": 30, "Tienda": 20}
    assert tipo("canales", ["Web, App", "Web", "App, Tienda", "Tienda"] * 10)["tipo"] == "seleccion_multiple"


def test_segmento_y_seleccion_unica():
    p = tipo("sede", ["Norte", "Sur", "Centro", "Norte"] * 10)
    assert p["tipo"] == "segmento" and p["opciones"][0] == {"valor": "Norte", "n": 20}
    p = tipo("canal_preferido", ["Web", "App", "Tienda", "Web"] * 10)
    assert p["tipo"] == "seleccion_unica" and p["valores_distintos"] == 3
    # un título largo que contiene una palabra de grupo no basta
    assert tipo("¿Cómo evalúa la sede?", ["Bueno", "Malo", "Regular", "Bueno"] * 10)["tipo"] == "seleccion_unica"


def test_abierta_y_corta_con_pocas_filas():
    df = pd.DataFrame({"c": [f"respuesta {i}" for i in range(6)]})
    assert detectar(df)["preguntas"][0]["tipo"] == "abierta"  # todas distintas: no son opciones
    p = tipo("c2", ["Muy buena", "Mala", "Muy buena", "Regular"] * 10)
    assert p["tipo"] == "seleccion_unica"


def test_forma_y_recorte_de_ejemplos():
    largo = "palabra " * 40
    df = pd.DataFrame({"t": [largo + str(i) for i in range(20)]})
    p = detectar(df)["preguntas"][0]
    assert set(p) == {"columna", "tipo", "motivo", "n_respuestas", "n_vacias", "valores_distintos", "ejemplos"}
    assert len(p["ejemplos"]) == 3 and all(len(e) == 121 and e.endswith("…") for e in p["ejemplos"])
    assert set(detectar(df)) == {"n_filas", "preguntas", "advertencias"}


def test_excel_floats_enteros_y_titulos_repetidos():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0, np.nan] * 10, "b": ABIERTAS})
    df.columns = ["x", "x"]  # mismo título dos veces
    ps = detectar(df)["preguntas"]
    assert [p["tipo"] for p in ps] == ["escala", "abierta"]
    assert ps[0]["ejemplos"] == ["1", "2", "3"] and ps[0]["n_vacias"] == 10


# ---------- dataset demo ----------

def test_dataset_demo():
    r = detectar(pd.read_csv(DEMO))
    tipos = {p["columna"]: p["tipo"] for p in r["preguntas"]}
    assert tipos == {"id_respuesta": "identificador", "carrera": "segmento", "asignatura": "segmento",
                     "anio_cursado": "segmento", "genero": "segmento", "pregunta": "constante", "respuesta": "abierta"}
    assert r["n_filas"] == 320 and r["advertencias"] == []


# ---------- advertencias ----------

def test_advertencias():
    sin_abiertas = detectar(pd.DataFrame({"sede": ["N", "S"] * 20, "nota": [1, 2, 3, 4] * 10}))
    assert sin_abiertas["advertencias"] == ["Esta encuesta no tiene preguntas abiertas. El análisis de preguntas cerradas llegará pronto."]
    pocas = detectar(pd.DataFrame({"c": [f"un comentario largo número {i}" for i in range(5)]}))
    assert pocas["advertencias"] == ["La encuesta tiene muy pocas respuestas (5); los resultados serán poco representativos."]
    vacia = detectar(pd.DataFrame({"c": ABIERTAS, "opcional": [None] * 30 + ["x"] * 10}))
    assert vacia["advertencias"] == ["La columna «opcional» tiene más de la mitad de sus respuestas vacías."]


# ---------- rendimiento (RNF-10) ----------

def test_rendimiento_10000_filas_por_30_columnas():
    rng = np.random.default_rng(1)
    n = 10_000
    gen = [lambda: [f"respuesta {j} del curso, " + "texto " * 5 + str(rng.integers(10**6)) for j in range(n)],
           lambda: rng.integers(1, 6, n), lambda: rng.choice(["N", "S", "C"], n), lambda: [f"U{j:06d}" for j in range(n)],
           lambda: pd.date_range("2024-01-01", periods=n, freq="h").astype(str), lambda: rng.choice(["a;b", "b;c", "a"], n)]
    df = pd.DataFrame({f"c{i}": gen[i % 6]() for i in range(30)})
    t = time.perf_counter()
    r = detectar(df)
    assert time.perf_counter() - t < 2 and len(r["preguntas"]) == 30


# ---------- endpoints ----------

@pytest.fixture(scope="module")
def env():
    mp = pytest.MonkeyPatch()
    mp.setattr(thematic, "client", lambda: (_ for _ in ()).throw(AssertionError("llamada a la API real de Anthropic")))
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/auth/signup", json={"email": "tipos@x.cl", "password": "clave12345"})
    admin = {"Authorization": f"Bearer {r.json()['token']}"}
    org = r.json()["user"]["organizacion"]["id"]
    lector = User(id="usr_tipos_lector", email="tipos-lector@x.cl", password_hash=hash_password("clave12345"), nombre="L",
                  empresa="", created_at=store.now_iso(), org_id=org, rol="lector")
    get_db().users.insert_one(user_to_doc(lector))
    yield {"c": c, "h": admin, "hl": {"Authorization": f"Bearer {create_token(lector.id)}"}}
    mp.undo()


def _conteos():
    db = get_db()
    return db.projects.count_documents({}), db.audit_events.count_documents({})


def _csv(texto, nombre="e.csv"):
    return {"file": (nombre, io.BytesIO(texto.encode()), "text/csv")}


def test_endpoint_archivo_forma_y_sin_efectos(env):
    antes = _conteos()
    r = env["c"].post("/api/projects/preview", headers=env["h"], files={"file": ("demo.csv", DEMO.read_bytes(), "text/csv")})
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"n_filas", "preguntas", "advertencias"} and body["n_filas"] == 320
    assert {p["columna"]: p["tipo"] for p in body["preguntas"]}["respuesta"] == "abierta"
    assert _conteos() == antes


def test_endpoint_archivo_xlsx(env):
    buf = io.BytesIO()
    pd.DataFrame({"p": [1, 2, 3, 4] * 3, "c": [f"comentario largo número {i}" for i in range(12)]}).to_excel(buf, index=False)
    r = env["c"].post("/api/projects/preview", headers=env["h"], files={"file": ("e.xlsx", buf.getvalue(), "application/vnd.ms-excel")})
    assert r.status_code == 200 and [p["tipo"] for p in r.json()["preguntas"]] == ["escala", "abierta"]


def test_endpoint_archivo_ilegible_vacio_grande_y_lector(env):
    c, h = env["c"], env["h"]
    antes = _conteos()
    r = c.post("/api/projects/preview", headers=h, files={"file": ("x.xlsx", b"esto no es un excel", "application/octet-stream")})
    assert r.status_code == 400 and r.json()["detail"].startswith("No se pudo leer el archivo")
    r = c.post("/api/projects/preview", headers=h, files=_csv("a,b\n"))
    assert r.status_code == 400 and r.json()["detail"] == "Los datos no contienen filas"
    r = c.post("/api/projects/preview", headers=h, files=_csv("a\n" + "x" * (20 * 1024 * 1024)))
    assert r.status_code == 413 and r.json()["detail"] == "El archivo supera el máximo de 20 MB."
    r = c.post("/api/projects/preview", headers=env["hl"], files=_csv("a,b\n1,2\n"))
    assert r.status_code == 403 and r.json()["detail"] == "Tu rol (Lector) no permite esta acción."
    assert c.post("/api/projects/preview", files=_csv("a,b\n1,2\n")).status_code == 401
    assert _conteos() == antes


# ---- Qualtrics y Google Forms con requests simulado ----

class Resp:
    def __init__(self, status=200, jdata=None, content=b"", ctype="application/json"):
        self.status_code, self._j, self.content = status, jdata, content
        self.headers = {"Content-Type": ctype}
        self.text = json.dumps(jdata) if jdata else ""
        self.ok = 200 <= status < 300

    def json(self):
        return self._j


QUALTRICS_CSV = ("QID1,QID2\nComentario,Edad\n"
                 '{"ImportId":"QID1"},{"ImportId":"QID2"}\n'
                 "El servicio fue excelente y rapido,34\nMuy lenta la atencion en la sucursal,51\nTodo bien pero el precio es alto,28\n")


def _zip(texto):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("export.csv", texto)
    return buf.getvalue()


def fake_get(url, headers=None, timeout=None, allow_redirects=True):
    if "qualtrics.com" in url:
        if (headers or {}).get("X-API-TOKEN") != "TOK123":
            return Resp(401)
        if "/export-responses/PROG" in url:
            return Resp(jdata={"result": {"status": "complete", "fileId": "FILE1"}})
        if "/FILE1/file" in url:
            return Resp(content=_zip(QUALTRICS_CSV))
    if "docs.google.com" in url:
        if "PRIVADA" in url:
            return Resp(content=b"<html>login</html>", ctype="text/html")
        return Resp(content=b"Marca temporal,Que opinas del taller?\n2026-07-01,Fue muy util y bien organizado el taller completo\n"
                            b"2026-07-02,Falto tiempo para la parte practica del taller\n", ctype="text/csv")
    return Resp(404)


def fake_post(url, headers=None, json=None, timeout=None):
    if "qualtrics.com" in url and url.endswith("/export-responses"):
        return Resp(jdata={"result": {"progressId": "PROG"}}) if (headers or {}).get("X-API-TOKEN") == "TOK123" else Resp(401)
    return Resp(404)


@pytest.fixture
def sin_internet(monkeypatch):
    monkeypatch.setattr(qualtrics.requests, "get", fake_get)
    monkeypatch.setattr(qualtrics.requests, "post", fake_post)
    monkeypatch.setattr(google_forms.requests, "get", fake_get)


def test_preview_qualtrics(env, sin_internet):
    c, h = env["c"], env["h"]
    antes = _conteos()
    r = c.post("/api/projects/preview/qualtrics", headers=h, json={"survey_id": "SV_1"})
    assert r.status_code == 400 and "credenciales" in r.json()["detail"]  # sin credenciales guardadas
    c.put("/api/integrations/qualtrics/credentials", headers=h, json={"api_token": "TOK123", "datacenter": "ca1"})
    r = c.post("/api/projects/preview/qualtrics", headers=h, json={"survey_id": "SV_1"})
    assert r.status_code == 200, r.text
    assert r.json()["n_filas"] == 3 and {p["columna"]: p["tipo"] for p in r.json()["preguntas"]}["Comentario"] == "abierta"
    c.put("/api/integrations/qualtrics/credentials", headers=h, json={"api_token": "MALO", "datacenter": "ca1"})
    assert c.post("/api/projects/preview/qualtrics", headers=h, json={"survey_id": "SV_1"}).status_code == 400
    assert c.post("/api/projects/preview/qualtrics", headers=env["hl"], json={"survey_id": "SV_1"}).status_code == 403
    assert _conteos() == antes


def test_preview_google_forms(env, sin_internet):
    c, h = env["c"], env["h"]
    antes = _conteos()
    r = c.post("/api/projects/preview/google-forms", headers=h, json={"sheet_url": "https://docs.google.com/spreadsheets/d/ABC/edit"})
    assert r.status_code == 200, r.text
    tipos = {p["columna"]: p["tipo"] for p in r.json()["preguntas"]}
    assert tipos == {"Marca temporal": "fecha", "Que opinas del taller?": "abierta"}
    assert r.json()["advertencias"] == ["La encuesta tiene muy pocas respuestas (2); los resultados serán poco representativos."]
    r = c.post("/api/projects/preview/google-forms", headers=h, json={"sheet_url": "https://docs.google.com/spreadsheets/d/PRIVADA/edit"})
    assert r.status_code == 400
    assert c.post("/api/projects/preview/google-forms", headers=env["hl"], json={"sheet_url": "https://x"}).status_code == 403
    assert _conteos() == antes
