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
from collections import Counter
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


# ---------- revisión 2: patrones de una encuesta real de Google Forms (datos sintéticos, 500 filas) ----------

N500 = 500
OPCIONES_LARGAS = ["Comprar una vivienda propia", "Viajar por distintos países", "Emprender un negocio propio",
                   "Estudiar un postgrado en el extranjero", "Ahorrar para la jubilación", "Cambiarme de ciudad",
                   "Dedicar más tiempo a mi familia", "Aprender un nuevo oficio"]


def tipo500(columna, valores):
    """Una columna de 500 filas; los valores que faltan hasta 500 quedan vacíos (como en una pregunta opcional)."""
    return detectar(pd.DataFrame({columna: list(valores) + [None] * (N500 - len(valores))}))["preguntas"][0]


def test_rev2_seleccion_multiple_con_opciones_largas():
    rng = np.random.default_rng(7)
    combos = [", ".join(rng.choice(OPCIONES_LARGAS, rng.integers(1, 4), replace=False)) for _ in range(N500)]
    assert len(set(combos)) > 30  # muchas combinaciones distintas, pero pocas partes
    for titulo in ("Puedes seleccionar más de una opción", "Selecciona hasta 3 metas", "Metas para los próximos años"):
        p = tipo500(titulo, combos)
        assert p["tipo"] == "seleccion_multiple", titulo
        assert {o["valor"] for o in p["opciones"]} <= set(OPCIONES_LARGAS)
    # con ";" como separador también
    assert tipo500("metas", [c.replace(", ", ";") for c in combos])["tipo"] == "seleccion_multiple"
    # la pista de título deja pasar una columna donde casi nadie marca más de una opción
    pocas = [c if i % 10 == 0 else c.split(", ")[0] for i, c in enumerate(combos)]
    assert tipo500("Selecciona tus metas", pocas)["tipo"] == "seleccion_multiple"
    assert tipo500("Metas", pocas)["tipo"] == "seleccion_unica"


def test_rev2_texto_libre_con_comas_sigue_abierta():
    libres = [f"Me gustó la clase número {i}, aunque el horario {i % 97} fue complicado, y el material {i * 3} llegó tarde" for i in range(N500)]
    assert tipo500("¿Qué comentarios tienes?", libres)["tipo"] == "abierta"
    assert tipo500("Selecciona tu comentario", libres)["tipo"] == "abierta"  # la pista sola no alcanza


def test_rev2_seleccion_unica_con_muchas_filas_y_opciones_largas():
    opciones = [f"Opción número {i} que describe una situación de vivienda distinta" for i in range(21)]
    valores = [opciones[i % 21] for i in range(N500)]
    p = tipo500("¿Cuál describe mejor tu situación de vivienda actual?", valores)
    assert p["tipo"] == "seleccion_unica" and p["valores_distintos"] == 21
    # con pocas respuestas (menos de 30) esa regla no aplica: 21 de 25 distintos no son opciones
    assert tipo500("situacion", valores[:25])["tipo"] == "abierta"


@pytest.mark.parametrize("titulo,valores", [
    ("1. ¿Cuál es tu edad?", ["18 a 24 años", "25 a 34 años", "35 a 44 años", "45 a 54 años", "55 años o más"]),
    ("2. ¿Con qué género te identificas?", ["Femenino", "Masculino", "Otro", "Prefiero no decirlo"]),
    ("3. ¿En qué región de Chile vives actualmente?", [f"Región {i}" for i in range(16)]),
    ("¿En qué comuna vives actualmente?", [f"Comuna {i}" for i in range(45)]),
    ("4. ¿Cuál es tu nivel educacional alcanzado?", ["Básica", "Media", "Técnica", "Universitaria", "Postgrado"]),
    ("Educación", ["Básica", "Media", "Técnica"]),
])
def test_rev2_pista_de_grupo_con_titulos_largos(titulo, valores):
    assert tipo500(titulo, [valores[i % len(valores)] for i in range(N500)])["tipo"] == "segmento"


def test_rev2_titulo_largo_numerico_o_evaluativo_no_es_grupo():
    assert tipo("¿Cómo evalúa el curso?", [1 + i % 5 for i in range(N)])["tipo"] == "escala"
    assert tipo("¿Cómo evalúa la sede?", ["Bueno", "Malo", "Regular", "Bueno"] * 10)["tipo"] == "seleccion_unica"


