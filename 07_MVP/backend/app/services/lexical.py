"""
Capa 1 — Análisis léxico automático.

Frecuencias de términos, bigramas, co-ocurrencias y sentimiento básico
por lexicón en español. Sin dependencias pesadas de NLP: para el MVP la
transparencia del método importa más que la sofisticación (cada conteo
es verificable a mano, lo que refuerza el posicionamiento de auditabilidad).
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from itertools import combinations

# Stopwords español + jerga universitaria chilena que no aporta señal
STOPWORDS = set("""
a al algo alguna algunas alguno algunos ante antes aunque bajo bien cada como con contra cual cuales cuando de del
desde donde dos durante e el ella ellas ellos en entre era eran es esa esas ese eso esos esta estas este esto estos
fue fueron ha haber habia han hasta hay la las le les lo los mas me mi mis mucho muy nada ni no nos nosotros o os
otra otras otro otros para pero poco por porque que quien se sea segun ser si sin sobre son su sus tal tambien
tanto te tener tiene tienen toda todas todo todos tras tu un una uno unos y ya yo
ser estar hacer ir dar ver
semestre ramo curso clase clases profesor profesora profe docente materia contenido contenidos estudiante
estudiantes alumno alumnos universidad asignatura programa
general gracias honestamente espero considere principal creo verdad opinion entiendo veces igual harto
""".split())

# Lexicón de sentimiento básico (es transparente y editable por el analista)
POSITIVE = set("""
excelente bueno buena buenos buenas bien mejor destacable destaco valoro genial claro clara claros claras
cercano cercana dispuesto dispuesta disposicion preocupa ayuda ayudar entretenida entretenidas entretenido
domina dominio experiencia profundidad seguridad confianza rapido rapida actualizada actualizado calidad
exigente comprometido comprometida motivacion agradezco gracias recomiendo aprende aprendizaje
""".split())

NEGATIVE = set("""
malo mala malos malas peor injusta injustas injusto monotona monotonas antigua antiguo desordenadas desordenado
eternas eterna dificil dificiles excesiva excesivo pesado pesada tarde nunca imposible falta faltan cuesta
incertidumbre demora cancela suspendio corriendo rapido confuso confusa problema problemas queja aburrida
aburrido lento lenta tedioso tediosa deficiente insuficiente
""".split())

# "rapido" aparece en ambos contextos; el negativo "va muy rapido" se captura por bigrama
NEGATIVE_BIGRAMS = {("muy", "rapido"), ("demasiado", "dificil"), ("no", "responde"), ("no", "hay"), ("no", "alcanza")}

TOKEN_RE = re.compile(r"[a-záéíóúüñ]+", re.IGNORECASE)


def normalize(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def tokenize(text: str, remove_stopwords: bool = True) -> list[str]:
    tokens = TOKEN_RE.findall(normalize(text))
    if remove_stopwords:
        tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    return tokens


def sentiment_score(text: str) -> dict:
    """Sentimiento por lexicón: (-1, 1). Transparente: devuelve los términos que gatillan el puntaje."""
    raw = TOKEN_RE.findall(normalize(text))
    pos_hits = [t for t in raw if t in POSITIVE]
    neg_hits = [t for t in raw if t in NEGATIVE]
    for a, b in zip(raw, raw[1:]):
        if (a, b) in NEGATIVE_BIGRAMS:
            neg_hits.append(f"{a} {b}")
    total = len(pos_hits) + len(neg_hits)
    score = 0.0 if total == 0 else (len(pos_hits) - len(neg_hits)) / total
    label = "neutro"
    if score > 0.2:
        label = "positivo"
    elif score < -0.2:
        label = "negativo"
    elif total > 0:
        label = "mixto"
    return {"score": round(score, 3), "label": label, "evidencia_positiva": pos_hits, "evidencia_negativa": neg_hits}


def analyze(responses: list[dict], top_n: int = 40) -> dict:
    """Análisis léxico completo sobre la lista de respuestas [{id, text, meta}]."""
    term_counter: Counter = Counter()
    bigram_counter: Counter = Counter()
    cooc_counter: Counter = Counter()
    sentiments = {}
    sentiment_dist = Counter()

    for r in responses:
        tokens = tokenize(r["text"])
        term_counter.update(tokens)
        bigram_counter.update(zip(tokens, tokens[1:]))
        # co-ocurrencia a nivel de respuesta (términos únicos)
        for pair in combinations(sorted(set(tokens)), 2):
            cooc_counter[pair] += 1
        s = sentiment_score(r["text"])
        sentiments[r["id"]] = s
        sentiment_dist[s["label"]] += 1

    return {
        "n_responses": len(responses),
        "top_terms": [{"term": t, "count": c} for t, c in term_counter.most_common(top_n)],
        "top_bigrams": [{"bigram": f"{a} {b}", "count": c} for (a, b), c in bigram_counter.most_common(20)],
        "top_cooccurrences": [
            {"pair": f"{a} + {b}", "count": c}
            for (a, b), c in cooc_counter.most_common(20) if c >= 3
        ],
        "sentiment_distribution": dict(sentiment_dist),
        "sentiment_by_response": sentiments,
        "method_note": (
            "Frecuencias sobre tokens normalizados (sin tildes, sin stopwords español/jerga académica). "
            "Sentimiento por lexicón transparente con evidencia por respuesta; el lexicón es editable y auditable."
        ),
    }
