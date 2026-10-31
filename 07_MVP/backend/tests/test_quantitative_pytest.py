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


def test_escala_donde_nadie_eligio_el_minimo_igual_parte_de_1():
    q = _calc("escala", ["2", "3", "4", "5", "5"])
    assert [(o["valor"], o["n"]) for o in q["opciones"]] == [("1", 0), ("2", 1), ("3", 1), ("4", 1), ("5", 2)]
    e = q["escala"]
    assert (e["min"], e["max"]) == (1, 5)
    assert e["bottom2"] == {"valores": [1, 2], "n": 1, "pct": 20.0}  # el 3 (neutral) no cuenta como bajo
    assert _calc("escala", ["0", "3", "5"])["escala"]["min"] == 0


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


# ---------- RF-31 (T-022): cruces por grupo ----------

def _gente(filas):
    """filas: lista de dicts {pregunta: valor}; devuelve respondentes."""
    return [{"id": f"R{i}", "valores": f} for i, f in enumerate(filas)]


PREG = [{"id": "g", "titulo": "Género", "tipo": "segmento"}, {"id": "e", "titulo": "Nota", "tipo": "escala"},
        {"id": "s", "titulo": "Sí/No", "tipo": "si_no"}]


def _cruce(genero_nota_si, **kw):
    gente = _gente([{"g": g, "e": e, "s": s} for g, e, s in genero_nota_si])
    return calcular(PREG, gente, "g", **kw)


def test_grupos_en_orden_de_t020_sin_grupo_y_sumas():
    datos = [("M", "5", "Sí")] * 3 + [("H", "4", "No")] * 2 + [("O", "1", None)] + [(None, "3", "Sí")] * 2
    r = _cruce(datos)
    assert r["por"] == {"id": "g", "titulo": "Género", "tipo": "segmento"} and r["umbral_pocos_datos"] == 10
    assert [(g["valor"], g["n_personas"]) for g in r["grupos"]] == [("M", 3), ("H", 2), ("O", 1)]
    assert r["n_sin_grupo"] == 2 and sum(g["n_personas"] for g in r["grupos"]) + r["n_sin_grupo"] == r["n_personas"] == 8
    assert [p["id"] for p in r["preguntas"]] == ["e", "s"]  # la pregunta `por` no aparece
    for p in r["preguntas"]:
        assert [x["valor"] for x in p["por_grupo"]] == ["M", "H", "O"]
        for x, g in zip(p["por_grupo"], r["grupos"]):
            assert x["n_respuestas"] + x["n_na"] == g["n_personas"]


def test_grupo_con_numeros_conocidos_y_rango_y_opciones_del_total():
    # Mujer: 5,4,4 -> promedio 4,33, top2 100 %. Hombre: 1,2 -> promedio 1,5. El total usa 1..5.
    datos = [("M", "5", "Sí"), ("M", "4", "Sí"), ("M", "4", "Sí"), ("H", "1", "No"), ("H", "2", "No")]
    r = _cruce(datos)
    nota, si = r["preguntas"]
    m = nota["por_grupo"][0]
    assert m["escala"] == {"min": 1, "max": 5, "promedio": 4.33, "desviacion": 0.58,
                           "top2": {"valores": [4, 5], "n": 3, "pct": 100.0}, "bottom2": {"valores": [1, 2], "n": 0, "pct": 0.0}}
    assert [(o["valor"], o["n"]) for o in m["opciones"]] == [("1", 0), ("2", 0), ("3", 0), ("4", 2), ("5", 1)]
    h = nota["por_grupo"][1]
    assert h["escala"]["max"] == 5 and h["escala"]["promedio"] == 1.5  # el grupo no usa el 5 y aun así el rango es el del total
    assert h["escala"]["bottom2"] == {"valores": [1, 2], "n": 2, "pct": 100.0}
    # categórica: mismas opciones y orden del total, con n 0
    assert [o["valor"] for o in si["opciones"]] == ["Sí", "No"]
    assert [(o["valor"], o["n"], o["pct"]) for o in si["por_grupo"][0]["opciones"]] == [("Sí", 3, 100.0), ("No", 0, 0.0)]


