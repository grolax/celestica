# Plan de implementación — SoftInsight, siguiente etapa

Fecha: 2026-10-14 · Autor: supervisor · Estado: **aprobado por el usuario (2026-10-14)**
Fuente: `CONTEXTO_SOFTINSIGHT.md` (§4, §5, §6, §8.3, §10) y el código de `07_MVP/` v1.1.

## 1. Punto de partida (verificado hoy en `main`)

| Hallazgo | Evidencia | Consecuencia |
| --- | --- | --- |
| **`pytest tests -q` está en rojo: 7 de 14 fallan** | `test_report_v2_pytest.py`: `FileNotFoundError app/prompts.json`. El archivo está en `.gitignore` y `prompt_store.get_prompts()` no tiene respaldo cuando falta | No se puede aprobar ninguna tarea con pruebas en rojo → hay que arreglarlo primero (T-001) |
| Las pruebas de aislamiento multi-tenant **no las corre pytest** | `test_e2e.py`, `test_fase1/3/5.py` son scripts (`python tests/x.py`) y `conftest.py` los excluye. Hoy pasan: 19 + 39 + 9 + 20 checks | El comando de revisión oficial no protege el aislamiento → incorporarlos a pytest (T-002) antes de tocar el tenant |
| Cambios sin commitear que no reconozco | `frontend/package.json`: `react-router-dom` 6 → **7.18**, `vite` 5 → **8.3** (`@vitejs/plugin-react` sigue en ^4) | Bloquea toda tarea de frontend hasta que el usuario decida (ver §6) |
| Tenant = `user_id` en una sola función | `store._tenant_filter(project_id, user_id)`; todos los helpers reciben `user_id` | RF-02 es un cambio acotado en `store.py` + cambiar el argumento en los routers |
| `main.py` con 948 líneas y todos los endpoints | 40+ rutas con `Depends(get_current_user)`; progreso en dicts globales `_codify_progress` / `_report_progress` | Separar en routers **antes** de RF-02/03 para que esos diffs sean legibles |
| Usuario sin organización real | `User.empresa` es texto libre; signup no crea nada más | RF-02 crea la organización en el signup y en la migración |

## 2. Grafo de dependencias

```
T-001 prompts.json ─┐
T-002 scripts→pytest┴─► T-003 routers ─► T-004 organizaciones (RF-02) ─► T-005 roles (RF-03) ─┬─► T-006 miembros mínimos* ─┐
                                                                                             └───────────────────────────┴─► T-007 UI por rol
[decisión deps frontend] ─► T-008 asistente de creación (RF-40, contra API actual)

T-004 ─► T-009 detección de tipos + vista previa (RF-22, RF-25 backend)
          └─► T-010 projects.questions[] + proyectos sin abiertas (RF-24) ─► T-011 varias abiertas (RF-23)
T-008 + T-009 ─► T-012 paso "revisar preguntas" con API real (RF-25 UI)
T-010/T-011 ─► T-013 selector de pregunta en las pestañas de análisis
T-010 ─► Fase 3 (RF-30, RF-31: cuantitativo y cruces necesitan saber el tipo de cada pregunta)
T-004 ─► Fase 4 (RF-10/11/12: el perfil y las plantillas cuelgan de la organización)
```
`*` T-006 depende de una decisión del usuario (§6, punto 3).

## 3. Cómo se corta el trabajo

La regla del equipo es **una tarea = un solo lado** (los programadores comparten directorio y git). El corte vertical se hace a nivel de **funcionalidad**: cada una avanza contrato → backend → revisión → frontend → revisión y termina usable de punta a punta antes de pasar a la siguiente. No se hacen "todas las tablas primero, todas las pantallas después".

Excepción declarada: T-003 (separar `main.py`) es un movimiento mecánico de ~950 líneas; supera el límite orientativo de 400 líneas, pero se revisa como "solo mover, sin cambiar comportamiento" con la suite completa como red.

## 4. Fases y tareas

### Fase 0 — Línea base en verde (backend)

**T-001 · backend · RNF-18 — `prompt_store` funciona sin `prompts.json`**
- Si `prompts.json` no existe, se crea copiando `prompts_default.json` (o se lee el default). Sin cambiar el contenido de los prompts.
- Aceptación: en un clon limpio `pytest tests -q` pasa 14/14; prueba nueva que borra el archivo temporal y verifica el respaldo; `save_prompt`/`reset_prompt` siguen funcionando.
- Verificación: `git stash -u` no aplica (archivo ignorado) → renombrar `prompts.json` local y correr la suite.

