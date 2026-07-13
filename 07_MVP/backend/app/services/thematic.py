"""
Capa 2 — Análisis temático asistido por IA.

Flujo metodológico (no caja negra):
1. Claude PROPONE categorías a partir del marco teórico + muestra de respuestas.
2. El analista VALIDA, edita o descarta cada categoría (vía frontend).
3. Claude CODIFICA cada respuesta solo contra categorías validadas,
   entregando justificación y confianza por asignación.
4. El analista puede RE-CODIFICAR manualmente; todo queda en el audit log.

Los prompts (system + instrucciones de output) se cargan desde prompt_store.py
y son editables en vivo desde el panel de administración sin reiniciar el servidor.
El proveedor de IA es intercambiable: este módulo es el único punto de
contacto con la API (ver DEC-05).
"""
from __future__ import annotations

import json
import os
import re
from typing import Optional

from anthropic import Anthropic
from dotenv import load_dotenv

from app import prompt_store  # carga dinámica — cambios en vivo sin reiniciar

load_dotenv()

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")

_client: Optional[Anthropic] = None


def client() -> Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY no configurada. Copia backend/.env.example a backend/.env y agrega tu key."
            )
        _client = Anthropic(api_key=api_key)
    return _client


def _extract_json(text: str):
    """Extrae el primer bloque JSON de la respuesta del modelo."""
    match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError(f"El modelo no devolvió JSON parseable: {text[:300]}")
    return json.loads(match.group(0))


def _call(system: str, user: str, max_tokens: int = 4000) -> str:
    msg = client().messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text


# ---------- Propuesta de categorías ----------

def propose_categories(marco_teorico: str, sample_texts: list[str]) -> list[dict]:
    p = prompt_store.get_prompts()["propose_categories"]
    system = p["system"]
    instructions = p["instructions"]

    sample = "\n".join(f"- {t}" for t in sample_texts[:60])
    data_section = (
        "MARCO TEÓRICO DEL PROYECTO:\n"
        + (marco_teorico or "No definido — usa análisis temático inductivo (Braun & Clarke).")
        + "\n\nMUESTRA DE RESPUESTAS ABIERTAS:\n"
        + sample
    )
    user = data_section + "\n\n" + instructions

    data = _extract_json(_call(system, user))
    return data["categorias"] if isinstance(data, dict) else data


# ---------- Codificación ----------

def codify_batch(marco_teorico: str, categories: list[dict], batch: list[dict]) -> list[dict]:
    """batch: [{id, text}] → [{response_id, assignments: [{category_id, rationale, confidence}]}]"""
    p = prompt_store.get_prompts()["codify"]
    system = p["system"]
    instructions = p["instructions"]

    codebook = "\n".join(
        '- id "' + c["id"] + '" | ' + c["nombre"] + ": " + c["definicion"]
        + " | Incluye: " + c.get("criterios_inclusion", "")
        + " | Excluye: " + c.get("criterios_exclusion", "")
        for c in categories
    )
    respuestas = "\n".join("[" + r["id"] + "] " + r["text"] for r in batch)

    data_section = (
        "MARCO TEÓRICO: " + (marco_teorico or "Análisis temático inductivo.")
        + "\n\nLIBRO DE CÓDIGOS (validado por el analista):\n"
        + codebook
        + "\n\nRESPUESTAS A CODIFICAR:\n"
        + respuestas
    )
    user = data_section + "\n\n" + instructions

    data = _extract_json(_call(system, user, max_tokens=8000))
    return data["codificaciones"]


def codify_all(
    marco_teorico: str,
    categories: list[dict],
    responses: list[dict],
    batch_size: int = 25,
    progress_cb=None,
) -> list[dict]:
    results = []
    for i in range(0, len(responses), batch_size):
        batch = responses[i : i + batch_size]
        results.extend(codify_batch(marco_teorico, categories, batch))
        if progress_cb:
            progress_cb(min(i + batch_size, len(responses)), len(responses))
    return results


# ---------- Interpretación léxica ----------