def test_grupo_sin_respuestas_validas_y_pocos_datos_en_9_y_10():
    r = _cruce([("M", None, "Sí")] * 9 + [("H", "3", "Sí"), ("H", "5", "No")] * 5)
    assert [(g["valor"], g["n_personas"], g["pocos_datos"]) for g in r["grupos"]] == [("H", 10, False), ("M", 9, True)]
    m = r["preguntas"][0]["por_grupo"][1]
    assert m["n_respuestas"] == 0 and m["n_na"] == 9 and len(m["opciones"]) == 5 and "escala" not in m


def test_numerica_como_por_tramos_por_defecto_y_cortes():
    preg = [{"id": "ed", "titulo": "Edad", "tipo": "numerica"}, {"id": "s", "titulo": "S", "tipo": "si_no"}]
    edades = ["17", "18", "24", "24.5", "25", "40", "64", "65", "90", "abc", None, ""]
    gente = _gente([{"ed": e, "s": "Sí"} for e in edades])
    r = calcular(preg, gente, "ed")
    assert [(g["valor"], g["n_personas"]) for g in r["grupos"]] == [
        ("Menos de 18", 1), ("18–24", 3), ("25–34", 1), ("35–44", 1), ("45–54", 0), ("55–64", 1), ("65+", 2)]
    assert r["n_sin_grupo"] == 3  # "abc", N/A y vacío
    assert [g["valor"] for g in calcular(preg, gente[1:], "ed")["grupos"]][0] == "18–24"  # sin menores de 18 no hay "Menos de"
    r = calcular(preg, gente, "ed", "30,50")
    assert [(g["valor"], g["n_personas"]) for g in r["grupos"]] == [("Menos de 30", 5), ("30–49", 1), ("50+", 3)]


@pytest.mark.parametrize("por,cortes", [("zz", None), ("a", None), ("m", None), ("ed", "30,x"), ("ed", "50,30"), ("ed", "30,30"),
                                        ("ed", ""), ("g", "30,50"), (None, "30,50")])
def test_errores_de_por_y_cortes(por, cortes):
    preg = [{"id": "a", "titulo": "A", "tipo": "abierta"}, {"id": "m", "titulo": "M", "tipo": "seleccion_multiple"},
            {"id": "ed", "titulo": "Edad", "tipo": "numerica"}, {"id": "g", "titulo": "G", "tipo": "segmento"}]
    esperado = "Esa pregunta no se puede usar para separar en grupos." if por in ("zz", "a", "m") else \
        "Los tramos deben ser números enteros, separados por coma y de menor a mayor."
    with pytest.raises(ValueError, match=esperado):
        calcular(preg, [], por, cortes)


def test_endpoint_cruce_lector_otra_organizacion_y_errores_400(env):
    from app import store as st
    from app.auth import create_token, hash_password
    from app.database import get_db
    from app.models import User, user_to_doc
    c, hs = env
    csv = "Comentario,Género,Edad\n" + "\n".join(f"texto largo número {i},{'M' if i % 2 else 'H'},{20 + i}" for i in range(10))
    pid = _crear(c, hs["a"], csv, [{"titulo": "Comentario", "columnas": ["Comentario"], "tipo": "abierta"},
                                   {"titulo": "Género", "columnas": ["Género"], "tipo": "segmento"},
                                   {"titulo": "Edad", "columnas": ["Edad"], "tipo": "numerica"}])
    org = c.post("/auth/login", json={"email": "quant-a@x.cl", "password": "clave12345"}).json()["user"]["organizacion"]["id"]
    u = User(id="usr_lectorq", email="quant-lector@x.cl", password_hash=hash_password("clave12345"), nombre="L", empresa="",
             created_at=st.now_iso(), org_id=org, rol="lector")
    get_db().users.insert_one(user_to_doc(u))
    hl = {"Authorization": f"Bearer {create_token(u.id)}"}
    url = f"/api/projects/{pid}/closed-results"
    r = c.get(url, headers=hl, params={"por": "q_2"})
    assert r.status_code == 200 and [g["valor"] for g in r.json()["grupos"]] == ["H", "M"]
    assert [p["id"] for p in r.json()["preguntas"]] == ["q_3"]
    r = c.get(url, headers=hl, params={"por": "q_3", "cortes": "25"})
    assert [(g["valor"], g["n_personas"]) for g in r.json()["grupos"]] == [("Menos de 25", 5), ("25+", 5)]
    assert c.get(url, headers=hs["b"], params={"por": "q_2"}).status_code == 404
    assert c.get(url, headers=hs["a"]).json().keys() == {"n_personas", "preguntas"}  # sin `por`, como en T-020
    for params in ({"por": "q_1"}, {"por": "q_9"}, {"por": "q_3", "cortes": "b"}, {"cortes": "30"}):
        r = c.get(url, headers=hs["a"], params=params)
        assert r.status_code == 400 and r.json()["detail"].startswith(("Esa pregunta", "Los tramos")), params


