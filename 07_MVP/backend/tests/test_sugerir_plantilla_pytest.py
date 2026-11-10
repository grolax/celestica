"""RF-40 (T-044): POST /api/projects/suggest-template. Misma regla que RF-41, sin IA y sin escribir. mongomock."""
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

URL = "/api/projects/suggest-template"
ABIERTA = {"titulo": "Comentario", "tipo": "abierta"}


def _q(*titulos):
    return [{"titulo": t, "tipo": "seleccion_unica"} for t in titulos]


@pytest.fixture(scope="module")
def env():
    c = TestClient(app)
    r = c.post("/auth/signup", json={"email": "sug-admin@x.cl", "password": "clave12345"})
    org = r.json()["user"]["organizacion"]["id"]
    heads = {"admin": {"Authorization": f"Bearer {r.json()['token']}"}}
    for rol in ("analista", "lector"):
        u = User(id=f"usr_sug_{rol}", email=f"sug-{rol}@x.cl", password_hash=hash_password("clave12345"), nombre=rol,
                 empresa="", created_at=store.now_iso(), org_id=org, rol=rol)
        get_db().users.insert_one(user_to_doc(u))
        heads[rol] = {"Authorization": f"Bearer {create_token(u.id)}"}
    return c, heads


def _sugerir(env, preguntas, rol="analista"):
    c, heads = env
    r = c.post(URL, headers=heads[rol], json={"preguntas": preguntas})
    assert r.status_code == 200, r.text
    return r.json()["plantilla"]


def test_sugiere_con_dos_coincidencias_y_una_abierta(env):
    p = _sugerir(env, _q("¿Cómo evalúa al profesor?", "¿Qué opina de las clases?") + [ABIERTA])
    assert p == {"key": "evaluacion_docente_cna", "nombre": "Evaluación Docente (marco CNA)", "industria": "Educación Superior",
                 "motivo": "La encuesta menciona «profesor» y «clase»."}


def test_coincide_con_recommendations_de_un_proyecto_con_esos_titulos(env):
    c, heads = env
    h = heads["admin"]
    csv = "id_respuesta,Género,Opinión sobre la clase del profesor\n" + "\n".join(
        f"E{i:03d},{'F' if i % 2 else 'M'},Me gustó la clase del profesor {i}" for i in range(24))
    pid = c.post("/api/projects", headers=h, data={"name": "P"},
                 files={"file": ("e.csv", io.BytesIO(csv.encode()), "text/csv")}).json()["id"]
    reco = c.get(f"/api/projects/{pid}/recommendations", headers=h).json()["plantilla"]
    preguntas = [{"titulo": q["titulo"], "tipo": q["tipo"]} for q in c.get(f"/api/projects/{pid}", headers=h).json()["preguntas"]]
    assert reco is not None and _sugerir(env, preguntas) == reco


def test_null_sin_abierta_con_una_coincidencia_y_con_lista_vacia(env):
    docente = _q("¿Cómo evalúa al profesor?", "¿Qué opina de las clases?")
    assert _sugerir(env, docente) is None  # coinciden, pero no hay abierta
    assert _sugerir(env, _q("¿Cómo evalúa al profesor?", "Otra cosa") + [ABIERTA]) is None
    assert _sugerir(env, []) is None


@pytest.mark.parametrize("titulos, key", [
    (("Cliente", "¿Nos recomiendes a un amigo?"), "satisfaccion_clientes_nps"),
    (("Tu compra", "¿Nos recomiendes a un amigo?"), "retail_post_compra_nps"),
])
def test_recomiendes_cuenta_como_coincidencia(env, titulos, key):
    assert _sugerir(env, _q(*titulos) + [ABIERTA])["key"] == key


def test_limites_422(env):
    c, heads = env
    h = heads["analista"]
    assert c.post(URL, headers=h, json={"preguntas": [{"titulo": "x" * 2001, "tipo": "abierta"}]}).status_code == 422
    assert c.post(URL, headers=h, json={"preguntas": [{"titulo": "x" * 2000, "tipo": "abierta"}]}).status_code == 200
    assert c.post(URL, headers=h, json={"preguntas": [ABIERTA] * 1001}).status_code == 422
    assert c.post(URL, headers=h, json={"preguntas": [ABIERTA] * 1000}).status_code == 200
    assert c.post(URL, headers=h, json={}).status_code == 422


def test_roles(env):
    c, heads = env
    body = {"preguntas": []}
    assert c.post(URL, json=body).status_code == 401
    r = c.post(URL, headers=heads["lector"], json=body)
    assert r.status_code == 403 and r.json()["detail"] == "Tu rol (Lector) no permite esta acción."
    assert c.post(URL, headers=heads["analista"], json=body).status_code == 200
    assert c.post(URL, headers=heads["admin"], json=body).status_code == 200


def test_no_escribe_proyectos_ni_auditoria(env):
    db = get_db()
    antes = (db.projects.count_documents({}), db.audit_events.count_documents({}))
    assert _sugerir(env, _q("profesor", "clase") + [ABIERTA]) is not None
    assert (db.projects.count_documents({}), db.audit_events.count_documents({})) == antes
