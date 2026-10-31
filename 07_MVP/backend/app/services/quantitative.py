"""Resultados de las preguntas cerradas (RF-30): conteos, porcentajes y estadísticos.

Función pura y sin IA: recibe las preguntas y los respondentes del proyecto y devuelve el cuerpo de
`GET /api/projects/{id}/closed-results`. Las reglas están en docs/API_CONTRATOS.md.
"""
from __future__ import annotations

import json
import math
import re
import statistics
from bisect import bisect_right
from collections import Counter

from app.services.question_types import separar_opciones

CERRADAS = {"escala", "nps", "si_no", "seleccion_unica", "seleccion_multiple", "segmento", "numerica"}
NOTA_MULTIPLE = "Cada persona puede elegir varias opciones; los porcentajes pueden sumar más de 100 %."
POR_TIPOS = {"segmento", "seleccion_unica", "si_no", "numerica"}
UMBRAL_POCOS_DATOS = 10
CORTES_DEFECTO = "18,25,35,45,55,65"
ERR_POR = "Esa pregunta no se puede usar para separar en grupos."
ERR_CORTES = "Los tramos deben ser números enteros, separados por coma y de menor a mayor."
ERR_UNIR = "La forma de unir grupos no es válida."
ERR_UNIR_POR = "Solo se pueden unir opciones de una pregunta de grupos."
ERR_UNIR_MIN = "Un grupo unido necesita al menos dos opciones."
ERR_UNIR_NOMBRE = "Cada grupo unido necesita un nombre distinto."


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


def _escala(q: dict, vals: list[str], ref: dict | None = None) -> dict:
    """`ref` = la `escala` del total: en un grupo se usa su rango para comparar sobre las mismas opciones."""
    nps = q["tipo"] == "nps"
    # shortcut: la escala no guarda su rango; el mínimo se asume 1 (0 si alguien respondió 0) y el máximo es el
    # mayor valor respondido, así que un máximo que nadie eligió no aparece. Guardar min/max al confirmar la vista previa.
    enteros = [int(x) for x in map(_num, vals) if x is not None and x == int(x)]
    if nps:
        enteros = [x for x in enteros if 0 <= x <= 10]
    out = {"n_invalidas": len(vals) - len(enteros)}
    if not enteros and not ref:
        return {**out, "opciones": []}
    lo, hi = (ref["min"], ref["max"]) if ref else (0, 10) if nps else (min(1, *enteros), max(enteros))
    c, base = Counter(enteros), len(enteros)
    out["opciones"] = [{"valor": str(k), "n": c[k], "pct": _pct(c[k], base)} for k in range(lo, hi + 1)]
    if not enteros:  # grupo sin respuestas válidas: opciones en 0, sin estadísticos
        return out
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


def _categorica(q: dict, vals: list[str], orden: list[str] | None = None, split: dict | None = None) -> dict:
    """`orden` = las opciones del total: en un grupo se listan todas, en ese orden, con n 0 si nadie la eligió.
    `split` = respuesta -> opciones, separada una sola vez sobre todas las respuestas (así un grupo cuenta igual que el total)."""
    multiple = q["tipo"] == "seleccion_multiple"
    c = Counter(o for v in vals for o in dict.fromkeys(split[v])) if multiple else Counter(vals)
    items = sorted(c.items(), key=lambda kv: (-kv[1], kv[0].casefold()))
    if not multiple:  # tramos ("Menos de $360.000", "20-24"): orden natural, las opciones sin número al final
        nums = {v: _primer_numero(v) for v, _ in items}
        if sum(x is None for x in nums.values()) <= 2:
            items.sort(key=lambda kv: (nums[kv[0]] is None, nums[kv[0]] or 0))  # estable: respeta el orden por n
    if orden:
        items = [(v, c[v]) for v in orden]
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


def _pregunta(q: dict, resp: list[dict], ref: dict | None = None, split: dict | None = None) -> dict:
    """Resultado de una pregunta sobre `resp` (sin id/título/tipo). `ref` = el resultado del total, al calcular un grupo."""
    vals = [v for r in resp if (v := r["valores"].get(q["id"])) is not None]
    if q["tipo"] in ("escala", "nps"):
        detalle = _escala(q, vals, ref and ref.get("escala"))
    elif q["tipo"] == "numerica":
        detalle = _numerica(vals)
    else:
        detalle = _categorica(q, vals, ref and [o["valor"] for o in ref["opciones"]], split)
    if not detalle.get("n_invalidas"):
        detalle.pop("n_invalidas", None)
    return {"n_respuestas": len(vals), "n_na": len(resp) - len(vals), "tasa_respuesta": _pct(len(vals), len(resp)), **detalle}


def _cortes(texto: str) -> list[int]:
    try:
        cs = [int(x) for x in texto.split(",")]
    except ValueError:
        raise ValueError(ERR_CORTES) from None
    if any(a >= b for a, b in zip(cs, cs[1:])):
        raise ValueError(ERR_CORTES)
    return cs