# ---------- RF-31 (T-023): unir grupos ----------

TRAMOS = [{"id": "ed", "titulo": "Edad", "tipo": "segmento"}, {"id": "n", "titulo": "Nota", "tipo": "escala"}]


def _tramos(unir, **conteos):
    """conteos: tramo -> lista de notas; devuelve el cruce por edad con `unir` (lista Python)."""
    gente = _gente([{"ed": t, "n": n} for t, notas in conteos.items() for n in notas] + [{"ed": None, "n": "3"}])
    return calcular(TRAMOS, gente, "ed", unir=json.dumps(unir))


def test_unir_suma_personas_calcula_a_mano_deja_intactos_los_otros_y_pocos_datos_se_recalcula():
    r = _tramos([{"nombre": "20-29", "valores": ["20-24", "25-29"]}],
                **{"20-24": ["1", "2"] * 3, "25-29": ["4", "5"] * 3, "30-34": ["3"] * 12, "35-39": ["5"] * 2})
    # orden natural de T-022: 20-24, 25-29, 30-34, 35-39 -> el unido ocupa el lugar de "20-24"
    assert [(g["valor"], g["n_personas"], g["pocos_datos"], g.get("unidos")) for g in r["grupos"]] == [
        ("20-29", 12, False, ["20-24", "25-29"]), ("30-34", 12, False, None), ("35-39", 2, True, None)]
    assert "unidos" not in r["grupos"][1]
    assert sum(g["n_personas"] for g in r["grupos"]) + r["n_sin_grupo"] == r["n_personas"] == 27 and r["n_sin_grupo"] == 1
    por_grupo = r["preguntas"][0]["por_grupo"]
    assert [x["valor"] for x in por_grupo] == ["20-29", "30-34", "35-39"]
    # a mano: notas 1,2 (x3) y 4,5 (x3) -> promedio (1+2+4+5)*3/12 = 3
    assert por_grupo[0]["n_respuestas"] == 12 and por_grupo[0]["escala"]["promedio"] == 3.0
    assert [(o["valor"], o["n"]) for o in por_grupo[0]["opciones"]] == [("1", 3), ("2", 3), ("3", 0), ("4", 3), ("5", 3)]
    assert por_grupo[1]["escala"]["promedio"] == 3.0 and por_grupo[2]["escala"]["promedio"] == 5.0


def test_unir_sin_unir_igual_que_t022_y_varios_grupos_con_posicion_de_la_primera_opcion():
    datos = {"A": ["1"] * 2, "B": ["2"] * 3, "C": ["3"] * 4, "D": ["4"] * 5}
    gente = _gente([{"ed": t, "n": n} for t, notas in datos.items() for n in notas])
    base = calcular(TRAMOS, gente, "ed")
    assert calcular(TRAMOS, gente, "ed", unir=None) == base
    assert [g["valor"] for g in base["grupos"]] == ["D", "C", "B", "A"]  # de más a menos personas
    r = calcular(TRAMOS, gente, "ed", unir=json.dumps([{"nombre": " Z ", "valores": ["B", "D"]}]))
    assert [(g["valor"], g["n_personas"], g.get("unidos")) for g in r["grupos"]] == [
        ("Z", 8, ["D", "B"]), ("C", 4, None), ("A", 2, None)]  # lugar de la primera opción, unidos en el orden de T-022
    # el nombre puede repetir una de las opciones que se unen
    r = calcular(TRAMOS, gente, "ed", unir=json.dumps([{"nombre": "A", "valores": ["A", "C"]}]))
    assert [(g["valor"], g["n_personas"]) for g in r["grupos"]] == [("D", 5), ("A", 6), ("B", 3)]


