"""RF-10 (T-046): perfil de organización (nombre, rubro, color) y logo.

mongomock; ninguna llamada a Anthropic.
"""
from __future__ import annotations

import base64
import io
import os
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

from app import store  # noqa: E402
from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402

c = TestClient(app, raise_server_exceptions=False)
PNG = b"\x89PNG\r\n\x1a\n" + b"1" * 50
JPG = b"\xff\xd8\xff\xe0" + b"2" * 50
ROL = "Tu rol (%s) no permite esta acción."
COLOR_MSG = "El color debe tener el formato #RRGGBB, por ejemplo #1F6FEB."
NOMBRE_MSG = "Escribe el nombre de la organización."


def H(token):
    return {"Authorization": f"Bearer {token}"}


def nuevo_admin(empresa="Org"):
    email = f"adm-{uuid.uuid4().hex[:8]}@x.cl"
    r = c.post("/auth/signup", json={"email": email, "password": "clave12345", "empresa": empresa}).json()
    return {"h": H(r["token"]), "org": r["user"]["organizacion"]["id"]}


def miembro(a, rol):
    email = f"m-{uuid.uuid4().hex[:8]}@x.cl"
    m = c.post("/api/org/members", headers=a["h"], json={"email": email, "rol": rol}).json()
    h = H(c.post("/auth/login", json={"email": email, "password": m["password_temporal"]}).json()["token"])
    assert c.post("/auth/change-password", headers=h,
                  json={"password_actual": m["password_temporal"], "password_nueva": "clave12345"}).status_code == 200
    return h


def subir(h, datos, nombre="logo.png", tipo="image/png"):
    return c.put("/api/org/logo", headers=h, files={"file": (nombre, io.BytesIO(datos), tipo)})


def eventos(org, accion):
    return list(get_db().audit_events.find({"org_id": org, "action": accion}))


def test_organizacion_vieja_sale_con_null_y_sin_logo():
    a = nuevo_admin("Vieja")
    get_db().organizations.update_one({"_id": a["org"]}, {"$unset": {"rubro": "", "color": ""}})
    org = c.get("/auth/me", headers=a["h"]).json()["organizacion"]
    assert org == {"id": a["org"], "nombre": "Vieja", "rubro": None, "color": None, "tiene_logo": False}


def test_admin_edita_perfil_y_me_lo_refleja():
    a = nuevo_admin("Antes ")
    r = c.put("/api/org/profile", headers=a["h"], json={"nombre": "  Universidad del Sur ", "rubro": "Educación Superior",
                                                        "color": "#1F6FEB"})
    esperado = {"id": a["org"], "nombre": "Universidad del Sur", "rubro": "Educación Superior", "color": "#1f6feb",
                "tiene_logo": False}
    assert r.status_code == 200 and r.json() == esperado
    assert c.get("/auth/me", headers=a["h"]).json()["organizacion"] == esperado
    # reemplaza los tres campos: rubro y color null los borran
    r = c.put("/api/org/profile", headers=a["h"], json={"nombre": "Universidad del Sur"})
    assert r.json()["rubro"] is None and r.json()["color"] is None


def test_login_devuelve_el_perfil():
    email = f"lg-{uuid.uuid4().hex[:8]}@x.cl"
    r = c.post("/auth/signup", json={"email": email, "password": "clave12345", "empresa": "Org"}).json()
    assert r["user"]["organizacion"]["tiene_logo"] is False  # signup ya trae los campos nuevos
    h = H(r["token"])
    c.put("/api/org/profile", headers=h, json={"nombre": "Org", "rubro": "Retail", "color": "#000000"})
    org = c.post("/auth/login", json={"email": email, "password": "clave12345"}).json()["user"]["organizacion"]
    assert org["rubro"] == "Retail" and org["color"] == "#000000" and org["tiene_logo"] is False


