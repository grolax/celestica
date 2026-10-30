# T-002: Pruebas de aislamiento multi-tenant dentro de pytest
Lado: backend
Requerimientos: RNF-01, RNF-18
Rama: tarea/T-002-aislamiento-pytest
Depende de: —

## Objetivo
`pytest tests -q` debe fallar si un usuario puede ver o modificar un proyecto ajeno. Hoy los scripts `test_e2e.py` y `test_fase1/3/5.py` están excluidos en `conftest.py` y solo corren a mano, y el acceso cruzado se prueba en ~8 de las 25 rutas `/api/projects/{project_id}/...`. Esta tarea es la red de seguridad antes de pasar de `user_id` a `org_id` (RF-02).

## Alcance
- SÍ: que pytest ejecute los 4 scripts. La forma más simple y segura: un archivo `tests/test_scripts_pytest.py` con un test parametrizado que corre cada script en un **subproceso** (`sys.executable tests/<script>.py`, `cwd` = `07_MVP/backend`) y exige código de salida 0, mostrando su stdout si falla. Así sus parches globales de módulo (`thematic.codify_all = ...`, `requests.get = ...`, `database._client = ...`) no contaminan a los demás tests. Quitar esos 4 nombres de `collect_ignore` solo si se reescriben como tests; si se usan subprocesos, `collect_ignore` se mantiene (los scripts no deben importarse en el proceso de pytest).
- SÍ: archivo nuevo `tests/test_aislamiento_pytest.py` (mongomock, IA simulada, sin API real) con un test **parametrizado sobre todas las rutas** que reciben `project_id` en `app/main.py` (hoy 25: GET/DELETE del proyecto, responses, apply-template, lexical GET/POST, categories propose/POST/PATCH, comments POST/DELETE, codify POST y progress, codings PUT, summary, audit, export traceability/pdf/docx/csv/xlsx, report POST/GET/progress, usage). Para cada una: el usuario B, con un cuerpo **válido** (para que la respuesta no sea 422 por validación), recibe **404** sobre el proyecto de A. Después se verifica que el proyecto de A quedó intacto (categorías, codificaciones, conteo de auditoría) y que no se registró ninguna llamada a la IA simulada a nombre de B.
- SÍ: un test que recorre `app.routes` y falla si aparece una ruta con `{project_id}` que no está en la lista parametrizada, para que cada ruta nueva obligue a agregar su prueba de acceso cruzado (RNF-01).
- SÍ: `GET /api/projects` de B no lista proyectos de A, y `GET /api/integrations/qualtrics/credentials` de B no expone la configuración de A.
- SÍ: si alguna ruta **no** devuelve 404 (fuga real), corregirla en la capa `store`/`_get_or_404`, no en el router, y explicarlo en el resumen.
- NO: reescribir los scripts existentes, separar `main.py` en routers (es la tarea siguiente), cambiar el esquema, introducir `org_id`.

## Contrato de API
No cambia. Si se corrige una fuga, el comportamiento esperado es 404 (igual que el resto).

## Archivos probables
- Crear: `07_MVP/backend/tests/test_scripts_pytest.py`, `07_MVP/backend/tests/test_aislamiento_pytest.py`.
- Tocar: `07_MVP/backend/tests/conftest.py` (solo el comentario, si cambia el motivo), `07_MVP/backend/tests/README.md` (que diga que `pytest tests -q` ya corre todo).
- Tocar solo si hay fuga: `07_MVP/backend/app/store.py` o `_get_or_404` en `app/main.py`.
- No tocar: `07_MVP/frontend/**`, `docs/**`, el contenido de `test_e2e.py` y `test_fase*.py`.

## Criterios de aceptación
- [ ] `pytest tests -q` en verde (hoy 19) e incluye los 4 scripts y el test de aislamiento.
- [ ] Prueba de control: rompe a propósito el filtro de un endpoint en local (sin commitearlo) y confirma que `pytest` falla; cuéntalo en el resumen.
- [ ] Las 25 rutas con `{project_id}` están cubiertas, y el test de `app.routes` falla si se agrega una sin cubrir.
- [ ] Ninguna prueba llama a la API real de Anthropic ni a internet.
- [ ] `tests/README.md` actualizado.
- [ ] Commits con el formato `T-002 RNF-01: ...`.

## Notas
- Los scripts dependen de `cwd`: usa `cwd` explícito en el subproceso para que funcione igual desde la raíz del repo o desde `07_MVP/backend`.
- `test_fase3.py` duerme ~2 s para simular streaming; es aceptable.
- Para codify y report, parchea `thematic` en el test (fixture con `monkeypatch`) para que una fuga no gaste API y quede registrada en el doble.

## Revisión
2026-10-30 — **Aprobada** (supervisor).
- `pytest tests -q`: 51 pasan (19 + 4 scripts en subproceso + 28 de aislamiento), ~35 s.
- `test_scripts_pytest.py`: cada script en subproceso con `cwd` explícito y `ANTHROPIC_API_KEY=sk-test`; `collect_ignore` se mantiene.
- `test_aislamiento_pytest.py`: las 25 rutas con `{project_id}` (26 casos, `report` en v1 y v2) con cuerpos válidos y IDs reales; exige 404 con detalle "Proyecto no encontrado", documento de A idéntico, conteo de auditoría igual y cero llamadas al doble de IA (`thematic.client` lanza error). Los dobles parchean las mismas funciones que usa `main.py` (`thematic.<fn>`).
- `test_toda_ruta_con_project_id_esta_cubierta` falla si aparece una ruta nueva sin prueba. Listado de proyectos y credenciales de Qualtrics de B no exponen lo de A.
- Prueba de control del programador: quitar el filtro de dueño en `store.get_project` o `store.delete_project` hace fallar 25 de 28 casos.
- Sin fugas encontradas; `app/` no se tocó.
- A considerar en RF-02: `store.inc_project_usage` filtra solo por `id` (escritura del sistema, sin endpoint) y `_codify_progress`/`_report_progress` en memoria indexados por `project_id` (protegidos por `_get_or_404`).
