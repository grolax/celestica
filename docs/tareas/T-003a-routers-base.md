# T-003a: Separar main.py en routers (1/2): base común, proyectos e integraciones
Lado: backend
Requerimientos: RNF-17
Rama: tarea/T-003a-routers-base
Depende de: T-002 (fusionada; sus 51 pruebas son la red de seguridad)

## Objetivo
`app/main.py` (948 líneas) concentra todos los endpoints. Esta primera mitad crea la base compartida y saca a routers propios las plantillas, los proyectos y las integraciones. Es un **movimiento de código puro**: la API queda idéntica, byte a byte en su OpenAPI, y ninguna prueba se modifica.

## Alcance
- SÍ: `app/deps.py` con lo que comparten los routers, movido tal cual desde `main.py`: `_get_or_404`, `_check_admin`, `ADMIN_PASSWORD`, `_slug`, `_codify_progress`, `_report_progress` y `_REPORT_EXPECTED_CHARS`. Se pueden quitar los guiones bajos iniciales al hacerlos públicos, pero sin cambiar su lógica.
- SÍ: paquete `app/routers/` con:
  - `projects.py`: plantillas (`/api/framework-templates`, `apply-template`), listar, crear, obtener, borrar, `import-legacy`, `responses` y `/api/projects/{project_id}/usage`. Incluye `_create_project_from_df`.
  - `integrations.py`: credenciales y encuestas de Qualtrics, `from-qualtrics` y `from-google-forms`, con sus modelos Pydantic y `_qualtrics_config`.
- SÍ: `main.py` incluye estos routers con `app.include_router(...)`, **sin** `prefix` ni `tags` (las rutas completas quedan escritas en cada decorador, como hoy, para que el OpenAPI no cambie). El resto de los endpoints sigue en `main.py` hasta T-003b.
- SÍ: `main.py` sigue exportando `app` y `ADMIN_PASSWORD` (`tests/test_report_endpoints_pytest.py` hace `from app.main import ADMIN_PASSWORD, app`).
- SÍ: los routers llaman a la IA y a los servicios como `thematic.<fn>`, `store.<fn>`, `qualtrics.<fn>` (atributo de módulo, no `from ... import fn`), porque las pruebas parchean esos atributos.
- SÍ: mantener el orden relativo de declaración de rutas que comparten método y prefijo (por ejemplo `POST /api/projects/import-legacy`, `from-qualtrics` y `from-google-forms` frente a las rutas con `{project_id}`).
- NO: cambiar rutas, métodos, nombres de funciones de endpoint (forman el `operationId`), parámetros, respuestas, mensajes de error ni lógica; mover análisis, informe, exportación o admin (eso es T-003b); renombrar `store`, tocar `auth.py`, agregar `org_id`; modificar pruebas.

## Contrato de API
Sin cambios. Verificación: el OpenAPI generado (`app.openapi()`) es idéntico al de `main` (mismo SHA-256 de `json.dumps(spec, sort_keys=True)`).

## Archivos probables
- Crear: `07_MVP/backend/app/deps.py`, `07_MVP/backend/app/routers/__init__.py`, `routers/projects.py`, `routers/integrations.py`.
- Tocar: `07_MVP/backend/app/main.py`, `07_MVP/COMO_FUNCIONA.md` (la parte de estructura del backend).
- No tocar: `07_MVP/frontend/**`, `docs/**`, `07_MVP/backend/tests/**`, `store.py`, `auth.py`, `services/**`.

## Criterios de aceptación
- [ ] `pytest tests -q`: 51 pasan **sin modificar ninguna prueba**.
- [ ] OpenAPI idéntico al de `main` (mismo SHA-256); indica en el resumen cómo lo comprobaste.
- [ ] `main.py` ya no contiene los endpoints de proyectos, plantillas ni integraciones; cada uno vive en su router, con el mismo código.
- [ ] Sin importaciones circulares: `deps.py` no importa `main`, los routers no importan `main`.
- [ ] `COMO_FUNCIONA.md` describe la nueva estructura.
- [ ] Commits con el formato `T-003a RNF-17: ...`; idealmente un commit por router, para que `git diff --color-moved` muestre bloques movidos.

## Notas
- Revisión con `git diff --color-moved=dimmed-zebra`: el supervisor espera ver casi solo líneas movidas.
- `_usage_sink`, `_usage_step`, el `exception_handler`, CORS y `init_db` quedan en `main.py` (configuración de la app).

## Revisión
2026-10-30 — **Aprobada** (supervisor).
- `pytest tests -q`: 51 pasan; ninguna prueba modificada.
- OpenAPI: el supervisor comparó por su cuenta la lista de 43 operaciones (método, ruta, `operationId`) y el SHA-256 contra la huella tomada en `main` antes de delegar: idénticos (`00ff476d…b6eda4`).
- `main.py` de 948 a 639 líneas; `deps.py` (46), `routers/projects.py` (186), `routers/integrations.py` (123). Los routers se incluyen sin `prefix` ni `tags`; `main` sigue exportando `ADMIN_PASSWORD`.
- Sin importaciones circulares (`deps` y routers no importan `main`). `integrations.py` importa `_create_project_from_df` desde `routers.projects`; aceptado.
- Se conservan los guiones bajos de los helpers; aceptado (renombrar no aporta hoy).
- `COMO_FUNCIONA.md` y `README.md` describen la nueva estructura.
