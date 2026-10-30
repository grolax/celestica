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
