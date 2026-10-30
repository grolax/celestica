"""Migración RF-02 (T-004): envoltorio de línea de comandos. La lógica vive en app/migrations.py.

Uso (desde 07_MVP/backend, con MongoDB corriendo):
    python scripts/migrate_orgs.py
"""
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.database import get_db
    from app.migrations import migrate_orgs

    print(migrate_orgs(get_db()))
