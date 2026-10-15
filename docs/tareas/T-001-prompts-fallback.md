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
