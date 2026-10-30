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

import pandas as pd

from app.services.question_types import contexto_por_defecto, detectar

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


# ---------- RF-23 (T-011a): un proyecto guarda todas sus preguntas y un análisis por pregunta abierta ----------

# Campos que hoy viven en la raíz y pasan a analisis.q_1
CAMPOS_ANALISIS = ("lexical", "lexical_interpretation", "categories", "codings", "qualitative_report",
                   "v2_analyses_cache")
CAMPOS_VIEJOS = ("responses", *CAMPOS_ANALISIS)  # salen de la raíz


def convertir_proyecto(p: dict) -> dict:
    """Documento antiguo (responses en la raíz) → {preguntas, respondentes, analisis}. Función pura."""
    responses = p.get("responses") or []
    texto = p.get("text_column") or ""
    meta_keys = list(dict.fromkeys(k for r in responses for k in r.get("meta", {})))
    meta_cols = [c for c in (p.get("columns") or []) if c in meta_keys]
    meta_cols += [k for k in meta_keys if k not in meta_cols]
    preguntas = [{"id": "q_1", "titulo": texto, "columnas": [texto], "tipo": "abierta", "contexto_ia": False}]
    if meta_cols and responses:
        df = pd.DataFrame([{c: r.get("meta", {}).get(c) or None for c in meta_cols} for r in responses])
        tipos = {x["columna"]: x["tipo"] for x in detectar(df)["preguntas"]}
        for i, c in enumerate(meta_cols, start=2):
            preguntas.append({"id": f"q_{i}", "titulo": c, "columnas": [c], "tipo": tipos[c],
                              "contexto_ia": contexto_por_defecto(tipos[c], c)})
    ids = {q["titulo"]: q["id"] for q in preguntas[1:]}
    respondentes = [
        {"id": r["id"], "valores": {"q_1": r.get("text") or None,
                                    **{ids[c]: v or None for c, v in r.get("meta", {}).items()}}}
        for r in responses
    ]
    return {"preguntas": preguntas, "respondentes": respondentes,
            "analisis": {"q_1": {c: p[c] for c in CAMPOS_ANALISIS if c in p}}}


def migrate_preguntas(db) -> dict:
    """Todo proyecto sin `preguntas` pasa al esquema por pregunta; `q_1` es la columna de texto de siempre.

    Idempotente: solo toca proyectos sin `preguntas` y el filtro del update lo vuelve a exigir (dos procesos a la
    vez no se pisan). `columns` y `text_column` quedan como dato de origen. `init_db()` la corre al arrancar.
    """
    n = 0
    for p in db.projects.find({"preguntas": {"$exists": False}}):
        nuevo = convertir_proyecto(p)
        r = db.projects.update_one(
            {"_id": p["_id"], "preguntas": {"$exists": False}},
            {"$set": nuevo, "$unset": {c: "" for c in CAMPOS_VIEJOS}},
        )
        n += r.modified_count
    return {"proyectos": n}
