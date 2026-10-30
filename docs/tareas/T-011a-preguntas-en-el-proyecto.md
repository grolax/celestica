# T-011a: Preguntas del proyecto y un análisis por pregunta abierta
Lado: backend
Requerimientos: RF-23, RF-22 (persistencia), RNF-05, RNF-08, RNF-21
Rama: tarea/T-011a-preguntas-en-el-proyecto
Depende de: T-010 (fusionada)

## Objetivo
El proyecto deja de girar en torno a una sola columna: guarda **todas las preguntas** confirmadas (con su tipo), las **respuestas de cada persona** a cada pregunta (vacías = N/A) y **un análisis independiente por cada pregunta abierta**. Todas las operaciones de análisis, informe y exportación funcionan sobre una pregunta elegida (por defecto, la primera abierta). Los proyectos existentes se migran solos y se ven igual que hoy.

## Decisiones del usuario (2026-10-30)
- Un análisis por pregunta abierta; la IA solo corre a pedido y pregunta por pregunta (cuidar tokens).
- Respuesta vacía = N/A (`null`), nunca una opción.
- Columnas ramificadas (por ejemplo, comuna por región) se unen en una pregunta.
- A la IA solo se le envía como contexto lo marcado `contexto_ia`; por defecto **solo género y edad**. **Nunca** identificadores (nombre, RUT, email…). Hoy el informe v2 envía todas las demás columnas: esto se corrige aquí.

## Esquema (proyecto)
- `preguntas`: `[{id, titulo, columnas[], tipo, contexto_ia}]` (ids estables `q_<n>` o `q_<hex>`).
- `respondentes`: `[{id, valores: {<pregunta_id>: str | null}}]`. El `id` es el de hoy (`id_respuesta` si existe, o `R0001`…). Una sola fila por persona.
- `analisis`: `{<pregunta_id abierta>: {lexical, lexical_interpretation, categories, codings, qualitative_report, v2_analyses_cache, ...}}`: lo que hoy vive en la raíz del proyecto, ahora por pregunta.
- Se eliminan de la raíz `responses`, `lexical`, `lexical_interpretation`, `categories`, `codings`, `qualitative_report`, `v2_analyses_cache` (pasan a `analisis`). `columns` y `text_column` se pueden conservar como datos informativos de origen.
- Documento proyectado: 500 personas × 47 preguntas cabe con holgura en 16 MB; no mover a otra colección en esta tarea (RNF-11 queda como deuda).

## Alcance
- SÍ, **una sola vista por pregunta** en `store` (por ejemplo `vista_pregunta(project, pregunta_id) -> dict`) que arma, para esa pregunta abierta, un diccionario con la misma forma que hoy usan routers, `export.py` y `thematic.py`: `responses` = `[{id, text, meta}]` solo de personas con texto no vacío, con `meta` = **solo** las preguntas `contexto_ia` (clave = título) y **jamás** de tipo `identificador`; y los campos de análisis de `analisis[pregunta_id]`. Toda lectura de análisis pasa por esa vista; nada vuelve a leer `project["responses"]` ni `project["categories"]` de la raíz.
- SÍ, **escrituras por pregunta**: las funciones de `store` que hoy escriben en la raíz (`set_project_field`, `push_category`, `update_category_fields`, `push_comment`, `pull_comment`, `set_codings_for_response`, `set_codings_bulk`, `_set_categories_array`) reciben `pregunta_id` y escriben en `analisis.<pregunta_id>.…` con `$set`/`$push` puntuales, siempre con `_tenant_filter`.
- SÍ, **creación** con `preguntas` según el contrato (y el camino de compatibilidad sin `preguntas`). La unión de columnas toma el primer valor no vacío. Validaciones y errores del contrato. Auditoría `creacion_proyecto` con el número de preguntas por tipo (sin valores).
- SÍ, **parámetro `pregunta`** en todas las operaciones listadas en el contrato, resuelto en un solo lugar (por ejemplo, una dependencia o un helper junto a `_get_or_404`), con 404 "Pregunta no encontrada".
- SÍ, **progreso por pregunta**: `_codify_progress` y `_report_progress` indexados por `(project_id, pregunta_id)`; los hilos de fondo capturan `pregunta_id`.
- SÍ, **informe v2 y v1, exportaciones, trazabilidad, resumen y uso** funcionan sobre la vista de la pregunta (con `?pregunta`). El caché del informe v2 es por pregunta.
- SÍ, **migración idempotente** en `app/migrations.py` (llamada desde `init_db`, como la de organizaciones): todo proyecto sin `preguntas` →
  - `preguntas`: una pregunta `abierta` para `text_column` con id fijo `q_1`, más una por cada otra columna original, con el tipo que dé `detectar()` sobre los valores guardados en `meta` (las de `identificador` quedan `contexto_ia: false`; `contexto_ia: true` solo para segmento de género/sexo/edad, como en la creación sin `preguntas`).
  - `respondentes` desde `responses` (`text` → `q_1`, `meta` → el resto; `""` → `null`).
  - `analisis.q_1` con los campos de análisis de la raíz (`categories`, `codings`, `lexical`, `lexical_interpretation`, `qualitative_report`, `v2_analyses_cache`, etc.); luego se quitan de la raíz.
  - Segunda corrida: no cambia nada. Proyecto ya migrado: no se toca.
