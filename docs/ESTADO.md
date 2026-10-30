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
| T-017 Nombre y colores Celestica en PDF/DOCX | backend | RNF-16 | 2026-10-30 | `tarea/T-017-exportaciones-celestica` (fusionada, PR #5) |
| T-016a Encabezados, menú agrupado y estado vacío | frontend | RNF-13, RNF-14, RNF-16 | 2026-10-30 | `tarea/T-016a-encabezados-y-navegacion` (fusionada, PR #6) |
| T-016b Encabezados en pestañas del proyecto | frontend | RNF-13, RNF-16 | 2026-10-30 | `tarea/T-016b-encabezados-de-analisis` (fusionada, PR #7) |
| T-002 Aislamiento multi-tenant en pytest | backend | RNF-01, RNF-18 | 2026-10-30 | `tarea/T-002-aislamiento-pytest` (fusionada, PR #8) |
| T-003a Routers (1/2): base, proyectos, integraciones | backend | RNF-17 | 2026-10-30 | `tarea/T-003a-routers-base` (fusionada, PR #9) |

## En curso

- T-003b routers (2/2): análisis, informes y exportaciones, admin (backend), rama `tarea/T-003b-routers-analisis`.
- En cola: RF-02 organizaciones → RF-03 roles.

## Bloqueado / requiere decisión del usuario

- Ninguno. (Nombre interno `SoftInsight` en API, base de datos y logs se mantiene por ahora, decisión del usuario 2026-10-30. Correo `soporte@softinsight.cl`: se mantiene por ahora, decisión del usuario 2026-10-30.)

## Deuda técnica detectada

- Docs de prompts desactualizados: `COMO_FUNCIONA.md` §6 dice "4 prompts" (son 10); `schemas_v2.py:16` y el docstring de `thematic.py` nombran solo `prompts.json`.
- Para RF-02: `store.inc_project_usage` filtra solo por `id`, y `_codify_progress`/`_report_progress` en memoria se indexan solo por `project_id` (hoy protegidos por `_get_or_404`).
- La suite tarda ~35 s, sobre todo por los scripts en subproceso (`test_fase3` duerme para simular streaming).
- `backend/app/main.py`: quedan 639 líneas con análisis, informe, exportación y admin → T-003b.
- Progreso de codificación e informe vive en memoria; se pierde si el servidor se reinicia (RNF-12).
- La presentación muestra "Iniciar sesión" un instante mientras carga la sesión (`LandingPage` no espera `loading` de `useAuth`); menor.
- Tablas del DOCX con estilo de Word "Light Grid Accent 1" (azul del tema de Word, no la paleta Celestica); menor.
- `select` sin `label` en Auditoría (filtro de actor) y Libro de códigos (plantillas) (RNF-14).
- Stopwords del análisis léxico fijas y orientadas a educación superior chilena (RF-14).
- La bitácora para el equipo vive en `docs/BITACORA.md`, dentro del repositorio (pedido del usuario, 2026-10-30).
