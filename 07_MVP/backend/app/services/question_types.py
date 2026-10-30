"""Detección determinística (sin IA, sin costo) del tipo de cada columna de una encuesta.

`detectar(df)` es una función pura: lee un DataFrame y devuelve el cuerpo de la vista previa
(`n_filas`, `preguntas`, `advertencias`). Las reglas están documentadas en COMO_FUNCIONA.md.
Todo es vectorizado en pandas; las comparaciones por valor se hacen sobre los valores únicos.
"""
from __future__ import annotations

import re
import unicodedata

import pandas as pd

MAX_OPCIONES = 20
SI_NO = {"si", "no", "s", "n", "yes", "y", "true", "false", "verdadero", "falso", "1", "0"}
TITULO_ID = {"id", "rut", "folio", "email", "mail", "correo", "dni", "uuid", "matricula", "ip", "ipaddress"}
TITULO_GRUPO = {"tienda", "sede", "sucursal", "comuna", "region", "carrera", "area", "cargo", "sexo", "genero",
                "edad", "tramo", "asignatura", "facultad", "departamento", "ciudad", "pais", "curso", "seccion",
                "jornada", "zona"}
TITULO_ANIO = {"anio", "ano", "edad", "curso", "cursado", "semestre", "ciclo"}
FECHA = r"^\d{4}-\d{1,2}-\d{1,2}|^\d{4}/\d{1,2}/\d{1,2}|^\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}"