- SÍ, pruebas nuevas `tests/test_preguntas_pytest.py` (mongomock, IA simulada):
  - Crear con `preguntas` (dos abiertas, un segmento unido de 3 columnas, un identificador, género y edad con `contexto_ia`): respuesta según contrato; N/A como `null`; la unión toma el primer no vacío.
  - Errores 400/422 del contrato.
  - Análisis independiente: categorías y codificación de `q_A` no aparecen en `q_B`; léxico por pregunta; progreso de codificación por pregunta.
  - **Privacidad y tokens:** con la IA simulada, capturar lo que reciben `propose_categories`, `codify_all` y el informe v1/v2: solo el texto de la pregunta elegida y, como contexto, solo las preguntas `contexto_ia`; un email/RUT de una columna `identificador` **no aparece en ningún argumento** (búscalo en el JSON de los argumentos).
  - `?pregunta` inexistente o cerrada → 404; sin `pregunta` → la primera abierta.
  - Migración: un proyecto "antiguo" (raíz con `responses`, `categories`, `codings`, `lexical`, `qualitative_report`) queda con `q_1` y el mismo contenido visible por la API (`GET /api/projects/{id}` y `summary` dan lo mismo antes y después); segunda corrida sin cambios.
- SÍ, **pruebas existentes**: se permite adaptar solo lo que dependa de la forma interna del documento (por ejemplo, pruebas que lean `project["responses"]` o `project["categories"]` directo de la base o llamen a `store` con la firma vieja). Cada adaptación debe mantener lo que la prueba verifica; enuméralas en el resumen. Las pruebas que solo usan la API no deberían cambiar. `test_aislamiento_pytest.py` y `test_permisos_pytest.py` deben seguir cubriendo todas las rutas.
- NO: frontend (T-012/T-013), análisis cuantitativo de cerradas (RF-30), agrupar "Otro", agregar preguntas a un proyecto existente (RF-27), cambiar prompts.

## Contrato de API
`docs/API_CONTRATOS.md`, sección **RF-23 · Preguntas del proyecto y varias preguntas abiertas (T-011a)**.

## Archivos probables
- Tocar: `app/store.py`, `app/migrations.py`, `app/deps.py`, `app/routers/{projects,integrations,analysis,reports}.py`, `app/services/export.py` (solo si no basta con la vista), `07_MVP/COMO_FUNCIONA.md`.
- Crear: `tests/test_preguntas_pytest.py`.
- No tocar: `07_MVP/frontend/**`, `docs/**`, los prompts y la lógica de `thematic.py` (recibe la vista; si necesitas tocarla, explica por qué).

## Criterios de aceptación
- [ ] `pytest tests -q` en verde (hoy 176 + las nuevas), con las adaptaciones permitidas enumeradas.
- [ ] `grep` en `app/`: ningún acceso a `project["responses"]`, `project["categories"]`, `project["codings"]`, `project["lexical"]` o `project["qualitative_report"]` fuera de la vista y de la migración (cuéntalo en el resumen).
- [ ] Ningún argumento enviado a la IA contiene datos de columnas `identificador` ni de preguntas sin `contexto_ia` (prueba).
- [ ] Migración idempotente; un proyecto migrado responde igual por la API.
- [ ] El frontend actual sigue funcionando sin cambios (todas las rutas aceptan llamadas sin `pregunta`).
- [ ] `COMO_FUNCIONA.md` describe el nuevo esquema, la vista por pregunta y la regla de contexto para la IA.
- [ ] Commits con el formato `T-011a RF-23: ...`, en pasos lógicos (esquema y vista → escrituras → creación → routers → migración → pruebas). El diff puede superar las 400 líneas: avísalo.

