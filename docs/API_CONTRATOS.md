# Contratos de API

Archivo mantenido por el agente `supervisor`. Es la única fuente de verdad entre backend y frontend.
Los endpoints ya existentes en la v1.1 están documentados en `07_MVP/COMO_FUNCIONA.md` y en `/docs` del backend (FastAPI).
Aquí solo se registran endpoints **nuevos o modificados**.

## Formato de cada entrada

### `MÉTODO /api/ruta`
- **Tarea:** T-xxx · **Requerimiento:** RF-xx
- **Roles permitidos:** admin | analista | lector
- **Entrada:** (JSON de ejemplo o parámetros)
- **Respuesta 200:** (JSON de ejemplo)
- **Errores:** código — mensaje para la UI — cuándo ocurre

---

## RF-02 · Organizaciones (T-004)

Sin endpoints nuevos. Cambia la **forma del usuario** que devuelven los tres endpoints de autenticación, y el alcance de todos los endpoints de proyectos pasa de "proyectos del usuario" a "proyectos de su organización". Rutas, entradas y el resto de las respuestas no cambian.

### Objeto `user` (compartido por `POST /auth/signup`, `POST /auth/login` y `GET /auth/me`)
Campos nuevos: `rol` y `organizacion`. Los existentes se mantienen (incluido `empresa`, por compatibilidad).
```json
{
  "id": "usr_1a2b3c4d5e",
  "email": "ana@udp.cl",
  "nombre": "Ana",
  "empresa": "UDP",
  "rol": "admin",
  "organizacion": { "id": "org_9f8e7d6c5b", "nombre": "UDP" }
}
```
- `rol`: `"admin" | "analista" | "lector"`. En T-004 todo usuario es `"admin"` de su organización; los permisos por rol llegan con RF-03.

### `POST /auth/signup`
- **Tarea:** T-004 · **Requerimiento:** RF-02
- **Roles permitidos:** público
- **Entrada:** sin cambios: `{"email": "ana@udp.cl", "password": "clave12345", "nombre": "Ana", "empresa": "UDP"}`
- **Efecto nuevo:** crea una organización y deja al usuario como su `admin`. Nombre de la organización: `empresa` (sin espacios sobrantes); si está vacío, `"Organización de <nombre>"`; si también falta el nombre, `"Organización de <email>"`.
- **Respuesta 200:** `{"token": "<jwt>", "user": <objeto user>}`
- **Errores:** sin cambios. 409 — "Ya existe una cuenta con ese email." · 422 — validación (contraseña < 8 caracteres, email inválido).

### `POST /auth/login` y `GET /auth/me`
- **Tarea:** T-004 · **Requerimiento:** RF-02
- **Roles permitidos:** público (login) · cualquier usuario autenticado (me)
- **Entrada:** sin cambios.
- **Respuesta 200:** login `{"token": "<jwt>", "user": <objeto user>}`; me `<objeto user>`.
- **Errores:** sin cambios (401 en ambos casos).

### Endpoints de proyectos (`/api/projects`, `/api/projects/{project_id}/...`, `from-qualtrics`, `from-google-forms`, `import-legacy`)
- **Tarea:** T-004 · **Requerimiento:** RF-02
- **Cambio de alcance:** un usuario ve y opera los proyectos **de su organización**. Un proyecto de otra organización responde **404 — "Proyecto no encontrado"**, igual que hoy con proyectos de otro usuario.
- **Entradas y respuestas:** sin cambios.

---

## RF-03 · Permisos por rol (T-006)

Sin endpoints nuevos. Se agrega un error **403** en las operaciones que el rol no permite y un campo `author_id` en los comentarios. Decisiones del usuario del 2026-10-30.

### Matriz de permisos
| Operación | Lector | Analista | Admin |
| --- | --- | --- | --- |
| Ver: `GET /api/projects`, `GET /api/projects/{id}`, `responses`, `GET lexical`, `codify/progress`, `summary`, `audit`, `GET report`, `report/progress`, `usage`, `GET /api/framework-templates` | ✅ | ✅ | ✅ |
| Descargar: `export/traceability`, `export/pdf`, `docx`, `csv`, `xlsx` | ✅ | ✅ | ✅ |
| Comentar: `POST .../categories/{cid}/comments` | ✅ | ✅ | ✅ |
| Borrar comentario: `DELETE .../comments/{comid}` | solo los suyos | todos | todos |
| Crear proyecto: `POST /api/projects`, `from-qualtrics`, `from-google-forms`, `import-legacy` | ❌ | ✅ | ✅ |
| Analizar: `apply-template`, `POST lexical`, `categories/propose`, `POST categories`, `PATCH categories/{cid}`, `POST codify`, `PUT responses/{rid}/codings`, `POST report` | ❌ | ✅ | ✅ |
| Borrar proyecto: `DELETE /api/projects/{id}` | ❌ | ✅ | ✅ |
| Credenciales y encuestas de Qualtrics: `/api/integrations/qualtrics/*` | ❌ | ✅ | ✅ |
| Gestión de miembros (`/api/org/members`, T-007) | ❌ | ❌ | ✅ |

