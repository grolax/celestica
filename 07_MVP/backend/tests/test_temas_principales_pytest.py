"""RF-43 (T-041): temas principales con citas para el panel de resultados.

Datos armados a mano (ninguna pregunta de la base local tiene codificaciones). mongomock e IA simulada que falla
si se llama: ninguna llamada real a Anthropic.
"""
from __future__ import annotations

import copy
import os
import sys
import time
from pathlib import Path

import mongomock
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")

from app import database  # noqa: E402

database._client = mongomock.MongoClient()

from fastapi.testclient import TestClient  # noqa: E402

from app import store  # noqa: E402
from app.main import app  # noqa: E402
from app.services import thematic  # noqa: E402
from app.services.temas_principales import temas_principales  # noqa: E402

FRASE = "esta es una respuesta con varias palabras"  # 7 palabras


def _cat(id_, nombre, status="validada", definicion="def"):
    return {"id": id_, "nombre": nombre, "definicion": definicion, "status": status, "origen": "analista", "comments": []}


def _a(cid, source="claude", confidence=0.9, status="propuesta"):
    return {"category_id": cid, "rationale": "secreto", "confidence": confidence, "source": source, "status": status}


def _proyecto(textos, categorias, codings, extra_preguntas=(), pid="proy_t"):
    """Proyecto con una abierta q_1 (`textos`: {id: texto}); `extra_preguntas`: [(id, tipo, {rid: valor}), ...]."""
    preguntas = [{"id": "q_1", "titulo": "P1", "columnas": ["P1"], "tipo": "abierta", "contexto_ia": False}]
    resp = {rid: {"q_1": t} for rid, t in textos.items()}
    for qid, tipo, vals in extra_preguntas:
        preguntas.append({"id": qid, "titulo": qid.upper(), "columnas": [qid], "tipo": tipo, "contexto_ia": False})
        for rid, v in vals.items():
            resp.setdefault(rid, {})[qid] = v
    return {
        "id": pid, "org_id": "org_x", "preguntas": preguntas, "audit_log": [],
        "respondentes": [{"id": rid, "valores": v} for rid, v in resp.items()],
        "analisis": {"q_1": {**store.analisis_vacio(), "categories": categorias, "codings": codings}},
    }


def _temas(project, i=0):
    return temas_principales(project)["preguntas"][i]


# ---------- Temas ----------

def test_forma_exacta_y_orden_con_varias_abiertas():
    p = _proyecto({"r1": FRASE, "r2": "otra respuesta distinta con palabras"}, [_cat("c1", "Precio", definicion="Costo")],
                  {"r1": [_a("c1")], "r2": [_a("c1")]},
                  extra_preguntas=[("q_2", "abierta", {"r1": "x"}), ("q_3", "escala", {"r1": 3})])
    p["analisis"]["q_2"] = store.analisis_vacio()
    r = temas_principales(p)
    assert list(r) == ["preguntas"] and [q["pregunta_id"] for q in r["preguntas"]] == ["q_1", "q_2"]
    q1 = r["preguntas"][0]
    assert q1 == {"pregunta_id": "q_1", "titulo": "P1", "n_respuestas": 2, "n_codificadas": 2, "n_temas": 1,
                  "temas": [{"category_id": "c1", "nombre": "Precio", "definicion": "Costo", "personas": 2,
                             "porcentaje": 100.0, "citas": [FRASE, "otra respuesta distinta con palabras"]}]}


def test_sin_abiertas_y_sin_codificar():
    p = _proyecto({"r1": FRASE}, [_cat("c1", "A")], {})
    assert _temas(p) == {"pregunta_id": "q_1", "titulo": "P1", "n_respuestas": 1, "n_codificadas": 0, "n_temas": 0, "temas": []}
    p["preguntas"][0]["tipo"] = "escala"
    assert temas_principales(p) == {"preguntas": []}


