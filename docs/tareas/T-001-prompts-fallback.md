# T-001: `prompt_store` funciona sin `prompts.json`
Lado: backend
Requerimientos: RNF-18, RNF-21
Rama: tarea/T-001-prompts-fallback
Depende de: —

## Objetivo
`pytest tests -q` falla en `main` con 7 de 14 pruebas en rojo. El error es `FileNotFoundError: app/prompts.json`: ese archivo está en `.gitignore` y `prompt_store` no tiene respaldo cuando no existe. Tras esta tarea, un clon limpio corre la suite completa en verde y la app arranca sin `prompts.json`.

## Alcance
- SÍ: en `app/prompt_store.py`, `get_prompts()` devuelve los defaults (`prompts_default.json`) con encima lo que haya en `prompts.json`, si existe. Así también funcionan las claves agregadas a los defaults después de crear el `prompts.json` local (por ejemplo, las `*_v2`).
- SÍ: `save_prompt` y `reset_prompt` funcionan aunque `prompts.json` no exista (lo crean al primer guardado) y aceptan cualquier clave presente en los defaults.
- SÍ: pruebas pytest nuevas.
- NO: cambiar el texto de ningún prompt ni de `prompts_default.json`; sacar `prompts.json` de `.gitignore`; tocar `thematic.py` ni los endpoints `/api/admin/prompts*`; mover los prompts a Mongo (eso es RF-15).

## Contrato de API
No aplica: los endpoints `/api/admin/prompts*` no cambian de forma ni de comportamiento visible.

## Archivos probables
- Tocar: `07_MVP/backend/app/prompt_store.py`, una prueba nueva en `07_MVP/backend/tests/` (por ejemplo `test_prompt_store_pytest.py`) y `07_MVP/COMO_FUNCIONA.md` §3 y §6 (una línea sobre el respaldo).
- No tocar: `prompts_default.json`, `services/thematic.py`, `main.py`, `07_MVP/frontend/**`, `docs/**`.

## Criterios de aceptación
- [ ] Sin `app/prompts.json` en disco, `cd 07_MVP/backend && pytest tests -q` pasa completo (14/14 + las nuevas). Para comprobarlo, renombra temporalmente tu `prompts.json` local si existe y restáuralo al terminar.
- [ ] Prueba: sin archivo, `get_prompts()` devuelve exactamente los defaults.
- [ ] Prueba: un `prompts.json` con solo una clave modificada → `get_prompts()` trae esa versión y el resto desde los defaults.
- [ ] Prueba: `save_prompt` sin archivo lo crea y persiste el cambio; `reset_prompt` lo vuelve al default; una clave inexistente en los defaults sigue lanzando `KeyError`.
- [ ] Las pruebas usan un directorio temporal (monkeypatch de las rutas o `tmp_path`) y nunca escriben en el `app/prompts.json` real.
- [ ] Los scripts `python tests/test_e2e.py`, `test_fase1.py`, `test_fase3.py` y `test_fase5.py` siguen pasando.
- [ ] Sin llamadas reales a la API de Anthropic.
- [ ] Commits con el formato `T-001 RNF-18: ...`.

## Notas
- `thematic.py` lee las claves `propose_categories`, `codify`, `interpret_lexical`, `qualitative_report`, `analyze_respondent_v2`, `synthesize_clusters_v2_partial`, `synthesize_clusters_v2_map_names`, `synthesize_clusters_v2_select_quotes`, `synthesize_clusters_v2` y `write_report_v2`.
- Mantén el `threading.Lock` existente en las escrituras.

## Revisión 1
2026-10-14 · **Con cambios** (1 observación).

Verificado: `pytest tests -q` da 18 passed sin `app/prompts.json`; `test_e2e`, `test_fase1`, `test_fase3` y `test_fase5` terminan en "TODO OK"; el diff se limita a `prompt_store.py`, la prueba nueva y `COMO_FUNCIONA.md`.

1. **`07_MVP/backend/app/prompt_store.py`, `reset_prompt` (`overrides[key] = defaults[key]`).** Restaurar escribe una copia del default actual en `prompts.json`. Si después se mejora `prompts_default.json`, esa clave sigue usando la copia vieja: el prompt queda congelado, que es justo lo que tu propia decisión de `save_prompt` buscaba evitar.
   **Esperado:** `reset_prompt` quita la clave de `prompts.json` (`overrides.pop(key, None)` y luego escribir), y sigue devolviendo `defaults[key]`. Mantén el `KeyError` para claves que no estén en los defaults.
   **Prueba:** en `test_save_sin_archivo_lo_crea_y_reset_restaura`, después del reset, verifica que `"a"` ya no está en el JSON de `tmp_path / "prompts.json"`.

No cambies nada más. Commit con el formato `T-001 RNF-18: ...`.

## Revisión 2
2026-10-14 · **Aprobada**.
- Commit `7042c7f`: `reset_prompt` hace `overrides.pop(key, None)` y la prueba verifica que la clave ya no está en `prompts.json`. Es exactamente lo pedido; no hay otros cambios.
- Verificado por el supervisor sin `app/prompts.json`: `pytest tests -q` da 18 passed; `test_e2e`, `test_fase1`, `test_fase3` y `test_fase5` terminan en "TODO OK".
- Se cumplen todos los criterios de aceptación.
- Fuera de alcance, para más adelante: `schemas_v2.py` (línea 16), el docstring de `thematic.py` y `COMO_FUNCIONA.md` §6 ("Los 4 prompts", cuando hoy son 10) siguen describiendo los prompts como antes. Queda anotado como deuda menor de documentación.