Los endpoints `/api/admin/*` siguen protegidos por la contraseña interna (`X-Admin-Password`) hasta RF-07; no dependen del rol.

### Error nuevo (todas las operaciones marcadas ❌)
- **403** — `"Tu rol (Lector) no permite esta acción."` (el texto usa la etiqueta en español del rol del usuario).
- Orden de verificación: sesión (401) → rol (403) → proyecto de la organización (404). El 403 no depende de que el proyecto exista, así que no revela proyectos de otras organizaciones.
- Borrar un comentario ajeno siendo lector: **403** — `"Solo puedes borrar tus propios comentarios."`

### Comentarios (`POST .../comments`, y dentro de `categories[].comments[]` en `GET /api/projects/{id}`)
Campo nuevo `author_id` (id del usuario). Los comentarios antiguos no lo tienen: un lector no puede borrarlos.
```json
{ "id": "com_ab12cd34", "text": "Revisar esta definición", "author": "Ana", "author_id": "usr_1a2b3c4d5e", "timestamp": "2026-10-30T15:00:00+00:00" }
```

---

## RF-03 · Gestión de miembros (T-007)

Solo el **admin** de la organización. Todas responden **403** `"Tu rol (<rol>) no permite esta acción."` a analistas y lectores. Un `user_id` que no pertenece a la organización del admin responde **404** `"Miembro no encontrado"`.

### Objeto `member`
```json
{ "id": "usr_5f6g7h8i9j", "email": "luis@udp.cl", "nombre": "Luis", "rol": "lector", "activo": true, "debe_cambiar_password": true, "created_at": "2026-10-30T15:00:00+00:00" }
```

### `GET /api/org/members`
- **Roles permitidos:** admin
- **Respuesta 200:** `[<member>, ...]` (incluye desactivados, ordenados por `created_at`).

### `POST /api/org/members`
- **Roles permitidos:** admin
- **Entrada:** `{"email": "luis@udp.cl", "nombre": "Luis", "rol": "lector"}`
- **Efecto:** crea el usuario en la organización del admin con una **contraseña temporal generada por el servidor** (12 caracteres aleatorios) y `debe_cambiar_password: true`.
- **Respuesta 201:** `{"member": <member>, "password_temporal": "k7Q2-mX9p-Lr4z"}`. La contraseña temporal **solo se entrega en esta respuesta**; no se guarda en claro ni se puede volver a consultar.
- **Errores:** 409 — "Ya existe una cuenta con ese email." · 422 — email inválido o rol fuera de `admin | analista | lector`.

### `PATCH /api/org/members/{user_id}`
- **Roles permitidos:** admin
- **Entrada:** uno o ambos campos: `{"rol": "analista"}`, `{"activo": false}` (desactivar = "quitar"), `{"activo": true}` (reactivar).
- **Respuesta 200:** `<member>` actualizado.
- **Errores:** 404 — "Miembro no encontrado" · 409 — "La organización debe tener al menos un administrador activo." (al quitar el rol admin o desactivar al último admin activo) · 400 — "No puedes desactivar tu propia cuenta." · 422 — rol inválido o cuerpo vacío.
- **Precedencia:** el 409 se evalúa antes que el 400. Si el admin es el único admin activo y se desactiva a sí mismo, recibe 409; con otro admin activo, recibe 400. Un admin puede cambiarse su propio rol si queda otro admin activo.
- **Sesiones:** cambiar la contraseña no cierra las sesiones abiertas (el token anterior vale hasta que expira). La revocación llega con RNF-04.

### `POST /auth/change-password`
- **Roles permitidos:** cualquier usuario autenticado (también con `debe_cambiar_password: true`)
- **Entrada:** `{"password_actual": "k7Q2-mX9p-Lr4z", "password_nueva": "miClaveNueva1"}`
- **Respuesta 200:** `{"user": <objeto user>}` con `debe_cambiar_password: false`.
- **Errores:** 400 — "La contraseña actual no es correcta." · 422 — "La contraseña debe tener al menos 8 caracteres" · 400 — "La contraseña nueva debe ser distinta de la actual."

### Cambios en endpoints existentes
- **Objeto `user`** (signup, login, me, change-password): campo nuevo `debe_cambiar_password: boolean`.
- **Contraseña temporal pendiente:** mientras `debe_cambiar_password` sea `true`, toda ruta salvo `GET /auth/me` y `POST /auth/change-password` responde **403** — `"Debes cambiar tu contraseña temporal antes de continuar."`
- **Miembro desactivado:** `POST /auth/login` y cualquier ruta con su token responden **401** — `"Tu cuenta fue desactivada. Contacta al administrador de tu organización."`
- **Auditoría:** crear miembro, cambiar rol, desactivar/reactivar y cambiar contraseña quedan en `audit_events` con `org_id`, `project_id: null`, actor y detalle (sin contraseñas).