def test_solo_categorias_validadas_y_sin_categoria_cuenta_en_codificadas():
    cats = [_cat("v", "Valida"), _cat("p", "Prop", "propuesta"), _cat("d", "Desc", "descartada")]
    p = _proyecto({"r1": FRASE, "r2": FRASE + " 2", "r3": FRASE + " 3"}, cats,
                  {"r1": [_a("v"), _a("p"), _a("d")], "r2": [_a("SIN_CATEGORIA")], "r3": [_a("p")]})
    q = _temas(p)
    assert [t["category_id"] for t in q["temas"]] == ["v"] and q["n_temas"] == 1
    assert q["n_codificadas"] == 3 and q["temas"][0]["porcentaje"] == 33.3


def test_maximo_5_orden_y_desempate_por_nombre():
    cats = [_cat(f"c{i}", n) for i, n in enumerate(["Zeta", "Beta", "Alfa", "Gamma", "Delta", "Épsilon", "Mayor"])]
    textos = {f"r{i}": f"{FRASE} {i}" for i in range(10)}
    codings = {"r0": [_a("c6")], "r1": [_a("c6")], "r2": [_a("c6")]}  # Mayor: 3 personas
    for i, cid in enumerate(["c0", "c1", "c2", "c3", "c4", "c5"]):  # los demás: 1 persona cada uno
        codings[f"r{i + 3}"] = [_a(cid)]
    q = _temas(_proyecto(textos, cats, codings))
    assert [t["nombre"] for t in q["temas"]] == ["Mayor", "Alfa", "Beta", "Delta", "Gamma"]
    assert q["n_temas"] == 7


def test_asignacion_repetida_cuenta_una_vez_y_respuesta_inexistente_se_ignora():
    p = _proyecto({"r1": FRASE, "r2": FRASE + " b"}, [_cat("c1", "A")],
                  {"r1": [_a("c1"), _a("c1", source="analista")], "fantasma": [_a("c1")], "r2": []})
    q = _temas(p)
    assert q["n_codificadas"] == 2  # r1 y r2 (lista vacía); "fantasma" no existe
    assert q["temas"][0]["personas"] == 1 and q["temas"][0]["porcentaje"] == 50.0


def test_porcentaje_un_decimal_y_dos_temas_por_respuesta():
    textos = {f"r{i}": f"{FRASE} {i}" for i in range(3)}
    q = _temas(_proyecto(textos, [_cat("a", "A"), _cat("b", "B")],
                         {"r0": [_a("a"), _a("b")], "r1": [_a("a")], "r2": [_a("SIN_CATEGORIA")]}))
    assert [(t["nombre"], t["personas"], t["porcentaje"]) for t in q["temas"]] == [("A", 2, 66.7), ("B", 1, 33.3)]


def test_baja_confianza_o_sin_confianza_cuenta_igual():
    sin = _a("c1")
    del sin["confidence"]
    q = _temas(_proyecto({"r1": FRASE, "r2": FRASE + " b"}, [_cat("c1", "A")], {"r1": [_a("c1", confidence=0.1)], "r2": [sin]}))
    assert q["temas"][0]["personas"] == 2


# ---------- Citas ----------

def test_cada_cita_es_el_texto_exacto_de_una_respuesta_asignada():
    textos = {"r1": "  Texto con espacios y «comillas» y más palabras…  ", "r2": "Línea uno\nlínea dos con cinco palabras", "r3": "ajena a ese tema"}
    q = _temas(_proyecto(textos, [_cat("c1", "A")], {"r1": [_a("c1")], "r2": [_a("c1")], "r3": [_a("SIN_CATEGORIA")]}))
    assert sorted(q["temas"][0]["citas"]) == sorted([textos["r1"], textos["r2"]])
    assert all(c in textos.values() for c in q["temas"][0]["citas"]) and textos["r3"] not in q["temas"][0]["citas"]


