# Estado del desarrollo

Archivo mantenido por el agente `supervisor`. Una línea por entrada.

## Hecho

| Tarea | Lado | Requerimientos | Fecha | Rama |
| --- | --- | --- | --- | --- |
| — | — | Línea base: MVP v1.1 (ver `07_MVP/COMO_FUNCIONA.md`) | 2026-10 | main |
| T-000 Vite 8 + React Router 7 | frontend | RNF-17, RNF-19 | 2026-10-14 | `tarea/T-000-deps-frontend` (fusionada, PR #1) |
| T-001 `prompt_store` sin `prompts.json` | backend | RNF-18, RNF-21 | 2026-10-14 | `tarea/T-001-prompts-fallback` (fusionada, PR #2) |

## En curso

- T-014 · frontend · RNF-16 · identidad visual Celestica · rama `tarea/T-014-identidad-celestica` (2026-10-15)
- En cola (Fase UX, prioridad del usuario): T-015 presentación pública, T-016 área de trabajo, T-017 nombre en exportaciones. T-002 queda después.

## Bloqueado / requiere decisión del usuario

- Textos de la página de presentación (T-015): borrador del supervisor, el usuario debe revisarlos (sobre todo "Quiénes somos").

## Deuda técnica detectada

- Docs de prompts desactualizados: `COMO_FUNCIONA.md` §6 dice "4 prompts" (son 10); `schemas_v2.py:16` y el docstring de `thematic.py` nombran solo `prompts.json`.
- Los scripts de aislamiento (`test_e2e`, `test_fase1/3/5`) no los ejecuta pytest; hoy pasan corriéndolos a mano → T-002.
- `backend/app/main.py` concentra todos los endpoints (~950 líneas); separar en routers (RNF-17).
- Progreso de codificación e informe vive en memoria; se pierde si el servidor se reinicia (RNF-12).
- Stopwords del análisis léxico fijas y orientadas a educación superior chilena (RF-14).
- La bitácora para el equipo vive fuera del repositorio: `C:/Users/isral/OneDrive/Desktop/Proyectos/Celestica/BITACORA.md` (pedido del usuario, 2026-10-15).
