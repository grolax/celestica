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

## Revisión 1
2026-10-30 — **Con cambios** (supervisor).

Lo que está bien: 58 pruebas pasan; `store.py` ya no filtra proyectos por `user_id` (verificado con `grep`: solo quedan escrituras de "creado por", el `$project` del panel admin y la autoría del evento); los hilos de codificación e informe capturan `org_id`; signup sigue el contrato; la migración cumple las decisiones del usuario. Se acepta el `org_id: null` de los proyectos huérfanos (con el resguardo del punto 2).

Cambios pedidos:

1. **`tests/test_aislamiento_pytest.py` quedó debilitado** (líneas 101 y 112). `store.set_project_field(pid, users["a"][1], ...)` y `store.get_project(..., e["uid_a"])` reciben el **id de usuario** donde ahora va el `org_id`. Por eso el informe de A no se guarda y `_snapshot` compara `None == None`: la comprobación "el proyecto de A quedó intacto" ya no prueba nada. **Se autoriza modificar esa prueba solo en esto:** obtener el `org_id` de A (de la respuesta de signup, `user.organizacion.id`), usarlo en esas dos llamadas y agregar `assert before[0] is not None` en el test parametrizado para que no vuelva a pasar en silencio. No cambies nada más de esa prueba.

2. **Resguardo contra `org_id` vacío o nulo** en `store._tenant_filter` (y en el `$match` de `list_projects`). Hoy un usuario con `org_id` `None` (por ejemplo, un documento mal escrito a mano o por otro script) coincidiría con los proyectos huérfanos, que tienen `org_id: null`. Si `org_id` es falsy, la función debe no encontrar nada: devolver un filtro imposible o lanzar `ValueError`, como prefieras, pero sin abrir acceso. Agrega una prueba: un usuario con `org_id: None` insertado a mano no ve ni abre el proyecto huérfano (404 y lista vacía).

3. **`init_db()` no debe importar desde `scripts/`.** `from scripts.migrate_orgs import migrate` depende de que `backend/` esté en `sys.path` y de que `scripts` funcione como paquete implícito; en un despliegue con otro directorio de trabajo, el servidor no arrancaría. Mueve la lógica a `app/migrations.py` (función `migrate_orgs(db) -> dict`). `scripts/migrate_orgs.py` queda como envoltorio de línea de comandos que la importa desde `app` (RNF-21 pide el script en `scripts/`). Ajusta tus pruebas nuevas al nuevo lugar.

Aceptado sin cambios: el orden usuario → organización en signup (la ventana de falla es mínima; queda como deuda) y que el panel admin siga mostrando `user_id`.

## Revisión 2
2026-10-30 — **Aprobada** (supervisor).
- `pytest tests -q`: 59 pasan.
- Punto 1: `test_aislamiento_pytest.py` usa el `org_id` de A (cambio de 1 línea más `assert before[0] is not None`); el snapshot vuelve a comparar el documento real. Las claves `uid_a`/`uid_b` conservan su nombre aunque guardan `org_id`; aceptado.
- Punto 2: `_tenant_filter` y `list_projects` usan `{"$in": []}` con `org_id` falsy; prueba nueva con usuario `org_id: None` frente a proyecto huérfano (lista vacía, 404, `get_project` con `None`/`""` y `delete_project` sin efecto). El programador verificó que falla sin el resguardo.
- Punto 3: lógica en `app/migrations.py` (`migrate_orgs`), importada al inicio de `database.py`; `scripts/migrate_orgs.py` es solo envoltorio CLI. Sin ciclos.
- Deuda aceptada: ventana mínima en signup (usuario creado antes que la organización) y panel admin que sigue mostrando `user_id`.
