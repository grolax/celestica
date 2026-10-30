"""RF-30 (T-020): resultados de preguntas cerradas, calculados sin IA. Números verificables a mano."""
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

from app.main import app  # noqa: E402
from app.services.quantitative import calcular  # noqa: E402


def _calc(tipo, valores, titulo="P"):
    """Una pregunta con una respuesta por persona (None = N/A); devuelve su resultado."""
    resp = [{"id": f"R{i}", "valores": {"q_1": v}} for i, v in enumerate(valores)]
    r = calcular([{"id": "q_1", "titulo": titulo, "tipo": tipo}], resp)
    assert r["n_personas"] == len(valores)
    return r["preguntas"][0]


def test_escala_con_un_valor_sin_elegir_promedio_desviacion_y_top2_bottom2():
    q = _calc("escala", ["1", "1", "2", "4", "5", "5", "5", None, "x"])
    assert q["n_respuestas"] == 8 and q["n_na"] == 1 and q["tasa_respuesta"] == 88.9
    assert q["n_invalidas"] == 1  # "x" no es número: no entra en los cálculos
    assert [(o["valor"], o["n"]) for o in q["opciones"]] == [("1", 2), ("2", 1), ("3", 0), ("4", 1), ("5", 3)]
    assert q["opciones"][0]["pct"] == 28.6  # 2 de 7 válidas
    e = q["escala"]
    # media 23/7 = 3,2857; suma de cuadrados 21,4286 / 6 = 3,5714; raíz = 1,89
    assert (e["min"], e["max"], e["promedio"], e["desviacion"]) == (1, 5, 3.29, 1.89)
    assert e["top2"] == {"valores": [4, 5], "n": 4, "pct": 57.1}
    assert e["bottom2"] == {"valores": [1, 2], "n": 3, "pct": 42.9}


def test_escala_con_una_sola_respuesta_tiene_desviacion_cero_y_sin_invalidas_no_trae_el_campo():
    q = _calc("escala", ["3"])
    assert q["escala"]["desviacion"] == 0.0 and "n_invalidas" not in q


def test_nps_tres_grupos_y_valor():
    # 0..10: 4 promotores (9,9,10,10), 3 pasivos (7,8,8), 3 detractores (0,5,6)
    q = _calc("nps", ["9", "9", "10", "10", "7", "8", "8", "0", "5", "6"])
    assert len(q["opciones"]) == 11 and q["opciones"][1]["n"] == 0  # 1 no lo eligió nadie y aparece
    assert q["nps"] == {"valor": 10.0, "promotores": {"n": 4, "pct": 40.0}, "pasivos": {"n": 3, "pct": 30.0},
                        "detractores": {"n": 3, "pct": 30.0}}
    assert (q["escala"]["min"], q["escala"]["max"], q["escala"]["promedio"]) == (0, 10, 7.2)
    assert "top2" not in q["escala"]
    assert _calc("nps", ["11", "5"])["n_invalidas"] == 1  # fuera de 0-10


def test_seleccion_multiple_separa_opciones_con_coma_y_el_porcentaje_es_de_personas():
    a, b = "Subsidios (DS1, DS19)", "Ahorro"
    q = _calc("seleccion_multiple", [f"{a}, {b}", a, f"{b}, {a}", b, None])
    assert q["n_respuestas"] == 4 and q["n_na"] == 1
    assert [(o["valor"], o["n"], o["pct"]) for o in q["opciones"]] == [(b, 3, 75.0), (a, 3, 75.0)] or \
           [(o["valor"], o["n"], o["pct"]) for o in q["opciones"]] == [(a, 3, 75.0), (b, 3, 75.0)]
    assert sum(o["pct"] for o in q["opciones"]) == 150.0 and "100 %" in q["nota"]
    assert a in {o["valor"] for o in q["opciones"]}  # la coma de "(DS1, DS19)" no parte la opción


def test_seleccion_unica_orden_por_frecuencia_con_empate_alfabetico():
    q = _calc("seleccion_unica", ["Rojo", "Verde", "Azul", "Verde", "Rojo", "Amarillo"])
    assert [(o["valor"], o["n"]) for o in q["opciones"]] == [("Rojo", 2), ("Verde", 2), ("Amarillo", 1), ("Azul", 1)]
    assert "nota" not in q