**T-002 · backend · RNF-01, RNF-18 — Los scripts de verificación corren dentro de pytest**
- Un archivo `test_scripts_pytest.py` ejecuta cada script (`test_e2e`, `test_fase1/3/5`) en un subproceso y exige código de salida 0. Sin reescribir los scripts.
- Aceptación: `pytest tests -q` reporta 4 pruebas más; si un check de aislamiento falla, pytest queda en rojo (verificar rompiendo uno a propósito en local).

> **Checkpoint 0:** suite verde y completa en `main`. Usuario fusiona T-001 y T-002.

### Fase 1 — Organizaciones, roles y asistente (iteración 1 de §8.3)

**T-003 · backend · RNF-17 — Separar `main.py` en routers**
- Routers: `auth` (ya existe), `projects`, `analysis`, `reports`, `exports`, `integrations`, `admin`. Estado de progreso a un módulo compartido. `main.py` queda en app + middleware + `include_router`.
- No incluye: cambiar rutas, respuestas, nombres de campos ni lógica.
- Aceptación: mismas rutas en `/openapi.json` (comparar antes/después); suite completa verde; `main.py` < 150 líneas.

**Contrato C-01 (lo escribe el supervisor antes de T-004):** `POST /auth/signup`, `POST /auth/login`, `GET /auth/me` agregan `org: {id, nombre}` y `rol` al usuario; `GET /api/org` (datos de la organización actual); error 403 común `"No tienes permiso para esta acción."`; matriz de permisos por rol.

**T-004 · backend · RF-02, RNF-01, RNF-21 — Entidad Organización y tenant por `org_id`**
- Colección `organizations`; `users.org_id` + `users.rol`; signup crea la organización (nombre = `empresa`, o el email si viene vacío) con el usuario como `admin`.
- `projects.org_id` + `created_by`; `_tenant_filter(project_id, org_id)`; `list_projects`, `log_event`, `audit_events` con `org_id`; índices nuevos.
- `scripts/migrate_orgs.py` idempotente: cada usuario sin org → su propia org como admin; cada proyecto sin `org_id` → la org de su `user_id`.
- Fuera de alcance: roles (T-005), credenciales de Qualtrics (siguen por usuario), perfil/marca (RF-10).
- Aceptación: dos usuarios de la **misma** org ven los mismos proyectos; usuario de **otra** org → 404 en lectura, escritura, export, borrado y progreso; la migración corrida dos veces deja el mismo estado; los proyectos existentes se abren tras migrar; `COMO_FUNCIONA.md` §3 actualizado.
- Riesgo: el diff toca todas las firmas de `store`; si pasa de ~500 líneas se divide en (a) modelo + migración, (b) store + routers.

**T-005 · backend · RF-03, RNF-02 — Roles y permisos en el backend**
- Dependencia común `require_role(...)` junto a `get_current_user`. Matriz propuesta (a confirmar, §6 punto 4):
  - **lector:** solo `GET` de proyectos, resultados, informe y exportaciones + comentar categorías.
  - **analista:** todo lo de proyectos y análisis (crear, codificar, validar, informe, borrar).
  - **admin:** lo de analista + gestión de la organización y sus miembros.
- `/api/admin/*` (prompts con `ADMIN_PASSWORD`) no cambia aquí: lo reemplaza RF-07.
- Aceptación: prueba parametrizada que recorre las rutas con mutación y verifica 403 para lector; analista no accede a gestión de org; la auditoría registra quién hizo cada acción (`created_by`/actor con id de usuario).

**T-006 · backend · RF-04 (parcial) — Gestión mínima de miembros** *(solo si el usuario lo aprueba, §6 punto 3)*
- Admin lista, agrega (email + contraseña temporal + rol), cambia rol y quita acceso. Sin emails ni enlaces de invitación.
- Aceptación: no se puede quitar el último admin; un usuario quitado recibe 401/403 en su siguiente petición; acceso cruzado entre orgs → 404.

**T-007 · frontend · RF-03 (UI), RNF-13 — Navegación y acciones según rol**
- Tipos de `auth` con `org` y `rol`; Header muestra la organización; se ocultan acciones de mutación al lector; `client.ts` muestra el mensaje 403 del backend. Si existe T-006: pantalla de miembros en Configuración.
- Aceptación: `npm run build` sin errores; probado a mano con tres usuarios (admin/analista/lector); la UI nunca es la única barrera (el backend ya responde 403).

