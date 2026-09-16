"""
Registro persistente y observabilidad de costo de TODAS las llamadas a Claude.

Por qué existe este módulo: el incidente de septiembre 2026 (informe V2 con 122
respondentes) costó >US$10 en reintentos y horas de depuración a ciegas porque
no había ningún registro en disco de qué devolvía Claude, con qué max_tokens
ni con qué stop_reason. Este módulo garantiza que cada llamada deje huella:

1. `logs/claude_calls.jsonl` — una línea JSON por llamada: etiqueta del paso,
   modelo, max_tokens pedido, stop_reason, tokens de entrada/salida, costo
   estimado, duración y proyecto. Se puede leer con `jq` o pandas.
2. `logs/claude_raw/<ts>_<label>.txt` — el texto/JSON CRUDO devuelto por el
   modelo, guardado SIEMPRE que la llamada termina mal (truncada, JSON
   inválido, error) y, opcionalmente, en todas las llamadas si
   CLAUDE_LOG_RAW=1 (útil para calibrar prompts; ojo con el espacio en disco).
3. `logs/softinsight.log` — logger estándar de Python (INFO) con los mismos
   eventos en formato legible.

Además, cada llamada alimenta un "sink" de uso por proyecto (ver
`set_usage_sink`) para que el costo acumulado quede en Mongo y sea visible en
el panel de administración.

Contexto por hilo: el flujo V2 usa ThreadPoolExecutor. Para que las llamadas
lanzadas desde los workers sepan a qué proyecto pertenecen, el contexto se
lleva en `contextvars` y los pools deben enviar trabajo con
`contextvars.copy_context().run(...)` (ver thematic.py).
"""
from __future__ import annotations

import contextvars
import json
import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

from dotenv import load_dotenv

# Este módulo se importa ANTES de que thematic.py cargue el .env, así que lee
# el .env él mismo (sin override: si la variable ya está en el entorno, gana).
load_dotenv()

# ---------- Ubicación de los logs ----------
# Default: backend/logs (dos niveles arriba de app/services). Configurable
# para producción vía CLAUDE_LOG_DIR.
_DEFAULT_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_DIR = Path(os.environ.get("CLAUDE_LOG_DIR", str(_DEFAULT_LOG_DIR)))
LOG_RAW_ALWAYS = os.environ.get("CLAUDE_LOG_RAW", "0") == "1"

_lock = threading.Lock()
_logger: Optional[logging.Logger] = None


def _get_logger() -> logging.Logger:
    """Logger de archivo, creado perezosamente (así los tests pueden apuntar
    CLAUDE_LOG_DIR a una carpeta temporal antes del primer uso)."""
    global _logger
    if _logger is None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        lg = logging.getLogger("softinsight.claude")
        lg.setLevel(logging.INFO)
        if not any(isinstance(h, logging.FileHandler) for h in lg.handlers):
            fh = logging.FileHandler(LOG_DIR / "softinsight.log", encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            lg.addHandler(fh)
        _logger = lg
    return _logger


# ---------- Contexto (proyecto actual) ----------
current_project_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "claude_project_id", default=None
)

# Sink de uso: callable(project_id, record) que persiste el consumo. Lo fija
# main.py al arrancar (guarda en Mongo). Si no hay sink, solo se loguea a disco.
_usage_sink: Optional[Callable[[Optional[str], dict], None]] = None


def set_usage_sink(fn: Optional[Callable[[Optional[str], dict], None]]) -> None:
    global _usage_sink
    _usage_sink = fn


# ---------- Precios (USD por millón de tokens) ----------
# Son ESTIMACIONES para observabilidad, no facturación: los precios cambian y
# la tabla se puede sobreescribir sin tocar código con CLAUDE_PRICING_JSON,
# ej: {"claude-sonnet-4-6": [3, 15]}. El match es por prefijo del nombre del
# modelo, del más específico al más genérico.
_DEFAULT_PRICING = {
    "claude-sonnet-4": (3.0, 15.0),
    "claude-opus-4-1": (15.0, 75.0),
    "claude-opus-4": (15.0, 75.0),
    "claude-haiku-4": (1.0, 5.0),
    "claude-3-5-haiku": (0.8, 4.0),
}


def _pricing_table() -> dict:
    table = dict(_DEFAULT_PRICING)
    raw = os.environ.get("CLAUDE_PRICING_JSON")
    if raw:
        try:
            for k, v in json.loads(raw).items():
                table[k] = (float(v[0]), float(v[1]))
        except Exception:
            _get_logger().warning("CLAUDE_PRICING_JSON inválido; se usa la tabla por defecto")
    return table


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    table = _pricing_table()
    price = None
    for prefix in sorted(table, key=len, reverse=True):  # el prefijo más largo gana
        if model.startswith(prefix):
            price = table[prefix]
            break
    if price is None:
        return 0.0
    return round(input_tokens / 1e6 * price[0] + output_tokens / 1e6 * price[1], 6)


# ---------- Registro de llamadas ----------

def _safe_label(label: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", label)[:60]


def record_call(
    *,
    label: str,
    model: str,
    max_tokens: int,
    stop_reason: Optional[str],
    input_tokens: int,
    output_tokens: int,
    duration_s: float,
    ok: bool,
    error: Optional[str] = None,
    raw_output: Optional[str] = None,
    extra: Optional[dict] = None,
) -> dict:
    """Registra una llamada terminada (bien o mal). Nunca lanza: el logging
    no debe botar el análisis. Devuelve el registro escrito."""
    project_id = current_project_id.get()
    rec: dict[str, Any] = {
        "ts": time.time(),
        "project_id": project_id,
        "label": label,
        "model": model,
        "max_tokens": max_tokens,
        "stop_reason": stop_reason,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": estimate_cost_usd(model, input_tokens, output_tokens),
        "duration_s": round(duration_s, 1),
        "ok": ok,
        "error": error,
    }
    if extra:
        rec.update(extra)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        # El texto crudo se guarda aparte (puede pesar decenas de KB) y solo
        # cuando sirve para depurar: fallo, truncamiento, o modo verboso.
        if raw_output is not None and (not ok or stop_reason == "max_tokens" or LOG_RAW_ALWAYS):
            raw_dir = LOG_DIR / "claude_raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            fname = f"{int(rec['ts'])}_{_safe_label(label)}_{threading.get_ident()}.txt"
            header = (
                f"# label={label} model={model} max_tokens={max_tokens} "
                f"stop_reason={stop_reason} in={input_tokens} out={output_tokens} "
                f"ok={ok} error={error}\n\n"
            )
            (raw_dir / fname).write_text(header + raw_output, encoding="utf-8")
            rec["raw_file"] = str(raw_dir / fname)
        with _lock:
            with open(LOG_DIR / "claude_calls.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        lg = _get_logger()
        msg = (
            f"claude_call label={label!r} project={project_id} model={model} "
            f"max_tokens={max_tokens} stop={stop_reason} in={input_tokens} "
            f"out={output_tokens} cost=${rec['cost_usd']:.4f} dur={rec['duration_s']}s ok={ok}"
        )
        (lg.info if ok else lg.warning)(msg + (f" error={error}" if error else ""))
    except Exception:
        pass
    if _usage_sink is not None:
        try:
            _usage_sink(project_id, rec)
        except Exception:
            pass
    return rec


def log_info(msg: str) -> None:
    try:
        _get_logger().info(msg)
    except Exception:
        pass


def log_warning(msg: str) -> None:
    try:
        _get_logger().warning(msg)
    except Exception:
        pass