@pytest.mark.parametrize("dato", [
    "escribeme a ana@correo.cl", "mi rut 12.345.678-9", "mi rut 12345678-K", "mi rut 1234567-8", "rut 1.234.567-k",
    "llamame al +56 9 1234 5678", "mi cel es 912345678", "fono 9-1234-5678",
])
def test_respuestas_con_datos_personales_no_se_citan_pero_cuentan(dato):
    textos = {"r1": f"{dato} para coordinar el tema", "r2": FRASE}
    q = _temas(_proyecto(textos, [_cat("c1", "A")], {"r1": [_a("c1")], "r2": [_a("c1")]}))
    assert q["temas"][0]["personas"] == 2 and q["temas"][0]["citas"] == [FRASE]


def test_todo_con_datos_personales_deja_citas_vacias_y_conserva_el_tema():
    textos = {"r1": "ana@correo.cl", "r2": "12.345.678-9"}
    t = _temas(_proyecto(textos, [_cat("c1", "A")], {"r1": [_a("c1")], "r2": [_a("c1")]}))["temas"][0]
    assert t["citas"] == [] and t["personas"] == 2


def test_numeros_cortos_no_son_datos_personales():
    textos = {"r1": "tardaron 15 días en 2024 con 3 pasos"}
    assert _temas(_proyecto(textos, [_cat("c1", "A")], {"r1": [_a("c1")]}))["temas"][0]["citas"] == [textos["r1"]]


def test_orden_de_preferencia_completo():
    corta = "muy corta"
    larga = "palabra " * 60  # 480 caracteres
    textos = {"corta": corta, "larga": larga, "claude_baja": FRASE + " a", "claude_alta": FRASE + " b",
              "analista": FRASE + " c", "sin_conf": FRASE + " d", "igual1": FRASE + " e", "igual2": FRASE + " f"}
    asign = {"corta": _a("c1", "analista", 1.0), "larga": _a("c1", "analista", 1.0),
             "claude_baja": _a("c1", "claude", 0.2), "claude_alta": _a("c1", "claude", 0.95),
             "analista": _a("c1", "analista", 0.1), "igual1": _a("c1", "claude", 0.5), "igual2": _a("c1", "claude", 0.5)}
    sin = _a("c1", "claude")
    del sin["confidence"]
    asign["sin_conf"] = sin
    p = _proyecto(textos, [_cat("c1", "A")], {rid: [a] for rid, a in asign.items()})

    def citas(project):
        # Se pide el orden completo quitando de a una las ya elegidas.
        out = []
        while True:
            temas = _temas(project)["temas"]
            if not temas or not temas[0]["citas"]:
                return out
            c = temas[0]["citas"]
            out.append(c[0])
            del project["analisis"]["q_1"]["codings"][next(r for r, t in textos.items() if t == c[0])]
    # Grupo de 5+ palabras y hasta 400 caracteres primero; dentro: analista, luego confianza (sin confianza al final).
    esperado = [textos[r] for r in ("analista", "claude_alta", "igual1", "igual2", "claude_baja", "sin_conf", "corta", "larga")]
    assert citas(copy.deepcopy(p)) == esperado
    assert _temas(p) == _temas(copy.deepcopy(p))  # determinista
    assert _temas(p)["temas"][0]["citas"] == [textos["analista"], textos["claude_alta"]]


def test_una_respuesta_no_se_repite_en_otro_tema_salvo_que_no_haya_otra():
    textos = {"r1": FRASE + " 1", "r2": FRASE + " 2", "r3": FRASE + " 3"}
    cats = [_cat("a", "A"), _cat("b", "B"), _cat("c", "C")]
    codings = {"r1": [_a("a"), _a("b"), _a("c")], "r2": [_a("a"), _a("b")], "r3": [_a("a")]}
    # A: 3 personas (citas r1, r2). B: 2 (r1 y r2 ya citadas, no tiene otra: se repiten). C: 1 (r1, ya citada: se repite).
    t = {x["nombre"]: x["citas"] for x in _temas(_proyecto(textos, cats, codings))["temas"]}
    assert t["A"] == [textos["r1"], textos["r2"]]
    assert t["B"] == [textos["r1"], textos["r2"]] and t["C"] == [textos["r1"]]
    # Con otra respuesta disponible, no se repite.
    codings["r3"] = [_a("a"), _a("b")]
    t = {x["nombre"]: x["citas"] for x in _temas(_proyecto(textos, cats, codings))["temas"]}
    assert t["B"] == [textos["r3"]]


