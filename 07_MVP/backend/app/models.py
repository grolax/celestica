"""
Modelos de dominio (sin ORM).

Con MongoDB los documentos viajan como dicts; lo único que se materializa
como objeto es el usuario autenticado, porque los endpoints lo reciben como
dependencia (`user: User = Depends(get_current_user)`) y acceden a sus
atributos (user.id, user.email, ...).

Colecciones en Mongo:
- `organizations`: {_id: "org_<10 hex>", nombre, created_at}
- `users`:        {_id, email, password_hash, nombre, empresa, created_at, integrations, org_id, rol,
                   activo, debe_cambiar_password}
                  (una sola organización por usuario; `rol`: admin | analista | lector, ver app/deps.py;
                   `activo`/`debe_cambiar_password` faltantes se leen como true/false, sin migración)
- `projects`:     {_id, org_id, user_id, name, created_at, ...documento completo del proyecto}
                  `org_id` es el dueño y la clave de aislamiento; `user_id` significa
                  "creado por" y NO se usa para filtrar acceso.
- `audit_events`: {_id, project_id, org_id, user_id, actor, action, timestamp, detail}
  (copia consultable del audit log; el registro canónico vive en el proyecto)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    id: str
    email: str
    password_hash: str
    nombre: str = ""
    empresa: str = ""
    created_at: str = ""
    integrations: dict = field(default_factory=dict)  # credenciales cifradas (Qualtrics, etc.)
    org_id: str = ""
    rol: str = "admin"
    activo: bool = True                  # False = desactivado: no entra, se conserva autoría y auditoría
    debe_cambiar_password: bool = False  # True = contraseña temporal pendiente de cambio


def user_from_doc(doc: Optional[dict]) -> Optional[User]:
    if not doc:
        return None
    return User(
        id=doc["_id"],
        email=doc["email"],
        password_hash=doc["password_hash"],
        nombre=doc.get("nombre", ""),
        empresa=doc.get("empresa", ""),
        created_at=doc.get("created_at", ""),
        integrations=doc.get("integrations", {}) or {},
        org_id=doc.get("org_id", ""),
        rol=doc.get("rol", "admin"),
        activo=doc.get("activo", True),
        debe_cambiar_password=doc.get("debe_cambiar_password", False),
    )


def user_to_doc(user: User) -> dict:
    return {
        "_id": user.id,
        "email": user.email,
        "password_hash": user.password_hash,
        "nombre": user.nombre,
        "empresa": user.empresa,
        "created_at": user.created_at,
        "integrations": user.integrations,
        "org_id": user.org_id,
        "rol": user.rol,
        "activo": user.activo,
        "debe_cambiar_password": user.debe_cambiar_password,
    }
