# T-007: Gestión de miembros y cambio de contraseña
Lado: backend
Requerimientos: RF-03, RF-04 (versión sin correo), RNF-02, RNF-03
Rama: tarea/T-007-gestion-de-miembros
Depende de: T-006 (fusionada; usa `require_role`)

## Objetivo
El admin de una organización puede listar, crear (con contraseña temporal generada por el servidor), cambiar de rol, desactivar y reactivar miembros. Todo usuario puede cambiar su contraseña; quien tiene una temporal debe cambiarla antes de usar la plataforma. Los desactivados no pueden entrar.

## Decisiones del usuario (2026-10-30)
1. La contraseña temporal es obligatoria de cambiar en el primer ingreso. 2. Quitar = desactivar (se conserva autoría y auditoría). 3. La organización nunca queda sin admin activo. 4. El admin cambia roles. 5. La contraseña temporal la genera el servidor y se muestra una sola vez.

## Alcance
- SÍ: endpoints exactamente como en `docs/API_CONTRATOS.md`, sección **RF-03 · Gestión de miembros (T-007)**:
  - `GET /api/org/members`, `POST /api/org/members`, `PATCH /api/org/members/{user_id}` con `require_role("admin")`, en un router nuevo `app/routers/org.py`.
  - `POST /auth/change-password` en `auth.py`.
- SÍ: esquema de `users`: + `activo: bool` (por defecto `true`) y `debe_cambiar_password: bool` (por defecto `false`). `user_from_doc` usa esos valores por defecto si faltan (los usuarios existentes quedan activos y sin cambio pendiente), así que **no** hace falta migración. Si prefieres escribirlos en la base, hazlo dentro de `app/migrations.py`, idempotente.
- SÍ: objeto `user` con `debe_cambiar_password` (signup, login, me, change-password).
- SÍ: contraseña temporal con `secrets` (12 caracteres, alfabeto sin caracteres ambiguos como `0/O/1/l/I`, agrupada `xxxx-xxxx-xxxx`). Se guarda **solo el hash**; se devuelve una única vez en la respuesta 201. Nunca aparece en logs ni en auditoría.
- SÍ: bloqueos en `get_current_user` (o una variante):
  - Usuario `activo: false` → 401 `"Tu cuenta fue desactivada. Contacta al administrador de tu organización."` (en `login` solo si la contraseña es correcta; con contraseña incorrecta sigue "Email o contraseña incorrectos.").
  - `debe_cambiar_password: true` → 403 `"Debes cambiar tu contraseña temporal antes de continuar."` en toda ruta salvo `GET /auth/me` y `POST /auth/change-password`. Implementa esto con dos dependencias explícitas (por ejemplo `get_current_user` bloquea y `get_current_user_pendiente` no), no con listas de rutas en texto.
- SÍ: reglas de `PATCH`: no dejar la organización sin admin **activo** (409), no desactivarse a sí mismo (400), cuerpo vacío o rol inválido (422), miembro de otra organización (404 `"Miembro no encontrado"`).
- SÍ: auditoría de organización: crear miembro, cambio de rol, desactivar/reactivar y cambio de contraseña se insertan en `audit_events` con `org_id`, `project_id: None`, `actor: "analista"` (como el resto de acciones humanas), `user_id` de quien actúa y `detail` (email y rol afectado; **sin contraseñas**). Solo inserción; ningún endpoint los edita ni borra.
- SÍ: `tests/test_permisos_pytest.py`: **solo agregar** las 3 rutas nuevas de `/api/org/members` a la tabla con rol mínimo `admin` (y lo mínimo para que esa tabla admita el nivel admin), para que su test de cobertura siga cubriendo todo. `/auth/*` no está bajo `/api/`.
- SÍ: pruebas nuevas `tests/test_miembros_pytest.py` (mongomock):
  - El admin crea un lector: 201, `password_temporal` con el formato pedido, la base guarda solo el hash, el lector inicia sesión con ella y queda en `debe_cambiar_password: true`.
  - Con la temporal pendiente, `GET /api/projects` da 403 con el mensaje exacto; `GET /auth/me` y `POST /auth/change-password` funcionan; después del cambio, `GET /api/projects` da 200 y ve los proyectos de su organización.
  - change-password: actual incorrecta (400), nueva corta (422), nueva igual a la actual (400).
  - Analista y lector reciben 403 en los 3 endpoints de miembros; un admin de otra organización recibe 404 al hacer PATCH sobre un miembro ajeno y no lo ve en su lista.
  - Cambio de rol funciona y se refleja en los permisos de T-006 (un lector ascendido a analista puede crear proyectos).
  - Desactivar: el miembro no puede iniciar sesión (mensaje exacto) y su token vigente responde 401; reactivar le devuelve el acceso. Sus proyectos siguen en la organización y conservan su `user_id`.
  - Último admin: quitarle el rol o desactivarlo da 409; con dos admins activos, sí se puede. Desactivarse a sí mismo da 400.
  - Email duplicado da 409 y no crea nada.
  - Los eventos de auditoría de organización existen, tienen `project_id: None` y **no** contienen la contraseña temporal (busca el texto en todo el documento).