@pytest.mark.parametrize("body,msg", [
    ({"nombre": "   "}, NOMBRE_MSG),
    ({}, NOMBRE_MSG),
    ({"nombre": "x" * 101}, "El nombre puede tener hasta 100 caracteres."),
    ({"nombre": "Ok", "rubro": "Astrología"}, "Elige un rubro de la lista."),
    ({"nombre": "Ok", "color": "azul"}, COLOR_MSG),
    ({"nombre": "Ok", "color": "#12345"}, COLOR_MSG),
    ({"nombre": "Ok", "color": "#12345g"}, COLOR_MSG),
])
def test_perfil_422_con_mensaje_exacto(body, msg):
    a = nuevo_admin()
    antes = c.get("/auth/me", headers=a["h"]).json()["organizacion"]
    r = c.put("/api/org/profile", headers=a["h"], json=body)
    assert r.status_code == 422 and r.json()["detail"] == msg
    assert c.get("/auth/me", headers=a["h"]).json()["organizacion"] == antes
    assert eventos(a["org"], "organizacion_editada") == []


def test_nombre_de_100_caracteres_se_acepta():
    a = nuevo_admin()
    assert c.put("/api/org/profile", headers=a["h"], json={"nombre": "x" * 100}).status_code == 200


def test_auditoria_solo_campos_cambiados_y_nada_sin_cambios():
    a = nuevo_admin("Org")
    body = {"nombre": "Org", "rubro": "Salud", "color": "#AABBCC"}
    c.put("/api/org/profile", headers=a["h"], json=body)
    ev = eventos(a["org"], "organizacion_editada")
    assert len(ev) == 1 and ev[0]["detail"] == {"rubro": {"antes": None, "despues": "Salud"},
                                                "color": {"antes": None, "despues": "#aabbcc"}}
    c.put("/api/org/profile", headers=a["h"], json={**body, "color": "#aabbcc"})  # igual, otra capitalización
    assert len(eventos(a["org"], "organizacion_editada")) == 1


@pytest.mark.parametrize("rol", ["analista", "lector"])
def test_no_admin_recibe_403_y_nada_cambia(rol):
    a = nuevo_admin("Org")
    h = miembro(a, rol)
    msg = ROL % rol.capitalize()
    for r in (c.put("/api/org/profile", headers=h, json={"nombre": "Hack"}), subir(h, PNG),
              c.delete("/api/org/logo", headers=h)):
        assert r.status_code == 403 and r.json()["detail"] == msg
    assert c.get("/auth/me", headers=a["h"]).json()["organizacion"]["nombre"] == "Org"
    assert not store.get_org_logo(a["org"])
    assert c.get("/api/org/logo", headers=h).status_code == 404  # leer sí se permite (aquí no hay logo)


def test_sin_sesion_401():
    assert c.put("/api/org/profile", json={"nombre": "x"}).status_code == 401
    assert c.get("/api/org/logo").status_code == 401
    assert c.delete("/api/org/logo").status_code == 401


@pytest.mark.parametrize("datos,nombre,tipo", [(PNG, "a.png", "image/png"), (JPG, "a.jpg", "image/jpeg"),
                                               (JPG, "a.png", "image/png")])  # el tipo lo dicen los bytes
def test_logo_png_y_jpg_se_aceptan(datos, nombre, tipo):
    a = nuevo_admin()
    r = subir(a["h"], datos, nombre, tipo)
    esperado = "image/png" if datos is PNG else "image/jpeg"
    assert r.status_code == 200 and r.json()["tiene_logo"] is True
    logo = c.get("/api/org/logo", headers=a["h"]).json()["logo"]
    assert logo == f"data:{esperado};base64,{base64.b64encode(datos).decode()}"
    assert eventos(a["org"], "logo_actualizado")[-1]["detail"] == {"tipo": esperado, "bytes": len(datos)}
    assert c.get("/auth/me", headers=a["h"]).json()["organizacion"]["tiene_logo"] is True


