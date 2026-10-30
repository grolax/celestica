"""
Migración RF-02 (T-004): usuarios y proyectos pasan a pertenecer a una organización.

- Cada usuario sin `org_id` recibe su PROPIA organización (nombre = `empresa`, o
  "Organización de <nombre|email>") y `rol="admin"`. No se unen usuarios por el
  texto de `empresa`, aunque coincida.
- Cada proyecto sin `org_id` hereda el de su usuario (`user_id`). Si ese usuario
  no existe, el proyecto queda inaccesible (como antes) y se cuenta como huérfano.
- Cada audit_event sin `org_id` hereda el de su proyecto.

Idempotente: solo toca documentos con `org_id` ausente. La segunda corrida no
cambia nada y devuelve todos los conteos en 0. `init_db()` la corre al arrancar.

Uso (desde 07_MVP/backend, con MongoDB corriendo):
    python scripts/migrate_orgs.py
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

SIN_ORG = {"org_id": {"$exists": False}}


def migrate_orgs(db) -> dict:
    counts = {"usuarios": 0, "proyectos": 0, "proyectos_huerfanos": 0, "eventos": 0}

    for u in db.users.find(SIN_ORG):
        nombre = (u.get("nombre") or "").strip()
        org_id = f"org_{uuid.uuid4().hex[:10]}"
        db.organizations.insert_one({
            "_id": org_id,
            "nombre": (u.get("empresa") or "").strip() or f"Organización de {nombre or u['email']}",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        db.users.update_one({"_id": u["_id"]}, {"$set": {"org_id": org_id, "rol": "admin"}})
        counts["usuarios"] += 1

    # shortcut: el huérfano queda con org_id=None (no ausente) para no recontarlo
    # en cada arranque; sigue inaccesible porque ningún usuario tiene org_id None.
    for uid in db.projects.distinct("user_id", SIN_ORG):
        owner = db.users.find_one({"_id": uid}, {"org_id": 1})
        org_id = owner["org_id"] if owner else None
        n = db.projects.update_many({**SIN_ORG, "user_id": uid}, {"$set": {"org_id": org_id}}).modified_count
        counts["proyectos" if owner else "proyectos_huerfanos"] += n
    # proyectos sin user_id: no hay a quién asignarlos
    n = db.projects.update_many({**SIN_ORG, "user_id": {"$exists": False}}, {"$set": {"org_id": None}}).modified_count
    counts["proyectos_huerfanos"] += n

    for pid in db.audit_events.distinct("project_id", SIN_ORG):
        proj = db.projects.find_one({"_id": pid}, {"org_id": 1}) or {}
        org_id = proj.get("org_id")
        n = db.audit_events.update_many({**SIN_ORG, "project_id": pid}, {"$set": {"org_id": org_id}}).modified_count
        if org_id:
            counts["eventos"] += n
    return counts