- NO: envío de correos, recuperación de contraseña, invitación por enlace (RF-04/RF-05 completos), varias organizaciones por usuario, cambios en `/api/admin/*`, renombrar la organización, frontend.

## Contrato de API
`docs/API_CONTRATOS.md`, sección **RF-03 · Gestión de miembros (T-007)**.

## Archivos probables
- Crear: `app/routers/org.py`, `tests/test_miembros_pytest.py`.
- Tocar: `app/auth.py`, `app/models.py`, `app/deps.py` (si las dependencias viven ahí), `app/store.py` (función de auditoría de organización), `app/main.py` (`include_router`), `tests/test_permisos_pytest.py` (solo agregar las rutas nuevas), `07_MVP/COMO_FUNCIONA.md`.
- No tocar: `07_MVP/frontend/**`, `docs/**`, el resto de las pruebas existentes.

## Criterios de aceptación
- [ ] `pytest tests -q` en verde; las 99 existentes pasan (la única modificación permitida es agregar entradas en `test_permisos_pytest.py`).
- [ ] Endpoints, campos y mensajes exactamente como el contrato.
- [ ] La contraseña temporal solo existe en claro en la respuesta 201 (verificado en base y auditoría).
- [ ] Las pruebas de cobertura de T-002 y T-006 siguen afirmando que encontraron rutas y cubren las nuevas.
- [ ] `COMO_FUNCIONA.md` actualizado (miembros, estados de cuenta, auditoría de organización).
- [ ] Commits con el formato `T-007 RF-03: ...`.

## Revisión
2026-10-30 — **Aprobada** (supervisor).
- `pytest tests -q`: 113 pasan (99 + 14 nuevas). En `test_permisos_pytest.py` solo se agregaron las 3 rutas con rol `admin`.
- Bloqueos: `get_current_user_pendiente` (sesión + cuenta activa, consultando la base en cada petición) y `get_current_user` (además, temporal pendiente → 403). `require_role` y todas las rutas `/api/` usan la segunda; solo `/auth/me` y `/auth/change-password` usan la primera. `test_pendiente_bloquea_toda_ruta_protegida_de_la_api` recorre OpenAPI (>30 rutas, con umbral) y exige 403 en todas.
- Contraseña temporal con `secrets`, 12 caracteres sin ambiguos, solo hash en la base; prueba que la busca en `users` y `audit_events`.
- Login de desactivado solo revela el estado con contraseña correcta. Auditoría de organización solo por inserción, sin contraseñas.
- Precedencia 409 antes que 400 aceptada y documentada en el contrato; también que cambiar la contraseña no revoca sesiones.
- Deuda aceptada: comprobación del último admin no atómica (`shortcut:` en `org.py`); funciones de miembros en `store` sin resguardo explícito ante `org_id` vacío (hoy solo las llama un admin con `org_id` válido).
