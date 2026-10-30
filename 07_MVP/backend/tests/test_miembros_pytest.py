"""RF-03 (T-007): gestión de miembros, contraseña temporal y cuentas desactivadas.

mongomock; ninguna llamada a Anthropic.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import uuid
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

c = TestClient(app, raise_server_exceptions=False)
CSV = "id_respuesta,respuesta\nE001,Muy bueno\nE002,Regular\n"
FORMATO = re.compile(r"^[a-km-np-zA-HJ-NP-Z2-9]{4}(-[a-km-np-zA-HJ-NP-Z2-9]{4}){2}$")  # sin 0 O o 1 l I
DESACTIVADA = "Tu cuenta fue desactivada. Contacta al administrador de tu organización."
PENDIENTE = "Debes cambiar tu contraseña temporal antes de continuar."


def H(token):
    return {"Authorization": f"Bearer {token}"}


def archivo():
    return {"file": ("d.csv", io.BytesIO(CSV.encode()), "text/csv")}


def nuevo_admin():
    email = f"adm-{uuid.uuid4().hex[:8]}@x.cl"
    r = c.post("/auth/signup", json={"email": email, "password": "clave12345", "empresa": "Org"}).json()
    return {"h": H(r["token"]), "id": r["user"]["id"], "email": email, "org": r["user"]["organizacion"]["id"]}


def crear(a, rol, nombre="Luis"):
    email = f"m-{uuid.uuid4().hex[:8]}@x.cl"
    r = c.post("/api/org/members", headers=a["h"], json={"email": email, "nombre": nombre, "rol": rol})
    assert r.status_code == 201, r.text
    return r.json()["member"], r.json()["password_temporal"]


def login(email, password):
    return c.post("/auth/login", json={"email": email, "password": password})


def cambiar(h, actual, nueva):
    return c.post("/auth/change-password", headers=h, json={"password_actual": actual, "password_nueva": nueva})


def miembro_activo(a, rol, clave="clave12345"):
    """Miembro que ya cambió su contraseña temporal: (member, headers)."""
    m, temp = crear(a, rol)
    h = H(login(m["email"], temp).json()["token"])
    assert cambiar(h, temp, clave).status_code == 200
    return m, h


def patch(a, user_id, **cuerpo):
    return c.patch(f"/api/org/members/{user_id}", headers=a["h"], json=cuerpo)


def test_admin_crea_lector_y_este_entra_con_la_temporal():
    a = nuevo_admin()
    r = c.post("/api/org/members", headers=a["h"], json={"email": "Luis@Udp.cl", "nombre": " Luis ", "rol": "lector"})
    assert r.status_code == 201
    m, temp = r.json()["member"], r.json()["password_temporal"]
    assert FORMATO.match(temp), temp
    assert (m["email"], m["nombre"], m["rol"], m["activo"], m["debe_cambiar_password"]) == ("luis@udp.cl", "Luis", "lector", True, True)
    doc = get_db().users.find_one({"_id": m["id"]})
    assert doc["org_id"] == a["org"] and doc["password_hash"].startswith("pbkdf2$")
    assert temp not in json.dumps(doc, default=str)  # en la base solo existe el hash
    u = login("luis@udp.cl", temp).json()["user"]
    assert u["debe_cambiar_password"] is True and u["rol"] == "lector"
    assert m in c.get("/api/org/members", headers=a["h"]).json()
    assert FORMATO.match(crear(a, "lector")[1])


def test_contrasena_temporal_bloquea_todo_salvo_me_y_cambio():
    a = nuevo_admin()
    pid = c.post("/api/projects", headers=a["h"], data={"name": "P"}, files=archivo()).json()["id"]
    m, temp = crear(a, "lector")
    h = H(login(m["email"], temp).json()["token"])
    r = c.get("/api/projects", headers=h)
    assert r.status_code == 403 and r.json()["detail"] == PENDIENTE
    assert c.get(f"/api/projects/{pid}", headers=h).json()["detail"] == PENDIENTE
    assert c.get("/auth/me", headers=h).json()["debe_cambiar_password"] is True

    # actual incorrecta, nueva corta o igual a la actual: no se cambia nada
    r = cambiar(h, "incorrecta1", "otraClave123")
    assert r.status_code == 400 and r.json()["detail"] == "La contraseña actual no es correcta."
    assert cambiar(h, temp, "corta").status_code == 422
    r = cambiar(h, temp, temp)
    assert r.status_code == 400 and r.json()["detail"] == "La contraseña nueva debe ser distinta de la actual."
    assert c.get("/api/projects", headers=h).status_code == 403

    r = cambiar(h, temp, "miClaveNueva1")
    assert r.status_code == 200 and r.json()["user"]["debe_cambiar_password"] is False
    ps = c.get("/api/projects", headers=h)
    assert ps.status_code == 200 and [p["id"] for p in ps.json()] == [pid]
    assert login(m["email"], temp).status_code == 401 and login(m["email"], "miClaveNueva1").status_code == 200
    assert get_db().users.find_one({"_id": m["id"]})["debe_cambiar_password"] is False


def test_pendiente_bloquea_toda_ruta_protegida_de_la_api():
    """Recorre OpenAPI: ninguna ruta /api/ (salvo /api/admin/*, que va por X-Admin-Password) deja pasar una temporal."""
    a = nuevo_admin()
    m, temp = crear(a, "admin")
    h = H(login(m["email"], temp).json()["token"])
    rutas = [(met.upper(), p) for p, ops in app.openapi()["paths"].items()
             if p.startswith("/api/") and not p.startswith("/api/admin/") for met in ops]
    assert len(rutas) > 30
    for met, p in rutas:
        r = c.request(met, re.sub(r"\{[^}]+\}", "x", p), headers=h)
        assert r.status_code == 403 and r.json()["detail"] == PENDIENTE, (met, p, r.status_code)


@pytest.mark.parametrize("rol", ["analista", "lector"])
def test_solo_admin_gestiona_miembros(rol):
    a = nuevo_admin()
    _, h = miembro_activo(a, rol)
    otro, _ = crear(a, "lector")
    for r in (c.get("/api/org/members", headers=h),
              c.post("/api/org/members", headers=h, json={"email": "z@x.cl", "rol": "lector"}),
              c.patch(f"/api/org/members/{otro['id']}", headers=h, json={"rol": "admin"})):
        assert r.status_code == 403 and r.json()["detail"].startswith("Tu rol ("), r.text
    assert get_db().users.find_one({"email": "z@x.cl"}) is None
    assert get_db().users.find_one({"_id": otro["id"]})["rol"] == "lector"


def test_otra_organizacion_no_ve_ni_modifica_miembros():
    a, b = nuevo_admin(), nuevo_admin()
    m, _ = crear(a, "lector")
    r = patch(b, m["id"], activo=False)
    assert r.status_code == 404 and r.json()["detail"] == "Miembro no encontrado"
    assert get_db().users.find_one({"_id": m["id"]})["activo"] is True
    assert m["id"] not in [x["id"] for x in c.get("/api/org/members", headers=b["h"]).json()]
    assert patch(a, "usr_inexistente", activo=False).status_code == 404


def test_cambio_de_rol_se_refleja_en_los_permisos():
    a = nuevo_admin()
    m, h = miembro_activo(a, "lector")
    assert c.post("/api/projects", headers=h, data={"name": "N"}, files=archivo()).status_code == 403
    r = patch(a, m["id"], rol="analista")
    assert r.status_code == 200 and r.json()["rol"] == "analista"
    # mismo token: el rol se lee de la base en cada petición
    assert c.post("/api/projects", headers=h, data={"name": "N"}, files=archivo()).status_code == 200


def test_validaciones_de_alta_y_cambio():
    a = nuevo_admin()
    m, _ = crear(a, "lector")
    assert c.post("/api/org/members", headers=a["h"], json={"email": "no-es-email", "rol": "lector"}).status_code == 422
    assert c.post("/api/org/members", headers=a["h"], json={"email": "q@x.cl", "rol": "dios"}).status_code == 422
    assert patch(a, m["id"]).status_code == 422
    assert patch(a, m["id"], rol="dios").status_code == 422
    assert get_db().users.find_one({"email": "q@x.cl"}) is None


def test_email_duplicado_da_409_y_no_crea_nada():
    a, b = nuevo_admin(), nuevo_admin()
    m, _ = crear(a, "lector")
    n = get_db().users.count_documents({})
    for admin, email in ((a, m["email"]), (b, m["email"].upper()), (a, a["email"])):
        r = c.post("/api/org/members", headers=admin["h"], json={"email": email, "rol": "lector"})
        assert r.status_code == 409 and r.json()["detail"] == "Ya existe una cuenta con ese email."
    assert get_db().users.count_documents({}) == n


def test_desactivar_y_reactivar():
    a = nuevo_admin()
    m, h = miembro_activo(a, "analista")
    pid = c.post("/api/projects", headers=h, data={"name": "Del analista"}, files=archivo()).json()["id"]
    r = patch(a, m["id"], activo=False)
    assert r.status_code == 200 and r.json()["activo"] is False
    r = login(m["email"], "clave12345")
    assert r.status_code == 401 and r.json()["detail"] == DESACTIVADA
    assert login(m["email"], "incorrecta12").json()["detail"] == "Email o contraseña incorrectos."  # no revela el estado
    for ruta in ("/api/projects", "/auth/me"):  # su token vigente deja de servir
        r = c.get(ruta, headers=h)
        assert r.status_code == 401 and r.json()["detail"] == DESACTIVADA
    assert cambiar(h, "clave12345", "otraClave12").status_code == 401
    # sus proyectos siguen en la organización, con su autoría; y él sigue en la lista
    assert c.get(f"/api/projects/{pid}", headers=a["h"]).status_code == 200
    assert get_db().projects.find_one({"_id": pid})["user_id"] == m["id"]
    assert next(x for x in c.get("/api/org/members", headers=a["h"]).json() if x["id"] == m["id"])["activo"] is False

    assert patch(a, m["id"], activo=True).json()["activo"] is True
    assert login(m["email"], "clave12345").status_code == 200
    assert c.get("/api/projects", headers=h).status_code == 200


def test_desactivado_con_temporal_pendiente_recibe_401_no_403():
    a = nuevo_admin()
    m, temp = crear(a, "lector")
    h = H(login(m["email"], temp).json()["token"])
    patch(a, m["id"], activo=False)
    assert c.get("/api/projects", headers=h).json()["detail"] == DESACTIVADA


def test_la_organizacion_no_queda_sin_admin_activo():
    a = nuevo_admin()
    ultimo = "La organización debe tener al menos un administrador activo."
    for cuerpo in ({"rol": "analista"}, {"activo": False}):
        r = patch(a, a["id"], **cuerpo)
        assert r.status_code == 409 and r.json()["detail"] == ultimo
    assert get_db().users.find_one({"_id": a["id"]})["rol"] == "admin"

    # un segundo admin desactivado no cuenta como respaldo
    otro, _ = miembro_activo(a, "admin")
    patch(a, otro["id"], activo=False)
    assert patch(a, a["id"], rol="analista").status_code == 409
    patch(a, otro["id"], activo=True)

    # con dos admins activos sí se puede quitar el rol o desactivar al otro
    assert patch(a, otro["id"], rol="lector").status_code == 200
    patch(a, otro["id"], rol="admin")
    assert patch(a, otro["id"], activo=False).status_code == 200
    patch(a, otro["id"], activo=True)
    # y a sí mismo no se desactiva, aunque haya otro admin; sí puede dejar de ser admin
    r = patch(a, a["id"], activo=False)
    assert r.status_code == 400 and r.json()["detail"] == "No puedes desactivar tu propia cuenta."
    assert get_db().users.find_one({"_id": a["id"]})["activo"] is True
    assert patch(a, a["id"], rol="analista").status_code == 200


def test_auditoria_de_organizacion_sin_contrasenas():
    a = nuevo_admin()
    m, temp = crear(a, "lector")
    hm = H(login(m["email"], temp).json()["token"])
    cambiar(hm, temp, "miClaveNueva1")
    patch(a, m["id"], rol="analista")
    patch(a, m["id"], activo=False)
    patch(a, m["id"], activo=True)
    patch(a, m["id"], activo=True)  # sin cambio: no audita

    evs = list(get_db().audit_events.find({"org_id": a["org"]}).sort("timestamp", 1))
    assert [(e["action"], e["user_id"]) for e in evs] == [
        ("miembro_creado", a["id"]), ("cambio_password", m["id"]), ("miembro_rol_cambiado", a["id"]),
        ("miembro_desactivado", a["id"]), ("miembro_reactivado", a["id"])]
    assert all(e["project_id"] is None and e["actor"] == "analista" and e["detail"]["email"] == m["email"] for e in evs)
    assert evs[2]["detail"] == {"email": m["email"], "rol_anterior": "lector", "rol": "analista"}
    todo = json.dumps(evs, default=str)
    assert temp not in todo and "miClaveNueva1" not in todo


def test_usuarios_existentes_sin_los_campos_nuevos_siguen_activos():
    a = nuevo_admin()
    get_db().users.update_one({"_id": a["id"]}, {"$unset": {"activo": "", "debe_cambiar_password": ""}})
    r = c.get("/auth/me", headers=a["h"])
    assert r.status_code == 200 and r.json()["debe_cambiar_password"] is False
    assert c.get("/api/projects", headers=a["h"]).status_code == 200
