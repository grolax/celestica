"""RF-41 (T-032): recomendaciones automáticas (alertas, segmentos, plantilla), sin IA. Datos mínimos en los bordes de cada regla."""
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

from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.services.recommendations import recomendar  # noqa: E402
from app.templates import FRAMEWORK_TEMPLATES  # noqa: E402


def _proyecto(*cols, name="P", marco=""):
    """cols = (título, tipo, valores): una pregunta por columna, una persona por posición (None = N/A)."""
    n = len(cols[0][2])
    preguntas = [{"id": f"q_{i}", "titulo": t, "tipo": tipo} for i, (t, tipo, _) in enumerate(cols, 1)]
    respondentes = [{"id": f"R{j}", "valores": {f"q_{i}": v[j] for i, (_, _, v) in enumerate(cols, 1)}} for j in range(n)]
    return {"name": name, "marco_teorico": marco, "preguntas": preguntas, "respondentes": respondentes}


def _alertas(*cols, **kw):
    return recomendar(_proyecto(*cols, **kw))["alertas"]


def _ids(alertas):
    return [a["id"] for a in alertas]


# ---------- alertas ----------

@pytest.mark.parametrize("n,esperada", [(9, "pocas_respuestas"), (10, "pocas_respuestas_30"), (29, "pocas_respuestas_30"), (30, None)])
def test_pocas_respuestas_bordes(n, esperada):
    a = _alertas(("P", "escala", ["3"] * n))
    assert _ids(a) == ([esperada] if esperada else [])


def test_mensajes_de_pocas_respuestas_son_los_del_contrato():
    a = _alertas(("P", "escala", ["3"] * 9))[0]
    assert a == {"id": "pocas_respuestas", "nivel": "importante", "pregunta_id": None,
                 "mensaje": "La encuesta tiene muy pocas respuestas (9); los resultados serán poco representativos."}
    a = _alertas(("P", "escala", ["3"] * 24))[0]
    assert a == {"id": "pocas_respuestas_30", "nivel": "aviso", "pregunta_id": None,
                 "mensaje": "La encuesta tiene 24 respuestas: los resultados pueden variar mucho. Tómalos como una primera mirada."}


def test_muchas_vacias_justo_en_la_mitad_no_y_una_mas_si():
    base = ["a"] * 30
    mitad = _alertas(("Ingreso", "seleccion_unica", ["x"] * 15 + [None] * 15), ("B", "seleccion_unica", base))
    assert mitad == []
    a = _alertas(("Ingreso", "seleccion_unica", ["x"] * 14 + [None] * 16), ("B", "seleccion_unica", base))
    assert a == [{"id": "muchas_vacias", "nivel": "aviso", "pregunta_id": "q_1",
                  "mensaje": "Más de la mitad de las personas no respondió «Ingreso» (16 de 30)."}]


def test_muchas_vacias_ignora_identificadores():
    assert _alertas(("Rut", "identificador", [None] * 30), ("B", "seleccion_unica", ["a"] * 30)) == []


def test_titulo_de_mas_de_80_caracteres_se_recorta():
    largo = "x" * 81
    m = _alertas((largo, "seleccion_unica", [None] * 30), ("B", "seleccion_unica", ["a"] * 30))[0]["mensaje"]
    assert f"«{'x' * 80}…»" in m
    ochenta = "y" * 80
    assert f"«{ochenta}»" in _alertas((ochenta, "seleccion_unica", [None] * 30), ("B", "seleccion_unica", ["a"] * 30))[0]["mensaje"]


def test_abierta_repetida_bordes():
    largo = [f"respuesta numero {i % 10} del grupo" for i in range(20)]  # 10 distintas
    a = [x for x in _alertas(("Comentario", "abierta", largo)) if x["id"] == "abierta_repetida"]
    assert a == [{"id": "abierta_repetida", "nivel": "aviso", "pregunta_id": "q_1",
                  "mensaje": "Las respuestas de «Comentario» se repiten mucho (solo 10 distintas): quizás es una pregunta cerrada."}]
    once = [f"respuesta numero {i % 11} del grupo" for i in range(20)]  # 11 distintas
    assert "abierta_repetida" not in _ids(_alertas(("Comentario", "abierta", once)))
    assert "abierta_repetida" not in _ids(_alertas(("Comentario", "abierta", largo[:19])))  # 19 respuestas