@pytest.mark.parametrize("por,unir,mensaje", [
    ("ed", "no json", "La forma de unir grupos no es válida."),
    ("ed", '{"nombre": "x"}', "La forma de unir grupos no es válida."),
    ("ed", '[{"nombre": "x"}]', "La forma de unir grupos no es válida."),
    ("ed", '[{"nombre": 1, "valores": ["a", "b"]}]', "La forma de unir grupos no es válida."),
    ("ed", '[{"nombre": "x", "valores": ["a", 2]}]', "La forma de unir grupos no es válida."),
    ("ed", '["a"]', "La forma de unir grupos no es válida."),
    (None, '[{"nombre": "x", "valores": ["a", "b"]}]', "Solo se pueden unir opciones de una pregunta de grupos."),
    ("num", '[{"nombre": "x", "valores": ["a", "b"]}]', "Solo se pueden unir opciones de una pregunta de grupos."),
    ("ed", '[{"nombre": "x", "valores": ["a"]}]', "Un grupo unido necesita al menos dos opciones."),
    ("ed", '[{"nombre": "x", "valores": ["a", "a"]}]', "Un grupo unido necesita al menos dos opciones."),
    ("ed", '[{"nombre": "x", "valores": ["a", "zz"]}]', "La opción «zz» no existe en esa pregunta."),
    ("ed", '[{"nombre": "x", "valores": ["a", "b"]}, {"nombre": "y", "valores": ["b", "c"]}]', "La opción «b» está en más de un grupo."),
    ("ed", '[{"nombre": "  ", "valores": ["a", "b"]}]', "Cada grupo unido necesita un nombre distinto."),
    ("ed", '[{"nombre": "x", "valores": ["a", "b"]}, {"nombre": "x ", "valores": ["c", "d"]}]', "Cada grupo unido necesita un nombre distinto."),
    ("ed", '[{"nombre": "e", "valores": ["a", "b"]}]', "Cada grupo unido necesita un nombre distinto."),  # "e" queda sin unir
])
def test_unir_errores_con_su_mensaje_exacto(por, unir, mensaje):
    preg = TRAMOS + [{"id": "num", "titulo": "N", "tipo": "numerica"}]
    gente = _gente([{"ed": t, "num": "30"} for t in "abcde"])
    with pytest.raises(ValueError) as e:
        calcular(preg, gente, por, unir=unir)
    assert str(e.value) == mensaje


def test_endpoint_unir_lector_200_otra_organizacion_404_y_400(env):
    from app import store as st
    from app.auth import create_token, hash_password
    from app.database import get_db
    from app.models import User, user_to_doc
    c, hs = env
    csv = "Comentario,Tramo\n" + "\n".join(f"texto largo número {i},{'abc'[i % 3]}" for i in range(9))
    pid = _crear(c, hs["a"], csv, [{"titulo": "Comentario", "columnas": ["Comentario"], "tipo": "abierta"},
                                   {"titulo": "Tramo", "columnas": ["Tramo"], "tipo": "segmento"}])
    org = c.post("/auth/login", json={"email": "quant-a@x.cl", "password": "clave12345"}).json()["user"]["organizacion"]["id"]
    u = User(id="usr_lectoru", email="quant-lectoru@x.cl", password_hash=hash_password("clave12345"), nombre="L", empresa="",
             created_at=st.now_iso(), org_id=org, rol="lector")
    get_db().users.insert_one(user_to_doc(u))
    hl = {"Authorization": f"Bearer {create_token(u.id)}"}
    url = f"/api/projects/{pid}/closed-results"
    unir = json.dumps([{"nombre": "a o b", "valores": ["a", "b"]}])
    r = c.get(url, headers=hl, params={"por": "q_2", "unir": unir})
    assert r.status_code == 200
    assert [(g["valor"], g["n_personas"], g.get("unidos")) for g in r.json()["grupos"]] == [("a o b", 6, ["a", "b"]), ("c", 3, None)]
    assert c.get(url, headers=hs["b"], params={"por": "q_2", "unir": unir}).status_code == 404
    r = c.get(url, headers=hs["a"], params={"por": "q_2", "unir": json.dumps([{"nombre": "x", "valores": ["a", "q"]}])})
    assert r.status_code == 400 and r.json()["detail"] == "La opción «q» no existe en esa pregunta."
    assert c.get(url, headers=hs["a"], params={"unir": unir}).json()["detail"] == "Solo se pueden unir opciones de una pregunta de grupos."


