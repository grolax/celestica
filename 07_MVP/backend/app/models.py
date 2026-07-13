"""
Modelos de dominio (sin ORM).

Con MongoDB los documentos viajan como dicts; lo único que se materializa
como objeto es el usuario autenticado, porque los endpoints lo reciben como
dependencia (`user: User = Depends(get_current_user)`) y acceden a sus
atributos (user.id, user.email, ...).

Colecciones en Mongo:
- `users`:        {_id, email, password_hash, nombre, empresa, created_at, integrations}
- `projects`:     {_id, user_id, name, created_at, ...documento completo del proyecto}
- `audit_events`: {_id, project_id, user_id, actor, action, timestamp, detail}
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
    }