**T-008 · frontend · RF-40 — Asistente de creación en pasos (contra la API actual)**
- Reemplaza el formulario único de `NewProject.tsx` por 4 pasos: (1) subir/importar, (2) elegir la columna de texto (como hoy; en Fase 2 pasa a "revisar preguntas detectadas"), (3) objetivo y plantilla, (4) confirmar. Texto de ayuda en lenguaje simple en cada paso; navegable con teclado.
- Usa solo los endpoints existentes (`POST /api/projects`, `/from-qualtrics`, `/from-google-forms`, `/api/framework-templates`). Sin datos simulados.
- Aceptación: build verde; los 3 orígenes crean proyecto igual que antes; volver atrás no pierde lo ingresado.

> **Checkpoint 1:** el usuario fusiona; prueba manual de punta a punta con la migración corrida sobre una copia de su base local. Antes de seguir, el supervisor re-planifica la Fase 2 con lo aprendido.

### Fase 2 — Modelo de preguntas (iteración 2)

**Contrato C-02:** `POST /api/imports/preview` (archivo o configuración de fuente) → columnas con tipo detectado, n° de vacías, ejemplos y opciones; `POST /api/projects*` acepta `questions: [{columna, tipo}]` confirmadas; `GET /api/projects/{id}` expone `questions[]`.

| Tarea | Lado | RF | Resumen | Aceptación clave |
| --- | --- | --- | --- | --- |
| T-009 | backend | RF-22, RF-25 | Detector de tipos determinístico (abierta, Likert, NPS, única, múltiple, sí/no, numérica, fecha, id, segmento) + endpoint de vista previa | Pruebas por tipo con columnas de ejemplo; sin IA |
| T-010 | backend | RF-22, RF-24 | `projects.questions[]`; creación con preguntas confirmadas; proyecto sin abiertas omite léxico/codificación; migración que deriva `questions` de `columns` + `text_column` | Proyectos viejos se abren; migración idempotente |
| T-011 | backend | RF-23 | Varias abiertas: léxico, categorías, codificación e informe por `question_id` (por defecto, la primera abierta para compatibilidad) | **Requiere diseño propio antes de delegar**; probablemente se divide en 2 |
| T-012 | frontend | RF-25 | Paso 2 del asistente con la vista previa real y corrección de tipos | Build verde; corrige un tipo y se respeta al crear |
| T-013 | frontend | RF-23, RF-24 | Selector de pregunta abierta en pestañas de análisis; ocultar léxico/codificación sin abiertas | Build verde; proyecto viejo se ve igual que hoy |

> **Checkpoint 2:** re-planificar Fase 3.

### Fases 3 a 5 — esbozo (se detallan en su checkpoint)

| Fase | Backend | Frontend |
| --- | --- | --- |
| 3 | RF-30 cuantitativo, RF-31 cruces con umbral n<10 (principio 6), RF-17 plantillas retail y municipal | RF-43 panel para lectores, RF-41 recomendaciones por reglas |
| 4 | RF-10 perfil de org, RF-11 marca en PDF/DOCX, RF-12 plantillas en Mongo | Configuración de org, marca y vocabulario (RF-10, RF-13) |
| 5 | RF-51 informe integrado, RNF-12 trabajos persistentes y reanudables | RF-42 modo guiado/experto, RF-45 ayuda contextual, Playwright (RNF-18) |

## 5. Riesgos

| Riesgo | Mitigación |
| --- | --- |
| La migración a `org_id` deja proyectos inaccesibles | Script idempotente con prueba; checkpoint 1 la corre sobre una copia de la base real antes de fusionar |
| Regresión de aislamiento al cambiar el filtro | T-002 primero: los 39 checks de `test_fase1` pasan a ser obligatorios en pytest |
| RF-23 (varias abiertas) cambia la forma de `categories`/`codings` y toca casi todo | Diseño aparte en el checkpoint 1; campo `question_id` con valor por defecto para no romper lo existente |
| Documento del proyecto crece con varias abiertas (límite 16 MB, RNF-11) | Medir en Fase 2 con 50.000 filas sintéticas; si se acerca, tarea dedicada para mover respuestas a colección propia |
| Subida de Vite 8 / React Router 7 sin revisar | No tocar el frontend hasta que el usuario decida |

## 6. Decisiones del usuario (2026-10-14)

1. **Dependencias del frontend:** se mantienen Vite 8 y React Router 7. Se consolidan en **T-000 (frontend)**: plugin-react compatible e instalación limpia verificada.
2. **Un usuario = una organización** (`users.org_id`). Las membresías múltiples quedan para asesores (RF-06).
3. **T-006 aprobada:** gestión mínima de miembros sin email, en la Fase 1.
4. **Matriz de permisos aprobada:** lector = ver, descargar y comentar; analista = todo en proyectos, incluido borrar; admin = analista + gestión de la organización.
