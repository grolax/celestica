# T-004: Organizaciones como dueñas de los proyectos (aislamiento por org_id)
Lado: backend
Requerimientos: RF-02, RNF-01, RNF-21
Rama: tarea/T-004-organizaciones
Depende de: T-002, T-003a, T-003b (fusionadas)

## Objetivo
Cada usuario pertenece a **una** organización y los proyectos pertenecen a la organización, no al usuario. El filtro de aislamiento de la capa `store` pasa de `user_id` a `org_id`. Los datos actuales se migran con un script idempotente: cada usuario existente pasa a ser admin de su propia organización.

## Decisiones del usuario (2026-10-30)
1. Al registrarse se crea una organización nueva y el usuario queda como `admin`. Nombre: `empresa`, o `"Organización de <nombre>"` si viene vacío (o `"Organización de <email>"` si tampoco hay nombre).
2. Migración: cada usuario existente → su propia organización con sus proyectos. **No** se unen usuarios por el texto `empresa`, aunque coincida.
3. Las credenciales de Qualtrics siguen siendo **por usuario** (`users.integrations`), sin cambios.
4. Contrato y migración automática en `init_db()` aprobados por el usuario.
5. (Para RF-03, no en esta tarea) Los miembros nuevos los crea el admin con contraseña temporal.

## Alcance
- SÍ, esquema:
  - Colección nueva `organizations`: `{_id: "org_<10 hex>", nombre, created_at}`. Nada más por ahora (industria, marca y config llegan con RF-10).
  - `users`: + `org_id`, + `rol` (`"admin"` para todos en esta tarea). `User` (dataclass) gana ambos campos; `user_from_doc`/`user_to_doc` los leen y escriben.
  - `projects`: + `org_id`. El campo `user_id` existente se **conserva** con el significado "creado por" (no se renombra, para no migrar más de lo necesario); documéntalo en `models.py`.
  - `audit_events`: + `org_id` en cada evento nuevo.
  - Índices en `init_db`: `projects.org_id` y `(org_id, created_at desc)`; `users.org_id`. Se pueden dejar los índices de `user_id` existentes.
- SÍ, `store.py`: `_tenant_filter(project_id, org_id)` filtra por `{"_id": project_id, "org_id": org_id}`. Todas las funciones que hoy reciben `user_id` para aislar reciben `org_id` (renombrar el parámetro). `create_project(org_id, created_by, ...)` guarda ambos. `list_projects(org_id)`. `import_legacy_projects` asigna `org_id` y `user_id`. `inc_project_usage` no cambia (escritura del sistema).
- SÍ, routers y `deps._get_or_404`: pasan `user.org_id`. Los hilos de fondo de codificación e informe capturan `org_id` antes de arrancar (como hoy capturan `user_id`).
- SÍ, `auth.py`: `signup` crea la organización y el usuario (con `org_id` y `rol="admin"`); `_user_out` devuelve el objeto `user` del contrato (`rol` y `organizacion: {id, nombre}`). Si al crear el usuario falla por email duplicado, no debe quedar una organización huérfana (crea la org después del usuario o bórrala en el `except`).
- SÍ, migración `backend/scripts/migrate_orgs.py`, idempotente, con una función `migrate(db) -> dict` (conteos) y uso por línea de comandos:
  1. Cada usuario sin `org_id` → organización nueva (nombre según la regla 1, con su `empresa`/`nombre`/`email`), `org_id` y `rol="admin"`.
  2. Cada proyecto sin `org_id` → `org_id` del usuario de su `user_id`. Si el usuario no existe, dejar el proyecto sin `org_id` (inaccesible, como hoy) y contarlo en el resultado como "huérfano"; no inventar organizaciones.
  3. Cada `audit_event` sin `org_id` → `org_id` de su proyecto.
  4. Correrlo dos veces no crea nada nuevo (segunda corrida: todos los conteos en 0).
- SÍ, `init_db()` llama a `migrate(db)` al arrancar, para que nadie quede sin organización tras actualizar. Debe ser barato cuando no hay nada que migrar (consultas con `{"org_id": {"$exists": false}}`).
- NO: endpoints nuevos, gestión de miembros, permisos por rol (RF-03), perfil de organización (RF-10), cambios en Qualtrics, cambios en el frontend.

## Contrato de API
`docs/API_CONTRATOS.md`, sección **RF-02 · Organizaciones (T-004)**: nueva forma del objeto `user` y alcance por organización de los endpoints de proyectos.

## Archivos probables
- Crear: `07_MVP/backend/scripts/migrate_orgs.py`, `07_MVP/backend/tests/test_organizaciones_pytest.py`.
- Tocar: `app/models.py`, `app/auth.py`, `app/store.py`, `app/database.py`, `app/deps.py`, `app/routers/*.py` (solo `user.id` → `user.org_id` donde es aislamiento; `user.id` se mantiene como "creado por" y en Qualtrics), `07_MVP/COMO_FUNCIONA.md`, `07_MVP/README.md` (migración).
- No tocar: `07_MVP/frontend/**`, `docs/**`, `services/**` (salvo que algo registre `user_id` como tenant; avísalo), las pruebas existentes.

## Criterios de aceptación
- [ ] `pytest tests -q`: las 51 existentes pasan **sin modificarlas** (dos signups ⇒ dos organizaciones, así que `test_aislamiento_pytest.py` pasa a probar acceso entre organizaciones).
- [ ] Pruebas nuevas (mongomock, sin IA real):
  - [ ] signup crea organización con el nombre correcto en los 3 casos (empresa, solo nombre, ni nombre ni empresa) y deja `rol="admin"`; signup/login/me devuelven el objeto `user` del contrato.
  - [ ] Email duplicado no deja organización huérfana.
  - [ ] Dos usuarios de la **misma** organización (el segundo insertado directo en `users` con el mismo `org_id`) ven y editan los proyectos del otro; un tercero de otra organización recibe 404.
  - [ ] Migración: con datos "antiguos" (usuarios y proyectos sin `org_id`, dos usuarios con la misma `empresa`, un proyecto huérfano), `migrate` asigna organizaciones, **no** une a los dos usuarios, cuenta el huérfano, completa `org_id` en `audit_events`; la segunda corrida devuelve todo en 0 y no cambia nada.
  - [ ] Un usuario migrado puede iniciar sesión y ve exactamente sus proyectos de antes.
- [ ] Ninguna consulta de proyectos en `store` filtra por `user_id` (búscalo con `grep` y cuéntalo en el resumen).
- [ ] `COMO_FUNCIONA.md` (modelo de datos y aislamiento) y `README.md` (cómo correr la migración) actualizados.
- [ ] Commits con el formato `T-004 RF-02: ...`.

## Notas
- Riesgo principal: un `user.id` olvidado como filtro de aislamiento. El test de las 25 rutas lo detectaría solo si el olvido rompe el acceso del dueño; por eso el `grep` del criterio es obligatorio.
- `test_report_endpoints_pytest.py` y otros pueden leer `project["user_id"]`; como se conserva, no deberían romperse.
- El frontend no necesita cambios para seguir funcionando (campos nuevos, ninguno quitado). Mostrar la organización en la UI será una tarea de frontend aparte.
