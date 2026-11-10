"""Miembros (RF-03, T-007) y perfil de la organización (RF-10, T-046). Escribe solo el admin."""
from __future__ import annotations

import base64
import re
import secrets
import uuid
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, EmailStr, model_validator
from pymongo.errors import DuplicateKeyError

from app import store
from app.auth import get_current_user, hash_password
from app.database import get_db
from app.deps import require_role
from app.models import User, user_from_doc, user_to_doc

router = APIRouter(prefix="/api/org")

Rol = Literal["admin", "analista", "lector"]
# Sin 0/O/o/1/l/I: la contraseña se dicta o se copia a mano.
_ALFABETO = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _password_temporal() -> str:
    c = [secrets.choice(_ALFABETO) for _ in range(12)]
    return "-".join("".join(c[i:i + 4]) for i in (0, 4, 8))


def _member_out(doc: dict) -> dict:
    u = user_from_doc(doc)
    return {"id": u.id, "email": u.email, "nombre": u.nombre, "rol": u.rol, "activo": u.activo,
            "debe_cambiar_password": u.debe_cambiar_password, "created_at": u.created_at}


class MemberCreate(BaseModel):
    email: EmailStr
    nombre: str = ""
    rol: Rol


class MemberPatch(BaseModel):
    rol: Optional[Rol] = None
    activo: Optional[bool] = None

    @model_validator(mode="after")
    def alguno(self):
        if self.rol is None and self.activo is None:
            raise ValueError("Indica el rol o el estado (activo) que quieres cambiar.")
        return self


@router.get("/members")
def list_members(admin: User = Depends(require_role("admin"))):
    return [_member_out(d) for d in store.list_members(admin.org_id)]


@router.post("/members", status_code=201)
def create_member(body: MemberCreate, admin: User = Depends(require_role("admin"))):
    email = body.email.lower()
    if get_db().users.find_one({"email": email}):
        raise HTTPException(409, "Ya existe una cuenta con ese email.")
    password = _password_temporal()
    user = User(id=f"usr_{uuid.uuid4().hex[:10]}", email=email, password_hash=hash_password(password),
                nombre=body.nombre.strip(), created_at=store.now_iso(), org_id=admin.org_id, rol=body.rol,
                debe_cambiar_password=True)
    try:
        # el índice único de email cubre la carrera entre el find_one y el insert
        get_db().users.insert_one(user_to_doc(user))
    except DuplicateKeyError:
        raise HTTPException(409, "Ya existe una cuenta con ese email.")
    store.log_org_event(admin.org_id, admin.id, "miembro_creado", {"email": email, "rol": body.rol})
    return {"member": _member_out(user_to_doc(user)), "password_temporal": password}


@router.patch("/members/{user_id}")
def patch_member(user_id: str, body: MemberPatch, admin: User = Depends(require_role("admin"))):
    doc = store.get_member(admin.org_id, user_id)
    if not doc:
        raise HTTPException(404, "Miembro no encontrado")
    m = user_from_doc(doc)
    rol, activo = body.rol or m.rol, m.activo if body.activo is None else body.activo
    # Se evalúa antes que "no te desactives": con un solo admin, el 409 es el que explica por qué.
    # shortcut: comprobar-y-luego-escribir no es atómico; dos admins quitándose mutuamente a la vez
    # podrían dejar la organización sin admin. Mejorar con una transacción si hay uso concurrente real.
    if m.rol == "admin" and m.activo and (rol != "admin" or not activo) \
            and store.count_active_admins(admin.org_id, excluding=m.id) == 0:
        raise HTTPException(409, "La organización debe tener al menos un administrador activo.")
    if m.id == admin.id and not activo:
        raise HTTPException(400, "No puedes desactivar tu propia cuenta.")
    store.update_member(admin.org_id, m.id, {"rol": rol, "activo": activo})
    if rol != m.rol:
        store.log_org_event(admin.org_id, admin.id, "miembro_rol_cambiado",
                            {"email": m.email, "rol_anterior": m.rol, "rol": rol})
    if activo != m.activo:
        store.log_org_event(admin.org_id, admin.id, "miembro_reactivado" if activo else "miembro_desactivado",
                            {"email": m.email, "rol": rol})
    return _member_out(store.get_member(admin.org_id, m.id))


# ---------- Perfil y logo (RF-10, T-046) ----------

LOGO_MAX = 512_000
_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
_MAGIC = ((bytes.fromhex("89504e470d0a1a0a"), "image/png"), (bytes.fromhex("ffd8ff"), "image/jpeg"))


class ProfileBody(BaseModel):
    nombre: str = ""
    rubro: Optional[str] = None
    color: Optional[str] = None


@router.put("/profile")
def put_profile(body: ProfileBody, admin: User = Depends(require_role("admin"))):
    nombre = body.nombre.strip()
    if not nombre:
        raise HTTPException(422, "Escribe el nombre de la organización.")
    if len(nombre) > 100:
        raise HTTPException(422, "El nombre puede tener hasta 100 caracteres.")
    if body.rubro is not None and body.rubro not in store.RUBROS:
        raise HTTPException(422, "Elige un rubro de la lista.")
    if body.color is not None and not _COLOR.fullmatch(body.color):
        raise HTTPException(422, "El color debe tener el formato #RRGGBB, por ejemplo #1F6FEB.")
    nuevo = {"nombre": nombre, "rubro": body.rubro, "color": body.color and body.color.lower()}
    antes = store.org_out(admin.org_id)
    cambios = {k: {"antes": antes[k], "despues": v} for k, v in nuevo.items() if antes[k] != v}
    if cambios:
        store.update_org_profile(admin.org_id, nuevo)
        store.log_org_event(admin.org_id, admin.id, "organizacion_editada", cambios)
    return store.org_out(admin.org_id)


@router.put("/logo")
async def put_logo(file: UploadFile = File(...), admin: User = Depends(require_role("admin"))):
    datos = await file.read(LOGO_MAX + 1)  # un byte de más basta para saber que se pasa
    tipo = next((t for firma, t in _MAGIC if datos.startswith(firma)), None)
    if not tipo:
        raise HTTPException(422, "El logo debe ser una imagen PNG o JPG.")
    if len(datos) > LOGO_MAX:
        raise HTTPException(422, "El logo pesa más de 500 KB. Usa una imagen más liviana.")
    store.set_org_logo(admin.org_id, tipo, datos)
    store.log_org_event(admin.org_id, admin.id, "logo_actualizado", {"tipo": tipo, "bytes": len(datos)})
    return store.org_out(admin.org_id)


@router.get("/logo")
def get_logo(user: User = Depends(get_current_user)):
    logo = store.get_org_logo(user.org_id)
    if not logo:
        raise HTTPException(404, "Tu organización no tiene logo.")
    return {"logo": f"data:{logo['tipo']};base64,{base64.b64encode(logo['datos']).decode()}"}


@router.delete("/logo")
def delete_logo(admin: User = Depends(require_role("admin"))):
    if store.delete_org_logo(admin.org_id):
        store.log_org_event(admin.org_id, admin.id, "logo_eliminado", {})
    return store.org_out(admin.org_id)