def interpret_lexical(marco_teorico: str, lexical_data: dict) -> str:
    p = prompt_store.get_prompts()["interpret_lexical"]
    system = p["system"]
    instructions = p["instructions"]

    top_terms = ", ".join(t["term"] for t in lexical_data.get("top_terms", [])[:12])
    top_bigrams = ", ".join(b["bigram"] for b in lexical_data.get("top_bigrams", [])[:8])
    sent = lexical_data.get("sentiment_distribution", {})
    n = lexical_data.get("n_responses", 0)

    data_section = (
        "MARCO TEÓRICO: " + (marco_teorico or "Análisis temático inductivo (Braun & Clarke).")
        + "\n\nANÁLISIS LÉXICO (" + str(n) + " respuestas):"
        + "\n- Términos más frecuentes: " + top_terms
        + "\n- Bigramas destacados: " + top_bigrams
        + "\n- Sentimiento: " + str(sent)
    )
    user = data_section + "\n\n" + instructions

    return _call(system, user, max_tokens=500)


# ---------- Informe cualitativo (Fase 2) ----------

def generate_qualitative_report(
    marco_teorico: str,
    categories: list[dict],
    codings: dict,
    responses: list[dict],
    lexical_data: Optional[dict],
    progress_cb=None,
) -> str:
    p = prompt_store.get_prompts()["qualitative_report"]
    system = p["system"]
    instructions = p["instructions"]

    # Agregar conteos y ejemplos por categoría
    cat_counts: dict = {}
    cat_examples: dict = {}
    resp_map = {r["id"]: r["text"] for r in responses}

    for rid, assignments in codings.items():
        text = resp_map.get(rid, "")
        for a in assignments:
            cid = a.get("category_id", "SIN_CATEGORIA")
            cat_counts[cid] = cat_counts.get(cid, 0) + 1
            if cid not in cat_examples:
                cat_examples[cid] = []
            if len(cat_examples[cid]) < 3:
                conf = a.get("confidence")
                conf_str = f"{conf:.2f}" if isinstance(conf, (int, float)) else "?"
                cat_examples[cid].append('"' + text[:180] + '" (conf. ' + conf_str + ")")

    total_coded = len(codings)
    total_responses = len(responses)

    cat_section = ""
    for c in sorted(categories, key=lambda x: -cat_counts.get(x["id"], 0)):
        count = cat_counts.get(c["id"], 0)
        pct = (count / total_coded * 100) if total_coded > 0 else 0
        examples = cat_examples.get(c["id"], [])
        cat_section += (
            "\nCATEGORÍA: " + c["nombre"]
            + "\n  Definición: " + c["definicion"]
            + "\n  Frecuencia: " + str(count) + " respuestas (" + f"{pct:.1f}" + "% del total codificado)"
            + "\n  Incluye: " + c.get("criterios_inclusion", "")
            + "\n  Excluye: " + c.get("criterios_exclusion", "")
            + "\n  Ejemplos: " + ("; ".join(examples) if examples else "(sin ejemplos aún)")
            + "\n"
        )

    sent_summary = ""
    if lexical_data:
        sent = lexical_data.get("sentiment_distribution", {})
        top_terms = ", ".join(t["term"] for t in lexical_data.get("top_terms", [])[:10])
        sent_summary = (
            "\nDistribución de sentimiento: " + str(sent)
            + "\nTérminos léxicos más frecuentes: " + top_terms
        )

    data_section = (
        "MARCO TEÓRICO DEL PROYECTO:\n"
        + (marco_teorico or "Análisis temático inductivo (Braun & Clarke).")
        + "\n\nDATOS DEL CORPUS:"
        + "\n- Total de respuestas: " + str(total_responses)
        + "\n- Respuestas codificadas: " + str(total_coded)
        + sent_summary
        + "\n\nRESULTADOS DE LA CODIFICACIÓN TEMÁTICA:"
        + cat_section
    )
    user = data_section + "\n\n" + instructions

    if progress_cb is None:
        return _call(system, user, max_tokens=4000)

    # Streaming real: el progreso reportado son tokens efectivamente recibidos
    # del modelo (no un spinner falso). progress_cb recibe el texto acumulado.
    parts: list[str] = []
    with client().messages.stream(
        model=MODEL,
        max_tokens=4000,
        system=system,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        for chunk in stream.text_stream:
            parts.append(chunk)
            try:
                progress_cb("".join(parts))
            except Exception:
                pass  # el progreso nunca debe botar la generación
    return "".join(parts)
