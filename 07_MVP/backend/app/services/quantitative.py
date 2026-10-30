"""Resultados de las preguntas cerradas (RF-30): conteos, porcentajes y estadísticos.

Función pura y sin IA: recibe las preguntas y los respondentes del proyecto y devuelve el cuerpo de
`GET /api/projects/{id}/closed-results`. Las reglas están en docs/API_CONTRATOS.md.
"""
from __future__ import annotations

import math
import re
import statistics
from collections import Counter

from app.services.question_types import separar_opciones

CERRADAS = {"escala", "nps", "si_no", "seleccion_unica", "seleccion_multiple", "segmento", "numerica"}
NOTA_MULTIPLE = "Cada persona puede elegir varias opciones; los porcentajes pueden sumar más de 100 %."


def _pct(n: int, base: int) -> float:
    return round(n / base * 100, 1) if base else 0.0


def _num(v: str) -> float | None:
    try:
        x = float(v.replace(",", "."))
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def _desv(xs: list) -> float:
    return round(statistics.stdev(xs), 2) if len(xs) > 1 else 0.0


def _escala(q: dict, vals: list[str]) -> dict:
    nps = q["tipo"] == "nps"
    # shortcut: la escala no guarda su rango; el mínimo se asume 1 (0 si alguien respondió 0) y el máximo es el
    # mayor valor respondido, así que un máximo que nadie eligió no aparece. Guardar min/max al confirmar la vista previa.
    enteros = [int(x) for x in map(_num, vals) if x is not None and x == int(x)]
    if nps:
        enteros = [x for x in enteros if 0 <= x <= 10]
    out = {"n_invalidas": len(vals) - len(enteros)}
    if not enteros:
        return {**out, "opciones": []}
    lo, hi = (0, 10) if nps else (min(1, *enteros), max(enteros))
    c, base = Counter(enteros), len(enteros)
    out["opciones"] = [{"valor": str(k), "n": c[k], "pct": _pct(c[k], base)} for k in range(lo, hi + 1)]
    out["escala"] = {"min": lo, "max": hi, "promedio": round(statistics.mean(enteros), 2), "desviacion": _desv(enteros)}
    if nps:
        n_p, n_d = sum(c[k] for k in (9, 10)), sum(c[k] for k in range(7))
        out["nps"] = {"valor": round(n_p / base * 100 - n_d / base * 100, 2),
                      "promotores": {"n": n_p, "pct": _pct(n_p, base)},
                      "pasivos": {"n": c[7] + c[8], "pct": _pct(c[7] + c[8], base)},
                      "detractores": {"n": n_d, "pct": _pct(n_d, base)}}
    else:
        for nombre, vs in (("top2", [hi - 1, hi]), ("bottom2", [lo, lo + 1])):
            n = c[vs[0]] + c[vs[1]]
            out["escala"][nombre] = {"valores": vs, "n": n, "pct": _pct(n, base)}
    return out


def _primer_numero(v: str) -> int | None:
    m = re.search(r"\d{1,3}(?:\.\d{3})+|\d+", v)  # "360.001" es 360001 (punto de miles)
    return int(m.group().replace(".", "")) if m else None


def _categorica(q: dict, vals: list[str]) -> dict:
    multiple = q["tipo"] == "seleccion_multiple"
    c = Counter(o for fila in separar_opciones(vals) for o in dict.fromkeys(fila)) if multiple else Counter(vals)
    items = sorted(c.items(), key=lambda kv: (-kv[1], kv[0].casefold()))
    if not multiple:  # tramos ("Menos de $360.000", "20-24"): orden natural, las opciones sin número al final
        nums = {v: _primer_numero(v) for v, _ in items}
        if sum(x is None for x in nums.values()) <= 2:
            items.sort(key=lambda kv: (nums[kv[0]] is None, nums[kv[0]] or 0))  # estable: respeta el orden por n
    out = {"opciones": [{"valor": v, "n": n, "pct": _pct(n, len(vals))} for v, n in items]}
    return {**out, "nota": NOTA_MULTIPLE} if multiple else out


def _numerica(vals: list[str]) -> dict:
    xs = [x for x in map(_num, vals) if x is not None]
    out = {"n_invalidas": len(vals) - len(xs)}
    if xs:
        r = lambda x: int(x) if x == int(x) else round(x, 2)  # noqa: E731  (33.0 se muestra 33)
        out["numerica"] = {"promedio": round(statistics.mean(xs), 2), "desviacion": _desv(xs),
                           "mediana": r(statistics.median(xs)), "min": r(min(xs)), "max": r(max(xs))}
    return out


def calcular(preguntas: list[dict], respondentes: list[dict]) -> dict:
    n = len(respondentes)
    out = []
    for q in preguntas:
        if q["tipo"] not in CERRADAS:
            continue
        vals = [v for r in respondentes if (v := r["valores"].get(q["id"])) is not None]
        if q["tipo"] in ("escala", "nps"):
            detalle = _escala(q, vals)
        elif q["tipo"] == "numerica":
            detalle = _numerica(vals)
        else:
            detalle = _categorica(q, vals)
        if not detalle.get("n_invalidas"):
            detalle.pop("n_invalidas", None)
        out.append({"id": q["id"], "titulo": q["titulo"], "tipo": q["tipo"], "n_respuestas": len(vals),
                    "n_na": n - len(vals), "tasa_respuesta": _pct(len(vals), n), **detalle})
    return {"n_personas": n, "preguntas": out}
