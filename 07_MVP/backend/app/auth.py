"""
Autenticación JWT multi-tenant.

- Passwords: PBKDF2-HMAC-SHA256 (stdlib, 200k iteraciones, salt por usuario).
- Tokens: JWT HS256 firmados con SECRET_KEY (.env), expiración 7 días.
- `get_current_user` es la dependency que protege todos los endpoints de proyecto.
- Usuarios en la colección `users` de MongoDB (email con índice único); cada uno pertenece a una organización (`org_id`, `rol`).
"""
from __future__ import annotations

import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, field_validator
from pymongo.errors import DuplicateKeyError

from app.database import get_db
from app.models import User, user_from_doc, user_to_doc

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-cambiar-en-produccion")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7
_PBKDF2_ITERATIONS = 200_000

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)


# ---------- Passwords ----------

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _PBKDF2_ITERATIONS).hex()
    return f"pbkdf2${_PBKDF2_ITERATIONS}${salt}${digest}"

def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt, digest = stored.split("$")
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
        return secrets.compare_digest(candidate, digest)
    except (ValueError, AttributeError):
        return False


# ---------- Tokens ----------

def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRE_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer)) -> User:
    if credentials is None:
        raise HTTPException(401, "No autenticado. Inicia sesión.")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Sesión expirada. Inicia sesión nuevamente.")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token inválido.")
    user = user_from_doc(get_db().users.find_one({"_id": payload.get("sub", "")}))
    if not user:
        raise HTTPException(401, "Usuario no encontrado.")
    return user


# ---------- Schemas ----------

class SignupBody(BaseModel):
    email: EmailStr
    password: str
    nombre: str = ""
    empresa: str = ""

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v


class LoginBody(BaseModel):
    email: EmailStr
    password: str


def _user_out(user: User) -> dict:
    org = get_db().organizations.find_one({"_id": user.org_id}) or {}
    return {"id": user.id, "email": user.email, "nombre": user.nombre, "empresa": user.empresa,
            "rol": user.rol, "organizacion": {"id": user.org_id, "nombre": org.get("nombre", "")}}


# ---------- Endpoints ----------

@router.post("/signup")
def signup(body: SignupBody):
    db = get_db()
    email = body.email.lower()
    if db.users.find_one({"email": email}):
        raise HTTPException(409, "Ya existe una cuenta con ese email.")
    nombre, empresa = body.nombre.strip(), body.empresa.strip()
    org = {"_id": f"org_{uuid.uuid4().hex[:10]}",
           "nombre": empresa or f"Organización de {nombre or email}",
           "created_at": datetime.now(timezone.utc).isoformat()}
    user = User(
        id=f"usr_{uuid.uuid4().hex[:10]}",
        email=email,
        password_hash=hash_password(body.password),
        nombre=nombre,
        empresa=empresa,
        created_at=org["created_at"],
        org_id=org["_id"],
        rol="admin",
    )
    # La organización se crea DESPUÉS del usuario: si el email está duplicado
    # no queda ninguna organización huérfana.
    try:
        db.users.insert_one(user_to_doc(user))
    except DuplicateKeyError:
        # índice único de email: cubre la carrera entre el find_one y el insert
        raise HTTPException(409, "Ya existe una cuenta con ese email.")
    db.organizations.insert_one(org)
    return {"token": create_token(user.id), "user": _user_out(user)}


@router.post("/login")
def login(body: LoginBody):
    user = user_from_doc(get_db().users.find_one({"email": body.email.lower()}))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Email o contraseña incorrectos.")
    return {"token": create_token(user.id), "user": _user_out(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return _user_out(user)
