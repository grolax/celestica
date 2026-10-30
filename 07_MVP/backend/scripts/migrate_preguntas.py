"""Migración RF-23 (T-011a): cada proyecto pasa a guardar sus preguntas y un análisis por pregunta abierta.
La lógica vive en app/migrations.py; también corre sola al arrancar (init_db). Idempotente.

Uso (desde 07_MVP/backend, con MongoDB corriendo):
    python scripts/migrate_preguntas.py
"""
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.database import get_db
    from app.migrations import migrate_preguntas

    print(migrate_preguntas(get_db()))
