"""
Schemas JSON de las salidas estructuradas que le pedimos a Claude.

Por qué existen: hasta septiembre 2026 el backend le pedía a Claude "responde
solo con JSON" y luego rescataba el bloque con un regex + json.loads. Eso se
rompía de dos formas distintas que se confundían entre sí: (a) comillas sin
escapar dentro de citas textuales y (b) respuestas truncadas por max_tokens.
Con tool use forzado (`tool_choice={"type": "tool", ...}`) la API entrega el
resultado ya parseado como `input` del bloque tool_use, validado contra el
schema: no hay regex, no hay fences ```json, no hay json.loads que pueda
fallar, y el JSON viene compacto (sin indentación) — menos tokens de salida.

El truncamiento sigue siendo posible (stop_reason=max_tokens) y se detecta
aparte; la diferencia es que ahora es la ÚNICA causa posible de "no hay JSON".

Los textos de los prompts (prompts.json) siguen describiendo el formato: sirven
como instrucción semántica para el modelo y quedan editables desde el panel.
El schema de aquí es la garantía mecánica de forma. Si cambias campos en el
prompt, cámbialos también acá.
"""
from __future__ import annotations

# ---------- Fragmentos reutilizables ----------

_STR = {"type": "string"}
_NUM = {"type": "number"}
_INT = {"type": "integer"}

# {"clave": número} — desgloses por metadata (rol, herramienta, carrera...)
_COUNT_MAP = {"type": "object", "additionalProperties": _INT}

_BREAKDOWN = {
    "type": "object",
    "description": "Desglose de respondentes por campo de metadata: {campo: {valor: conteo}}",
    "additionalProperties": _COUNT_MAP,
}

_QUOTE = {
    "type": "object",
    "properties": {
        "quote": {"type": "string", "description": "Cita textual exacta, sin editar"},
        "respondent_profile": _STR,
        "rationale": {"type": "string", "description": "Una frase: por qué es representativa"},
    },
    "required": ["quote", "respondent_profile", "rationale"],
}

_VARIATION = {
    "type": "object",
    "properties": {"variation": _STR, "prevalence_note": _STR},
    "required": ["variation", "prevalence_note"],
}

# ---------- Prompt 1: análisis por respondente ----------

ANALYZE_RESPONDENT = {
    "name": "registrar_analisis_respondente",
    "description": "Registra el análisis estructurado de UNA respuesta abierta en contexto.",
    "input_schema": {
        "type": "object",
        "properties": {
            "respondent_id": _STR,
            "is_valid": {"type": "boolean"},
            "rejection_reason": {"type": ["string", "null"]},
            "subtopics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subtopic_name": _STR,
                        "context_connection": {
                            "type": "object",
                            "properties": {
                                "closed_question_id": _STR,
                                "closed_question_label": _STR,
                                "closed_answer": _STR,
                                "relevance_explanation": _STR,
                            },
                        },
                        "evidence_quote": {"type": "string", "description": "Cita exacta del texto"},
                        "analysis_cluster": _STR,
                    },
                    "required": ["subtopic_name", "evidence_quote", "analysis_cluster"],
                },
            },
            "respondent_profile_line": _STR,
            "metadata_snapshot": {"type": "object", "additionalProperties": _STR},
        },
        "required": ["is_valid", "subtopics", "respondent_profile_line"],
    },
}

# ---------- Prompt 2 (corpus chico, una sola llamada) ----------

_CLUSTER_FINAL = {
    "type": "object",
    "properties": {
        "cluster_name": _STR,
        "prevalence": {
            "type": "object",
            "properties": {"count": _INT, "percentage": _NUM},
            "required": ["count"],
        },
        "breakdown_by_metadata": _BREAKDOWN,
        "representative_quotes": {"type": "array", "items": _QUOTE, "maxItems": 3},
        "internal_variations": {"type": "array", "items": _VARIATION, "maxItems": 3},
    },
    "required": ["cluster_name", "prevalence", "representative_quotes"],
}

SYNTHESIZE_CLUSTERS = {
    "name": "registrar_sintesis_clusters",
    "description": "Registra la síntesis final de clusters del corpus completo.",
    "input_schema": {
        "type": "object",
        "properties": {
            "respondents_analyzed": {
                "type": "object",
                "properties": {
                    "total": _INT, "valid": _INT, "rejected": _INT,
                    "rejection_breakdown": _COUNT_MAP,
                },
            },
            "clusters": {"type": "array", "items": _CLUSTER_FINAL},
        },
        "required": ["clusters"],
    },
}

