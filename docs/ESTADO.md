# Estado del desarrollo

Archivo mantenido por el agente `supervisor`. Una línea por entrada.

## Hecho

| Tarea | Lado | Requerimientos | Fecha | Rama |
| --- | --- | --- | --- | --- |
| — | — | Línea base: MVP v1.1 (ver `07_MVP/COMO_FUNCIONA.md`) | 2026-10 | main |
| T-000 Vite 8 + React Router 7 | frontend | RNF-17, RNF-19 | 2026-10-14 | `tarea/T-000-deps-frontend` (fusionada, PR #1) |
| T-001 `prompt_store` sin `prompts.json` | backend | RNF-18, RNF-21 | 2026-10-14 | `tarea/T-001-prompts-fallback` (fusionada, PR #2) |
| T-014 Identidad visual Celestica | frontend | RNF-16, RNF-14, RNF-13 | 2026-10-15 | `tarea/T-014-identidad-celestica` (fusionada, PR #3) |
| T-015 Página de presentación y rutas | frontend | RNF-13, RNF-14, RNF-15, RNF-16 | 2026-10-30 | `tarea/T-015-pagina-presentacion` (fusionada, PR #4) |

## En curso

- T-017 nombre y colores Celestica en PDF/DOCX (backend), rama `tarea/T-017-exportaciones-celestica`.
- En cola (Fase UX): T-016a encabezados y menú, T-016b encabezados de análisis (textos aprobados 2026-10-30).
- Después, de vuelta al backend (pedido del usuario): T-002 aislamiento en pytest → separar `main.py` en routers → RF-02 organizaciones → RF-03 roles.

## Bloqueado / requiere decisión del usuario

- Ninguno. (Nombre interno `SoftInsight` en API, base de datos y logs se mantiene por ahora, decisión del usuario 2026-10-30. Correo `soporte@softinsight.cl`: se mantiene por ahora, decisión del usuario 2026-10-30.)

## Deuda técnica detectada

- Docs de prompts desactualizados: `COMO_FUNCIONA.md` §6 dice "4 prompts" (son 10); `schemas_v2.py:16` y el docstring de `thematic.py` nombran solo `prompts.json`.
- Los scripts de aislamiento (`test_e2e`, `test_fase1/3/5`) no los ejecuta pytest; hoy pasan corriéndolos a mano → T-002.
- `backend/app/main.py` concentra todos los endpoints (~950 líneas); separar en routers (RNF-17).
- Progreso de codificación e informe vive en memoria; se pierde si el servidor se reinicia (RNF-12).
- La presentación muestra "Iniciar sesión" un instante mientras carga la sesión (`LandingPage` no espera `loading` de `useAuth`); menor.
- Stopwords del análisis léxico fijas y orientadas a educación superior chilena (RF-14).
- La bitácora para el equipo vive en `docs/BITACORA.md`, dentro del repositorio (pedido del usuario, 2026-10-30).