def test_abierta_repetida_no_distingue_mayusculas_ni_espacios():
    v = ["Muy bueno el servicio", "muy  bueno el servicio ", "MUY BUENO EL SERVICIO"] * 7  # 21 respuestas, 1 distinta
    a = [x for x in _alertas(("C", "abierta", v)) if x["id"] == "abierta_repetida"]
    assert len(a) == 1 and "solo 1 distintas" in a[0]["mensaje"]


def test_abierta_corta_mediana_2_si_y_3_no():
    cortas = [f"bien {i}" for i in range(20)]  # 2 palabras, todas distintas
    a = [x for x in _alertas(("C", "abierta", cortas)) if x["id"] == "abierta_corta"]
    assert a == [{"id": "abierta_corta", "nivel": "aviso", "pregunta_id": "q_1",
                  "mensaje": "La mitad de las respuestas de «C» tiene 2 palabras o menos: el análisis de temas tendrá poco material."}]
    assert "abierta_corta" not in _ids(_alertas(("C", "abierta", [f"muy bien {i}" for i in range(20)])))  # 3 palabras
    assert "abierta_corta" not in _ids(_alertas(("C", "abierta", cortas[:19])))  # 19 respuestas


def test_abierta_corta_no_se_suma_a_abierta_repetida():
    a = _alertas(("C", "abierta", ["bien"] * 20))
    assert "abierta_repetida" in _ids(a) and "abierta_corta" not in _ids(a)


def test_cerrada_dispersa_bordes():
    def alertas(n, k):
        return _ids(_alertas(("Comuna", "segmento", [f"c{i % k}" for i in range(n)])))
    assert "cerrada_dispersa" not in alertas(30, 15)  # justo la mitad
    assert "cerrada_dispersa" in alertas(30, 16)
    assert "cerrada_dispersa" not in alertas(29, 29)  # menos de 30 respuestas
    m = [x for x in _alertas(("Comuna", "seleccion_unica", [f"c{i}" for i in range(30)])) if x["id"] == "cerrada_dispersa"]
    assert m[0]["mensaje"] == "«Comuna» tiene casi tantas opciones distintas como respuestas (30 de 30): quizás es una pregunta abierta."


def test_orden_de_las_alertas_es_el_de_la_tabla():
    p = _proyecto(("Vacía", "seleccion_unica", [None] * 10),
                  ("Texto", "abierta", ["bien"] * 10))
    p["respondentes"] = p["respondentes"] * 2  # 20 personas; "Texto" con 20 respuestas
    assert _ids(recomendar(p)["alertas"]) == ["pocas_respuestas_30", "muchas_vacias", "abierta_repetida"]


# ---------- segmentos ----------

def _seg(*cols):
    return recomendar(_proyecto(*cols))["segmentos"]


def test_segmento_basico_y_forma():
    s = _seg(("Género", "segmento", ["F"] * 20 + ["M"] * 20))
    assert s == [{"pregunta_id": "q_1", "titulo": "Género", "n_grupos": 2,
                  "motivo": "Separa a las personas en 2 grupos con datos suficientes."}]


def test_segmentos_orden_prioritario_primero_luego_mas_grupos_y_maximo_3():
    tres = ["a", "b", "c"] * 14
    cuatro = ["a", "b", "c", "d"] * 10
    dos = ["a", "b"] * 20
    n = 42
    s = _seg(("Pregunta cuatro", "seleccion_unica", cuatro[:n]),
             ("Pregunta tres", "seleccion_unica", tres[:n]),
             ("Género", "segmento", (dos + dos)[:n]),
             ("Pregunta dos", "seleccion_unica", (dos + dos)[:n]))
    assert [x["titulo"] for x in s] == ["Género", "Pregunta cuatro", "Pregunta tres"]  # máximo 3; "Pregunta dos" queda fuera
    assert [x["n_grupos"] for x in s] == [2, 4, 3]