# ---------- Endpoint ----------

@pytest.fixture(scope="module")
def env():
    ia: list[str] = []

    def no_ia(*a, **k):
        ia.append("ia")
        raise AssertionError("se llamó a la IA al calcular los temas")

    mp = pytest.MonkeyPatch()
    for f in ("propose_categories", "codify_all", "interpret_lexical", "generate_qualitative_report",
              "generate_qualitative_report_v2", "client"):
        mp.setattr(thematic, f, no_ia)
    c = TestClient(app, raise_server_exceptions=False)
    heads, orgs = {}, {}
    for who in ("a", "b"):
        r = c.post("/auth/signup", json={"email": f"temas-{who}@x.cl", "password": "clave12345"})
        heads[who] = {"Authorization": f"Bearer {r.json()['token']}"}
        orgs[who] = r.json()["user"]["organizacion"]["id"]
    yield {"c": c, "h": heads["a"], "hb": heads["b"], "org": orgs["a"], "ia": ia}
    mp.undo()
    assert ia == []


def _guardar(env, project):
    project["org_id"], project["user_id"] = env["org"], "u"
    store.save_project(project)
    return project["id"]


def test_endpoint_devuelve_los_temas_sin_cambiar_nada_ni_auditoria(env):
    meta = [("q_2", "seleccion_unica", {"r1": "Norte", "r2": "Sur"})]
    p = _proyecto({"r1": FRASE, "r2": FRASE + " b"}, [_cat("c1", "Precio")], {"r1": [_a("c1")], "r2": [_a("c1")]},
                  extra_preguntas=meta, pid="proy_endpoint")
    p["preguntas"][1]["contexto_ia"] = True
    pid = _guardar(env, p)
    antes = store.get_project(pid, env["org"])
    r = env["c"].get(f"/api/projects/{pid}/temas-principales", headers=env["h"])
    assert r.status_code == 200 and r.json() == temas_principales(antes)
    assert r.json()["preguntas"][0]["temas"][0]["personas"] == 2
    assert store.get_project(pid, env["org"]) == antes and antes["audit_log"] == []
    assert env["ia"] == []
    texto = r.text
    for prohibido in ("meta", "rationale", "secreto", "Norte", "Sur", "valores", "respondente"):
        assert prohibido not in texto


def test_endpoint_de_otra_organizacion_404_y_sin_sesion_401(env):
    pid = _guardar(env, _proyecto({"r1": FRASE}, [_cat("c1", "A")], {"r1": [_a("c1")]}, pid="proy_ajeno"))
    r = env["c"].get(f"/api/projects/{pid}/temas-principales", headers=env["hb"])
    assert r.status_code == 404 and r.json()["detail"] == "Proyecto no encontrado"
    assert env["c"].get(f"/api/projects/{pid}/temas-principales").status_code == 401


def test_rendimiento_con_10000_respuestas(capsys):
    n = 10_000
    textos = {f"r{i}": f"{FRASE} número {i}" for i in range(n)}
    cats = [_cat(f"c{k}", f"Tema {k}") for k in range(12)]
    codings = {rid: [_a(f"c{i % 12}", confidence=(i % 10) / 10), _a(f"c{(i + 5) % 12}")] for i, rid in enumerate(textos)}
    p = _proyecto(textos, cats, codings)
    t0 = time.perf_counter()
    q = _temas(p)
    seg = time.perf_counter() - t0
    with capsys.disabled():
        print(f"\n[T-041] 10.000 respuestas codificadas: {seg:.3f} s")
    assert q["n_codificadas"] == n and len(q["temas"]) == 5 and q["n_temas"] == 12  # sin límite de tiempo: medido, no exigido
