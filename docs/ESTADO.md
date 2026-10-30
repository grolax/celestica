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
| T-003b Routers (2/2): análisis, informes, admin | backend | RNF-17 | 2026-10-30 | `tarea/T-003b-routers-analisis` (fusionada, PR #10) |
| T-004 Organizaciones (aislamiento por `org_id` + migración) | backend | RF-02, RNF-01, RNF-21 | 2026-10-30 | `tarea/T-004-organizaciones` (fusionada, PR #11) |
| T-005 Organización y rol en la interfaz | frontend | RF-02, RNF-13 | 2026-10-30 | `tarea/T-005-organizacion-en-ui` (fusionada, PR #12) |
| T-006 Permisos por rol en el backend | backend | RF-03, RNF-02, RNF-01 | 2026-10-30 | `tarea/T-006-permisos-por-rol` (fusionada, PR #13) |
| T-007 Gestión de miembros y cambio de contraseña | backend | RF-03, RF-04 (sin correo), RNF-02 | 2026-10-30 | `tarea/T-007-gestion-de-miembros` (fusionada, PR #14) |
| T-008a Cambio de contraseña y estados de cuenta | frontend | RF-03, RNF-13, RNF-14 | 2026-10-30 | `tarea/T-008a-cuenta-y-contrasena` (aprobada, pendiente de subir) |

## En curso

- T-009 panel interno responde 403 (backend), rama `tarea/T-009-admin-403` sobre la rama de T-008a (PR #15 sin fusionar).
- En cola: T-008b pantalla de miembros y acciones por rol (frontend).
- Decisiones RF-03 del usuario (2026-10-30): contraseña temporal obligatoria de cambiar; quitar = desactivar; nunca sin admin activo; el admin cambia roles; el lector borra solo sus comentarios.

## Bloqueado / requiere decisión del usuario

- (Nombre interno `SoftInsight` en API, base de datos y logs se mantiene por ahora, decisión del usuario 2026-10-30. Correo `soporte@softinsight.cl`: se mantiene por ahora, decisión del usuario 2026-10-30.)

## Deuda técnica detectada

- Docs de prompts desactualizados: `COMO_FUNCIONA.md` §6 dice "4 prompts" (son 10); `schemas_v2.py:16` y el docstring de `thematic.py` nombran solo `prompts.json`.
- `store.inc_project_usage` filtra solo por `id` (escritura del sistema), y `_codify_progress`/`_report_progress` en memoria se indexan solo por `project_id` (protegidos por `_get_or_404`).
- Lección (T-006): la prueba de cobertura de T-002 pasó en vacío desde T-003a (`app.routes` con `_IncludedRouter`); corregida leyendo OpenAPI con umbral mínimo. Toda prueba de cobertura debe afirmar que encontró rutas.
- Último admin: comprobar-y-escribir no atómico en `PATCH /api/org/members` (dos admins quitándose a la vez); transacción si hay uso concurrente real.
- `store.list_members/get_member/update_member` sin resguardo ante `org_id` vacío (a diferencia de `_tenant_filter`).
- Cambiar la contraseña no revoca sesiones abiertas (RNF-04).
- `/api/admin/*` responde 401 con contraseña de admin incorrecta y cierra la sesión del usuario → en curso, T-009.
- `Input` genera ids con `label.replace(/\W/g, "_")`: la ñ pasa a `_` (colisión posible entre etiquetas que solo difieren en ñ).
- Signup crea el usuario antes que la organización: si la segunda inserción falla, queda un usuario con `org_id` inexistente (no ve nada; ventana mínima).
- Panel admin (`list_usage_all_projects`) muestra `user_id`, no `org_id`.
- La suite tarda ~35 s, sobre todo por los scripts en subproceso (`test_fase3` duerme para simular streaming).
- Progreso de codificación e informe vive en memoria; se pierde si el servidor se reinicia (RNF-12).
- La presentación muestra "Iniciar sesión" un instante mientras carga la sesión (`LandingPage` no espera `loading` de `useAuth`); menor.
- Tablas del DOCX con estilo de Word "Light Grid Accent 1" (azul del tema de Word, no la paleta Celestica); menor.
- `select` sin `label` en Auditoría (filtro de actor) y Libro de códigos (plantillas) (RNF-14).
- Stopwords del análisis léxico fijas y orientadas a educación superior chilena (RF-14).
- La bitácora para el equipo vive en `docs/BITACORA.md`, dentro del repositorio (pedido del usuario, 2026-10-30).