def test_tramos_van_en_orden_natural_y_lo_sin_numero_al_final():
    vals = ["$360.001 - $700.000"] * 3 + ["Menos de $360.000"] * 2 + ["Prefiero no responder"] * 4 + ["Más de $2.000.000"]
    q = _calc("segmento", vals)
    assert [o["valor"] for o in q["opciones"]] == ["Menos de $360.000", "$360.001 - $700.000", "Más de $2.000.000",
                                                   "Prefiero no responder"]
    assert [o["valor"] for o in _calc("segmento", ["25-29", "20-24", "20-24", "30-34"])["opciones"]] == \
           ["20-24", "25-29", "30-34"]


def test_numerica_con_un_valor_no_numerico():
    q = _calc("numerica", ["10", "20", "30", "40", "abc", None])
    assert q["n_invalidas"] == 1 and "opciones" not in q
    assert q["numerica"] == {"promedio": 25.0, "desviacion": 12.91, "mediana": 25, "min": 10, "max": 40}


def test_na_fuera_de_los_porcentajes_y_las_respuestas_mas_na_suman_las_personas():
    q = _calc("si_no", ["Sí", "No", "Sí", None, None])
    assert q["n_respuestas"] + q["n_na"] == 5 and q["tasa_respuesta"] == 60.0
    assert [(o["valor"], o["pct"]) for o in q["opciones"]] == [("Sí", 66.7), ("No", 33.3)]


def test_solo_cerradas_y_en_el_orden_del_proyecto():
    pregs = [{"id": "q_1", "titulo": "a", "tipo": "abierta"}, {"id": "q_2", "titulo": "b", "tipo": "si_no"},
             {"id": "q_3", "titulo": "c", "tipo": "identificador"}, {"id": "q_4", "titulo": "d", "tipo": "escala"}]
    r = calcular(pregs, [{"id": "R1", "valores": {"q_2": "Sí", "q_4": "3"}}])
    assert [p["id"] for p in r["preguntas"]] == ["q_2", "q_4"]
    vacio = calcular(pregs, [])  # sin respondentes no divide por cero
    assert vacio["n_personas"] == 0 and [p["tasa_respuesta"] for p in vacio["preguntas"]] == [0.0, 0.0]


# ---------- endpoint ----------

@pytest.fixture(scope="module")
def env():
    c = TestClient(app, raise_server_exceptions=False)
    hs = {}
    for who in ("a", "b"):
        r = c.post("/auth/signup", json={"email": f"quant-{who}@x.cl", "password": "clave12345"})
        hs[who] = {"Authorization": f"Bearer {r.json()['token']}"}
    return c, hs


def _crear(c, h, csv, preguntas):
    r = c.post("/api/projects", headers=h, data={"name": "E", "preguntas": json.dumps(preguntas)},
               files={"file": ("e.csv", io.BytesIO(csv.encode()), "text/csv")})
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_endpoint_resultados_otra_organizacion_404_y_proyecto_sin_cerradas_vacio(env):
    c, hs = env
    csv = "Comentario,Nota\n" + "\n".join(f"texto largo número {i},{(i % 5) + 1 if i != 4 else ''}" for i in range(10))
    pid = _crear(c, hs["a"], csv, [{"titulo": "Comentario", "columnas": ["Comentario"], "tipo": "abierta"},
                                   {"titulo": "Nota", "columnas": ["Nota"], "tipo": "escala"}])
    r = c.get(f"/api/projects/{pid}/closed-results", headers=hs["a"])
    assert r.status_code == 200
    body = r.json()
    assert body["n_personas"] == 10 and [p["id"] for p in body["preguntas"]] == ["q_2"]
    assert body["preguntas"][0]["n_na"] == 1 and body["preguntas"][0]["escala"]["max"] == 5
    ajeno = c.get(f"/api/projects/{pid}/closed-results", headers=hs["b"])
    assert ajeno.status_code == 404 and ajeno.json()["detail"] == "Proyecto no encontrado"

    solo = _crear(c, hs["a"], "Comentario\n" + "\n".join(f"texto largo número {i}" for i in range(5)),
                  [{"titulo": "Comentario", "columnas": ["Comentario"], "tipo": "abierta"}])
    assert c.get(f"/api/projects/{solo}/closed-results", headers=hs["a"]).json() == {"n_personas": 5, "preguntas": []}
