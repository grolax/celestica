"""
Gestión de prompts editables.

Los defaults viven en prompts_default.json (de solo lectura, para restaurar).
prompts.json (ignorado por git, editable en vivo) solo guarda lo que se cambió:
si no existe, o le faltan claves, get_prompts() usa los defaults.
Ambos archivos están en el mismo directorio que este módulo.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

_DIR = Path(__file__).resolve().parent
_PROMPTS_PATH = _DIR / "prompts.json"
_DEFAULTS_PATH = _DIR / "prompts_default.json"

_lock = threading.Lock()


def _read_overrides() -> dict:
    return json.loads(_PROMPTS_PATH.read_text(encoding="utf-8")) if _PROMPTS_PATH.exists() else {}


def _write_overrides(data: dict) -> None:
    _PROMPTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_prompts() -> dict:
    """Defaults con encima lo que haya en prompts.json. Thread-safe."""
    with _lock:
        return {**get_defaults(), **_read_overrides()}


def get_defaults() -> dict:
    """Carga los prompts por defecto. Solo lectura."""
    return json.loads(_DEFAULTS_PATH.read_text(encoding="utf-8"))


def save_prompt(key: str, system: str, instructions: str) -> dict:
    """Actualiza un prompt específico y guarda (crea prompts.json si falta). Thread-safe."""
    with _lock:
        overrides = _read_overrides()
        current = overrides.get(key) or get_defaults().get(key)
        if current is None:
            raise KeyError(f"Prompt '{key}' no encontrado")
        overrides[key] = {**current, "system": system, "instructions": instructions}
        _write_overrides(overrides)
        return overrides[key]


def reset_prompt(key: str) -> dict:
    """Restaura un prompt a su valor por defecto. Thread-safe."""
    defaults = get_defaults()
    if key not in defaults:
        raise KeyError(f"Prompt '{key}' no encontrado en defaults")
    with _lock:
        overrides = _read_overrides()
        overrides.pop(key, None)
        _write_overrides(overrides)
    return defaults[key]
