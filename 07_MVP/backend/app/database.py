"""
Conexión a MongoDB vía pymongo.

Beta: MongoDB Community local (brew services start mongodb-community).
Producción: MongoDB Atlas — basta cambiar MONGODB_URI en .env, el código
no cambia (DEC-03 actualizada en v1.1).

El modelo de datos es documental por diseño: cada proyecto es un documento
(responses, categories, codings, audit_log) y Mongo permite actualizarlo
parcialmente ($set/$push) e indexar campos anidados.
"""
from __future__ import annotations

import os

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.database import Database

from app.migrations import migrate_orgs

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/softinsight")

_client = None  # lazy: se crea en el primer uso (y es reemplazable en tests)


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000)
    return _client


def get_db() -> Database:
    db = get_client().get_default_database("softinsight")
    return db


def init_db() -> None:
    """Crea los índices si no existen. Idempotente.

    - users.email: único (una cuenta por email)
    - projects.org_id: aislamiento multi-tenant (toda lista filtra por organización)
    - users.org_id: miembros de una organización
    - audit_events.project_id: consultas de auditoría por proyecto
    Al final corre la migración a organizaciones (RF-02), barata si no hay nada pendiente.
    """
    db = get_db()
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.users.create_index([("org_id", ASCENDING)])
    db.projects.create_index([("user_id", ASCENDING)])
    db.projects.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    db.projects.create_index([("org_id", ASCENDING)])
    db.projects.create_index([("org_id", ASCENDING), ("created_at", DESCENDING)])
    db.audit_events.create_index([("project_id", ASCENDING)])
    migrate_orgs(db)