# ---------- Prompt 2a (map): clusters candidatos de UNA tanda ----------

_CLUSTER_CANDIDATE = {
    "type": "object",
    "properties": {
        "cluster_name": _STR,
        "member_count": {"type": "integer", "description": "Respondentes de esta tanda que lo mencionan"},
        "member_ids": {
            "type": "array", "items": _STR,
            "description": "IDs de los respondentes de esta tanda que integran el cluster",
        },
        "breakdown_by_metadata": _BREAKDOWN,
        "quote_candidates": {
            "type": "array", "items": _QUOTE, "maxItems": 3,
            "description": "Hasta 3 citas candidatas (la selección final se hace al fusionar)",
        },
        "internal_variations": {"type": "array", "items": _VARIATION, "maxItems": 3},
    },
    "required": ["cluster_name", "member_count", "quote_candidates"],
}

SYNTHESIZE_CLUSTERS_PARTIAL = {
    "name": "registrar_clusters_tanda",
    "description": "Registra los clusters candidatos identificados en una tanda parcial del corpus.",
    "input_schema": {
        "type": "object",
        "properties": {"clusters": {"type": "array", "items": _CLUSTER_CANDIDATE}},
        "required": ["clusters"],
    },
}

# ---------- Prompt 2b (reduce, paso 1): mapa de nombres → cluster canónico ----------
# Por qué así: pedirle al modelo que fusione candidatos COMPLETOS (con citas,
# desgloses y variaciones) producía salidas más grandes que la entrada y no
# convergía (fusión nivel 2 con 3 grupos, nivel 3...). Aquí el modelo solo
# decide la semántica — qué nombres son el mismo fenómeno — con una salida
# de unos pocos tokens por candidato; la aritmética (conteos, IDs, desgloses)
# la hace Python de forma determinista.

MAP_CLUSTER_NAMES = {
    "name": "registrar_agrupacion_de_candidatos",
    "description": "Registra qué clusters candidatos son el mismo fenómeno.",
    "input_schema": {
        "type": "object",
        "properties": {
            "groups": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "canonical_name": _STR,
                        "candidate_indices": {"type": "array", "items": _INT},
                    },
                    "required": ["canonical_name", "candidate_indices"],
                },
            },
        },
        "required": ["groups"],
    },
}

# ---------- Prompt 2b (reduce, paso 2): citas representativas por cluster ----------

SELECT_QUOTES = {
    "name": "registrar_citas_representativas",
    "description": "Registra las citas representativas y variaciones definitivas de cada cluster.",
    "input_schema": {
        "type": "object",
        "properties": {
            "clusters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "cluster_name": _STR,
                        "representative_quotes": {"type": "array", "items": _QUOTE, "maxItems": 3},
                        "internal_variations": {"type": "array", "items": _VARIATION, "maxItems": 3},
                    },
                    "required": ["cluster_name", "representative_quotes"],
                },
            },
        },
        "required": ["clusters"],
    },
}

# ---------- Flujo clásico: propuesta de categorías y codificación ----------

PROPOSE_CATEGORIES = {
    "name": "registrar_categorias_propuestas",
    "description": "Registra las categorías temáticas propuestas para el libro de códigos.",
    "input_schema": {
        "type": "object",
        "properties": {
            "categorias": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "nombre": _STR, "definicion": _STR,
                        "criterios_inclusion": _STR, "criterios_exclusion": _STR,
                        "ejemplo": _STR,
                    },
                    "required": ["nombre", "definicion", "criterios_inclusion", "criterios_exclusion"],
                },
            },
        },
        "required": ["categorias"],
    },
}

CODIFY = {
    "name": "registrar_codificaciones",
    "description": "Registra la codificación de cada respuesta contra el libro de códigos.",
    "input_schema": {
        "type": "object",
        "properties": {
            "codificaciones": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "response_id": _STR,
                        "assignments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "category_id": _STR,
                                    "rationale": _STR,
                                    "confidence": _NUM,
                                },
                                "required": ["category_id", "rationale", "confidence"],
                            },
                        },
                    },
                    "required": ["response_id", "assignments"],
                },
            },
        },
        "required": ["codificaciones"],
    },
}
