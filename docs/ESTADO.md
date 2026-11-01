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
| T-008a Cambio de contraseña y estados de cuenta | frontend | RF-03, RNF-13, RNF-14 | 2026-10-30 | `tarea/T-008a-cuenta-y-contrasena` (fusionada, PR #15) |
| T-009 Panel interno responde 403 | backend | RNF-13, RNF-02 | 2026-10-30 | `tarea/T-009-admin-403` (fusionada, PR #16) |
| T-008b Pantalla de miembros y acciones por rol | frontend | RF-03, RNF-13, RNF-14 | 2026-10-30 | `tarea/T-008b-miembros-y-acciones-por-rol` (fusionada, PR #17) |
| T-010 Detección de tipos y vista previa | backend | RF-22, RF-25 | 2026-10-30 | `tarea/T-010-deteccion-de-tipos` (fusionada, PR #18) |
| T-011a Preguntas en el proyecto, un análisis por pregunta, contexto IA y migración | backend | RF-23, RNF-05, RNF-08, RNF-21 | 2026-10-30 | `tarea/T-011a-preguntas-en-el-proyecto` (fusionada, PR #19) |
| T-012 Paso "Revisa las preguntas" al crear un proyecto | frontend | RF-25, RF-22, RF-40 (parcial) | 2026-10-30 | `tarea/T-012-revisar-preguntas` (fusionada, PR #20) |
| T-018 Campos de texto con estilo por defecto | frontend | RNF-16, RNF-14 | 2026-10-30 | `tarea/T-018-input-con-estilo` (fusionada, PR #21) |
| T-013 Selector de pregunta abierta | frontend | RF-23, RNF-08, RNF-13 | 2026-10-30 | `tarea/T-013-selector-de-pregunta` (fusionada, PR #22) |
| T-019 Una sola codificación a la vez por pregunta | backend | RF-23, RNF-08 | 2026-10-30 | `tarea/T-019-bloqueo-codificacion-doble` (fusionada, PR #23) |
| T-020 Resultados de preguntas cerradas | backend | RF-30, RNF-01, RNF-02 | 2026-10-30 | `tarea/T-020-resultados-cerradas` (fusionada, PR #24) |
| T-021 Pantalla "Preguntas cerradas" | frontend | RF-30, RNF-13, RNF-14, RNF-15 | 2026-10-31 | `tarea/T-021-pantalla-cerradas` (fusionada, PR #26) |
| T-022 Cruces por grupo de las cerradas | backend | RF-31, RNF-01, RNF-02, RNF-10 | 2026-10-31 | `tarea/T-022-cruces-por-grupo` (fusionada, PR #27) |
| T-023 Unir grupos en los cruces (+ arreglo de selección múltiple por grupo) | backend | RF-31, RNF-07 | 2026-10-31 | `tarea/T-023-unir-grupos` (fusionada, PR #28) |
| T-024 Pantalla de cruces por grupo | frontend | RF-31, RNF-13, RNF-14, RNF-15 | 2026-10-31 | `tarea/T-024-pantalla-cruces` (fusionada, PR #29) |
| T-025 Proyectos sin preguntas abiertas (servidor) | backend | RF-24, RNF-01, RNF-02 | 2026-10-31 | `tarea/T-025-proyectos-solo-cerradas` (fusionada, PR #30) |
| T-026 Proyectos sin preguntas abiertas (pantalla) | frontend | RF-24, RF-40, RNF-13 | 2026-10-31 | `tarea/T-026-pantalla-solo-cerradas` (fusionada, PR #31) |
| T-027 Excel de resultados de cerradas con grupos y gráficos | backend | RF-30, RF-31, RF-24, RF-52 | 2026-10-31 | `tarea/T-027-excel-cerradas` (fusionada, PR #32; revisión visual aprobada por el usuario 2026-11-01) |
| T-028 Botón "Descargar Excel" en Preguntas cerradas | frontend | RF-30, RF-31, RF-24, RF-52 | 2026-11-01 | `tarea/T-028-boton-excel-cerradas` (fusionada, PR #33) |
| T-029 Léxico y propuesta de categorías: una sola vez a la vez + `analysis-status` | backend | RF-23, RNF-08, RNF-01 | 2026-11-01 | `tarea/T-029-analisis-en-curso` (fusionada, PR #34) |
| T-030 Retomar léxico y propuesta de categorías al volver a la pestaña | frontend | RF-23, RNF-08, RNF-13 | 2026-11-01 | `tarea/T-030-retomar-analisis` (fusionada, PR #35) |
| T-031 Plantillas de marco Retail (4) y Municipal (3) | backend | RF-17 | 2026-11-01 | `tarea/T-031-plantillas-retail-municipal` (fusionada, PR #36) |
| T-032 Recomendaciones automáticas: alertas, segmentos y plantilla sugerida | backend | RF-41, RF-17, RNF-01, RNF-02 | 2026-11-01 | `tarea/T-032-recomendaciones` (PR #37, esperando merge) |

## En curso
- Iteración 3 (plan aprobado por el usuario 2026-10-30): T-020 resultados de cerradas (fusionada) → T-021 pantalla "Preguntas cerradas" (fusionada) → T-022 cruces (backend, fusionada) → T-023 unir grupos (backend, fusionada) → T-024 pantalla de cruces (frontend, fusionada) → T-025 proyectos sin abiertas (backend, fusionada) → T-026 proyectos sin abiertas (pantalla, fusionada) → T-027 Excel de resultados de cerradas con grupos y gráficos (backend, fusionada) → T-028 botón de descarga (pantalla, fusionada) → T-029 léxico y propuesta una sola vez a la vez (backend, fusionada) → T-030 retomarlos al volver a la pestaña (pantalla, fusionada) → T-031 plantillas Retail y Municipal, RF-17 (backend, fusionada) → T-032 recomendaciones RF-41 (backend, PR #37) → **T-033 tarjeta "Recomendaciones" (pantalla, en curso; rama sobre T-032)** → editar el marco teórico después de crear el proyecto → RF-43. Más adelante: sugerir la plantilla al crear el proyecto (paso 3 de RF-40).
- Decisiones iteración 3 (usuario, 2026-10-30): % sobre quienes respondieron (N/A aparte; múltiple = % de personas); escalas con palabras como selección única por ahora; umbral fijo n < 10 (configurable por organización en iteración 4); tramos de edad 18–24, 25–34, 35–44, 45–54, 55–64, 65+ **modificables por el cliente** (en T-022/T-023); opciones por frecuencia salvo escalas y tramos.
- Decisiones T-022 (usuario, 2026-10-31): los tramos de edad que elige el cliente valen solo para ese análisis (no se guardan, ni por proyecto ni por organización); cruzar temas de preguntas abiertas por grupo queda para una tarea posterior.
- Decisión (usuario, 2026-10-31): el cliente puede juntar grupos ya hechos (tramos de edad, comunas en zonas) según su preferencia, solo para ese análisis (T-023 servidor, T-024 pantalla).
- Decisión (usuario, 2026-10-31): los proyectos con solo cerradas entregan, por ahora, un **Excel con los resultados de las cerradas** (sin IA); el informe integrado llega con RF-51 (iteración 5).
- Decisión (usuario, 2026-10-31): el Excel incluye los grupos de Ver por y gráficos que tengan sentido (de tendencia): líneas en grupos ordenados (tramos), barras en grupos sin orden. La tendencia en el tiempo requiere olas (RF-27/RF-37).
- Pendiente posterior (usuario): convertir escalas con palabras a 1–5 (el usuario ordena las etiquetas en "Revisa las preguntas").

- Iteración 2 (encuestas completas), plan aprobado por el usuario 2026-10-30: T-010 detección de tipos (fusionada) → T-011a preguntas en el proyecto (aprobada; incluye informe y exportaciones por pregunta, así que T-011b no hace falta) → T-012 paso "Revisa las preguntas" (aprobada) → T-013 selector de pregunta (aprobada). **Iteración 2 completa.**
- Decisiones iteración 2 (usuario, 2026-10-30): RF-24 (proyectos solo cerradas) pospuesto a iteración 3 con RF-30; IA pregunta por pregunta a pedido del usuario (cuidar tokens sin perder calidad); un informe por pregunta abierta hasta RF-51; proyectos existentes quedan con su única pregunta abierta; agregar preguntas después llega con RF-27.
- Decisiones RF-03 del usuario (2026-10-30): contraseña temporal obligatoria de cambiar; quitar = desactivar; nunca sin admin activo; el admin cambia roles; el lector borra solo sus comentarios.

## Requerimientos agregados por el usuario

- **RF-51 (ampliación, 2026-10-30):** comparar temas **entre preguntas abiertas** de una misma encuesta (qué temas se repiten entre preguntas; quién menciona un tema en una y otro en otra). Conteos y cruces en Python sobre codificaciones validadas, **sin llamadas nuevas a la IA**; la IA solo redacta la lectura de conjunto sobre números ya calculados. Pendiente que el usuario lo agregue a `CONTEXTO_SOFTINSIGHT.md` §4.6 (el supervisor no escribe fuera de `docs/`).

- **Columnas ramificadas de Google Forms (decisión del usuario 2026-10-30):** una misma pregunta repartida en varias columnas ("¿En qué comuna vives actualmente?", "… 2", … "… 16", una por región) se ofrece unir en una sola en la revisión de preguntas (T-011/T-012).
- **Respuestas vacías = "N/A" (decisión del usuario 2026-10-30):** donde una persona no respondió (o la columna ramificada no le correspondía), la plataforma muestra **"N/A"**, nunca un valor que parezca elegido. "N/A" se cuenta aparte y no se trata como una opción más de la pregunta.

- **Contexto para la IA (decisión del usuario 2026-10-30):** a la IA solo se le envían como contexto las preguntas marcadas; por defecto solo **género y edad**; **nunca** identificadores (nombre, RUT, email). Hallazgo: el informe v2 enviaba todas las columnas `meta` de cada persona → corregido en T-011a.
- Decisión (usuario, 2026-11-01): antes de RF-41, arreglar que el léxico y la propuesta de categorías se pierdan al salir de la pestaña (T-029 servidor, T-030 pantalla). Recordar el «Ver por…» de cerradas al cambiar de pestaña queda fuera por ahora.
- Decisiones RF-41 (usuario, 2026-11-01): la plantilla se sugiere por palabras clave de la encuesta (título, marco y preguntas), sin pedir el rubro; el cliente puede modificar lo que trae la plantilla (categorías hoy; marco teórico después de crear el proyecto, en tarea aparte). Segundo aviso de calidad: con menos de 30 respuestas, "los resultados pueden variar mucho" (además del aviso con menos de 10). RF-17 (plantillas Retail y Municipal) va antes de RF-41. Primero la tarjeta en el panel del proyecto; la sugerencia al crear el proyecto, después.

## Bloqueado / requiere decisión del usuario

- (Nombre interno `SoftInsight` en API, base de datos y logs se mantiene por ahora, decisión del usuario 2026-10-30. Correo `soporte@softinsight.cl`: se mantiene por ahora, decisión del usuario 2026-10-30.)

## Deuda técnica detectada
- Recomendaciones (T-032): palabras clave genéricas ("comuna", "producto", "cliente", "proyecto", "desarrollo", "usuario") pueden sugerir una plantilla equivocada; afinar con encuestas reales. Un marco editado a partir de una plantilla puede volver a sugerirla.
- Plantillas (T-031): `feedback_empleados` y `percepcion_marca` tienen exclusiones que no nombran a la categoría vecina; las plantillas Retail y Municipal son un primer borrador para afinar con encuestas reales.
- Retomar léxico/propuesta (T-030): si el análisis falla en el servidor mientras la pantalla espera, el botón vuelve a aparecer sin explicar el error (el estado solo dice running/idle).
- Botón "Descargar Excel" (T-028): el error de una descarga fallida sigue visible tras cambiar "Ver por…" hasta la siguiente descarga.
- Proyectos sin abiertas (T-026): el contexto de las pestañas se tipa como `ProjectAbierta` con un cast; un enlace con `?pregunta=` a un proyecto sin abiertas muestra un 404.
- Panel interno (`list_usage_all_projects`) muestra `n_responses` 0 en proyectos sin abiertas (T-025).
- Pantalla de cruces (T-024): con un grupo elegido, las escalas repiten el total en tarjetas y en la fila "Todas las personas"; con 120 grupos (comuna) la pantalla tarda 3,5 s en la encuesta real (meta RNF-10: 2 s).
- Lección (T-023): la cuadratura de los cruces (suma de grupos = total) se verifica con todos los tipos de pregunta; en T-022 se excluyó la selección múltiple y se escapó un descuadre (corregido en T-023, con prueba).
- Cruces (T-022): la edad que llega en tramos ya hechos ("20-24") es `segmento` y no admite `cortes`; para cambiar esos tramos habría que unir opciones. Los tramos vacíos de `numerica` se devuelven con n 0. El router convierte cualquier `ValueError` del cálculo en un 400.
- Pantalla de cerradas (T-021): sin índice para saltar entre muchas preguntas; barras cortas en móvil; en móvil el nombre de la organización se desborda en la barra superior (preexistente). Sin suite Playwright (RNF-18).
- Resultados de cerradas (T-020): el rango de la escala (máximo = mayor valor respondido) y el separador de la selección múltiple se deducen; guardarlos al confirmar "Revisa las preguntas". Cálculo sin caché.
- El progreso de codificación/informe y su lock (y la marca de léxico/propuesta, T-029) viven en memoria de un solo proceso: no sirven con varios workers ni sobreviven a un reinicio (T-019).

- Docs de prompts desactualizados: `COMO_FUNCIONA.md` §6 dice "4 prompts" (son 10); `schemas_v2.py:16` y el docstring de `thematic.py` nombran solo `prompts.json`.
- `store.inc_project_usage` filtra solo por `id` (escritura del sistema), y `_codify_progress`/`_report_progress` en memoria se indexan solo por `project_id` (protegidos por `_get_or_404`).
- Lección (T-006): la prueba de cobertura de T-002 pasó en vacío desde T-003a (`app.routes` con `_IncludedRouter`); corregida leyendo OpenAPI con umbral mínimo. Toda prueba de cobertura debe afirmar que encontró rutas.
- Último admin: comprobar-y-escribir no atómico en `PATCH /api/org/members` (dos admins quitándose a la vez); transacción si hay uso concurrente real.
- `store.list_members/get_member/update_member` sin resguardo ante `org_id` vacío (a diferencia de `_tenant_filter`).
- Cambiar la contraseña no revoca sesiones abiertas (RNF-04).
- `Input` genera ids con `label.replace(/\W/g, "_")`: la ñ pasa a `_` (colisión posible entre etiquetas que solo difieren en ñ).
- El rol en la UI viene de `/auth/me` al cargar; un cambio de rol hecho por otro admin se ve tras recargar.
- `question_types`: pistas de título pueden dar `segmento` de más ("educación financiera"); respuestas "Otro" de Google Forms salen como opciones de 1 mención (agrupar en T-012); una continuación en minúscula que es opción real se une a la anterior (se corrige en T-012); peor caso 30 multi-selección × 4.000 combinaciones ≈ 2,2 s; detección por texto sobre muestra de 1.000 valores; enteros casi todos distintos → identificador (posible falso positivo).
- `codings.<response_id>` rompe con ids de respuesta que contienen puntos (preexistente); nombres de archivo de exportación sin la pregunta; `respondentes` en el mismo documento (RNF-11); un proyecto que falla la migración se reintenta en cada arranque.
- Lección (T-011a): una migración "automática al arrancar" se verifica llamando a `init_db()`, no a la función de migración; y contra una copia de MongoDB real.
- Signup crea el usuario antes que la organización: si la segunda inserción falla, queda un usuario con `org_id` inexistente (no ve nada; ventana mínima).
- Panel admin (`list_usage_all_projects`) muestra `user_id`, no `org_id`.
- La suite tarda ~35 s, sobre todo por los scripts en subproceso (`test_fase3` duerme para simular streaming).
- Progreso de codificación e informe vive en memoria; se pierde si el servidor se reinicia (RNF-12).
- La presentación muestra "Iniciar sesión" un instante mientras carga la sesión (`LandingPage` no espera `loading` de `useAuth`); menor.
- Tablas del DOCX con estilo de Word "Light Grid Accent 1" (azul del tema de Word, no la paleta Celestica); menor.
- `select` sin `label` en Auditoría (filtro de actor) y Libro de códigos (plantillas) (RNF-14).
- Stopwords del análisis léxico fijas y orientadas a educación superior chilena (RF-14).
- La bitácora para el equipo vive en `docs/BITACORA.md`, dentro del repositorio (pedido del usuario, 2026-10-30).