@pytest.mark.parametrize("datos,nombre,tipo", [
    (b"", "v.png", "image/png"),
    (b"<svg xmlns='http://www.w3.org/2000/svg'></svg>", "l.svg", "image/svg+xml"),
    (b"GIF89a" + b"0" * 20, "l.gif", "image/gif"),
    (b"hola, esto es texto", "l.png", "image/png"),
    (b"%PDF-1.4 ...", "l.png", "image/png"),
])
def test_logo_no_valido_422(datos, nombre, tipo):
    a = nuevo_admin()
    r = subir(a["h"], datos, nombre, tipo)
    assert r.status_code == 422 and r.json()["detail"] == "El logo debe ser una imagen PNG o JPG."
    assert not store.get_org_logo(a["org"]) and eventos(a["org"], "logo_actualizado") == []


def test_logo_limite_de_500_kb():
    a = nuevo_admin()
    r = subir(a["h"], PNG + b"0" * (512_001 - len(PNG)))
    assert r.status_code == 422 and r.json()["detail"] == "El logo pesa más de 500 KB. Usa una imagen más liviana."
    assert not store.get_org_logo(a["org"])
    assert subir(a["h"], PNG + b"0" * (512_000 - len(PNG))).status_code == 200


def test_reemplazar_y_quitar_logo():
    a = nuevo_admin()
    assert c.get("/api/org/logo", headers=a["h"]).json() == {"detail": "Tu organización no tiene logo."}
    assert c.delete("/api/org/logo", headers=a["h"]).json()["tiene_logo"] is False  # sin logo: 200 y sin evento
    assert eventos(a["org"], "logo_eliminado") == []
    subir(a["h"], PNG)
    subir(a["h"], JPG, "b.jpg", "image/jpeg")  # reemplaza
    assert get_db().org_logos.count_documents({"_id": a["org"]}) == 1
    assert c.get("/api/org/logo", headers=a["h"]).json()["logo"].startswith("data:image/jpeg;base64,")
    r = c.delete("/api/org/logo", headers=a["h"])
    assert r.status_code == 200 and r.json()["tiene_logo"] is False
    ev = eventos(a["org"], "logo_eliminado")
    assert len(ev) == 1 and ev[0]["detail"] == {}
    r = c.get("/api/org/logo", headers=a["h"])
    assert r.status_code == 404 and r.json()["detail"] == "Tu organización no tiene logo."


def test_el_lector_ve_el_logo_de_su_organizacion():
    a = nuevo_admin()
    subir(a["h"], PNG)
    h = miembro(a, "lector")
    assert c.get("/api/org/logo", headers=h).json()["logo"].startswith("data:image/png;base64,")
    assert c.get("/auth/me", headers=h).json()["organizacion"]["tiene_logo"] is True


def test_aislamiento_entre_organizaciones():
    a, b = nuevo_admin("Org A"), nuevo_admin("Org B")
    c.put("/api/org/profile", headers=a["h"], json={"nombre": "Secreta A", "rubro": "Salud", "color": "#111111"})
    subir(a["h"], PNG)
    ob = c.get("/auth/me", headers=b["h"]).json()["organizacion"]
    assert ob == {"id": b["org"], "nombre": "Org B", "rubro": None, "color": None, "tiene_logo": False}
    assert c.get("/api/org/logo", headers=b["h"]).status_code == 404
    # los cambios de B no tocan A
    c.put("/api/org/profile", headers=b["h"], json={"nombre": "Org B 2", "rubro": "Retail", "color": "#222222"})
    subir(b["h"], JPG, "b.jpg", "image/jpeg")
    c.delete("/api/org/logo", headers=b["h"])
    oa = c.get("/auth/me", headers=a["h"]).json()["organizacion"]
    assert oa == {"id": a["org"], "nombre": "Secreta A", "rubro": "Salud", "color": "#111111", "tiene_logo": True}
    assert c.get("/api/org/logo", headers=a["h"]).json()["logo"].startswith("data:image/png;base64,")
    assert eventos(a["org"], "logo_eliminado") == [] and eventos(b["org"], "logo_eliminado") != []
