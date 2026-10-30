"""RF-03 (T-006): permisos por rol verificados en el backend.

`PERMISOS` declara el rol mínimo de cada operación bajo /api/ (salvo /api/admin/*).
Si alguien agrega una ruta nueva, `test_toda_ruta_api_tiene_permiso_declarado` falla
hasta que se declare aquí. mongomock e IA simulada: ninguna llamada a Anthropic.
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
from app.auth import create_token, hash_password  # noqa: E402
from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User, user_to_doc  # noqa: E402
from app.services import thematic  # noqa: E402

P = "/api/projects/{project_id}"
CAT = P + "/categories/{category_id}"
CSV = "id_respuesta,respuesta\n" + "\n".join(f"E{i:03d},El curso fue bueno ({i})" for i in range(1, 6))


def _file():
    return {"data": {"name": "Nuevo"}, "files": {"file": ("n.csv", io.BytesIO(CSV.encode()), "text/csv")}}


# (método, ruta, rol mínimo, argumentos válidos de la petición como función)
OPS = [
    ("GET", "/api/projects", "lector", dict),
    ("GET", P, "lector", dict),
    ("GET", P + "/responses", "lector", dict),
    ("GET", P + "/lexical", "lector", dict),
    ("GET", P + "/codify/progress", "lector", dict),
    ("GET", P + "/summary", "lector", dict),
    ("GET", P + "/audit", "lector", dict),
    ("GET", P + "/report", "lector", dict),
    ("GET", P + "/report/progress", "lector", dict),
    ("GET", P + "/usage", "lector", dict),
    ("GET", "/api/framework-templates", "lector", dict),
    ("GET", P + "/export/traceability", "lector", dict),
    ("GET", P + "/export/pdf", "lector", dict),
    ("GET", P + "/export/docx", "lector", dict),
    ("GET", P + "/export/csv", "lector", dict),
    ("GET", P + "/export/xlsx", "lector", dict),
    ("POST", CAT + "/comments", "lector", lambda: {"json": {"text": "hola"}}),
    ("DELETE", CAT + "/comments/{comment_id}", "lector", dict),  # el lector solo borra los suyos
    ("POST", "/api/projects", "analista", _file),
    ("POST", "/api/projects/from-qualtrics", "analista", lambda: {"json": {"name": "Q", "survey_id": "SV_1"}}),
    ("POST", "/api/projects/from-google-forms", "analista", lambda: {"json": {"name": "G", "sheet_url": "https://x"}}),
    ("POST", "/api/projects/import-legacy", "analista", dict),
    ("POST", P + "/apply-template", "analista", lambda: {"params": {"template": "evaluacion_docente_cna"}}),
    ("POST", P + "/lexical", "analista", dict),
    ("POST", P + "/categories/propose", "analista", dict),
    ("POST", P + "/categories", "analista", lambda: {"json": {"nombre": "Intrusa"}}),
    ("PATCH", CAT, "analista", lambda: {"json": {"nombre": "Hackeada"}}),
    ("POST", P + "/codify", "analista", dict),
    ("PUT", P + "/responses/{response_id}/codings", "analista", lambda: {"json": {"category_ids": ["SIN_CATEGORIA"]}}),
    ("POST", P + "/report", "analista", dict),
    ("DELETE", P, "analista", dict),
    ("GET", "/api/integrations/qualtrics/credentials", "analista", dict),
    ("PUT", "/api/integrations/qualtrics/credentials", "analista", lambda: {"json": {"api_token": "t", "datacenter": "d"}}),
    ("DELETE", "/api/integrations/qualtrics/credentials", "analista", dict),
    ("GET", "/api/integrations/qualtrics/surveys", "analista", dict),
]
PERMISOS = {(m, p): rol for m, p, rol, _ in OPS}
ANALISTA = [o for o in OPS if o[2] == "analista"]
LECTOR = [o for o in OPS if o[2] == "lector" and o[:2] != ("DELETE", CAT + "/comments/{comment_id}")]  # ese se prueba aparte
ID = lambda o: f"{o[0]} {o[1]}"  # noqa: E731


@pytest.fixture(scope="module")
def env():
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

    def miembro(org_id, rol, email):
        u = User(id=f"usr_{rol[:3]}{abs(hash(email)) % 10**6}", email=email, password_hash=hash_password("clave12345"),
                 nombre=rol.capitalize(), empresa="", created_at=store.now_iso(), org_id=org_id, rol=rol)
        get_db().users.insert_one(user_to_doc(u))
        return u, {"Authorization": f"Bearer {create_token(u.id)}"}

    orgs, admins = {}, {}
    for who in ("a", "b"):
        r = c.post("/auth/signup", json={"email": f"perm-{who}@x.cl", "password": "clave12345"})
        admins[who] = {"Authorization": f"Bearer {r.json()['token']}"}
        orgs[who] = r.json()["user"]["organizacion"]["id"]
    ha = admins["a"]
    lector, hl = miembro(orgs["a"], "lector", "perm-lector@x.cl")
    analista, hn = miembro(orgs["a"], "analista", "perm-analista@x.cl")
    _, hl_otra = miembro(orgs["b"], "lector", "perm-lector-b@x.cl")
    raro, hr = miembro(orgs["a"], "superusuario", "perm-raro@x.cl")  # rol desconocido

    pid = c.post("/api/projects", headers=ha, data={"name": "Proyecto de A"},
                 files={"file": ("demo.csv", io.BytesIO(CSV.encode()), "text/csv")}).json()["id"]
    cid = c.post(f"/api/projects/{pid}/categories", headers=ha, json={"nombre": "Docencia"}).json()["id"]
    com = c.post(f"/api/projects/{pid}/categories/{cid}/comments", headers=ha, json={"text": "nota"}).json()["id"]
    c.post(f"/api/projects/{pid}/lexical", headers=ha)
    store.set_project_field(pid, orgs["a"], "qualitative_report", "# Informe de A")
    ai_calls.clear()

    yield {"c": c, "ha": ha, "hl": hl, "hn": hn, "hr": hr, "hl_otra": hl_otra, "lector": lector, "analista": analista,
           "org": orgs["a"], "ai_calls": ai_calls,
           "ids": {"project_id": pid, "category_id": cid, "comment_id": com, "response_id": "E001"}}
    mp.undo()


def _snapshot(e):
    return (store.get_project(e["ids"]["project_id"], e["org"]),
            get_db().audit_events.count_documents({"project_id": e["ids"]["project_id"]}))


def _call(e, op, headers, ids=None):
    m, p, _, kw = op
    return e["c"].request(m, p.format(**(ids or e["ids"])), headers=headers, **kw())


def test_toda_ruta_api_tiene_permiso_declarado():
    # Se lee de OpenAPI: en esta versión de FastAPI app.routes agrupa los routers y no expone cada ruta.
    declared = {(m.upper(), p) for p, ops in app.openapi()["paths"].items()
                if p.startswith("/api/") and not p.startswith("/api/admin/") for m in ops}
    assert len(declared) > 30  # evita que la prueba pase vacía
    assert declared - set(PERMISOS) == set(), f"rutas /api/ sin rol declarado en PERMISOS: {sorted(declared - set(PERMISOS))}"
    assert set(PERMISOS) - declared == set(), "PERMISOS declara rutas que ya no existen"


@pytest.mark.parametrize("op", ANALISTA, ids=map(ID, ANALISTA))
def test_lector_recibe_403_en_operaciones_de_analista(env, op):
    antes, n_proyectos = _snapshot(env), get_db().projects.count_documents({})
    r = _call(env, op, env["hl"])
    assert r.status_code == 403 and r.json()["detail"] == "Tu rol (Lector) no permite esta acción.", r.text[:200]
    assert _snapshot(env) == antes and get_db().projects.count_documents({}) == n_proyectos
    assert env["ai_calls"] == []
    assert env["lector"].org_id == env["org"]  # es de la misma organización: el 403 es por rol, no por tenant


@pytest.mark.parametrize("op", LECTOR, ids=map(ID, LECTOR))
def test_lector_puede_ver_descargar_y_comentar(env, op):
    r = _call(env, op, env["hl"])
    assert r.status_code != 403 and r.status_code < 500, r.text[:200]


def test_rol_desconocido_se_trata_como_lector(env):
    op = next(o for o in OPS if o[:2] == ("POST", P + "/codify"))
    r = _call(env, op, env["hr"])
    assert r.status_code == 403 and r.json()["detail"] == "Tu rol (Lector) no permite esta acción."


def test_analista_crea_analiza_y_borra_proyectos(env):
    c, h = env["c"], env["hn"]
    r = c.post("/api/projects", headers=h, **_file())
    assert r.status_code == 200, r.text
    pid = r.json()["id"]
    assert c.post(f"/api/projects/{pid}/categories", headers=h, json={"nombre": "X"}).status_code == 200
    assert c.post(f"/api/projects/{pid}/lexical", headers=h).status_code == 200
    assert c.delete(f"/api/projects/{pid}", headers=h).status_code == 200
    # un analista de la misma organización ve el proyecto del admin
    assert c.get(f"/api/projects/{env['ids']['project_id']}", headers=h).status_code == 200


def test_orden_401_403_404(env):
    c, ids = env["c"], {**env["ids"], "project_id": "proy_inexistente"}
    for op in OPS:
        if "{project_id}" not in op[1] or op[2] != "analista":
            continue
        assert _call(env, op, {}, ids).status_code == 401, ID(op)  # sin sesión
        r = _call(env, op, env["hl"], ids)  # rol insuficiente: 403 aunque el proyecto no exista
        assert r.status_code == 403 and r.json()["detail"] == "Tu rol (Lector) no permite esta acción.", ID(op)
        r = _call(env, op, env["hn"], ids)  # rol suficiente: ahora sí 404
        assert r.status_code == 404 and r.json()["detail"] == "Proyecto no encontrado", (ID(op), r.text[:100])


def test_lector_de_otra_organizacion(env):
    h = env["hl_otra"]
    deleted = next(o for o in OPS if o[:2] == ("DELETE", P))
    assert _call(env, deleted, h).status_code == 403  # rol primero
    lectura = next(o for o in OPS if o[:2] == ("GET", P))
    r = _call(env, lectura, h)  # y no se revela el proyecto ajeno
    assert r.status_code == 404 and r.json()["detail"] == "Proyecto no encontrado"


def test_comentarios_lector_solo_borra_los_suyos(env):
    c, ids, hl, hn = env["c"], env["ids"], env["hl"], env["hn"]
    base = f"/api/projects/{ids['project_id']}/categories/{ids['category_id']}/comments"
    suyo = c.post(base, headers=hl, json={"text": "del lector"}).json()
    assert suyo["author_id"] == env["lector"].id
    assert c.post(base, headers=hn, json={"text": "del analista"}).json()["author_id"] == env["analista"].id

    ajeno = c.delete(f"{base}/{ids['comment_id']}", headers=hl)
    assert ajeno.status_code == 403 and ajeno.json()["detail"] == "Solo puedes borrar tus propios comentarios."
    assert c.delete(f"{base}/{suyo['id']}", headers=hl).status_code == 200
    assert c.delete(f"{base}/com_inexistente", headers=hl).status_code == 404

    # comentario antiguo (sin author_id): el lector no puede borrarlo, el analista sí
    viejo = {"id": store.new_id("com"), "text": "antiguo", "author": "Ana", "timestamp": store.now_iso()}
    store.push_comment(ids["project_id"], env["org"], ids["category_id"], viejo)
    assert c.delete(f"{base}/{viejo['id']}", headers=hl).status_code == 403
    assert c.delete(f"{base}/{viejo['id']}", headers=hn).status_code == 200
    assert c.delete(f"{base}/{ids['comment_id']}", headers=hn).status_code == 200  # el del admin, siendo analista
