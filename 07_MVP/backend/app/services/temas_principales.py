"""Temas principales por pregunta abierta (RF-43): conteo, porcentaje y citas textuales, sin IA y sin escribir.

Recibe el proyecto y devuelve el cuerpo de `GET /api/projects/{id}/temas-principales` (docs/API_CONTRATOS.md).
"""
from __future__ import annotations

import re

from app import store

MAX_TEMAS = 5
MAX_CITAS = 2
MIN_PALABRAS = 5
MAX_CARACTERES = 400

_DATO_PERSONAL = re.compile(
    r"\S+@\S+\.\S+"                                  # correo
    r"|(?<!\d)\d{1,2}\.?\d{3}\.?\d{3}-[\dkK](?!\w)"  # RUT
    r"|\+?\d(?:[ .\-]?\d){7,}"                       # teléfono u otro número largo (8 dígitos o más)
)


def _conf(a: dict) -> float:
    c = a.get("confidence")
    return c if isinstance(c, (int, float)) and not isinstance(c, bool) else -1.0  # sin confianza: la última


def _mejor(a: dict) -> tuple:
    """Clave de una asignación: el analista antes que Claude, luego mayor confianza (menor = mejor)."""
    return (a.get("source") != "analista", -_conf(a))


def _pregunta(project: dict, q: dict) -> dict:
    vista = store.vista_pregunta(project, q["id"])
    textos = {r["id"]: r["text"] for r in vista["responses"]}
    orden = {rid: i for i, rid in enumerate(textos)}
    codings = {rid: asignaciones for rid, asignaciones in vista["codings"].items() if rid in textos}
    validadas = {c["id"]: c for c in vista["categories"] if c["status"] == "validada"}

    por_tema: dict[str, dict[str, dict]] = {}  # category_id -> {response_id: mejor asignación de esa respuesta}
    for rid, asignaciones in codings.items():
        for a in asignaciones:
            cid = a["category_id"]
            if cid in validadas and (rid not in por_tema.get(cid, {}) or _mejor(a) < _mejor(por_tema[cid][rid])):
                por_tema.setdefault(cid, {})[rid] = a

    ranking = sorted(por_tema, key=lambda cid: (-len(por_tema[cid]), validadas[cid]["nombre"]))
    n_codificadas = len(codings)
    citadas: set[str] = set()
    temas = []
    for cid in ranking[:MAX_TEMAS]:
        def clave(rid):
            t = textos[rid]
            largo_ok = len(t.split()) >= MIN_PALABRAS and len(t) <= MAX_CARACTERES
            return (not largo_ok, *_mejor(por_tema[cid][rid]), orden[rid])

        elegibles = [rid for rid in sorted(por_tema[cid], key=clave) if not _DATO_PERSONAL.search(textos[rid])]
        nuevas = [rid for rid in elegibles if rid not in citadas]
        citas = (nuevas or elegibles)[:MAX_CITAS]
        citadas.update(citas)
        temas.append({
            "category_id": cid, "nombre": validadas[cid]["nombre"], "definicion": validadas[cid].get("definicion", ""),
            "personas": len(por_tema[cid]), "porcentaje": round(len(por_tema[cid]) / n_codificadas * 100, 1),
            "citas": [textos[rid] for rid in citas],
        })
    return {"pregunta_id": q["id"], "titulo": q["titulo"], "n_respuestas": len(textos),
            "n_codificadas": n_codificadas, "n_temas": len(ranking), "temas": temas}


def temas_principales(project: dict) -> dict:
    return {"preguntas": [_pregunta(project, q) for q in project.get("preguntas", []) if q["tipo"] == "abierta"]}
