"""Aislamiento multi-tenant (RNF-01): el usuario B no ve ni toca el proyecto de A.

Una prueba por cada ruta con {project_id}. Si alguien agrega una ruta nueva,
`test_toda_ruta_con_project_id_esta_cubierta` falla hasta que se agregue aquí.
IA simulada y mongomock: ninguna llamada a Anthropic ni a internet.
"""
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

from app import store  # noqa: E402
from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.services import thematic  # noqa: E402

TPL = "evaluacion_docente_cna"
# (método, ruta tal como la declara main.py, argumentos válidos de la petición)
ROUTES = [
    ("GET", "/api/projects/{project_id}", {}),
    ("DELETE", "/api/projects/{project_id}", {}),
    ("GET", "/api/projects/{project_id}/responses", {}),
    ("POST", "/api/projects/{project_id}/apply-template", {"params": {"template": TPL}}),
    ("GET", "/api/projects/{project_id}/lexical", {}),
    ("POST", "/api/projects/{project_id}/lexical", {}),
    ("POST", "/api/projects/{project_id}/categories/propose", {}),
    ("POST", "/api/projects/{project_id}/categories", {"json": {"nombre": "Intrusa"}}),
    ("PATCH", "/api/projects/{project_id}/categories/{category_id}", {"json": {"nombre": "Hackeada"}}),
    ("POST", "/api/projects/{project_id}/categories/{category_id}/comments", {"json": {"text": "hola"}}),
    ("DELETE", "/api/projects/{project_id}/categories/{category_id}/comments/{comment_id}", {}),
    ("POST", "/api/projects/{project_id}/codify", {}),
    ("GET", "/api/projects/{project_id}/codify/progress", {}),
    ("PUT", "/api/projects/{project_id}/responses/{response_id}/codings", {"json": {"category_ids": ["SIN_CATEGORIA"]}}),
    ("GET", "/api/projects/{project_id}/summary", {}),
    ("GET", "/api/projects/{project_id}/audit", {}),
    ("GET", "/api/projects/{project_id}/export/traceability", {}),
    ("GET", "/api/projects/{project_id}/export/pdf", {}),
    ("GET", "/api/projects/{project_id}/export/docx", {}),
    ("GET", "/api/projects/{project_id}/export/csv", {}),
    ("GET", "/api/projects/{project_id}/export/xlsx", {}),
    ("POST", "/api/projects/{project_id}/report", {}),
    ("POST", "/api/projects/{project_id}/report", {"params": {"mode": "v1"}}),
    ("GET", "/api/projects/{project_id}/report/progress", {}),
    ("GET", "/api/projects/{project_id}/report", {}),
    ("GET", "/api/projects/{project_id}/usage", {}),
]


@pytest.fixture(scope="module")
def env():
    """Cuentas A y B, un proyecto completo de A, y la IA reemplazada por un doble que anota cada llamada."""
    ai_calls: list[str] = []

    def fake(name, ret):
        def f(*a, **k):
            ai_calls.append(name)
            return ret
        return f

    def no_client():
        ai_calls.append("client")
        raise AssertionError("llamada a la API real de Anthropic")

    mp = pytest.MonkeyPatch()
    mp.setattr(thematic, "propose_categories", fake("propose_categories", []))
    mp.setattr(thematic, "codify_all", fake("codify_all", []))
    mp.setattr(thematic, "interpret_lexical", fake("interpret_lexical", "interpretación simulada"))
    mp.setattr(thematic, "generate_qualitative_report", fake("report_v1", "# Informe"))
    mp.setattr(thematic, "generate_qualitative_report_v2", fake("report_v2", "# Informe"))
    mp.setattr(thematic, "client", no_client)

    c = TestClient(app, raise_server_exceptions=False)
    users = {}
    for who in ("a", "b"):
        r = c.post("/auth/signup", json={"email": f"aisla-{who}@x.cl", "password": "clave12345"})
        users[who] = ({"Authorization": f"Bearer {r.json()['token']}"}, r.json()["user"]["id"])
    ha = users["a"][0]

    csv = "id_respuesta,respuesta\n" + "\n".join(f"E{i:03d},El curso fue bueno ({i})" for i in range(1, 6))
    pid = c.post("/api/projects", headers=ha, data={"name": "Proyecto de A"},
                 files={"file": ("demo.csv", io.BytesIO(csv.encode()), "text/csv")}).json()["id"]
    cid = c.post(f"/api/projects/{pid}/categories", headers=ha, json={"nombre": "Docencia"}).json()["id"]
    com = c.post(f"/api/projects/{pid}/categories/{cid}/comments", headers=ha, json={"text": "nota"}).json()["id"]
    c.put(f"/api/projects/{pid}/responses/E001/codings", headers=ha, json={"category_ids": [cid]})
    c.post(f"/api/projects/{pid}/lexical", headers=ha)
    # Informe ya generado: así GET /report filtrado mal devolvería 200, no el 404 de "aún no generado".
    store.set_project_field(pid, users["a"][1], "qualitative_report", "# Informe de A")
    ai_calls.clear()  # solo interesa lo que ocurra a nombre de B

    yield {"c": c, "hb": users["b"][0], "ha": ha, "uid_a": users["a"][1], "uid_b": users["b"][1],
           "ids": {"project_id": pid, "category_id": cid, "comment_id": com, "response_id": "E001"},
           "ai_calls": ai_calls}
    mp.undo()


def _snapshot(e):
    db = get_db()
    return (store.get_project(e["ids"]["project_id"], e["uid_a"]),
            db.audit_events.count_documents({"project_id": e["ids"]["project_id"]}))


@pytest.mark.parametrize("method,path,kw", ROUTES, ids=[f"{m} {p}" for m, p, _ in ROUTES])
def test_otro_usuario_recibe_404_y_nada_cambia(env, method, path, kw):
    before = _snapshot(env)
    r = env["c"].request(method, path.format(**env["ids"]), headers=env["hb"], **kw)
    # El texto distingue "proyecto ajeno" de otros 404 (categoría, informe o léxico inexistentes).
    assert r.status_code == 404 and r.json()["detail"] == "Proyecto no encontrado", r.text[:200]
    assert _snapshot(env) == before
    assert env["ai_calls"] == []
    # Control: el dueño sí llega al proyecto (la ruta y el cuerpo de la prueba son válidos).
    mine = env["c"].request("GET", "/api/projects/{project_id}".format(**env["ids"]), headers=env["ha"])
    assert mine.status_code == 200


def test_toda_ruta_con_project_id_esta_cubierta():
    declared = {(m, r.path) for r in app.routes if "{project_id}" in getattr(r, "path", "")
                for m in r.methods - {"HEAD", "OPTIONS"}}
    covered = {(m, p) for m, p, _ in ROUTES}
    assert declared - covered == set(), f"rutas con {{project_id}} sin prueba de acceso cruzado: {sorted(declared - covered)}"


def test_listados_de_b_no_incluyen_lo_de_a(env):
    c, hb = env["c"], env["hb"]
    assert c.get("/api/projects", headers=hb).json() == []
    # Aunque B tenga credenciales propias, no ve las de A.
    c.put("/api/integrations/qualtrics/credentials", headers=env["ha"], json={"api_token": "tok-de-a", "datacenter": "dcA"})
    r = c.get("/api/integrations/qualtrics/credentials", headers=hb)
    assert r.json() == {"configured": False, "datacenter": ""}
    assert "tok-de-a" not in r.text and "dcA" not in r.text
