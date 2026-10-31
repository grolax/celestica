"""RF-23 (T-011a): el proyecto guarda todas sus preguntas y un análisis por pregunta abierta.

Mongomock e IA simulada (el cliente de Anthropic es un doble que anota lo que recibe): ninguna llamada real.
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
from pathlib import Path

import mongomock
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")
os.environ.setdefault("CLAUDE_MAX_OUTPUT_TOKENS", "16000")

from app import database  # noqa: E402

database._client = mongomock.MongoClient()

from fastapi.testclient import TestClient  # noqa: E402

from app import store  # noqa: E402
from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.migrations import migrate_preguntas  # noqa: E402
from app.services import claude_log, thematic  # noqa: E402
from test_report_v2_pytest import FakeClient  # noqa: E402  (cliente de Anthropic simulado, ya probado)

N = 12
C_ID, C_GEN, C_EDAD, C_REG = "Correo institucional", "1. ¿Cuál es tu género?", "2. ¿Cuál es tu edad?", "Región"
C_COM = ["Comuna A", "Comuna B", "Comuna C"]
C_P28, C_P30 = "28. ¿Qué tendría que cambiar?", "30. ¿Qué palabras asocias?"
EMAILS = [f"persona{i:02d}@secreto.cl" for i in range(N)]
PREGUNTAS = [  # lo que el usuario confirmó en la vista previa
    {"titulo": C_P28, "columnas": [C_P28], "tipo": "abierta", "contexto_ia": False},
    {"titulo": C_P30, "columnas": [C_P30], "tipo": "abierta", "contexto_ia": False},
    {"titulo": "Comuna", "columnas": C_COM, "tipo": "segmento", "contexto_ia": False},
    {"titulo": C_ID, "columnas": [C_ID], "tipo": "identificador", "contexto_ia": False},
    {"titulo": C_GEN, "columnas": [C_GEN], "tipo": "segmento", "contexto_ia": True},
    {"titulo": C_EDAD, "columnas": [C_EDAD], "tipo": "segmento", "contexto_ia": True},
    {"titulo": C_REG, "columnas": [C_REG], "tipo": "segmento", "contexto_ia": False},
]


def _df() -> pd.DataFrame:
    return pd.DataFrame({
        C_ID: EMAILS,
        C_GEN: ["Femenino" if i % 2 else "Masculino" for i in range(N)],
        C_EDAD: [20 + i for i in range(N)],
        C_REG: [f"RegionSecreta{i % 3}" for i in range(N)],
        **{c: [f"Comuna{k}_{i}" if i % 3 == k else "" for i in range(N)] for k, c in enumerate(C_COM)},
        C_P28: ["" if i == 3 else f"TEXTO28_{i} el profesor debería explicar mejor" for i in range(N)],
        C_P30: ["" if i < 6 else f"TEXTO30_{i} cercanía confianza exigencia" for i in range(N)],
    })


def _csv(df=None) -> bytes:
    return (_df() if df is None else df).to_csv(index=False).encode()


@pytest.fixture(scope="module")
def env():
    c = TestClient(app, raise_server_exceptions=False)
    users = {}
    for who in ("a", "b"):
        r = c.post("/auth/signup", json={"email": f"preg-{who}@x.cl", "password": "clave12345"})
        users[who] = ({"Authorization": f"Bearer {r.json()['token']}"}, r.json()["user"]["organizacion"]["id"])
    return {"c": c, "h": users["a"][0], "org": users["a"][1], "hb": users["b"][0]}


def _crear(env, preguntas=PREGUNTAS, name="Encuesta", df=None, **extra):
    data = {"name": name, **extra}
    if preguntas is not None:
        data["preguntas"] = preguntas if isinstance(preguntas, str) else json.dumps(preguntas)
    return env["c"].post("/api/projects", headers=env["h"], data=data,
                         files={"file": ("e.csv", io.BytesIO(_csv(df)), "text/csv")})


@pytest.fixture(scope="module")
def pid(env):
    r = _crear(env)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _wait(c, h, url):
    for _ in range(100):
        time.sleep(0.05)
        p = c.get(url, headers=h).json()
        if p["status"] in ("done", "error"):
            return p
    return p


# ---------- creación ----------

def test_crear_con_preguntas_devuelve_las_abiertas_y_guarda_na_como_null(env):
    r = _crear(env)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["n_responses"] == N - 1 and body["text_column"] == C_P28  # la primera abierta es la pregunta por defecto
    assert body["preguntas_abiertas"] == [{"id": "q_1", "titulo": C_P28, "n_respuestas": N - 1},
                                          {"id": "q_2", "titulo": C_P30, "n_respuestas": N - 6}]

    doc = get_db().projects.find_one({"_id": body["id"]})
    assert "responses" not in doc and "categories" not in doc and set(doc["analisis"]) == {"q_1", "q_2"}
    por_id = {r["id"]: r["valores"] for r in doc["respondentes"]}
    assert len(doc["respondentes"]) == N  # una fila por persona, también la que dejó una abierta en blanco
    assert por_id["R0004"]["q_1"] is None and por_id["R0001"]["q_2"] is None  # N/A = null, nunca ""
    # la unión de las 3 columnas ramificadas toma el primer valor no vacío
    assert por_id["R0001"]["q_3"] == "Comuna0_0" and por_id["R0002"]["q_3"] == "Comuna1_1" and por_id["R0003"]["q_3"] == "Comuna2_2"
    assert all(v["q_3"] for v in por_id.values())

    g = env["c"].get(f"/api/projects/{body['id']}", headers=env["h"]).json()
    por_pregunta = {p["id"]: p for p in g["preguntas"]}
    assert por_pregunta["q_3"]["columnas"] == C_COM and por_pregunta["q_3"]["tipo"] == "segmento"
    assert (por_pregunta["q_1"]["n_respuestas"], por_pregunta["q_1"]["n_na"]) == (N - 1, 1)
    assert por_pregunta["q_4"]["tipo"] == "identificador" and por_pregunta["q_4"]["contexto_ia"] is False
    assert [p["id"] for p in g["preguntas"] if p["contexto_ia"]] == ["q_5", "q_6"]
    assert g["pregunta"] == "q_1" and g["n_responses"] == N - 1 and g["text_column"] == C_P28


def test_auditoria_de_creacion_solo_lleva_conteos_por_tipo(env):
    r = _crear(env)
    ev = [e for e in env["c"].get(f"/api/projects/{r.json()['id']}/audit", headers=env["h"]).json()
          if e["action"] == "creacion_proyecto"][0]["detail"]
    assert ev["preguntas_por_tipo"] == {"abierta": 2, "segmento": 4, "identificador": 1}
    blob = json.dumps(ev, ensure_ascii=False)
    assert not any(e in blob for e in EMAILS) and "RegionSecreta" not in blob


@pytest.mark.parametrize("cambio,status,mensaje", [
    ([{"titulo": "X", "columnas": ["No existe"], "tipo": "abierta"}], 422, "La columna «No existe» no existe en los datos."),
    ([{"titulo": "X", "columnas": [C_P28], "tipo": "abierta"}, {"titulo": "Y", "columnas": [C_P28], "tipo": "abierta"}],
     422, f"La columna «{C_P28}» está en más de una pregunta."),
    ([{"titulo": "X", "columnas": [C_P28], "tipo": "inventado"}], 422, "Tipo de pregunta no válido: inventado."),
    ([{"titulo": "X", "columnas": [C_P28], "tipo": "abierta"},
      {"titulo": "Y", "columnas": [C_ID], "tipo": "identificador", "contexto_ia": True}],
     422, "Una columna de identificación no se puede enviar a la IA."),
    ([{"titulo": "X", "columnas": [C_ID], "tipo": "identificador"}], 400,  # RF-24: solo cerradas ya se acepta
     "Esta encuesta no tiene preguntas que se puedan analizar: marca al menos una pregunta abierta o cerrada."),
    ("esto no es json", 422, "Las preguntas enviadas no son un JSON válido."),
])
def test_errores_del_contrato_y_no_se_guarda_nada(env, cambio, status, mensaje):
    antes = get_db().projects.count_documents({})
    r = _crear(env, preguntas=cambio)
    assert r.status_code == status and r.json()["detail"] == mensaje, r.text
    assert get_db().projects.count_documents({}) == antes


def test_sin_preguntas_se_detectan_y_solo_genero_y_edad_van_a_la_ia(env):
    df = _df().drop(columns=C_COM + [C_REG])
    df = df.rename(columns={C_EDAD: "Edad"})  # un título corto con pocos valores repetidos: T-010 lo toma por segmento
    df["Edad"] = [20 + i % 4 for i in range(N)]
    df.insert(0, "id_respuesta", [f"E{i:03d}" for i in range(N)])
    r = _crear(env, preguntas=None, df=df, text_column=C_P28)
    assert r.status_code == 200 and r.json()["text_column"] == C_P28
    g = env["c"].get(f"/api/projects/{r.json()['id']}", headers=env["h"]).json()
    por_titulo = {p["titulo"]: p for p in g["preguntas"]}
    assert "id_respuesta" not in por_titulo  # es el id de cada persona, no una pregunta
    assert por_titulo[C_P28]["tipo"] == "abierta" and por_titulo[C_ID]["tipo"] == "identificador"
    assert {p["titulo"] for p in g["preguntas"] if p["contexto_ia"]} == {C_GEN, "Edad"}
    items = env["c"].get(f"/api/projects/{r.json()['id']}/responses", headers=env["h"]).json()["items"]
    assert items[0]["id"] == "E000" and set(items[0]["meta"]) == {C_GEN, "Edad"}


def test_listado_resume_la_pregunta_por_defecto(env, pid):
    item = next(p for p in env["c"].get("/api/projects", headers=env["h"]).json() if p["id"] == pid)
    assert item["n_responses"] == N - 1 and item["n_categories"] == 0 and item["has_lexical"] is False


# ---------- vista por pregunta ----------

def test_vista_solo_lleva_contexto_y_nunca_identificadores():
    proyecto = {
        "id": "p", "name": "n", "preguntas": [
            {"id": "q_1", "titulo": "Abierta", "columnas": ["a"], "tipo": "abierta", "contexto_ia": False},
            {"id": "q_2", "titulo": "Correo", "columnas": ["c"], "tipo": "identificador", "contexto_ia": True},  # mal marcada
            {"id": "q_3", "titulo": "Género", "columnas": ["g"], "tipo": "segmento", "contexto_ia": True},
            {"id": "q_4", "titulo": "Región", "columnas": ["r"], "tipo": "segmento", "contexto_ia": False}],
        "respondentes": [{"id": "R1", "valores": {"q_1": "hola", "q_2": "x@y.cl", "q_3": "F", "q_4": "RM"}},
                         {"id": "R2", "valores": {"q_1": None, "q_2": "z@y.cl", "q_3": "M", "q_4": "V"}},
                         {"id": "R3", "valores": {"q_1": "chao", "q_2": None, "q_3": None, "q_4": "V"}}],
        "analisis": {"q_1": {"categories": [{"id": "cat_1"}]}},
    }
    v = store.vista_pregunta(proyecto)
    assert v["pregunta"] == "q_1" and v["categories"] == [{"id": "cat_1"}] and v["codings"] == {}
    assert v["responses"] == [{"id": "R1", "text": "hola", "meta": {"Género": "F"}},
                              {"id": "R3", "text": "chao", "meta": {}}]  # R2 es N/A y no entra; el N/A de contexto no se envía
    assert store.vista_pregunta(proyecto, "q_3") is None and store.vista_pregunta(proyecto, "q_9") is None


# ---------- análisis independiente por pregunta ----------

def test_categorias_codificacion_y_lexico_son_independientes(env, pid, monkeypatch):
    c, h = env["c"], env["h"]
    base = f"/api/projects/{pid}"
    monkeypatch.setattr(thematic, "interpret_lexical", lambda marco, lex: "interpretación")
    monkeypatch.setattr(thematic, "codify_all", lambda marco, cats, responses, batch_size=25, progress_cb=None: [
        {"response_id": r["id"], "assignments": [{"category_id": cats[0]["id"], "rationale": "x", "confidence": 0.9}]}
        for r in responses])

    ca = c.post(f"{base}/categories?pregunta=q_1", headers=h, json={"nombre": "Docencia"}).json()
    cb = c.post(f"{base}/categories?pregunta=q_2", headers=h, json={"nombre": "Vínculo"}).json()
    c.patch(f"{base}/categories/{ca['id']}?pregunta=q_1", headers=h, json={"status": "validada"})
    nombres = lambda q: [x["nombre"] for x in c.get(f"{base}?pregunta={q}", headers=h).json()["categories"]]  # noqa: E731
    assert nombres("q_1") == ["Docencia"] and nombres("q_2") == ["Vínculo"]
    assert c.get(base, headers=h).json()["categories"][0]["nombre"] == "Docencia"  # sin ?pregunta: la primera abierta
    # una categoría de q_1 no se puede tocar desde q_2
    assert c.patch(f"{base}/categories/{ca['id']}?pregunta=q_2", headers=h, json={"nombre": "x"}).status_code == 404
    com = c.post(f"{base}/categories/{cb['id']}/comments?pregunta=q_2", headers=h, json={"text": "ojo"}).json()
    assert c.get(f"{base}?pregunta=q_2", headers=h).json()["categories"][0]["comments"][0]["id"] == com["id"]
    assert c.delete(f"{base}/categories/{cb['id']}/comments/{com['id']}?pregunta=q_2", headers=h).status_code == 200

    # léxico: solo q_1
    assert c.post(f"{base}/lexical?pregunta=q_1", headers=h).json()["n_responses"] == N - 1
    assert c.get(f"{base}/lexical?pregunta=q_1", headers=h).status_code == 200
    assert c.get(f"{base}/lexical?pregunta=q_2", headers=h).status_code == 404

    # codificación: el progreso es por pregunta
    assert c.post(f"{base}/codify?pregunta=q_1", headers=h).json() == {"status": "started", "total": N - 1}
    assert _wait(c, h, f"{base}/codify/progress?pregunta=q_1")["status"] == "done"
    assert c.get(f"{base}/codify/progress?pregunta=q_2", headers=h).json() == {"status": "idle"}
    assert c.get(f"{base}/summary?pregunta=q_1", headers=h).json()["n_coded"] == N - 1
    assert c.get(f"{base}/summary?pregunta=q_2", headers=h).json()["n_coded"] == 0
    assert c.post(f"{base}/codify?pregunta=q_2", headers=h).json() == {"status": "started", "total": N - 6}
    assert _wait(c, h, f"{base}/codify/progress?pregunta=q_2")["status"] == "done"
    assert [x["nombre"] for x in c.get(f"{base}/summary?pregunta=q_2", headers=h).json()["by_category"]] == ["Vínculo"]
    assert [x["nombre"] for x in c.get(f"{base}/summary?pregunta=q_1", headers=h).json()["by_category"]] == ["Docencia"]
    # recodificación manual y respuestas por pregunta
    assert c.put(f"{base}/responses/R0001/codings?pregunta=q_1", headers=h, json={"category_ids": [ca["id"]]}).status_code == 200
    r1 = c.get(f"{base}/responses?pregunta=q_1", headers=h).json()
    r2 = c.get(f"{base}/responses?pregunta=q_2", headers=h).json()
    assert (r1["total"], r2["total"]) == (N - 1, N - 6)
    assert r1["items"][0]["codings"][0]["category_id"] == ca["id"] and r2["items"][0]["codings"][0]["category_id"] == cb["id"]
    # trazabilidad y exportaciones siguen la pregunta
    assert len(c.get(f"{base}/export/traceability?pregunta=q_2", headers=h).json()) == N - 6
    assert c.get(f"{base}/export/csv?pregunta=q_1", headers=h).status_code == 200
    assert c.get(f"{base}/export/pdf?pregunta=q_2", headers=h).status_code == 200


def test_pregunta_inexistente_o_cerrada_es_404_y_sin_pregunta_es_la_primera_abierta(env, pid):
    c, h = env["c"], env["h"]
    base = f"/api/projects/{pid}"
    for q in ("q_99", "q_3"):  # inexistente / cerrada (segmento)
        for m, ruta in [("GET", ""), ("GET", "/responses"), ("GET", "/summary"), ("GET", "/lexical"), ("POST", "/lexical"),
                        ("POST", "/categories/propose"), ("POST", "/categories"), ("POST", "/codify"),
                        ("GET", "/codify/progress"), ("POST", "/report"), ("GET", "/report"), ("GET", "/report/progress"),
                        ("GET", "/export/csv"), ("GET", "/export/pdf")]:
            r = c.request(m, f"{base}{ruta}", headers=h, params={"pregunta": q}, json={"nombre": "x"} if ruta == "/categories" else None)
            assert r.status_code == 404 and r.json()["detail"] == "Pregunta no encontrada", (q, m, ruta, r.text[:100])
    assert c.get(base, headers=h).json() == {**c.get(f"{base}?pregunta=q_1", headers=h).json()}
    # un proyecto ajeno sigue siendo "Proyecto no encontrado", con o sin ?pregunta
    r = c.get(f"{base}?pregunta=q_1", headers=env["hb"])
    assert r.status_code == 404 and r.json()["detail"] == "Proyecto no encontrado"


# ---------- privacidad y tokens ----------

def test_a_la_ia_solo_llega_la_pregunta_elegida_y_el_contexto_marcado(env, monkeypatch, tmp_path):
    c, h = env["c"], env["h"]
    cliente = FakeClient(truncate_above=100)
    crudo: list[str] = []
    stream = cliente.stream

    def anota(**kw):  # exactamente lo que se enviaría a Anthropic
        crudo.append(json.dumps(kw, ensure_ascii=False, default=str))
        return stream(**kw)

    cliente.stream = anota
    monkeypatch.setattr(thematic, "_client", cliente)
    monkeypatch.setattr(thematic, "V2_MAX_WORKERS", 2)
    monkeypatch.setattr(claude_log, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(claude_log, "_logger", None)

    r = _crear(env, name="Privacidad")
    base = f"/api/projects/{r.json()['id']}"
    otra = {"q_1": "TEXTO30_", "q_2": "TEXTO28_"}  # el texto de la OTRA pregunta abierta
    for q in ("q_1", "q_2"):
        crudo.clear()
        assert c.post(f"{base}/categories/propose?pregunta={q}", headers=h).status_code == 200
        cid = next(x["id"] for x in c.get(f"{base}?pregunta={q}", headers=h).json()["categories"])
        c.patch(f"{base}/categories/{cid}?pregunta={q}", headers=h, json={"status": "validada"})
        assert c.post(f"{base}/lexical?pregunta={q}", headers=h).status_code == 200
        assert c.post(f"{base}/codify?pregunta={q}", headers=h).status_code == 200
        assert _wait(c, h, f"{base}/codify/progress?pregunta={q}")["status"] == "done"
        for modo in ("v1", "v2"):
            assert c.post(f"{base}/report?mode={modo}&pregunta={q}", headers=h).json()["status"] == "started"
            assert _wait(c, h, f"{base}/report/progress?pregunta={q}")["status"] == "done", modo
        todo = "\n".join(crudo)
        propio = {"q_1": "TEXTO28_", "q_2": "TEXTO30_"}[q]
        assert propio in todo and len(crudo) > 10  # la prueba no pasa vacía: sí se envía la pregunta elegida
        assert "Femenino" in todo and C_EDAD in todo  # y el contexto marcado (género y edad)
        for prohibido in [*EMAILS, "secreto.cl", C_ID, "RegionSecreta", "Comuna0_", "Comuna1_", "Comuna2_", otra[q]]:
            assert prohibido not in todo, f"{prohibido!r} llegó a la IA al analizar {q}"


# ---------- migración ----------

def _proyecto_antiguo(org_id: str, pid: str) -> dict:
    """Documento con la forma de antes de T-011a: todo en la raíz."""
    responses = [{"id": f"E{i:03d}", "text": f"Texto {i} del curso", "meta": {
        "Correo": f"p{i}@x.cl", "Género": "F" if i % 2 else "M", "Edad": str(20 + i % 4), "Sede": ["Norte", "Sur", "Este"][i % 3]}}
        for i in range(12)]
    return {
        "_id": pid, "id": pid, "org_id": org_id, "user_id": "u", "name": "Antiguo", "marco_teorico": "marco",
        "created_at": "2026-01-01T00:00:00+00:00", "columns": ["id_respuesta", "Correo", "Género", "Edad", "Sede", "Comentario"],
        "text_column": "Comentario", "responses": responses, "lexical": {"n_responses": 12, "sentiment_distribution": {"positivo": 5},
                                                                           "sentiment_by_response": {"E000": 1.0}, "top_terms": []},
        "lexical_interpretation": "interp",
        "categories": [{"id": "cat_1", "nombre": "A", "status": "validada", "comments": [{"id": "com_1", "text": "x"}]},
                       {"id": "cat_2", "nombre": "B", "status": "propuesta", "comments": []}],
        "codings": {"E000": [{"category_id": "cat_1", "confidence": 0.9}], "E001": [{"category_id": "cat_1", "confidence": 0.5}]},
        "qualitative_report": "# Informe", "v2_analyses_cache": {"fingerprint": "fp", "analyses": []},
        "audit_log": [{"id": "evt_1", "action": "creacion_proyecto"}],
    }


def test_migracion_conserva_lo_visible_y_es_idempotente(env, tmp_path):
    c, h, db = env["c"], env["h"], get_db()
    assert _crear(env, name="Ya migrado").status_code == 200  # nace con `preguntas`: la migración no lo toca
    antiguo = _proyecto_antiguo(env["org"], "proj_antiguo_1")
    db.projects.insert_one(antiguo)
    esperado_get = {
        "id": "proj_antiguo_1", "name": "Antiguo", "marco_teorico": "marco", "created_at": antiguo["created_at"],
        "columns": antiguo["columns"], "text_column": "Comentario", "categories": antiguo["categories"],
        "n_responses": 12, "has_lexical": True, "n_coded": 2, "has_report": True, "n_audit_events": 1}
    esperado_summary = {
        "by_category": [{"category_id": "cat_1", "nombre": "A", "count": 2}],
        "sentiment_distribution": {"positivo": 5}, "confidence_distribution": {"alta": 1, "media": 0, "baja": 1},
        "n_responses": 12, "n_coded": 2, "n_categories_validated": 1, "has_lexical": True, "has_report": True}

    migrados = {d["_id"]: d for d in db.projects.find({"preguntas": {"$exists": True}})}
    assert migrate_preguntas(db)["proyectos"] >= 1  # el mío y, según el orden de las pruebas, algún huérfano de otro módulo
    assert all(db.projects.find_one({"_id": k}) == v for k, v in migrados.items())
    g = c.get("/api/projects/proj_antiguo_1", headers=h).json()
    assert {k: g[k] for k in esperado_get} == esperado_get and g["pregunta"] == "q_1"
    assert c.get("/api/projects/proj_antiguo_1/summary", headers=h).json() == esperado_summary
    assert c.get("/api/projects/proj_antiguo_1/report", headers=h).json() == {"report": "# Informe"}
    assert c.get("/api/projects/proj_antiguo_1/lexical", headers=h).json()["n_responses"] == 12

    doc = db.projects.find_one({"_id": "proj_antiguo_1"})
    assert not {"responses", "categories", "codings", "lexical", "lexical_interpretation", "qualitative_report",
                "v2_analyses_cache"} & set(doc)
    assert "v2_analyses_cache" not in doc["analisis"]["q_1"]  # el caché v2 antiguo se descarta, no se mueve
    por_titulo = {p["titulo"]: p for p in doc["preguntas"]}
    assert doc["preguntas"][0] == {"id": "q_1", "titulo": "Comentario", "columnas": ["Comentario"], "tipo": "abierta", "contexto_ia": False}
    assert por_titulo["Correo"]["tipo"] == "identificador" and por_titulo["Correo"]["contexto_ia"] is False
    assert {t for t, p in por_titulo.items() if p["contexto_ia"]} == {"Género", "Edad"}
    assert doc["respondentes"][0] == {"id": "E000", "valores": {"q_1": "Texto 0 del curso", "q_2": "p0@x.cl", "q_3": "M",
                                                                "q_4": "20", "q_5": "Norte"}}
    # lo que se ve de las respuestas es lo de antes, salvo `meta`, que ahora solo lleva el contexto marcado
    items = c.get("/api/projects/proj_antiguo_1/responses", headers=h).json()["items"]
    assert [i["id"] for i in items][:3] == ["E000", "E001", "E002"] and items[0]["text"] == "Texto 0 del curso"
    assert items[0]["meta"] == {"Género": "M", "Edad": "20"} and items[0]["sentiment"] == 1.0

    # segunda corrida: nada cambia; un proyecto ya migrado no se toca
    antes = {d["_id"]: d for d in db.projects.find()}
    assert migrate_preguntas(db) == {"proyectos": 0, "fallidos": 0}
    assert {d["_id"]: d for d in db.projects.find()} == antes  # incluye el proyecto ya migrado de arriba


def test_importar_proyecto_pre_auth_nace_en_el_esquema_nuevo(env, tmp_path, monkeypatch):
    legacy = _proyecto_antiguo("", "proj_legacy_1")
    legacy.pop("_id"); legacy.pop("org_id"); legacy.pop("user_id")
    (tmp_path / "proj_legacy_1.json").write_text(json.dumps(legacy), encoding="utf-8")
    monkeypatch.setattr(store, "LEGACY_DIR", tmp_path)
    assert env["c"].post("/api/projects/import-legacy", headers=env["h"]).json() == {"imported": 1}
    g = env["c"].get("/api/projects/proj_legacy_1", headers=env["h"]).json()
    assert g["n_responses"] == 12 and g["pregunta"] == "q_1" and len(g["preguntas"]) == 5


def test_init_db_migra_proyectos_antiguos_al_arrancar(env):
    db = get_db()
    db.projects.insert_one(_proyecto_antiguo(env["org"], "proj_antiguo_arranque"))
    database.init_db()  # lo que corre el servidor al arrancar; no se llama a migrate_preguntas a mano
    doc = db.projects.find_one({"_id": "proj_antiguo_arranque"})
    assert doc["preguntas"][0]["id"] == "q_1" and "responses" not in doc and len(doc["respondentes"]) == 12
    r = env["c"].get("/api/projects/proj_antiguo_arranque", headers=env["h"])
    assert r.status_code == 200 and r.json()["n_responses"] == 12 and r.json()["pregunta"] == "q_1"


def test_un_proyecto_malformado_no_tumba_la_migracion(env, caplog):
    db = get_db()
    malo = _proyecto_antiguo(env["org"], "proj_malformado")
    malo["responses"][0]["meta"] = "SECRETO_EN_LOG"  # meta debería ser un dict
    sano = _proyecto_antiguo(env["org"], "proj_sano_junto_al_malo")
    db.projects.insert_many([malo, sano])
    try:
        with caplog.at_level("ERROR"):
            assert migrate_preguntas(db)["fallidos"] == 1
        assert db.projects.find_one({"_id": "proj_malformado"}) == malo  # sin tocar
        assert "preguntas" in db.projects.find_one({"_id": "proj_sano_junto_al_malo"})
        assert "proj_malformado" in caplog.text and "SECRETO_EN_LOG" not in caplog.text and "Texto 0" not in caplog.text
        database.init_db()  # el arranque tampoco se cae
    finally:
        db.projects.delete_one({"_id": "proj_malformado"})


def test_edad_numerica_va_como_contexto_por_defecto(env):
    n = 60
    df = pd.DataFrame({
        "id_respuesta": [f"E{i:03d}" for i in range(n)],
        "2. ¿Cuál es tu edad?": [18 + i % 50 for i in range(n)],  # 18-67
        "28. ¿Qué tendría que cambiar?": [f"TEXTO_{i} el profesor debería explicar mejor" for i in range(n)],
        "Correo institucional": [f"p{i}@secreto.cl" for i in range(n)],
    })
    r = _crear(env, preguntas=None, df=df, text_column="28. ¿Qué tendría que cambiar?")
    assert r.status_code == 200, r.text
    g = env["c"].get(f"/api/projects/{r.json()['id']}", headers=env["h"]).json()
    por_titulo = {p["titulo"]: p for p in g["preguntas"]}
    assert por_titulo["2. ¿Cuál es tu edad?"]["tipo"] == "numerica" and por_titulo["2. ¿Cuál es tu edad?"]["contexto_ia"] is True
    assert por_titulo["Correo institucional"]["tipo"] == "identificador" and por_titulo["Correo institucional"]["contexto_ia"] is False
    items = env["c"].get(f"/api/projects/{r.json()['id']}/responses", headers=env["h"]).json()["items"]
    assert items[0]["meta"] == {"2. ¿Cuál es tu edad?": "18"}
