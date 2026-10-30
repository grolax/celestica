"""Detección determinística (sin IA, sin costo) del tipo de cada columna de una encuesta.

`detectar(df)` es una función pura: lee un DataFrame y devuelve el cuerpo de la vista previa
(`n_filas`, `preguntas`, `advertencias`). Las reglas están documentadas en COMO_FUNCIONA.md.
Todo es vectorizado en pandas; las comparaciones por valor se hacen sobre los valores únicos.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

import pandas as pd

MAX_OPCIONES = 20
MAX_PARTES = 40  # opciones distintas admitidas en una selección múltiple (aunque cada opción sea una frase)
SI_NO = {"si", "no", "s", "n", "yes", "y", "true", "false", "verdadero", "falso", "1", "0"}
TITULO_ID = {"id", "rut", "folio", "email", "mail", "correo", "dni", "uuid", "matricula", "ip", "ipaddress"}
TITULO_GRUPO = {"tienda", "sede", "sucursal", "comuna", "region", "carrera", "area", "cargo", "sexo", "genero",
                "edad", "tramo", "asignatura", "facultad", "departamento", "ciudad", "pais", "curso", "seccion",
                "jornada", "zona", "educacional", "educacion"}
TITULO_ANIO = {"anio", "ano", "edad", "curso", "cursado", "semestre", "ciclo"}
EVALUA = r"evalu|calific|satisf|opin"  # "¿Cómo evalúa la sede?" pregunta por un servicio, no por el grupo
MULTIPLE = r"seleccion|mas de una|hasta \d"  # pista de título: "Selecciona…", "Puedes seleccionar más de una", "hasta 3"
FECHA = r"^\d{4}-\d{1,2}-\d{1,2}|^\d{4}/\d{1,2}/\d{1,2}|^\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}"


TIPOS = {"abierta", "seleccion_unica", "seleccion_multiple", "segmento", "escala", "nps", "si_no",
         "numerica", "fecha", "identificador", "constante", "sin_datos"}


def _sin_tildes(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", t.lower()) if not unicodedata.combining(c))


def _opciones(vc: pd.Series) -> list[dict]:
    return [{"valor": str(v), "n": int(n)} for v, n in vc.head(MAX_OPCIONES).items()]


def _pl(n: int, uno: str, otros: str) -> str:
    return f"{n} {uno if n == 1 else otros}"


def _reconstruir(vc: pd.Series, sep: str) -> tuple[list, Counter]:
    """Opciones de una selección múltiple, volviendo a unir las que traen el separador adentro.

    Google Forms une las opciones marcadas con ", ": una opción con coma ("Subsidios (DS1, DS19)") llega partida.
    Se une (1) lo que queda dentro de un paréntesis sin cerrar, (2) un trozo que empieza con minúscula al anterior
    (las alternativas de Google Forms empiezan con mayúscula), salvo que ese trozo también sea una respuesta completa, y
    (3) los trozos A y B que siempre van juntos: B solo aparece justo después de A y A siempre va seguido de B.
    Si A aparece a veces sin B, queda ambiguo y se deja separado.
    Devuelve ([(opciones de la respuesta, n)], conteo de cada opción).
    """
    filas = []
    solos = {v.strip() for v in vc.index}  # un trozo que también es una respuesta completa es una opción real
    for v, n in vc.items():
        ch = [c.strip() for c in v.split(sep) if c.strip()]
        out, i = [], 0
        while i < len(ch):
            j, txt = i, ch[i]
            while "(" in txt and txt.count("(") > txt.count(")") and j + 1 < len(ch):
                j += 1
                txt += f"{sep} {ch[j]}"
            if "(" in txt and txt.count("(") > txt.count(")"):  # el paréntesis nunca cierra: no se une
                j, txt = i, ch[i]
            if out and txt[0].islower() and txt not in solos:  # continuación ("pero…", "fondos mutuos…"), no una opción
                out[-1] += f"{sep} {txt}"
            else:
                out.append(txt)
            i = j + 1
        filas.append((out, int(n)))
    while True:
        ca, cp = Counter(), Counter()
        for ch, n in filas:
            for x in ch:
                ca[x] += n
            for par in zip(ch, ch[1:]):
                cp[par] += n
        ligas = {par for par, k in cp.items() if k == ca[par[0]] == ca[par[1]]}
        if not ligas:
            return filas, ca
        nuevas = []
        for ch, n in filas:
            out = []
            for x in ch:
                if out and (out[-1], x) in ligas:
                    out[-1] += f"{sep} {x}"
                else:
                    out.append(x)
            nuevas.append((out, n))
        filas = nuevas


def _recortar(v: str) -> str:
    return v if len(v) <= 120 else v[:120] + "…"


def _valores(s: pd.Series) -> pd.Series:
    """Valores no vacíos como texto. Enteros que vienen como float (Excel) quedan sin '.0'."""
    if pd.api.types.is_float_dtype(s) and (s.dropna() % 1 == 0).all():
        s = s.astype("Int64")
    v = s.astype("string").str.strip().dropna()
    return v[v != ""]


def _clasificar(col: str, vals: pd.Series, vc: pd.Series, n: int) -> tuple[str, str, dict]:
    """Devuelve (tipo, motivo, extras) de una columna con valores; `n` es el total de filas."""
    n_resp, nd = len(vals), len(vc)
    titulo = _sin_tildes(col)
    tokens = re.findall(r"[a-z0-9]+", titulo)
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

    es_num = nd > 1 and pd.to_numeric(m.str.replace(",", ".", regex=False), errors="coerce").notna().mean() >= 0.95
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

    # 8. selección múltiple: las opciones (ya reconstruidas) son pocas y se repiten, aunque cada una sea una frase larga
    pista = bool(re.search(MULTIPLE, titulo))
    umbral = 0.05 if pista else 0.2
    for sep in (";", ","):
        if m.str.contains(sep, regex=False).mean() < umbral or m.str.split(sep).explode().str.strip().nunique() > 3 * MAX_PARTES:
            continue
        filas, conteo = _reconstruir(vc, sep)
        total = sum(conteo.values())
        # casi todas las respuestas con una sola opción: la coma era parte de la opción, no un separador
        if sum(k for ch, k in filas if len(ch) > 1) / n_resp < umbral:
            continue
        pc = pd.Series(dict(conteo.most_common()))
        if len(pc) > MAX_PARTES or total < 2 * len(pc) or pc.head(MAX_OPCIONES).sum() < 0.8 * total:
            continue
        # pocos valores completos que todos se repiten y ningún trozo aparece solo en otra respuesta: son alternativas con comas
        # shortcut: una "marca exactamente dos" donde nadie elige una sola opción se toma como selección única; revisar en T-012.
        if nd <= 0.1 * n_resp and vc.min() >= 2 and not any(x in vc.index for ch, _ in filas if len(ch) > 1 for x in ch):
            continue
        return "seleccion_multiple", f'Cada respuesta puede tener varias opciones separadas por "{sep}".', {"opciones": _opciones(pc)}

    # 9. segmento / selección única. En texto la pista de grupo vale con cualquier largo de título (salvo que evalúe algo).
    clave = sorted(set(tokens) & TITULO_GRUPO)
    escritas = {_sin_tildes(w): w for w in re.findall(r"[^\W_]+", col.lower())}  # "región", no "region"
    grupo = bool(clave) and (corto or not re.search(EVALUA, titulo))
    palabras = m.str.count(r"\s+").mean() + 1
    escasa = n_resp < 10 and n_resp < n / 2  # casi toda la columna está vacía: no alcanza para hablar de texto libre
    if escasa or (nd <= 0.5 * n_resp and (nd <= MAX_OPCIONES or (grupo and nd <= min(100, 0.3 * n_resp))
                                          or (n_resp >= 30 and nd <= 0.1 * n_resp)))             or (palabras < 3 and nd <= 0.5 * n_resp):
        if grupo:
            return "segmento", f"{_pl(nd, 'valor distinto', 'valores distintos')} en {_pl(n_resp, 'respuesta', 'respuestas')} y el título sugiere un grupo ({', '.join(escritas.get(k, k) for k in clave)}).",                 {"opciones": _opciones(vc)}
        return "seleccion_unica", f"{_pl(nd, 'valor distinto', 'valores distintos')} en {_pl(n_resp, 'respuesta', 'respuestas')}: parecen opciones a elegir.",             {"opciones": _opciones(vc)}

    # 10. abierta
    if palabras >= 3:
        return "abierta", f"Textos de {_pl(round(palabras), 'palabra', 'palabras')} en promedio, con {_pl(nd, 'respuesta distinta', 'respuestas distintas')} de {n_resp}.", {}
    return "abierta", f"Respuestas cortas ({_pl(round(palabras), 'palabra', 'palabras')} en promedio) y casi todas distintas ({nd} de {n_resp}).", {}


def detectar(df: pd.DataFrame) -> dict:
    n = len(df)
    preguntas = []
    for i, col in enumerate(str(c) for c in df.columns):
        vals = _valores(df.iloc[:, i])  # por posición: tolera títulos repetidos
        vc = vals.value_counts()
        # 1. sin datos / constante (constante: todas las filas, o casi, tienen el mismo valor)
        if len(vc) == 0:
            tipo, motivo, extra = "sin_datos", "La columna está vacía.", {}
        elif len(vc) == 1 and len(vals) >= 0.9 * n:
            tipo, motivo, extra = "constante", "Tiene el mismo valor en todas las filas (por ejemplo, el enunciado de la pregunta).", {}
        else:
            tipo, motivo, extra = _clasificar(col, vals, vc, n)
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


def contexto_por_defecto(tipo: str, titulo: str) -> bool:
    """Qué preguntas van como contexto a la IA si el usuario no decide: solo segmentos de género/sexo/edad."""
    return tipo == "segmento" and bool(re.search(r"\b(genero|sexo|edad)\b", _sin_tildes(titulo)))
