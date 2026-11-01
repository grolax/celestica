"""Recomendaciones automáticas (RF-41): alertas de calidad de datos, segmentos para cruzar y plantilla sugerida.

Reglas fijas, sin IA y sin escribir nada. Recibe el proyecto y devuelve el cuerpo de
`GET /api/projects/{id}/recommendations` (docs/API_CONTRATOS.md).
"""
from __future__ import annotations

import re
import statistics

from app.services.quantitative import POR_TIPOS, UMBRAL_POCOS_DATOS, _grupos
from app.services.question_types import _sin_tildes
from app.templates import FRAMEWORK_TEMPLATES

PRIORIDAD = {"genero", "sexo", "edad", "comuna", "region", "sede", "carrera", "tienda", "area", "cargo"}
MAX_SEGMENTOS = 3


def _titulo(q: dict) -> str:
    t = q["titulo"]
    return t if len(t) <= 80 else t[:80] + "…"


def _alertas(preguntas: list[dict], respondentes: list[dict]) -> list[dict]:
    n = len(respondentes)
    vals = {q["id"]: [v for r in respondentes if (v := r["valores"].get(q["id"])) is not None] for q in preguntas}
    out = []

    def add(id_: str, nivel: str, mensaje: str, q: dict | None = None):
        out.append({"id": id_, "nivel": nivel, "pregunta_id": q and q["id"], "mensaje": mensaje})

    if n < 10:
        add("pocas_respuestas", "importante", f"La encuesta tiene muy pocas respuestas ({n}); los resultados serán poco representativos.")
    elif n < 30:
        add("pocas_respuestas_30", "aviso", f"La encuesta tiene {n} respuestas: los resultados pueden variar mucho. Tómalos como una primera mirada.")
    for q in preguntas:
        n_na = n - len(vals[q["id"]])
        if q["tipo"] != "identificador" and n_na * 2 > n:
            add("muchas_vacias", "aviso", f"Más de la mitad de las personas no respondió «{_titulo(q)}» ({n_na} de {n}).", q)
    for q in preguntas:
        v = vals[q["id"]]
        if q["tipo"] != "abierta" or len(v) < 20:
            continue
        k = len({" ".join(x.lower().split()) for x in v})
        if k <= 10:
            add("abierta_repetida", "aviso", f"Las respuestas de «{_titulo(q)}» se repiten mucho (solo {k} distintas): quizás es una pregunta cerrada.", q)
        elif statistics.median(len(x.split()) for x in v) <= 2:
            add("abierta_corta", "aviso", f"La mitad de las respuestas de «{_titulo(q)}» tiene 2 palabras o menos: el análisis de temas tendrá poco material.", q)
    for q in preguntas:
        v = vals[q["id"]]
        k = len(set(v))
        if q["tipo"] in ("seleccion_unica", "segmento") and len(v) >= 30 and k * 2 > len(v):
            add("cerrada_dispersa", "aviso", f"«{_titulo(q)}» tiene casi tantas opciones distintas como respuestas ({k} de {len(v)}): quizás es una pregunta abierta.", q)
    return out


def _segmentos(preguntas: list[dict], respondentes: list[dict]) -> list[dict]:
    out = []
    for q in preguntas:
        if q["tipo"] not in POR_TIPOS:
            continue
        grupos = _grupos(q, respondentes, None)  # la misma función que closed-results
        suficientes = sum(len(g) >= UMBRAL_POCOS_DATOS for g in grupos.values())
        if 2 <= len(grupos) <= 15 and suficientes >= 2 and sum(map(len, grupos.values())) * 2 >= len(respondentes):
            out.append({"pregunta_id": q["id"], "titulo": q["titulo"], "n_grupos": suficientes,
                        "motivo": f"Separa a las personas en {suficientes} grupos con datos suficientes."})
    # sort estable: dentro de cada bloque queda el orden de la encuesta
    out.sort(key=lambda s: (not set(re.findall(r"[a-z0-9]+", _sin_tildes(s["titulo"]))) & PRIORIDAD, -s["n_grupos"]))
    return out[:MAX_SEGMENTOS]


def _plantilla(project: dict) -> dict | None:
    preguntas = project.get("preguntas", [])
    marco = (project.get("marco_teorico") or "").strip()
    if not any(q["tipo"] == "abierta" for q in preguntas) or any(marco == t["marco_teorico"].strip() for t in FRAMEWORK_TEMPLATES.values()):
        return None
    texto = _sin_tildes(" ".join([project.get("name") or "", marco, *(q["titulo"] for q in preguntas)]))
    mejor, hallado = None, []
    for key, t in FRAMEWORK_TEMPLATES.items():  # estricto >: en un empate gana la primera
        h = [k for k in t["palabras_clave"] if re.search(r"\b" + re.escape(k), texto)]  # raíz al inicio de palabra
        if len(h) > len(hallado):
            mejor, hallado = key, h
    if len(hallado) < 2:
        return None
    citadas = [f"«{k}»" for k in hallado[:3]]
    t = FRAMEWORK_TEMPLATES[mejor]
    return {"key": mejor, "nombre": t["nombre"], "industria": t["industria"],
            "motivo": f"La encuesta menciona {', '.join(citadas[:-1])} y {citadas[-1]}."}


def recomendar(project: dict) -> dict:
    preguntas, respondentes = project.get("preguntas", []), project.get("respondentes", [])
    return {"alertas": _alertas(preguntas, respondentes), "segmentos": _segmentos(preguntas, respondentes),
            "plantilla": _plantilla(project)}
