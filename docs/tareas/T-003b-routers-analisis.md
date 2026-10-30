# T-003b: Separar main.py en routers (2/2): análisis, informes y exportaciones, admin
Lado: backend
Requerimientos: RNF-17
Rama: tarea/T-003b-routers-analisis
Depende de: T-003a (usa `app/deps.py` y `app/routers/`)

## Objetivo
Segunda mitad de la separación. Los endpoints restantes salen de `main.py`, que queda solo con la configuración de la app (creación de `FastAPI`, `init_db`, manejador de errores, observabilidad de costo, CORS e `include_router`). Movimiento de código puro, OpenAPI idéntico y pruebas sin modificar.

## Alcance
- SÍ: en `app/routers/`:
  - `analysis.py`: léxico (POST/GET), categorías (propose, POST, PATCH), comentarios (POST/DELETE), codificación (POST, progress), recodificación (PUT codings), `summary` y `audit`, con sus modelos Pydantic.
  - `reports.py`: informe (POST, progress, GET) con `_report_section`, `export/traceability`, `export/pdf`, `docx`, `csv`, `xlsx` y `_download`.
  - `admin.py`: `/api/admin/usage`, `/api/admin/health` y los 3 endpoints de prompts, con `PromptUpdate`.
- SÍ: los hilos de fondo de codificación e informe usan `deps.codify_progress`/`deps.report_progress` (o como se llamen tras T-003a), el **mismo objeto** compartido; no crear copias por router.
- SÍ: mismas reglas que T-003a: sin `prefix` ni `tags`, mismos nombres de función, servicios llamados como atributo de módulo (`thematic.<fn>`, `export_svc.<fn>`), `main.py` sigue exportando `app` y `ADMIN_PASSWORD`.
- NO: cambiar lógica, rutas, respuestas o mensajes; persistir el progreso en Mongo (eso es RNF-12); tocar pruebas.

## Contrato de API
Sin cambios. OpenAPI idéntico al de `main` (mismo SHA-256 de `json.dumps(app.openapi(), sort_keys=True)`).

## Archivos probables
- Crear: `07_MVP/backend/app/routers/analysis.py`, `reports.py`, `admin.py`.
- Tocar: `07_MVP/backend/app/main.py`, `07_MVP/backend/app/deps.py` (solo si falta algo compartido), `07_MVP/COMO_FUNCIONA.md`.
- No tocar: `07_MVP/frontend/**`, `docs/**`, `07_MVP/backend/tests/**`, `store.py`, `auth.py`, `services/**`.

## Criterios de aceptación
- [ ] `pytest tests -q`: 51 pasan sin modificar ninguna prueba.
- [ ] OpenAPI idéntico al de `main`; indica cómo lo comprobaste.
- [ ] `main.py` sin endpoints (solo configuración e `include_router`), de menos de unas 120 líneas.
- [ ] Sin importaciones circulares.
- [ ] `COMO_FUNCIONA.md` actualizado y la deuda "main.py concentra todos los endpoints" resuelta.
- [ ] Commits con el formato `T-003b RNF-17: ...`, idealmente uno por router.