def test_segmentos_se_excluyen_por_mas_de_15_grupos_menos_de_2_suficientes_y_menos_de_la_mitad():
    n = 60
    quince = [f"g{i % 15}" for i in range(n)]  # 15 grupos de 4: sin 2 grupos con 10, no entra
    assert _seg(("A", "seleccion_unica", quince)) == []
    quince_ok = [f"g{i % 15}" for i in range(15 * 10)]  # 15 grupos de 10: justo en el borde, entra
    assert _seg(("A", "seleccion_unica", quince_ok))[0]["n_grupos"] == 15
    dieciseis = [f"g{i % 16}" for i in range(16 * 10)]  # 16 grupos: se pasa
    assert _seg(("A", "seleccion_unica", dieciseis)) == []
    assert _seg(("A", "seleccion_unica", ["x"] * 40)) == []  # un solo grupo
    assert _seg(("A", "seleccion_unica", ["x"] * 20 + ["y"] * 9 + ["z"] * 9)) == []  # solo 1 grupo con >= 10
    assert _seg(("A", "seleccion_unica", ["x"] * 10 + ["y"] * 10)) != []  # 10 es suficiente
    # responden 19 de 40 (menos de la mitad) -> fuera; 20 de 40 -> dentro
    assert _seg(("A", "seleccion_unica", ["x"] * 10 + ["y"] * 9 + [None] * 21)) == []
    assert len(_seg(("A", "seleccion_unica", ["x"] * 10 + ["y"] * 10 + [None] * 20))) == 1


def test_segmento_numerica_se_agrupa_en_tramos_por_defecto():
    edades = ["20"] * 12 + ["30"] * 12 + ["40"] * 12 + ["abc"] * 4
    s = _seg(("Edad", "numerica", edades))
    assert s == [{"pregunta_id": "q_1", "titulo": "Edad", "n_grupos": 3,
                  "motivo": "Separa a las personas en 3 grupos con datos suficientes."}]


def test_segmentos_ignora_tipos_que_no_separan():
    assert _seg(("P", "escala", ["1"] * 20 + ["2"] * 20), ("Q", "abierta", ["a"] * 20 + ["b"] * 20)) == []


# ---------- cruces (T-035) ----------

def _cruces(*cols):
    return recomendar(_proyecto(*cols))["cruces"]


def test_cruces_forma_y_motivo():
    c = _cruces(("Género", "segmento", ["F"] * 20 + ["M"] * 20), ("Qué tan satisfecho estás", "escala", ["3"] * 40))
    assert c == [{"por": "q_1", "por_titulo": "Género", "ver": "q_2", "ver_titulo": "Qué tan satisfecho estás",
                  "motivo": "Compara «Qué tan satisfecho estás» entre los grupos de «Género»."}]


def test_cruces_orden_por_pregunta_luego_segmento_maximo_5_y_considera_mas_de_3_segmentos():
    dos = ["a", "b"] * 20
    cols = [(f"Seg {i}", "seleccion_unica", dos) for i in range(1, 5)] + [("Esc A", "escala", ["3"] * 40), ("Nps B", "nps", ["9"] * 40),
                                                                         ("Esc C", "escala", ["2"] * 40)]
    r = recomendar(_proyecto(*cols))
    assert len(r["segmentos"]) == 3  # sin cambios
    # 4 segmentos (no solo los 3 primeros): la primera escala con los 4 y luego el NPS con el primero
    assert [(c["ver_titulo"], c["por_titulo"]) for c in r["cruces"]] == [
        ("Esc A", "Seg 1"), ("Esc A", "Seg 2"), ("Esc A", "Seg 3"), ("Esc A", "Seg 4"), ("Nps B", "Seg 1")]


def test_cruces_recorta_titulos_largos_en_el_motivo_pero_no_en_los_campos():
    largo = "x" * 61
    c = _cruces((largo, "segmento", ["F"] * 20 + ["M"] * 20), ("y" * 60, "escala", ["3"] * 40))[0]
    assert c["por_titulo"] == largo and c["ver_titulo"] == "y" * 60
    assert c["motivo"] == f"Compara «{'y' * 60}» entre los grupos de «{'x' * 60}…»."


def test_cruces_vacio_sin_escalas_ni_nps_o_sin_segmentos():
    assert _cruces(("Género", "segmento", ["F"] * 20 + ["M"] * 20), ("Color", "seleccion_unica", ["a"] * 40)) == []
    assert _cruces(("Nota", "escala", ["3"] * 40)) == []


# ---------- plantilla ----------

def _tpl(*titulos, abierta=True, **kw):
    cols = [(t, "seleccion_unica", ["a"] * 30) for t in titulos]
    if abierta:
        cols.append(("Comentario", "abierta", [f"texto {i}" for i in range(30)]))
    return recomendar(_proyecto(*cols, **kw))["plantilla"]