# ---------- T-023 revisión 1: la separación de la selección múltiple no depende del grupo ----------

def _sumas_cuadran(r):
    """Para toda pregunta con opciones: la suma de `n` de cada opción entre los grupos es el `n` del total (sin personas sin grupo)."""
    assert r["n_sin_grupo"] == 0
    for p in r["preguntas"]:
        for o in p.get("opciones", []):
            assert sum(next(x["n"] for x in g["opciones"] if x["valor"] == o["valor"]) for g in p["por_grupo"]) == o["n"], (p["id"], o)


def test_seleccion_multiple_el_grupo_cuenta_igual_que_el_total_aunque_solo_separaria_distinto():
    # En el total "Ahorro" aparece solo y "Casa" también: son dos opciones. Solo con el grupo A, "Ahorro, Casa" iría siempre junto y se uniría.
    gente = _gente([{"g": "A", "m": "Ahorro, Casa"}] * 2 + [{"g": "B", "m": "Ahorro"}, {"g": "B", "m": "Casa"}])
    preg = [{"id": "g", "titulo": "G", "tipo": "segmento"}, {"id": "m", "titulo": "M", "tipo": "seleccion_multiple"}]
    r = calcular(preg, gente, "g")
    p = r["preguntas"][0]
    assert {o["valor"]: o["n"] for o in p["opciones"]} == {"Ahorro": 3, "Casa": 3}
    a = next(x for x in p["por_grupo"] if x["valor"] == "A")
    assert {o["valor"]: o["n"] for o in a["opciones"]} == {"Ahorro": 2, "Casa": 2}
    _sumas_cuadran(r)
    # "," sin ";" en el total y un grupo donde el ";" sí llega al 5 %: sigue contando como el total
    gente = _gente([{"g": "A", "m": "x; y"}] + [{"g": "B", "m": "x, y"}] * 30)
    _sumas_cuadran(calcular(preg, gente, "g"))


@pytest.mark.parametrize("unir", [None, [{"nombre": "AB", "valores": ["A", "B"]}]])
def test_para_toda_pregunta_con_opciones_la_suma_de_los_grupos_es_el_total(unir):
    filas = []
    for i in range(40):
        filas.append({"g": "ABC"[i % 3], "e": str(1 + i % 5), "s": "Sí" if i % 4 else "No",
                      "m": "Ahorro, Casa" if i % 3 == 0 else ["Ahorro", "Casa", "Subsidios (DS1, DS19), Ahorro", "Subsidios (DS1, DS19)"][i % 4],
                      "u": "xyz"[i % 2 + (i % 7 == 0)]})
    preg = [{"id": "g", "titulo": "G", "tipo": "segmento"}, {"id": "e", "titulo": "E", "tipo": "escala"},
            {"id": "s", "titulo": "S", "tipo": "si_no"}, {"id": "m", "titulo": "M", "tipo": "seleccion_multiple"},
            {"id": "u", "titulo": "U", "tipo": "seleccion_unica"}]
    r = calcular(preg, _gente(filas), "g", unir=json.dumps(unir) if unir else None)
    assert len(r["preguntas"]) == 4
    _sumas_cuadran(r)


def test_rendimiento_10000_personas_20_cerradas_50_grupos():
    import time
    preg = [{"id": "por", "titulo": "P", "tipo": "seleccion_unica"}] + \
           [{"id": f"q{i}", "titulo": f"Q{i}", "tipo": "escala"} for i in range(20)]
    gente = _gente([{"por": f"G{i % 50}", **{f"q{k}": str((i + k) % 5 + 1) for k in range(20)}} for i in range(10000)])
    t = time.perf_counter()
    r = calcular(preg, gente, "por")
    assert len(r["grupos"]) == 50 and len(r["preguntas"]) == 20
    assert time.perf_counter() - t < 10