def _grupos(q: dict, respondentes: list[dict], cortes: str | None) -> dict[str, list[dict]]:
    """Personas por grupo de la pregunta `q`, en orden; quien no tiene grupo no aparece."""
    vals = [v for r in respondentes if (v := r["valores"].get(q["id"])) is not None]
    if q["tipo"] != "numerica":
        grupos = {o["valor"]: [] for o in _categorica(q, vals)["opciones"]}
        for r in respondentes:
            if (g := r["valores"].get(q["id"])) in grupos:
                grupos[g].append(r)
        return grupos
    cs = _cortes(CORTES_DEFECTO if cortes is None else cortes)
    etiquetas = [f"{a}–{b - 1}" for a, b in zip(cs, cs[1:])] + [f"{cs[-1]}+"]
    cubos = [[] for _ in range(len(cs) + 1)]  # cubos[0] = bajo el primer corte
    for r in respondentes:
        x = _num(r["valores"].get(q["id"]) or "")
        if x is not None:
            cubos[bisect_right(cs, x)].append(r)
    grupos = {f"Menos de {cs[0]}": cubos[0]} if cubos[0] else {}
    return {**grupos, **dict(zip(etiquetas, cubos[1:]))}


def _unir(grupos: dict[str, list[dict]], texto: str) -> tuple[dict[str, list[dict]], dict[str, list[str]]]:
    """Junta opciones de `grupos` según `texto` (JSON). Devuelve los grupos nuevos y, por nombre, las opciones unidas en orden."""
    try:
        lista = json.loads(texto)
    except ValueError:
        raise ValueError(ERR_UNIR) from None
    if not isinstance(lista, list) or not all(
            isinstance(u, dict) and isinstance(u.get("nombre"), str) and isinstance(u.get("valores"), list)
            and all(isinstance(v, str) for v in u["valores"]) for u in lista):
        raise ValueError(ERR_UNIR)
    en_grupo: dict[str, str] = {}  # opción -> nombre del grupo unido
    for u in lista:
        vals = set(u["valores"])
        if len(vals) < 2:
            raise ValueError(ERR_UNIR_MIN)
        for v in u["valores"]:
            if v not in grupos:
                raise ValueError(f"La opción «{v}» no existe en esa pregunta.")
        for v in vals:
            if v in en_grupo:
                raise ValueError(f"La opción «{v}» está en más de un grupo.")
            en_grupo[v] = u["nombre"].strip()
    nombres = [u["nombre"].strip() for u in lista]
    if "" in nombres or len(set(nombres)) < len(nombres) or any(n in grupos and n not in en_grupo for n in nombres):
        raise ValueError(ERR_UNIR_NOMBRE)
    unidos: dict[str, list[str]] = {}
    for g in grupos:  # el orden de T-022 define dónde queda cada grupo unido
        if g in en_grupo:
            unidos.setdefault(en_grupo[g], []).append(g)
    nuevos = {}
    for g, resp in grupos.items():
        if g not in en_grupo:
            nuevos[g] = resp
        else:
            n = en_grupo[g]
            nuevos[n] = nuevos.get(n, []) + resp
    return nuevos, unidos


def calcular(preguntas: list[dict], respondentes: list[dict], por: str | None = None, cortes: str | None = None,
             unir: str | None = None) -> dict:
    """Con `por` (RF-31) agrega `grupos` y, en cada pregunta, `por_grupo`; `unir` (JSON) junta opciones de `por`.
    Errores de entrada: ValueError con el mensaje."""
    porq = None
    if por is not None:
        porq = next((q for q in preguntas if q["id"] == por and q["tipo"] in POR_TIPOS), None)
        if not porq:
            raise ValueError(ERR_POR)
    if cortes is not None and (not porq or porq["tipo"] != "numerica"):
        raise ValueError(ERR_CORTES)
    if unir is not None and (not porq or porq["tipo"] == "numerica"):
        raise ValueError(ERR_UNIR_POR)
    grupos = _grupos(porq, respondentes, cortes) if porq else {}
    unidos = {}
    if unir is not None:
        grupos, unidos = _unir(grupos, unir)
    out = []
    for q in preguntas:
        if q["tipo"] not in CERRADAS or q is porq:
            continue
        split = None
        if q["tipo"] == "seleccion_multiple":  # se separa una vez con todas las respuestas; el total y cada grupo usan ese resultado
            todas = [v for r in respondentes if (v := r["valores"].get(q["id"])) is not None]
            split = dict(zip(todas, separar_opciones(todas)))
        total = _pregunta(q, respondentes, split=split)
        item = {"id": q["id"], "titulo": q["titulo"], "tipo": q["tipo"], **total}
        if porq:
            item["por_grupo"] = [{"valor": g, **_pregunta(q, resp, total, split)} for g, resp in grupos.items()]
        out.append(item)
    res = {"n_personas": len(respondentes), "preguntas": out}
    if porq:
        res.update(por={"id": porq["id"], "titulo": porq["titulo"], "tipo": porq["tipo"]},
                   umbral_pocos_datos=UMBRAL_POCOS_DATOS,
                   n_sin_grupo=len(respondentes) - sum(map(len, grupos.values())),
                   grupos=[{"valor": g, "n_personas": len(r), "pocos_datos": len(r) < UMBRAL_POCOS_DATOS,
                            **({"unidos": unidos[g]} if g in unidos else {})}
                           for g, r in grupos.items()])
    return res
