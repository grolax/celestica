# Estado del desarrollo

Archivo mantenido por el agente `supervisor`. Una línea por entrada.

## Hecho

| Tarea | Lado | Requerimientos | Fecha | Rama |
| --- | --- | --- | --- | --- |
| — | — | Línea base: MVP v1.1 (ver `07_MVP/COMO_FUNCIONA.md`) | 2026-10 | main |

## En curso

- T-000 · frontend · RNF-17 · consolidar Vite 8 / React Router 7 · rama `tarea/T-000-deps-frontend` (2026-10-14)

## Bloqueado / requiere decisión del usuario

(nada; D-1 a D-4 resueltas el 2026-10-14, ver `tasks/plan.md` §6)

## Deuda técnica detectada

- `pytest tests -q` en rojo en `main` (7/14): `prompt_store` falla si no existe `app/prompts.json`, que está en `.gitignore` → T-001.
- Los scripts de aislamiento (`test_e2e`, `test_fase1/3/5`) no los ejecuta pytest; hoy pasan corriéndolos a mano → T-002.
- `backend/app/main.py` concentra todos los endpoints (~950 líneas); separar en routers (RNF-17).
- Progreso de codificación e informe vive en memoria; se pierde si el servidor se reinicia (RNF-12).
- Stopwords del análisis léxico fijas y orientadas a educación superior chilena (RF-14).