def test_rev2_columnas_con_muy_pocas_respuestas():
    # constante solo si (casi) todas las filas tienen el valor
    assert tipo500("pregunta", ["Sí, acepto"] * N500)["tipo"] == "constante"
    assert tipo500("pregunta", ["Sí, acepto"] * 460)["tipo"] == "constante"  # 92 % de las filas
    for k in (1, 2, 6):
        p = tipo500("Otro (especifica)", ["Ninguna de las anteriores"] * k)
        assert p["tipo"] == "seleccion_unica" and p["n_respuestas"] == k and p["n_vacias"] == N500 - k
        assert "mismo valor en todas" not in p["motivo"]
    assert tipo500("nota", [4, 4])["tipo"] != "constante"
    # 5 a 7 respuestas de 2 palabras: no son texto libre
    for k in (5, 6, 7):
        p = tipo500("Otro", [f"Mi {w}" for w in ("vecino", "hermano", "amigo", "primo", "tío", "socio", "jefe")[:k]])
        assert p["tipo"] == "seleccion_unica" and "palabras" not in p["motivo"]
    p = tipo500("Otra opción", ["Mi vecino", "Mi vecino", "Mi primo", "Mi vecino", "Mi primo"])
    assert p["tipo"] == "seleccion_unica"
    # con pista de grupo: segmento
    assert tipo500("¿En qué comuna vives?", ["Ñuñoa", "Maipú", "Ñuñoa", "Puente Alto", "Ñuñoa"])["tipo"] == "segmento"


def test_rev2_abierta_exige_tres_palabras_y_el_motivo_es_coherente():
    p = tipo500("comentario", [f"Me gustó mucho la clase número {i} de hoy" for i in range(200)])
    assert p["tipo"] == "abierta" and "9 palabras" in p["motivo"] and "200 respuestas distintas de 200" in p["motivo"]
    # todas distintas pero de 2 palabras, en una columna llena: sigue siendo abierta y el motivo no dice "largos"
    p = detectar(pd.DataFrame({"c": [f"respuesta {i}" for i in range(30)]}))["preguntas"][0]
    assert p["tipo"] == "abierta" and "2 palabras" in p["motivo"] and "largos" not in p["motivo"]


# ---------- revisión 4: opciones con comas internas, selección única con comas, redacción del motivo ----------

def _filas(opciones, marcas, n=N500):
    """Respuestas tipo Google Forms: las opciones marcadas unidas con ', '. `marcas` es una lista de tuplas de índices."""
    return [", ".join(opciones[i] for i in marcas[k % len(marcas)]) for k in range(n)]


def test_rev4_opciones_con_coma_interna_se_reconstruyen():
    ops = ["Invertir en depósitos a plazo, fondos mutuos, acciones u otros instrumentos",
           "Subsidios habitacionales (DS1, DS19, DS49)", "Transparencia en los precios, condiciones de compra y financiamiento",
           "Ahorrar", "Viajar"]
    marcas = [(0,), (1,), (2,), (3,), (4,), (0, 3), (1, 4), (2, 3, 4), (0, 1), (3, 4), (1, 2, 0)]
    p = tipo500("Selecciona tus metas", _filas(ops, marcas))
    assert p["tipo"] == "seleccion_multiple"
    # antes: 8 trozos falsos ("Invertir en depósitos a plazo", "fondos mutuos", "…(DS1", "DS19", "DS49)", …)
    assert {o["valor"] for o in p["opciones"]} == set(ops)
    esperado = Counter(ops[i] for k in range(N500) for i in marcas[k % len(marcas)])
    assert {o["valor"]: o["n"] for o in p["opciones"]} == dict(esperado)


def test_rev4_parentesis_sin_cerrar_no_se_corta_aunque_sea_ambiguo():
    # "(DS1" a veces aparece sin los demás trozos: no hay par fijo, pero el paréntesis manda
    ops = ["Subsidios (DS1, DS19)", "Ahorro", "Crédito"]
    marcas = [(0,), (1,), (2,), (0, 1), (1, 2)]
    p = tipo500("Selecciona tus metas", _filas(ops, marcas))
    assert p["tipo"] == "seleccion_multiple" and {o["valor"] for o in p["opciones"]} == set(ops)


