"""
Migración one-shot: SQLite (softinsight.db, v1.0) → MongoDB (v1.1).

Lee las tablas users / projects / audit_events del archivo SQLite y las
vuelca en las colecciones homónimas de Mongo. Idempotente: usa el id como
_id y reemplaza (upsert), así que correrlo dos veces no duplica nada.

Uso (desde 07_MVP/backend, con el venv activo):
    python scripts/migrate_sqlite_to_mongo.py [ruta/a/softinsight.db]

Requiere MongoDB corriendo (MONGODB_URI, default mongodb://localhost:27017/softinsight).
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

# Permitir `python scripts/migrate_sqlite_to_mongo.py` desde backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import get_db, init_db  # noqa: E402

DEFAULT_DB = Path(__file__).resolve().parent.parent / "softinsight.db"


def migrate(sqlite_path: Path) -> None:
    if not sqlite_path.exists():
        sys.exit(f"No existe el archivo SQLite: {sqlite_path}")

    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row
    db = get_db()
    init_db()  # índices (email único, user_id, project_id)

    counts = {"users": 0, "projects": 0, "audit_events": 0}
    skipped = {"users": 0, "projects": 0, "audit_events": 0}

    # ---- users ----
    for row in conn.execute("SELECT * FROM users"):
        doc = {
            "_id": row["id"],
            "email": row["email"],
            "password_hash": row["password_hash"],
            "nombre": row["nombre"] or "",
            "empresa": row["empresa"] or "",
            "created_at": str(row["created_at"] or ""),
            "integrations": {},
        }
        db.users.replace_one({"_id": doc["_id"]}, doc, upsert=True)
        counts["users"] += 1

    # ---- projects (documento JSON en la columna data) ----
    for row in conn.execute("SELECT * FROM projects"):
        try:
            data = json.loads(row["data"]) if isinstance(row["data"], str) else row["data"]
        except Exception as e:
            print(f"  ! proyecto {row['id']}: JSON ilegible, omitido ({e})")
            skipped["projects"] += 1
            continue
        doc = dict(data)
        doc["_id"] = row["id"]
        doc["id"] = row["id"]
        doc["user_id"] = row["user_id"]
        doc.setdefault("name", row["name"])
        doc.setdefault("created_at", row["created_at"])
        db.projects.replace_one({"_id": doc["_id"]}, doc, upsert=True)
        counts["projects"] += 1

    # ---- audit_events ----
    for row in conn.execute("SELECT * FROM audit_events"):
        try:
            detail = json.loads(row["detail"]) if isinstance(row["detail"], str) else (row["detail"] or {})
        except Exception:
            detail = {"_raw": str(row["detail"])}
        doc = {
            "_id": row["id"],
            "project_id": row["project_id"],
            "user_id": row["user_id"],
            "actor": row["actor"],
            "action": row["action"],
            "timestamp": row["timestamp"],
            "detail": detail,
        }
        db.audit_events.replace_one({"_id": doc["_id"]}, doc, upsert=True)
        counts["audit_events"] += 1

    conn.close()

    print("\n=== Migración SQLite → MongoDB completada ===")
    for k in ("users", "projects", "audit_events"):
        extra = f" ({skipped[k]} omitidos)" if skipped[k] else ""
        print(f"  {k:>13}: {counts[k]} migrados{extra}")
    print(f"\nTotales ahora en Mongo: users={db.users.count_documents({})}, "
          f"projects={db.projects.count_documents({})}, "
          f"audit_events={db.audit_events.count_documents({})}")
    print("Re-ejecutar este script es seguro (upsert por id, no duplica).")


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB
    migrate(path)
