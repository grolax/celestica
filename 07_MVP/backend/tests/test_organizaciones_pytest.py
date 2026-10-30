"""RF-02 (T-004): organizaciones dueñas de los proyectos y migración desde datos antiguos.
mongomock, sin IA real ni internet."""
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
from scripts.migrate_orgs import migrate  # noqa: E402

c = TestClient(app, raise_server_exceptions=False)
CSV = "id_respuesta,respuesta\nE001,Muy bueno\nE002,Regular\n"


def _signup(email, **extra):
    return c.post("/auth/signup", json={"email": email, "password": "clave12345", **extra})


def _hdr(token):
    return {"Authorization": f"Bearer {token}"}


def _nuevo_proyecto(headers, name="P"):
    r = c.post("/api/projects", headers=headers, data={"name": name},
               files={"file": ("d.csv", io.BytesIO(CSV.encode()), "text/csv")})
    assert r.status_code == 200, r.text
    return r.json()["id"]


@pytest.mark.parametrize("extra,esperado", [
    ({"nombre": "Ana", "empresa": "  UDP  "}, "UDP"),
    ({"nombre": "Beto", "empresa": "  "}, "Organización de Beto"),
    ({}, "Organización de sin-nada@x.cl"),
])
def test_signup_crea_organizacion_con_el_nombre_correcto(extra, esperado):
    email = "sin-nada@x.cl" if not extra else f"{extra['nombre'].lower()}-org@x.cl"
    r = _signup(email, **extra)
    assert r.status_code == 200
    user = r.json()["user"]
    assert user["rol"] == "admin"
    assert user["organizacion"]["nombre"] == esperado
    assert user["organizacion"]["id"].startswith("org_")
    assert get_db().organizations.find_one({"_id": user["organizacion"]["id"]})["nombre"] == esperado
    assert get_db().users.find_one({"_id": user["id"]})["org_id"] == user["organizacion"]["id"]
    # login y me devuelven el mismo objeto user
    login = c.post("/auth/login", json={"email": email, "password": "clave12345"})
    assert login.json()["user"] == user
    assert c.get("/auth/me", headers=_hdr(r.json()["token"])).json() == user


def test_email_duplicado_no_deja_organizacion_huerfana():
    assert _signup("dup@x.cl", empresa="Dup").status_code == 200
    antes = get_db().organizations.count_documents({})
    r = _signup("dup@x.cl", empresa="Otra")
    assert r.status_code == 409
    assert get_db().organizations.count_documents({}) == antes


def test_misma_organizacion_comparte_proyectos_y_otra_recibe_404():
    a = _signup("m1@x.cl", empresa="Compartida").json()
    pid = _nuevo_proyecto(_hdr(a["token"]), "De M1")
    # segundo miembro de la MISMA organización, insertado directo (RF-03 aún no existe)
    get_db().users.insert_one({"_id": "usr_miembro02", "email": "m2@x.cl", "password_hash": hash_password("clave12345"),
                               "nombre": "", "empresa": "", "created_at": "", "integrations": {},
                               "org_id": a["user"]["organizacion"]["id"], "rol": "admin"})
    h2 = _hdr(create_token("usr_miembro02"))
    assert [p["id"] for p in c.get("/api/projects", headers=h2).json()] == [pid]
    r = c.post(f"/api/projects/{pid}/categories", headers=h2, json={"nombre": "Del otro miembro"})
    assert r.status_code == 200
    assert c.get(f"/api/projects/{pid}", headers=_hdr(a["token"])).json()["categories"][0]["nombre"] == "Del otro miembro"
    evs = list(get_db().audit_events.find({"project_id": pid}))
    assert evs and all(e["org_id"] == a["user"]["organizacion"]["id"] for e in evs)  # eventos nuevos llevan org_id
    # "creado por" se conserva como el usuario que lo creó
    assert get_db().projects.find_one({"_id": pid})["user_id"] == a["user"]["id"]
    # un tercero de otra organización no lo ve
    h3 = _hdr(_signup("m3@x.cl", empresa="Ajena").json()["token"])
    assert c.get(f"/api/projects/{pid}", headers=h3).status_code == 404
    assert c.get("/api/projects", headers=h3).json() == []


def _datos_antiguos(db):
    for uid, email, nombre, empresa in [("usr_u1", "u1@x.cl", "Uno", "Misma"), ("usr_u2", "u2@x.cl", "Dos", "Misma"),
                                        ("usr_u3", "u3@x.cl", "", "")]:
        db.users.insert_one({"_id": uid, "email": email, "password_hash": hash_password("clave12345"),
                             "nombre": nombre, "empresa": empresa, "created_at": "", "integrations": {}})
    for pid, uid in [("proj_a", "usr_u1"), ("proj_b", "usr_u2"), ("proj_c", "usr_u2"), ("proj_huerfano", "usr_fantasma")]:
        db.projects.insert_one({"_id": pid, "id": pid, "user_id": uid, "name": pid, "responses": [], "categories": []})
        db.audit_events.insert_one({"_id": f"evt_{pid}", "project_id": pid, "user_id": uid, "actor": "sistema",
                                    "action": "x", "timestamp": "", "detail": {}})


def test_migracion_asigna_organizaciones_cuenta_huerfano_y_es_idempotente():
    db = mongomock.MongoClient().db
    _datos_antiguos(db)
    assert migrate(db) == {"usuarios": 3, "proyectos": 3, "proyectos_huerfanos": 1, "eventos": 3}
    u1, u2, u3 = (db.users.find_one({"_id": i}) for i in ("usr_u1", "usr_u2", "usr_u3"))
    assert len({u1["org_id"], u2["org_id"], u3["org_id"]}) == 3  # misma `empresa` NO une usuarios
    assert all(u["rol"] == "admin" for u in (u1, u2, u3))
    assert db.organizations.find_one({"_id": u1["org_id"]})["nombre"] == "Misma"
    assert db.organizations.find_one({"_id": u3["org_id"]})["nombre"] == "Organización de u3@x.cl"
    assert db.projects.find_one({"_id": "proj_c"})["org_id"] == u2["org_id"]
    assert db.audit_events.find_one({"_id": "evt_proj_b"})["org_id"] == u2["org_id"]
    assert not db.projects.find_one({"_id": "proj_huerfano"})["org_id"]  # inaccesible
    antes = {n: list(db[n].find()) for n in ("users", "projects", "audit_events", "organizations")}
    assert migrate(db) == {"usuarios": 0, "proyectos": 0, "proyectos_huerfanos": 0, "eventos": 0}
    assert antes == {n: list(db[n].find()) for n in antes}


def test_usuario_migrado_inicia_sesion_y_ve_sus_proyectos_de_antes():
    db = get_db()
    db.users.insert_one({"_id": "usr_viejo", "email": "viejo@x.cl", "password_hash": hash_password("clave12345"),
                         "nombre": "Viejo", "empresa": "Antigua", "created_at": "", "integrations": {}})
    p = store._empty_project("Antiguo", "", [], "respuesta", [])
    p["user_id"] = "usr_viejo"  # forma pre-RF-02: sin org_id
    store.save_project(p)
    migrate(db)
    r = c.post("/auth/login", json={"email": "viejo@x.cl", "password": "clave12345"})
    assert r.status_code == 200 and r.json()["user"]["organizacion"]["nombre"] == "Antigua"
    assert [x["id"] for x in c.get("/api/projects", headers=_hdr(r.json()["token"])).json()] == [p["id"]]
