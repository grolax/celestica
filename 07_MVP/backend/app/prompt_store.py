"""
Gestión de prompts editables.

Los prompts viven en prompts.json (editables en vivo).
Los defaults viven en prompts_default.json (de solo lectura, para restaurar).
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


def get_prompts() -> dict:
    """Carga los prompts actuales desde disco. Thread-safe."""
    with _lock:
        return json.loads(_PROMPTS_PATH.read_text(encoding="utf-8"))


def get_defaults() -> dict:
    """Carga los prompts por defecto. Solo lectura."""
    return json.loads(_DEFAULTS_PATH.read_text(encoding="utf-8"))


def save_prompt(key: str, system: str, instructions: str) -> dict:
    """Actualiza un prompt específico y guarda. Thread-safe."""
    with _lock:
        data = json.loads(_PROMPTS_PATH.read_text(encoding="utf-8"))
        if key not in data:
            raise KeyError(f"Prompt '{key}' no encontrado")
        data[key]["system"] = system
        data[key]["instructions"] = instructions
        _PROMPTS_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return data[key]


def reset_prompt(key: str) -> dict:
    """Restaura un prompt a su valor por defecto. Thread-safe."""
    defaults = get_defaults()
    if key not in defaults:
        raise KeyError(f"Prompt '{key}' no encontrado en defaults")
    with _lock:
        data = json.loads(_PROMPTS_PATH.read_text(encoding="utf-8"))
        data[key]["system"] = defaults[key]["system"]
        data[key]["instructions"] = defaults[key]["instructions"]
        _PROMPTS_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return defaults[key]