## Revisión 1
2026-10-30 — **Con cambios** (supervisor).

Lo que está bien: 192 pruebas pasan; `vista_pregunta` es el único punto de lectura y filtra el contexto (`contexto_ia`, nunca `identificador`, sin N/A); escrituras por pregunta con `_tenant_filter`; progreso por `(project_id, pregunta_id)`; la prueba de privacidad captura el JSON que iría a Anthropic y comprueba lo que sí y lo que no debe aparecer. El supervisor copió la base local real (11 proyectos, entre ellos la encuesta real de 484 respuestas y 8 categorías) a una base aparte y corrió la migración y `list_projects` **contra MongoDB real**: datos visibles iguales antes y después (respuestas, categorías, codificaciones, informe), campos viejos eliminados, pipeline de `list_projects` correcto, contexto de la encuesta real = edad y género.

Cambios pedidos:

1. **Bloqueante — `init_db()` no ejecuta la migración de preguntas.** `app/database.py` importa `migrate_preguntas` pero solo llama a `migrate_orgs(db)`. En la copia real, después de `init_db()` la segunda llamada manual migró los 11 proyectos (debía dar 0): al arrancar el servidor, los proyectos existentes quedarían en el esquema viejo y dejarían de abrirse. Llamarla en `init_db()` **después** de `migrate_orgs`. Agrega una prueba que inserte un proyecto con la forma antigua, llame a `init_db()` (no a `migrate_preguntas`) y verifique que quedó migrado y que `GET /api/projects/{id}` responde 200 con sus datos.
2. **La migración no debe tumbar el arranque.** Envuelve la conversión de **cada** proyecto en `try/except`: si uno falla, se registra en el log (id y tipo de error, sin datos de respuestas), se deja sin tocar y se cuenta en `{"proyectos": n, "fallidos": m}`; los demás se migran. Prueba con un proyecto antiguo malformado (por ejemplo, `meta` con un valor no texto, o `responses` sin `text`) junto a uno sano.
3. **Edad numérica como contexto por defecto.** Decisión del usuario: a la IA le importan **género y edad**. `contexto_por_defecto` hoy exige `tipo == "segmento"`, y `detectar()` puede dar `numerica` o `seleccion_unica` para la edad. Debe aceptar `segmento`, `numerica` y `seleccion_unica` cuando el título menciona género/sexo/edad (nunca `identificador`). Ajusta el contrato no hace falta: el supervisor lo actualiza. Prueba con edad numérica ("2. ¿Cuál es tu edad?" con valores 18–70).
4. **Caché v2 migrado.** Su huella ya no coincide con el `meta` nuevo (no ahorra nada) y su `metadata_snapshot` guarda las columnas antiguas, incluidos posibles identificadores. La migración debe **descartar** `v2_analyses_cache` en vez de moverlo a `analisis.q_1`. Ajusta la prueba de migración en consecuencia y `COMO_FUNCIONA.md`.

Aceptado sin cambios: `apply-template` con `?pregunta` (el supervisor lo agrega al contrato); `set_project_field` con `pregunta_id` opcional para campos de la raíz; contexto N/A omitido; una fila por persona; `pregunta` en el detalle de auditoría. Deuda: ids de respuesta con puntos en `codings.<id>`; nombres de archivo de exportación sin la pregunta; `respondentes` en el mismo documento (RNF-11).

## Revisión 2
2026-10-30 — **Aprobada** (supervisor).
- `pytest tests -q`: 195 pasan (3 nuevas: arranque con `init_db()`, proyecto malformado que no tumba la migración, edad numérica como contexto).
- Verificación contra **MongoDB real** sobre una copia de la base local (11 proyectos, incluida la encuesta real): importar `app.main` (que ejecuta `init_db()`) deja 0 proyectos sin migrar; segunda corrida `{"proyectos": 0, "fallidos": 0}`; con un token de su dueño real, cada proyecto responde 200 en `GET /api/projects/{id}`, aparece en `GET /api/projects` y conserva `n_responses`, categorías, `n_coded`, léxico e informe. Copia borrada al terminar; base original sin cambios.
- Caché v2 descartado al migrar; edad numérica o selección única con título de género/sexo/edad como contexto por defecto (nunca identificador).
- Riesgos anotados: un proyecto que falla la migración se reintenta y se registra en cada arranque; "edad" en `seleccion_unica` es amplio ("¿Qué edad tienen tus hijos?"), el usuario lo desmarca en T-012.