def test_rev4_mezcla_ambigua_queda_separada():
    # "fondos mutuos" aparece a veces sin "Invertir en depósitos": no se puede saber, se dejan separadas
    ops = ["Invertir en depósitos", "fondos mutuos", "Ahorrar", "Viajar"]
    marcas = [(0, 1), (1,), (2,), (3,), (0, 1, 2), (2, 3)]
    p = tipo500("Selecciona tus metas", _filas(ops, marcas))
    assert p["tipo"] == "seleccion_multiple" and {o["valor"] for o in p["opciones"]} == set(ops)


def test_rev4_seleccion_unica_con_comas_dentro_de_las_alternativas():
    alt = [f"Me interesa comprar, pero todavía no he buscado ({i})" if i % 2 else f"No me interesa, tengo otros planes ({i})"
           for i in range(21)]
    # cada alternativa completa trae una coma y se repite: 21 valores en 500 filas
    p = tipo500("¿Cuál es tu situación actual?", [alt[i % 21] for i in range(N500)])
    assert p["tipo"] == "seleccion_unica" and p["valores_distintos"] == 21
    assert {o["valor"] for o in p["opciones"]} <= set(alt)
    # trozos compartidos (ambiguos tras reconstruir) pero sin ningún trozo suelto: sigue siendo única
    comp = ["Me interesa comprar, pero ya busqué", "Me interesa comprar, pero aún no busco", "No me interesa, por ahora"]
    p = tipo500("¿Cuál es tu situación actual?", [comp[i % 3] for i in range(N500)])
    assert p["tipo"] == "seleccion_unica" and {o["valor"] for o in p["opciones"]} == set(comp)
    # con pista de grupo: segmento
    reg = ["Valparaíso, V Región", "Santiago, RM", "Concepción, VIII Región"]
    assert tipo500("¿En qué región vives?", [reg[i % 3] for i in range(N500)])["tipo"] == "segmento"


def test_rev4_no_rompe_la_multiple_real_con_pocos_valores():
    # 4 combinaciones en 40 filas (10 %), cada una se repite, pero "Web" y "App" también aparecen solas: es múltiple
    assert tipo("canales", ["Web, App", "Web", "App, Tienda", "Tienda"] * 10)["tipo"] == "seleccion_multiple"


def test_rev4_motivo_con_concordancia_y_ortografia():
    p = tipo500("Opcional", ["Sí"] * 1)
    assert "1 valor distinto en 1 respuesta" in p["motivo"]
    p = tipo500("¿En qué región vives?", ["Valparaíso", "Maule"] * 5)
    assert "(región)" in p["motivo"] and "2 valores distintos en 10 respuestas" in p["motivo"]
    assert "(género)" in tipo500("¿Con qué género te identificas?", ["F", "M", "Otro"] * 10)["motivo"]
    assert "(educación)" in tipo500("Educación", ["Básica", "Media", "Técnica"] * 20)["motivo"]
    assert "(área)" in tipo500("¿En qué área trabajas?", ["Ventas", "TI", "Finanzas"] * 20)["motivo"]


# ---------- revisión 5: continuación en minúscula ----------

def test_rev5_trozo_final_compartido_por_varias_alternativas_es_seleccion_unica():
    alt = ["Me interesa comprar para vivir, pero todavía no he buscado.",
           "Me interesa comprar como inversión, pero todavía no he buscado.",
           "No me interesa comprar."]
    # el final "pero todavía no he buscado." sigue a dos prefijos distintos: la regla de pares no lo une
    p = tipo500("¿Cuál es tu situación actual?", [alt[i % 3] for i in range(N500)])
    assert p["tipo"] == "seleccion_unica" and {o["valor"] for o in p["opciones"]} == set(alt)


def test_rev5_trozo_en_minuscula_que_tambien_aparece_solo_se_mantiene_separado():
    ops = ["Comprar para vivir", "Comprar como inversión", "pero todavía no he buscado."]
    marcas = [(0,), (1,), (2,), (0, 2), (1, 2), (0, 1)]
    p = tipo500("Selecciona tus metas", _filas(ops, marcas))
    assert p["tipo"] == "seleccion_multiple" and {o["valor"] for o in p["opciones"]} == set(ops)


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