def _sin_tildes(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", t.lower()) if not unicodedata.combining(c))


def _opciones(vc: pd.Series) -> list[dict]:
    return [{"valor": str(v), "n": int(n)} for v, n in vc.head(MAX_OPCIONES).items()]


def _recortar(v: str) -> str:
    return v if len(v) <= 120 else v[:120] + "…"


def _valores(s: pd.Series) -> pd.Series:
    """Valores no vacíos como texto. Enteros que vienen como float (Excel) quedan sin '.0'."""
    if pd.api.types.is_float_dtype(s) and (s.dropna() % 1 == 0).all():
        s = s.astype("Int64")
    v = s.astype("string").str.strip().dropna()
    return v[v != ""]


def _clasificar(col: str, vals: pd.Series, vc: pd.Series) -> tuple[str, str, dict]:
    """Devuelve (tipo, motivo, extras) para una columna con al menos 2 valores distintos."""
    n_resp, nd = len(vals), len(vc)
    tokens = re.findall(r"[a-z0-9]+", _sin_tildes(col))
    # shortcut: las pruebas por texto (formato, espacios, palabras) miran una muestra fija de 1.000 valores para cumplir RNF-10; conteos y rangos son exactos.
    m = vals if n_resp <= 1000 else vals.sample(1000, random_state=0)
    corto = len(tokens) <= 3  # "Edad", "anio_cursado": sí; "¿Cómo evalúa el curso?": no, es una pregunta

    # 2. identificador por el título
    if set(tokens) & TITULO_ID or re.search(r"[a-z]Id$", col):
        return "identificador", "El título sugiere un identificador (código, correo o similar).", {}

    # 3. fecha
    if m.str.match(FECHA).mean() >= 0.9:
        muestra = pd.to_datetime(m.drop_duplicates().head(100), errors="coerce", dayfirst=True, format="mixed")
        if muestra.notna().mean() >= 0.9:
            return "fecha", "Los valores tienen formato de fecha.", {}

    es_num = pd.to_numeric(m.str.replace(",", ".", regex=False), errors="coerce").notna().mean() >= 0.95
    enteros = False
    if es_num:
        num = pd.to_numeric(vals.str.replace(",", ".", regex=False), errors="coerce").dropna()
        enteros = bool((num % 1 == 0).all())

    # 2b. identificador por los valores: casi todos distintos, cortos y sin espacios
    # shortcut: un número entero con casi todos los valores distintos se toma como código, aunque sea una medida; revisar si hay falsos positivos.
    if n_resp >= 10 and nd >= 0.95 * n_resp and (not es_num or enteros) and m.str.len().max() <= 40 \
            and not m.str.contains(r"\s").any():
        return "identificador", "Casi todos los valores son distintos, cortos y sin espacios.", {}

    # 4. NPS
    if enteros and num.min() >= 0 and num.max() <= 10 and re.search(r"recomend|nps", _sin_tildes(col)):
        return "nps", 'Números enteros entre 0 y 10 y el título menciona "recomendar".', {"escala": {"min": 0, "max": 10}}

    # 5. sí/no
    if nd <= 12:
        norm = {v: _sin_tildes(v) for v in vc.index}
        if set(norm.values()) <= SI_NO and len(set(norm.values())) == 2:
            return "si_no", "Solo hay dos respuestas posibles (sí/no).", {"opciones": _opciones(vc)}

    # 6. escala  /  7. numérica
    if es_num:
        hint_anio = corto and bool(set(tokens) & TITULO_ANIO)
        if enteros and nd <= 11 and num.min() >= 0 and num.max() <= 10 and not hint_anio:
            return "escala", f"Números enteros entre {int(num.min())} y {int(num.max())} con pocos valores distintos.", \
                {"escala": {"min": int(num.min()), "max": int(num.max())}}
        if hint_anio and nd <= 20:
            return "segmento", "Pocos valores repetidos y el título sugiere un grupo (año, edad o curso).", \
                {"opciones": _opciones(vc)}
        return "numerica", "Valores numéricos con muchos valores distintos.", {}

    # 8. selección múltiple
    for sep in (";", ","):
        if m.str.contains(sep, regex=False).mean() >= 0.2 and m.str.split(sep).explode().str.strip().nunique() <= MAX_OPCIONES:
            partes = vals.str.split(sep).explode().str.strip()
            partes = partes[partes != ""]
            pc = partes.value_counts()
            if len(pc) <= MAX_OPCIONES and len(partes) >= 2 * len(pc) and partes.str.len().max() <= 40:
                return "seleccion_multiple", f'Cada respuesta puede tener varias opciones separadas por "{sep}".', \
                    {"opciones": _opciones(pc)}

    # 9. segmento / selección única
    grupo = corto and bool(set(tokens) & TITULO_GRUPO)
    if nd <= 0.5 * n_resp and (nd <= MAX_OPCIONES or (grupo and nd <= min(100, 0.3 * n_resp))):
        if grupo:
            return "segmento", f"Pocos valores repetidos y el título sugiere un grupo ({' '.join(tokens)}).", \
                {"opciones": _opciones(vc)}
        return "seleccion_unica", "Pocos valores distintos que se repiten: parecen opciones a elegir.", \
            {"opciones": _opciones(vc)}

    # 10. abierta
    palabras = m.str.count(r"\s+").mean() + 1
    if palabras >= 3 or nd > 0.5 * n_resp:
        return "abierta", f"Textos largos y casi todos distintos (promedio {palabras:.0f} palabras).", {}
    return "seleccion_unica", "Respuestas cortas que se repiten: parecen opciones a elegir.", {"opciones": _opciones(vc)}


def detectar(df: pd.DataFrame) -> dict:
    n = len(df)
    preguntas = []
    for i, col in enumerate(str(c) for c in df.columns):
        vals = _valores(df.iloc[:, i])  # por posición: tolera títulos repetidos
        vc = vals.value_counts()
        # 1. sin datos / constante
        if len(vc) == 0:
            tipo, motivo, extra = "sin_datos", "La columna está vacía.", {}
        elif len(vc) == 1:
            tipo, motivo, extra = "constante", "Tiene el mismo valor en todas las filas (por ejemplo, el enunciado de la pregunta).", {}
        else:
            tipo, motivo, extra = _clasificar(col, vals, vc)
        preguntas.append({
            "columna": col, "tipo": tipo, "motivo": motivo,
            "n_respuestas": len(vals), "n_vacias": n - len(vals), "valores_distintos": len(vc),
            "ejemplos": [_recortar(v) for v in vals.drop_duplicates().head(3)], **extra,
        })

    advertencias = []
    if not any(p["tipo"] == "abierta" for p in preguntas):
        advertencias.append("Esta encuesta no tiene preguntas abiertas. El análisis de preguntas cerradas llegará pronto.")
    if n < 10:
        advertencias.append(f"La encuesta tiene muy pocas respuestas ({n}); los resultados serán poco representativos.")
    advertencias += [f"La columna «{p['columna']}» tiene más de la mitad de sus respuestas vacías."
                     for p in preguntas if p["n_vacias"] > n / 2]
    return {"n_filas": n, "preguntas": preguntas, "advertencias": advertencias}