def test_plantilla_docente_con_profesor_y_clase():
    t = _tpl("¿Cómo evalúa al profesor?", "¿Qué opina de las clases?")
    assert t == {"key": "evaluacion_docente_cna", "nombre": "Evaluación Docente (marco CNA)", "industria": "Educación Superior",
                 "motivo": "La encuesta menciona «profesor» y «clase»."}


def test_plantilla_despacho_con_despacho_y_pedido():
    t = _tpl("Despacho a domicilio", "¿Llegó bien tu pedido?")
    assert t["key"] == "retail_despacho_ecommerce"
    assert t["motivo"] == "La encuesta menciona «despacho», «pedido» y «domicilio»."


def test_plantilla_busca_en_nombre_y_marco_y_sin_tildes_ni_mayusculas():
    t = _tpl("Hola", name="Encuesta de CLIMA", marco="El LIDERAZGO de las jefaturas")
    assert t["key"] == "clima_organizacional"


def test_plantilla_raiz_al_inicio_de_palabra_no_en_medio():
    assert _tpl("Reprofesorado", "Subclase") is None  # "profesor" y "clase" dentro de otra palabra no cuentan
    assert _tpl("Profesores", "Clases")["key"] == "evaluacion_docente_cna"


def test_plantilla_null_sin_abiertas_con_una_sola_coincidencia_o_con_marco_de_plantilla():
    assert _tpl("¿Cómo evalúa al profesor?", "¿Qué opina de las clases?", abierta=False) is None
    assert _tpl("¿Cómo evalúa al profesor?", "Otra cosa") is None  # 1 coincidencia
    marco = FRAMEWORK_TEMPLATES["clima_organizacional"]["marco_teorico"]
    assert _tpl("¿Cómo evalúa al profesor?", "¿Qué opina de las clases?", marco=marco) is None
    assert _tpl("¿Cómo evalúa al profesor?", "¿Qué opina de las clases?", marco="Mi marco propio") is not None


def test_plantilla_en_empate_gana_la_primera():
    # "estudiante" y "alumno" (satisfaccion_estudiantil) contra "profesor" y "clase" (docente): empate 2-2, gana la primera del orden
    t = _tpl("profesor", "clase", "estudiante", "alumno")
    assert t["key"] == "evaluacion_docente_cna"


def test_plantilla_gana_la_de_mas_coincidencias():
    t = _tpl("profesor", "clase", "docente")
    assert t["key"] == "evaluacion_docente_cna" and t["motivo"].count("«") == 3
    assert _tpl("estudiante", "alumno", "campus", "profesor", "clase")["key"] == "satisfaccion_estudiantil"


# ---------- endpoint ----------

@pytest.fixture(scope="module")
def env():
    c = TestClient(app)
    r = c.post("/auth/signup", json={"email": "reco@x.cl", "password": "clave12345"})
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    csv = "id_respuesta,Género,Opinión sobre la clase del profesor\n" + "\n".join(
        f"E{i:03d},{'F' if i % 2 else 'M'},Me gustó la clase del profesor {i}" for i in range(24))
    pid = c.post("/api/projects", headers=h, data={"name": "Docentes"},
                 files={"file": ("e.csv", io.BytesIO(csv.encode()), "text/csv")}).json()["id"]
    return c, h, pid


def test_endpoint_devuelve_la_forma_del_contrato_y_no_escribe(env):
    c, h, pid = env
    db = get_db()
    antes = (db.audit_events.count_documents({"project_id": pid}), db.projects.find_one({"id": pid}))
    r = c.get(f"/api/projects/{pid}/recommendations", headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"alertas", "segmentos", "cruces", "plantilla"}
    assert _ids(body["alertas"]) == ["pocas_respuestas_30"]
    assert [s["titulo"] for s in body["segmentos"]] == ["Género"]
    assert body["plantilla"]["key"] == "evaluacion_docente_cna"
    assert (db.audit_events.count_documents({"project_id": pid}), db.projects.find_one({"id": pid})) == antes


def test_endpoint_sin_sesion_401_y_proyecto_inexistente_404(env):
    c, h, pid = env
    assert c.get(f"/api/projects/{pid}/recommendations").status_code == 401
    r = c.get("/api/projects/no_existe/recommendations", headers=h)
    assert r.status_code == 404 and r.json()["detail"] == "Proyecto no encontrado"
