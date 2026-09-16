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

Cómo se habla con Claude (decisiones de septiembre 2026, tras el incidente de
truncamiento con 122 respondentes — ver COMO_FUNCIONA.md):

- Toda salida estructurada se pide con TOOL USE FORZADO y un schema
  (schemas_v2.py). La API entrega el JSON ya parseado; desaparece el patrón
  regex + json.loads y con él los errores "Expecting ',' delimiter".
- Todas las llamadas van por STREAMING (`messages.stream`). No es por la barra
  de progreso: el SDK rechaza llamadas no-streaming con max_tokens grandes
  ("Streaming is required for operations that may take longer than 10
  minutes"), y necesitamos techos altos para no truncar.
- El techo de max_tokens de cada llamada se acota al LÍMITE REAL del modelo,
  consultado a la API una vez (`model_max_output_tokens`), no a un número
  elegido a ojo.
- Los pasos cuyo tamaño de salida depende del tamaño del corpus (síntesis de
  clusters) NO dependen de que "quepan" en max_tokens: se parten por
  presupuesto de tokens de entrada y, si aun así una tanda se trunca, se
  DIVIDE en dos y se reintenta (recursivo). La fusión de clusters separa
  semántica (el modelo agrupa NOMBRES de candidatos, salida chica) de
  aritmética (Python une IDs, suma desgloses, calcula prevalencia) y la
  elección de citas va en tandas acotadas. Subir max_tokens nunca es la
  solución: un corpus más grande siempre puede volver a superarlo.
- Cada llamada queda registrada en disco con tokens, costo, stop_reason y
  (si falló) el texto crudo — ver claude_log.py.
"""
from __future__ import annotations

import contextvars
import hashlib
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

from anthropic import Anthropic, BadRequestError
from dotenv import load_dotenv

from app import prompt_store  # carga dinámica — cambios en vivo sin reiniciar
from app.services import claude_log, schemas_v2

load_dotenv(override=True)

# Versión del módulo, expuesta en /api/admin/health para confirmar desde la UI
# que el backend corriendo cargó este archivo y no una versión anterior.
THEMATIC_VERSION = "3.0.0-structured-2026-09-14"

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
# Modelo para el flujo multi-prompt V2 (default: el mismo Sonnet).
MODEL_V2 = os.environ.get("CLAUDE_MODEL_REPORT_V2", MODEL)
# Workers paralelos para el análisis por respondente (Prompt 1) y las tandas.
V2_MAX_WORKERS = int(os.environ.get("REPORT_V2_MAX_WORKERS", "6"))

# ---------- Presupuestos de tokens ----------
# Aproximación de tokens a partir de caracteres. Calibrada con datos reales
# del incidente: 91.945 caracteres de prompt = 27.837 tokens (3,3 chars/token
# en español con JSON). Se usa 3,0 para sobreestimar un poco. No se usa
# count_tokens de la API para partir tandas porque serían cientos de llamadas
# extra por informe; la garantía real de que nada se trunca es el split
# recursivo, no la exactitud del conteo.
_CHARS_PER_TOKEN = 3.0
# Máximo de tokens de ENTRADA (solo datos) por tanda de síntesis. Con ~700
# tokens por análisis individual, 10.000 tokens ≈ 14 respondentes por tanda;
# la salida de una tanda así ronda los 3-5k tokens, lejos de cualquier techo.
SYNTHESIS_BATCH_INPUT_TOKENS = int(os.environ.get("SYNTHESIS_BATCH_INPUT_TOKENS", "10000"))
# Máximo de tokens de entrada (candidatos) por llamada de fusión.
MERGE_INPUT_TOKENS = int(os.environ.get("MERGE_INPUT_TOKENS", "16000"))
# Techo de salida para las llamadas de síntesis/fusión/informe. Es alto a
# propósito: max_tokens no cuesta nada si no se usa, y solo se paga lo que
# el modelo efectivamente escribe. Se acota al límite real del modelo.
LARGE_OUTPUT_TOKENS = int(os.environ.get("CLAUDE_LARGE_OUTPUT_TOKENS", "32000"))
# Niveles máximos de fusión jerárquica antes de caer al fusionador Python.
_MAX_MERGE_LEVELS = 6

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


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / _CHARS_PER_TOKEN))


# ---------- Límite real de salida del modelo ----------

_model_output_limits: dict[str, int] = {}
_FALLBACK_OUTPUT_LIMIT = 8192  # conservador; solo si la API no responde a la sonda


def model_max_output_tokens(model: str) -> int:
    """Máximo real de max_tokens que acepta el modelo, consultado a la API.

    La API rechaza (400, sin costo) un max_tokens mayor al permitido y dice
    cuál es el máximo: "max_tokens: X > 128000, which is the maximum allowed
    number of output tokens for claude-sonnet-4-6". Se sondea una vez por
    proceso y se cachea. CLAUDE_MAX_OUTPUT_TOKENS en .env lo fija a mano
    (útil en tests y si la sonda no está disponible).
    """
    env = os.environ.get("CLAUDE_MAX_OUTPUT_TOKENS")
    if env:
        return int(env)
    if model in _model_output_limits:
        return _model_output_limits[model]
    limit = _FALLBACK_OUTPUT_LIMIT
    try:
        with client().messages.stream(
            model=model, max_tokens=10_000_000, messages=[{"role": "user", "content": "hi"}]
        ) as stream:
            stream.get_final_message()
    except BadRequestError as e:
        m = re.search(r">\s*(\d+)", str(e))
        if m:
            limit = int(m.group(1))
        else:
            claude_log.log_warning(f"No pude leer el límite de salida de {model} en: {e}")
    except Exception as e:
        claude_log.log_warning(f"Sonda de límite de salida falló para {model}: {e}")
    _model_output_limits[model] = limit
    claude_log.log_info(f"Límite de salida del modelo {model}: {limit} tokens")
    return limit


def _cap_tokens(requested: int, model: str) -> int:
    return max(1, min(requested, model_max_output_tokens(model)))


# ---------- Errores ----------

class _TruncatedResponseError(RuntimeError):
    """La respuesta del modelo se cortó por max_tokens (stop_reason=max_tokens).

    No se arregla reintentando igual: el output necesario es más grande que
    el límite. Quien la atrapa decide: dividir el trabajo (pasos que dependen
    del tamaño del corpus) o reportar un error claro (pasos acotados por el
    propio prompt, donde esto no debería pasar nunca).
    """

    def __init__(self, label: str, max_tokens: int, model: str, raw_len: int):
        super().__init__(
            f"La respuesta de Claude en '{label}' se cortó por max_tokens={max_tokens} "
            f"(modelo {model}, {raw_len} caracteres recibidos, stop_reason=max_tokens)."
        )
        self.label = label
        self.max_tokens = max_tokens


class _StructuredOutputError(RuntimeError):
    """El modelo no devolvió el bloque tool_use esperado (no debería ocurrir con
    tool_choice forzado; se reintenta una vez y luego se reporta)."""


# ---------- Llamada base ----------

def _invoke(
    *,
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    label: str,
    tool: Optional[dict] = None,
    on_text: Optional[Callable[[str], None]] = None,
):
    """Una llamada a Claude, por streaming, con registro completo.

    - tool=None: devuelve el texto (markdown/prosa).
    - tool=schema: fuerza tool use y devuelve el `input` ya parseado (dict).
    Lanza _TruncatedResponseError si stop_reason == "max_tokens".
    """
    max_tokens = _cap_tokens(max_tokens, model)
    kwargs: dict = dict(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user}],
    )
    if tool is not None:
        kwargs["tools"] = [tool]
        kwargs["tool_choice"] = {"type": "tool", "name": tool["name"]}
    t0 = time.time()
    try:
        with client().messages.stream(**kwargs) as stream:
            if on_text is not None and tool is None:
                parts: list[str] = []
                for chunk in stream.text_stream:
                    parts.append(chunk)
                    try:
                        on_text("".join(parts))
                    except Exception:
                        pass  # el progreso nunca debe botar la generación
            msg = stream.get_final_message()
    except Exception as e:
        claude_log.record_call(
            label=label, model=model, max_tokens=max_tokens, stop_reason=None,
            input_tokens=0, output_tokens=0, duration_s=time.time() - t0, ok=False,
            error=f"{type(e).__name__}: {e}",
        )
        raise

    usage = getattr(msg, "usage", None)
    in_tok = int(getattr(usage, "input_tokens", 0) or 0)
    out_tok = int(getattr(usage, "output_tokens", 0) or 0)
    text = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text")
    payload = None
    if tool is not None:
        for b in msg.content:
            if getattr(b, "type", "") == "tool_use":
                payload = b.input
                break
    raw = json.dumps(payload, ensure_ascii=False) if payload else text
    truncated = msg.stop_reason == "max_tokens"
    claude_log.record_call(
        label=label, model=model, max_tokens=max_tokens, stop_reason=msg.stop_reason,
        input_tokens=in_tok, output_tokens=out_tok, duration_s=time.time() - t0,
        ok=not truncated, error="truncada por max_tokens" if truncated else None,
        raw_output=raw, extra={"structured": tool is not None, "raw_chars": len(raw)},
    )
    if truncated:
        raise _TruncatedResponseError(label, max_tokens, model, len(raw))
    if tool is not None:
        if not isinstance(payload, dict):
            raise _StructuredOutputError(
                f"Claude no devolvió el bloque estructurado esperado en '{label}' "
                f"(stop_reason={msg.stop_reason}). Texto: {text[:300]}"
            )
        return payload
    return text


def _call_text(system: str, user: str, *, label: str, max_tokens: int,
               model: str = MODEL, on_text: Optional[Callable[[str], None]] = None) -> str:
    """Salida en prosa/markdown. Su largo lo acota el propio prompt (no el
    corpus), así que un truncamiento aquí es un error de configuración y se
    reporta como tal, con contexto."""
    try:
        return _invoke(model=model, system=system, user=user, max_tokens=max_tokens,
                       label=label, on_text=on_text)
    except _TruncatedResponseError as e:
        raise RuntimeError(
            f"{e} El largo de este texto lo fija el prompt, no el corpus: revisa el "
            f"prompt '{label}' en el panel de administración o sube "
            "CLAUDE_LARGE_OUTPUT_TOKENS en .env."
        ) from e


def _call_structured(system: str, user: str, *, tool: dict, label: str, max_tokens: int,
                     model: str = MODEL, attempts: int = 2) -> dict:
    """Salida JSON garantizada por schema (tool use forzado).

    Reintenta solo si el modelo no emitió el bloque estructurado (rarísimo con
    tool_choice forzado). El truncamiento NO se reintenta aquí: se propaga
    como _TruncatedResponseError para que el llamador divida el trabajo.
    """
    last: Optional[Exception] = None
    for attempt in range(1, attempts + 1):
        try:
            return _invoke(model=model, system=system, user=user, max_tokens=max_tokens,
                           label=f"{label}" + (f" (reintento {attempt})" if attempt > 1 else ""),
                           tool=tool)
        except _StructuredOutputError as e:
            last = e
    raise RuntimeError(
        f"No se obtuvo salida estructurada de Claude en '{label}' tras {attempts} intento(s): {last}"
    ) from last


def _submit_with_context(pool: ThreadPoolExecutor, fn, *args, **kwargs):
    """Envía trabajo al pool conservando las contextvars (project_id del log).
    Cada tarea necesita SU copia del contexto: un Context no puede entrarse
    desde dos hilos a la vez."""
    ctx = contextvars.copy_context()
    return pool.submit(ctx.run, fn, *args, **kwargs)


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
    data = _call_structured(
        system, user, tool=schemas_v2.PROPOSE_CATEGORIES,
        label="propuesta de categorías", max_tokens=8000,
    )
    return data["categorias"]


# ---------- Codificación ----------

def codify_batch(marco_teorico: str, categories: list[dict], batch: list[dict]) -> list[dict]:
    """batch: [{id, text}] → [{response_id, assignments: [{category_id, rationale, confidence}]}]

    Si Claude falla para este lote, el lote queda sin asignaciones en vez de
    tumbar la codificación completa del corpus: el resto de lotes sigue
    procesándose y estas respuestas quedan disponibles para recodificar
    manualmente desde la UI. El motivo queda en `codify_error` y en el log.
    """
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

    try:
        data = _call_structured(
            system, user, tool=schemas_v2.CODIFY,
            label=f"codificación de respuestas ({len(batch)})", max_tokens=16000,
        )
        return data["codificaciones"]
    except Exception as e:
        claude_log.log_warning(f"codify_batch falló ({len(batch)} respuestas): {e}")
        return [
            {"response_id": r["id"], "assignments": [], "codify_error": str(e)}
            for r in batch
        ]


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

    return _call_text(system, user, label="interpretación léxica", max_tokens=1000)


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

    # Streaming real: el progreso reportado son tokens efectivamente recibidos
    # del modelo (no un spinner falso). progress_cb recibe el texto acumulado.
    return _call_text(system, user, label="informe cualitativo v1", max_tokens=8000,
                      on_text=progress_cb)


# ---------- Informe cualitativo V2 — arquitectura multi-prompt ----------
#
# Flujo: Prompt 1 (análisis contextual por respondente, en paralelo)
#      → Prompt 2 (síntesis en clusters: map por tandas + reduce jerárquico)
#      → Prompt 3 (redacción del informe, una llamada)
#
# progress_cb (si se entrega) recibe: (stage: str, done: int, total: int)


def _analyze_respondent_v2(
    respondent_id: str,
    open_response_text: str,
    closed_responses: dict,
    respondent_metadata: dict,
    marco_teorico: str,
) -> dict:
    """Prompt 1: analiza UNA respuesta abierta en contexto de sus respuestas cerradas.

    Devuelve dict estructurado (schema ANALYZE_RESPONDENT). Si el modelo falla,
    retorna un análisis inválido con la razón — un respondente nunca debe
    botar el informe completo. Su salida está acotada por el prompt (1-3
    subtemas), así que 4000 tokens de techo sobran; si se truncara igual, se
    registra como error de análisis de ese respondente.
    """
    p = prompt_store.get_prompts()["analyze_respondent_v2"]
    data_section = (
        "ID DEL RESPONDENTE: " + respondent_id
        + "\n\nRESPUESTA ABIERTA:\n" + (open_response_text or "")
        + "\n\nCONTEXTO DEL RESPONDENTE (preguntas cerradas):\n"
        + json.dumps(closed_responses, ensure_ascii=False, indent=2)
        + "\n\nMETADATA:\n"
        + json.dumps(respondent_metadata, ensure_ascii=False, indent=2)
        + "\n\nMARCO TEÓRICO:\n"
        + (marco_teorico or "Análisis temático inductivo (Braun & Clarke).")
    )
    user = data_section + "\n\n" + p["instructions"]
    try:
        data = _call_structured(
            p["system"], user, tool=schemas_v2.ANALYZE_RESPONDENT,
            label=f"análisis del respondente {respondent_id}", max_tokens=4000, model=MODEL_V2,
        )
        data["respondent_id"] = respondent_id  # el ID lo fija el sistema, no el modelo
        data.setdefault("is_valid", False)
        data.setdefault("subtopics", [])
        data.setdefault("metadata_snapshot", respondent_metadata)
        return data
    except Exception as e:
        return {
            "respondent_id": respondent_id,
            "is_valid": False,
            "rejection_reason": f"error_de_analisis: {e}",
            "subtopics": [],
            "respondent_profile_line": "",
            "metadata_snapshot": respondent_metadata,
        }


def _rejection_breakdown(compact_analyses: list[dict]) -> dict:
    """Clasifica los rechazos (is_valid=False) en 3 baldes a partir del texto
    libre de `rejection_reason` (ver prompt analyze_respondent_v2, sección A) —
    sin gastar una llamada a Claude en algo que es un simple conteo."""
    counts = {"empty": 0, "off_topic": 0, "other": 0}
    for a in compact_analyses:
        if a.get("is_valid", False):
            continue
        reason = (a.get("rejection_reason") or "").lower()
        if any(k in reason for k in ("vac", "n/a", "nada", "no sé", "no se", "empty")):
            counts["empty"] += 1
        elif any(k in reason for k in ("off-topic", "off topic", "no responde", "fuera de tema")):
            counts["off_topic"] += 1
        else:
            counts["other"] += 1
    return counts


def _chunk_by_tokens(items: list[dict], budget_tokens: int) -> list[list[dict]]:
    """Parte una lista de dicts en tandas consecutivas cuyo tamaño estimado en
    tokens no supere `budget_tokens` (una tanda siempre tiene al menos 1 ítem).
    Por tokens y no por cantidad: dos corpus con la misma cantidad de
    respondentes pueden pesar el doble uno que el otro."""
    chunks: list[list[dict]] = []
    current: list[dict] = []
    current_tokens = 0
    for item in items:
        t = estimate_tokens(json.dumps(item, ensure_ascii=False))
        if current and current_tokens + t > budget_tokens:
            chunks.append(current)
            current, current_tokens = [], 0
        current.append(item)
        current_tokens += t
    if current:
        chunks.append(current)
    return chunks


def _marco(marco_teorico: str) -> str:
    return marco_teorico or "Análisis temático inductivo (Braun & Clarke)."


# ---- Prompt 2: síntesis (map) ----

def _synthesize_clusters_batch_v2(
    compact_batch: list[dict], marco_teorico: str, batch_label: str
) -> list[dict]:
    """Prompt 2a (map): clusters candidatos DENTRO de una tanda. No calcula
    prevalencia final — la tanda no conoce el total del corpus. Lanza
    _TruncatedResponseError si la salida no cupo (lo maneja el llamador)."""
    p = prompt_store.get_prompts()["synthesize_clusters_v2_partial"]
    data_section = (
        "ANÁLISIS INDIVIDUALES DE ESTA TANDA (" + str(len(compact_batch)) + " respondentes):\n"
        + json.dumps(compact_batch, ensure_ascii=False)
        + "\n\nMARCO TEÓRICO:\n" + _marco(marco_teorico)
    )
    user = data_section + "\n\n" + p["instructions"]
    data = _call_structured(
        p["system"], user, tool=schemas_v2.SYNTHESIZE_CLUSTERS_PARTIAL,
        label=f"síntesis de clusters — {batch_label} ({len(compact_batch)} resp.)",
        max_tokens=LARGE_OUTPUT_TOKENS, model=MODEL_V2,
    )
    return [c for c in data.get("clusters", []) if isinstance(c, dict)]


def _synthesize_batch_adaptive(
    compact_batch: list[dict], marco_teorico: str, batch_label: str
) -> list[dict]:
    """Sintetiza una tanda y, si su salida se trunca, la DIVIDE en dos mitades
    y reintenta cada una (recursivo). Así ninguna tanda depende de "caber":
    en el peor caso se llega a tandas de 1 respondente, cuya salida es
    trivialmente acotada. Los candidatos de ambas mitades se fusionan después
    con los de las demás tandas, igual que si hubieran sido tandas
    independientes desde el principio."""
    try:
        return _synthesize_clusters_batch_v2(compact_batch, marco_teorico, batch_label)
    except _TruncatedResponseError as e:
        if len(compact_batch) <= 1:
            raise RuntimeError(
                f"La síntesis de un solo respondente se truncó ({e}); esto indica un "
                "análisis individual anómalo. Revisa logs/claude_raw."
            ) from e
        mid = len(compact_batch) // 2
        claude_log.log_warning(
            f"{batch_label}: salida truncada con {len(compact_batch)} respondentes; "
            f"se divide en {mid} + {len(compact_batch) - mid}"
        )
        left = _synthesize_batch_adaptive(compact_batch[:mid], marco_teorico, batch_label + "a")
        right = _synthesize_batch_adaptive(compact_batch[mid:], marco_teorico, batch_label + "b")
        return left + right


# ---- Prompt 2: fusión (reduce) ----
#
# Diseño en tres pasos con responsabilidades separadas (decidido tras medir
# que pedirle al modelo que fusionara candidatos COMPLETOS — citas, desgloses,
# variaciones — producía salidas más grandes que su entrada y no convergía):
#  1. El modelo agrupa solo NOMBRES de candidatos (≈20 tokens por candidato,
#     entrada y salida chicas). Si hay más nombres de los que caben en una
#     llamada, se agrupan por tandas y los nombres canónicos resultantes se
#     vuelven a agrupar (jerárquico); Python compone el mapa.
#  2. Python fusiona de forma determinista: unión de member_ids, suma de
#     desgloses, pool de citas y variaciones.
#  3. El modelo elige citas/variaciones por cluster desde un pool acotado
#     (_QUOTE_POOL), en tandas por presupuesto de tokens; una tanda que se
#     trunca se divide en dos, igual que en el map.
# Ningún paso depende del tamaño del corpus para "caber" en max_tokens.

_QUOTE_POOL = 8       # citas candidatas máximas que ve el modelo por cluster
_VARIATION_POOL = 6   # variaciones máximas por cluster en el pool


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (name or "").lower()).strip("_")


def _interleave(lists: list[list]) -> list:
    """[a1,a2],[b1] → [a1,b1,a2]: al recortar un pool, ninguna tanda queda
    sin representación por venir después en la lista."""
    out = []
    for i in range(max((len(l) for l in lists), default=0)):
        for l in lists:
            if i < len(l):
                out.append(l[i])
    return out


def _new_merged(name: str) -> dict:
    return {
        "cluster_name": name, "member_count": 0, "member_ids": [],
        "breakdown_by_metadata": {}, "quote_sources": [], "variation_sources": [],
        "_has_ids": False,
    }


def _absorb(m: dict, c: dict) -> None:
    """Suma el candidato `c` al cluster fusionado `m` (aritmética en Python)."""
    ids = [i for i in (c.get("member_ids") or []) if isinstance(i, str)]
    if ids:
        m["_has_ids"] = True
        m["member_ids"].extend(ids)
    m["member_count"] += int(c.get("member_count") or 0)
    for field, per_value in (c.get("breakdown_by_metadata") or {}).items():
        if isinstance(per_value, dict):
            dst = m["breakdown_by_metadata"].setdefault(field, {})
            for k, v in per_value.items():
                try:
                    dst[str(k)] = dst.get(str(k), 0) + int(v)
                except (TypeError, ValueError):
                    pass
    quotes = c.get("quote_candidates") or c.get("representative_quotes") or []
    m["quote_sources"].append([q for q in quotes if isinstance(q, dict) and q.get("quote")])
    variations = c.get("internal_variations") or []
    m["variation_sources"].append([v for v in variations if isinstance(v, dict)])


def _merge_by_groups(candidates: list[dict], groups: list[tuple[str, list[int]]]) -> list[dict]:
    """Aplica un mapa {nombre canónico: índices} a los candidatos. Un índice
    no asignado por el modelo forma su propio cluster; uno repetido se
    respeta solo la primera vez. Los member_ids se deduplican (un respondente
    cuenta una vez por cluster aunque venga de dos tandas)."""
    seen: set[int] = set()
    merged: list[dict] = []
    for canonical, idxs in groups:
        m = _new_merged(canonical or "")
        for i in idxs:
            if isinstance(i, int) and 0 <= i < len(candidates) and i not in seen:
                seen.add(i)
                _absorb(m, candidates[i])
        if not m["cluster_name"] and m["quote_sources"]:
            m["cluster_name"] = candidates[idxs[0]].get("cluster_name", "")
        if seen and m["quote_sources"]:
            merged.append(m)
    for i, c in enumerate(candidates):
        if i not in seen:
            m = _new_merged(c.get("cluster_name", ""))
            _absorb(m, c)
            merged.append(m)
    for m in merged:
        m["member_ids"] = list(dict.fromkeys(m["member_ids"]))
        if m["_has_ids"]:
            m["member_count"] = len(m["member_ids"])
    return merged


def _merged_to_candidate(m: dict) -> dict:
    """Un cluster fusionado vuelve a ser candidato para otro nivel de fusión."""
    return {
        "cluster_name": m["cluster_name"], "member_count": m["member_count"],
        "member_ids": m["member_ids"], "breakdown_by_metadata": m["breakdown_by_metadata"],
        "quote_candidates": _interleave(m["quote_sources"])[:_QUOTE_POOL],
        "internal_variations": _interleave(m["variation_sources"])[:_VARIATION_POOL],
    }


def _map_names_call(names: list[dict], label: str) -> list[tuple[str, list[int]]]:
    p = prompt_store.get_prompts()["synthesize_clusters_v2_map_names"]
    data_section = (
        "CLUSTERS CANDIDATOS (" + str(len(names)) + "):\n"
        + json.dumps(names, ensure_ascii=False)
    )
    user = data_section + "\n\n" + p["instructions"]
    data = _call_structured(
        p["system"], user, tool=schemas_v2.MAP_CLUSTER_NAMES,
        label=f"{label} ({len(names)} candidatos)", max_tokens=LARGE_OUTPUT_TOKENS, model=MODEL_V2,
    )
    out = []
    for g in data.get("groups", []):
        if isinstance(g, dict):
            out.append((str(g.get("canonical_name") or ""), [i for i in (g.get("candidate_indices") or []) if isinstance(i, int)]))
    return out


def _map_names_adaptive(names: list[dict], label: str) -> list[tuple[str, list[int]]]:
    """Agrupa nombres; si la salida se trunca (solo posible con miles de
    candidatos), parte la lista en dos. Las mitades no se fusionan entre sí
    aquí: lo hace el siguiente nivel de `_fuse_candidates`."""
    try:
        return _map_names_call(names, label)
    except _TruncatedResponseError:
        if len(names) <= 1:
            return [(names[0]["cluster_name"], [names[0]["idx"]])] if names else []
        mid = len(names) // 2
        claude_log.log_warning(f"{label}: agrupación de nombres truncada; se parte en 2")
        return _map_names_adaptive(names[:mid], label + "a") + _map_names_adaptive(names[mid:], label + "b")


def _fuse_candidates(candidates: list[dict], notify: Optional[Callable[[str], None]] = None) -> list[dict]:
    """Pasos 1 y 2 del reduce: agrupación semántica por nombres (modelo) +
    fusión aritmética (Python), repetida por niveles solo si los nombres no
    caben en una llamada. Devuelve clusters fusionados con pools de citas."""
    if not candidates:
        return []
    items = candidates
    for level in range(1, _MAX_MERGE_LEVELS + 1):
        names = []
        for i, c in enumerate(items):
            quotes = c.get("quote_candidates") or []
            hint = ""
            if quotes and isinstance(quotes[0], dict):
                hint = (quotes[0].get("rationale") or quotes[0].get("quote") or "")[:120]
            names.append({
                "idx": i, "cluster_name": c.get("cluster_name", ""),
                "member_count": int(c.get("member_count") or 0), "hint": hint,
            })
        chunks = _chunk_by_tokens(names, MERGE_INPUT_TOKENS)
        if notify:
            notify(f"Fusionando clusters (nivel {level}: {len(items)} candidatos, {len(chunks)} llamada(s))")
        groups: list[tuple[str, list[int]]] = []
        if len(chunks) == 1:
            groups = _map_names_adaptive(names, f"agrupación de clusters nivel {level}")
        else:
            results: list[Optional[list]] = [None] * len(chunks)
            with ThreadPoolExecutor(max_workers=min(V2_MAX_WORKERS, len(chunks))) as pool:
                futures = {
                    _submit_with_context(pool, _map_names_adaptive, chunk,
                                         f"agrupación de clusters nivel {level} tanda {k + 1}"): k
                    for k, chunk in enumerate(chunks)
                }
                for fut in as_completed(futures):
                    results[futures[fut]] = fut.result()
            groups = [g for r in results if r for g in r]
        merged = _merge_by_groups(items, groups)
        claude_log.log_info(f"fusión nivel {level}: {len(items)} → {len(merged)} clusters")
        # Converge cuando todos los nombres cupieron en una sola llamada (ya se
        # compararon todos contra todos) o cuando un nivel más no reduce nada.
        if len(chunks) == 1 or len(merged) >= len(items):
            return merged
        items = [_merged_to_candidate(m) for m in merged]
    return [m for m in merged]


def _select_quotes_call(clusters_input: list[dict], label: str) -> dict[str, dict]:
    p = prompt_store.get_prompts()["synthesize_clusters_v2_select_quotes"]
    data_section = (
        "CLUSTERS FUSIONADOS CON SU POOL DE CITAS (" + str(len(clusters_input)) + "):\n"
        + json.dumps(clusters_input, ensure_ascii=False)
    )
    user = data_section + "\n\n" + p["instructions"]
    data = _call_structured(
        p["system"], user, tool=schemas_v2.SELECT_QUOTES,
        label=f"{label} ({len(clusters_input)} clusters)", max_tokens=LARGE_OUTPUT_TOKENS, model=MODEL_V2,
    )
    out: dict[str, dict] = {}
    for c in data.get("clusters", []):
        if isinstance(c, dict):
            out[_normalize_name(c.get("cluster_name", ""))] = c
    return out


def _select_quotes_adaptive(clusters_input: list[dict], label: str) -> dict[str, dict]:
    try:
        return _select_quotes_call(clusters_input, label)
    except _TruncatedResponseError:
        if len(clusters_input) <= 1:
            return {}  # el llamador usa el pool tal cual
        mid = len(clusters_input) // 2
        claude_log.log_warning(f"{label}: selección de citas truncada; se parte en 2")
        left = _select_quotes_adaptive(clusters_input[:mid], label + "a")
        left.update(_select_quotes_adaptive(clusters_input[mid:], label + "b"))
        return left


def _select_quotes(merged: list[dict], notify: Optional[Callable[[str], None]] = None) -> list[dict]:
    """Paso 3 del reduce: citas representativas y variaciones por cluster,
    elegidas por el modelo desde un pool acotado. Devuelve clusters en el
    formato final (sin porcentaje: lo pone _finalize_clusters)."""
    inputs = []
    for m in merged:
        inputs.append({
            "cluster_name": m["cluster_name"],
            "member_count": m["member_count"],
            "quote_pool": _interleave(m["quote_sources"])[:_QUOTE_POOL],
            "variation_pool": _interleave(m["variation_sources"])[:_VARIATION_POOL],
        })
    chunks = _chunk_by_tokens(inputs, MERGE_INPUT_TOKENS)
    if notify:
        notify(f"Seleccionando citas representativas ({len(inputs)} clusters, {len(chunks)} llamada(s))")
    selected: dict[str, dict] = {}
    if len(chunks) == 1:
        selected = _select_quotes_adaptive(inputs, "selección de citas")
    else:
        results: list[Optional[dict]] = [None] * len(chunks)
        with ThreadPoolExecutor(max_workers=min(V2_MAX_WORKERS, len(chunks))) as pool:
            futures = {
                _submit_with_context(pool, _select_quotes_adaptive, chunk, f"selección de citas tanda {k + 1}"): k
                for k, chunk in enumerate(chunks)
            }
            for fut in as_completed(futures):
                results[futures[fut]] = fut.result()
        for r in results:
            if r:
                selected.update(r)

    final = []
    for m, inp in zip(merged, inputs):
        sel = selected.get(_normalize_name(m["cluster_name"])) or {}
        quotes = [q for q in (sel.get("representative_quotes") or []) if isinstance(q, dict) and q.get("quote")]
        if not quotes:  # el modelo omitió este cluster: se usa el pool tal cual
            quotes = inp["quote_pool"][:3]
        final.append({
            "cluster_name": m["cluster_name"],
            "prevalence": {"count": m["member_count"], "percentage": 0.0},
            "member_ids": m["member_ids"],
            "breakdown_by_metadata": m["breakdown_by_metadata"],
            "representative_quotes": quotes[:3],
            "internal_variations": [v for v in (sel.get("internal_variations") or inp["variation_pool"][:3]) if isinstance(v, dict)][:3],
        })
    return final


def _reduce_candidates_v2(candidates: list[dict], notify: Optional[Callable[[str], None]] = None) -> list[dict]:
    """Reduce completo: fusión semántica + aritmética + selección de citas."""
    merged = _fuse_candidates(candidates, notify=notify)
    return _select_quotes(merged, notify=notify)


def _finalize_clusters(clusters: list[dict], total_respondents: int) -> list[dict]:
    """Los números finales los calcula el sistema, no el modelo: count a partir
    de member_ids únicos cuando existen (más confiable que sumas hechas por el
    modelo entre llamadas), porcentaje sobre el total real, orden descendente."""
    out = []
    for c in clusters:
        prev = c.get("prevalence") or {}
        ids = list(dict.fromkeys(c.get("member_ids") or []))  # únicos, orden estable
        count = len(ids) if ids else int(prev.get("count") or 0)
        count = min(count, total_respondents) if total_respondents else count
        pct = round(count / total_respondents * 100, 1) if total_respondents else 0.0
        c = dict(c)
        c["prevalence"] = {"count": count, "percentage": pct}
        c["member_ids"] = ids
        out.append(c)
    out.sort(key=lambda c: -c["prevalence"]["count"])
    return out


def _synthesize_clusters_v2(
    survey_id: str,
    all_respondent_analyses: list[dict],
    total_respondents: int,
    marco_teorico: str,
    notify: Optional[Callable[[str], None]] = None,
) -> dict:
    """Prompt 2: agrega todos los análisis individuales en clusters con
    prevalencia, desglose por metadata y citas representativas.

    Estrategia: si el corpus compactado cabe en una tanda
    (SYNTHESIS_BATCH_INPUT_TOKENS), una sola llamada con el prompt completo.
    Si no, map-reduce: tandas por presupuesto de tokens sintetizadas en
    paralelo (cada una se divide sola si se trunca) y fusión jerárquica. En
    ningún punto el resultado depende de que "quepa" en max_tokens.
    """
    # Compactar: solo lo que la síntesis necesita (reduce tokens de entrada).
    compact = []
    for a in all_respondent_analyses:
        compact.append({
            "respondent_id": a.get("respondent_id"),
            "is_valid": a.get("is_valid", False),
            "rejection_reason": a.get("rejection_reason"),
            "subtopics": a.get("subtopics", []),
            "respondent_profile_line": a.get("respondent_profile_line", ""),
            "metadata_snapshot": a.get("metadata_snapshot", {}),
        })

    valid_count = sum(1 for a in compact if a.get("is_valid"))
    rejected_count = len(compact) - valid_count
    breakdown = _rejection_breakdown(compact)

    batches = _chunk_by_tokens(compact, SYNTHESIS_BATCH_INPUT_TOKENS)
    clusters: Optional[list[dict]] = None

    if len(batches) == 1:
        p = prompt_store.get_prompts()["synthesize_clusters_v2"]
        data_section = (
            "ANÁLISIS INDIVIDUALES (" + str(len(compact)) + " respondentes):\n"
            + json.dumps(compact, ensure_ascii=False)
            + "\n\nTOTAL DE RESPONDENTES: " + str(total_respondents)
            + "\n\nMARCO TEÓRICO:\n" + _marco(marco_teorico)
        )
        user = data_section + "\n\n" + p["instructions"]
        if notify:
            notify(f"Sintetizando clusters ({len(compact)} respondentes, una tanda)")
        try:
            data = _call_structured(
                p["system"], user, tool=schemas_v2.SYNTHESIZE_CLUSTERS,
                label=f"síntesis de clusters ({len(compact)} resp.)",
                max_tokens=LARGE_OUTPUT_TOKENS, model=MODEL_V2,
            )
            clusters = [c for c in data.get("clusters", []) if isinstance(c, dict)]
        except _TruncatedResponseError:
            # Cabía por tokens de entrada pero la salida no: mismo remedio que
            # con corpus grandes — partir en tandas y fusionar.
            claude_log.log_warning("síntesis en una tanda truncada; se pasa a map-reduce")
            mid = max(1, len(compact) // 2)
            batches = [compact[:mid], compact[mid:]] if len(compact) > 1 else batches

    if clusters is None:
        if notify:
            notify(f"Sintetizando clusters ({len(batches)} tandas en paralelo)")
        partial: list[Optional[list[dict]]] = [None] * len(batches)
        with ThreadPoolExecutor(max_workers=min(V2_MAX_WORKERS, len(batches))) as pool:
            futures = {
                _submit_with_context(
                    pool, _synthesize_batch_adaptive, batch, marco_teorico,
                    f"tanda {i + 1}/{len(batches)}",
                ): i
                for i, batch in enumerate(batches)
            }
            done = 0
            for fut in as_completed(futures):
                partial[futures[fut]] = fut.result()
                done += 1
                if notify:
                    notify(f"Sintetizando clusters (tanda {done}/{len(batches)} lista)")
        candidates = [c for pc in partial if pc for c in pc]
        clusters = _reduce_candidates_v2(candidates, notify=notify)

    return {
        "survey_id": survey_id,
        # Los conteos globales los calcula el sistema, no el modelo.
        "respondents_analyzed": {
            "total": total_respondents,
            "valid": valid_count,
            "rejected": rejected_count,
            "rejection_breakdown": breakdown,
        },
        "clusters": _finalize_clusters(clusters, total_respondents),
    }


def _write_report_v2(clusters_analysis: dict, marco_teorico: str) -> str:
    """Prompt 3: redacta el informe integrado (markdown plano, sin JSON). Su
    largo lo acota el prompt (máx. 1500 palabras), no el corpus."""
    p = prompt_store.get_prompts()["write_report_v2"]
    # member_ids son para el sistema (conteo), no para el redactor.
    slim = json.loads(json.dumps(clusters_analysis, ensure_ascii=False))
    for c in slim.get("clusters", []):
        c.pop("member_ids", None)
    data_section = (
        "ANÁLISIS DE CLUSTERS SINTETIZADOS:\n"
        + json.dumps(slim, ensure_ascii=False, indent=2)
        + "\n\nMARCO TEÓRICO:\n" + _marco(marco_teorico)
    )
    user = data_section + "\n\n" + p["instructions"]
    return _call_text(p["system"], user, label="redacción del informe v2",
                      max_tokens=LARGE_OUTPUT_TOKENS, model=MODEL_V2)


def _v2_analyses_fingerprint(marco_teorico: str, responses: list[dict]) -> str:
    """Hash estable de lo único que determina el resultado del Prompt 1
    (texto abierto + respuestas cerradas/metadata de cada respondente + marco
    teórico). Si no cambia entre dos generaciones de informe, los análisis ya
    calculados siguen siendo válidos — no hace falta volver a pagar ~1 llamada
    a Claude POR RESPONDENTE solo porque un paso posterior (síntesis o
    redacción) falló."""
    payload = {
        "marco_teorico": marco_teorico or "",
        "responses": [
            {"id": r["id"], "text": r.get("text", ""), "meta": r.get("meta", {}) or {}}
            for r in responses
        ],
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def generate_qualitative_report_v2(
    survey_id: str,
    marco_teorico: str,
    categories: list[dict],
    codings: dict,
    responses: list[dict],
    columns: list[str],
    text_column: str,
    lexical_data: Optional[dict] = None,
    progress_cb: Optional[Callable[[str, int, int], None]] = None,
    cached_analyses: Optional[dict] = None,
    save_analyses_cb: Optional[Callable[[str, list], None]] = None,
    force_full: bool = False,
) -> str:
    """Orquesta el flujo multi-prompt: Prompt 1 (paralelo) → Prompt 2 → Prompt 3.

    categories/codings/lexical_data se aceptan por compatibilidad de firma y
    auditoría; el flujo V2 trabaja directamente sobre las respuestas con su
    contexto de preguntas cerradas.

    cached_analyses / save_analyses_cb: caché del Prompt 1 entre reintentos
    (ver `_v2_analyses_fingerprint`). `cached_analyses` es
    {"fingerprint": str, "analyses": [...]} — si el fingerprint calza y el
    tamaño coincide, se reutiliza sin llamar a Claude. `save_analyses_cb`
    recibe (fingerprint, analyses) para persistirlo después de calcularlo.
    El caché es solo una optimización de costo: si falta o falla, el informe
    se genera igual desde cero. `force_full=True` lo ignora a propósito (el
    analista pidió regenerar todo) y lo reemplaza al terminar el Prompt 1.
    """
    n = len(responses)
    total_steps = n + 2  # análisis por respondente + síntesis + redacción

    def _notify(stage: str, done: int):
        if progress_cb:
            try:
                progress_cb(stage, done, total_steps)
            except Exception:
                pass  # el progreso nunca debe botar la generación

    fingerprint = _v2_analyses_fingerprint(marco_teorico, responses)
    all_analyses: list[Optional[dict]] = [None] * n

    if (
        not force_full
        and cached_analyses
        and cached_analyses.get("fingerprint") == fingerprint
        and len(cached_analyses.get("analyses") or []) == n
    ):
        # Nada cambió desde el último intento: nos ahorramos las ~n llamadas
        # del Prompt 1 y vamos directo a síntesis/redacción.
        all_analyses = cached_analyses["analyses"]
        claude_log.log_info(f"informe v2 {survey_id}: reutilizando caché del Prompt 1 ({n} análisis)")
        _notify(f"Reutilizando análisis ya calculados de {n} respondentes", n)
    else:
        claude_log.log_info(
            f"informe v2 {survey_id}: Prompt 1 para {n} respondentes"
            + (" (regeneración forzada)" if force_full else "")
        )
        # PASO 1: estructura por respondente (texto abierto + cerradas + metadata)
        responses_structured = []
        for r in responses:
            meta = r.get("meta", {}) or {}
            responses_structured.append({
                "respondent_id": r["id"],
                "open_response": r["text"],
                "closed_responses": meta,
                "metadata": meta,  # las cerradas SON la metadata disponible (rol, facultad, etc.)
            })

        # PASO 2: Prompt 1 por respondente, en paralelo (orden preservado)
        done = 0
        _notify(f"Analizando respondentes (0/{n})", 0)
        with ThreadPoolExecutor(max_workers=V2_MAX_WORKERS) as pool:
            futures = {
                _submit_with_context(
                    pool, _analyze_respondent_v2,
                    respondent_id=rs["respondent_id"],
                    open_response_text=rs["open_response"],
                    closed_responses=rs["closed_responses"],
                    respondent_metadata=rs["metadata"],
                    marco_teorico=marco_teorico,
                ): i
                for i, rs in enumerate(responses_structured)
            }
            for fut in as_completed(futures):
                all_analyses[futures[fut]] = fut.result()
                done += 1
                _notify(f"Analizando respondentes ({done}/{n})", done)

        if save_analyses_cb:
            try:
                save_analyses_cb(fingerprint, all_analyses)
            except Exception as e:
                claude_log.log_warning(f"no se pudo guardar el caché del Prompt 1: {e}")

    # PASO 3: Prompt 2 — síntesis y agregación
    _notify("Sintetizando clusters", n)
    clusters_result = _synthesize_clusters_v2(
        survey_id=survey_id,
        all_respondent_analyses=[a for a in all_analyses if a is not None],
        total_respondents=n,
        marco_teorico=marco_teorico,
        notify=lambda stage: _notify(stage, n),
    )

    # PASO 4: Prompt 3 — redacción del informe
    _notify("Redactando informe", n + 1)
    report = _write_report_v2(clusters_analysis=clusters_result, marco_teorico=marco_teorico)

    _notify("Informe completado", total_steps)
    return report
