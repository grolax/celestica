# T-008a: Cambio de contraseña y estados de cuenta en la interfaz
Lado: frontend
Requerimientos: RF-03, RNF-13, RNF-14
Rama: tarea/T-008a-cuenta-y-contrasena
Depende de: T-007 (fusionada)

## Objetivo
La interfaz respeta los dos estados de cuenta del backend: quien entra con una contraseña temporal es llevado a una pantalla obligatoria para cambiarla, y quien está desactivado ve un mensaje claro. Además, cualquier usuario puede cambiar su contraseña desde Configuración.

## Alcance
- SÍ: tipos en `auth/api.ts`: `User` gana `debe_cambiar_password: boolean`; `authApi.changePassword({password_actual, password_nueva})` → `{user}` (contrato **RF-03 · Gestión de miembros (T-007)**, `POST /auth/change-password`).
- SÍ: `useAuth` expone `changePassword(...)`, que actualiza el `user` en memoria con la respuesta.
- SÍ: ruta protegida nueva **`/cambiar-contrasena`**, pantalla centrada (como login) con: contraseña actual, nueva y confirmación (las dos últimas deben coincidir, mínimo 8, validado también en el cliente), botón "Cambiar contraseña" y los errores del backend tal cual.
  - Si `user.debe_cambiar_password` es `true`, `ProtectedLayout` redirige **cualquier** ruta protegida a `/cambiar-contrasena`, que en ese caso muestra el texto: **"Por seguridad, cambia la contraseña temporal que te entregó tu administrador antes de continuar."** y el botón "Salir". Tras el cambio exitoso, ir a `/proyectos`.
  - Si no es obligatorio, la pantalla se abre desde Configuración y tiene "Cancelar" (vuelve a `/configuracion`); tras el cambio, mensaje de éxito "Tu contraseña se cambió." y vuelta a Configuración.
- SÍ: en Configuración → "Mi cuenta", un botón "Cambiar contraseña" que lleva a `/cambiar-contrasena`.
- SÍ: **cuenta desactivada:** el login ya muestra el error del backend. Además, si una petición con sesión abierta responde 401 con el mensaje de cuenta desactivada, la persona vuelve a `/login` y ve ese mensaje (no un login vacío). Cambio mínimo permitido en `shared/api/client.ts`: el manejador de 401 recibe el `detail` del error; `useAuth` lo guarda y `LoginPage` lo muestra una vez como alerta.
- NO: pantalla de miembros ni ocultar botones por rol (eso es T-008b); recuperación de contraseña por correo; cambios en el backend.

## Contrato de API
`docs/API_CONTRATOS.md`, sección **RF-03 · Gestión de miembros (T-007)**: `POST /auth/change-password`, campo `debe_cambiar_password` del objeto `user`, 403 de temporal pendiente y 401 de cuenta desactivada.

## Archivos probables
- Crear: `src/features/auth/ChangePasswordPage.tsx`.
- Tocar: `src/features/auth/api.ts`, `useAuth.tsx`, `LoginPage.tsx`, `src/App.tsx`, `src/features/settings/Settings.tsx`, `src/shared/api/client.ts` (solo pasar el `detail` al manejador de 401).
- No tocar: `07_MVP/backend/**`, `docs/**`, `features/analysis/**`.

## Criterios de aceptación
- [ ] `npm run build` sin errores.
- [ ] Probado contra el backend local (sin IA): un admin crea un miembro con `POST /api/org/members` (por `curl` o script), el miembro entra con la temporal y es llevado a `/cambiar-contrasena` desde cualquier URL protegida; tras cambiarla llega a `/proyectos`.
- [ ] Errores del cambio visibles: actual incorrecta, nueva corta, nueva igual a la actual, confirmación distinta (esta última sin llamar al backend).
- [ ] Desactivar al miembro (PATCH) mientras tiene la sesión abierta: en su siguiente acción vuelve a `/login` con el mensaje "Tu cuenta fue desactivada. Contacta al administrador de tu organización."
- [ ] Formulario accesible: etiquetas, foco inicial, errores asociados a su campo, recorrible con Tab.
- [ ] Commits con el formato `T-008a RF-03: ...`.

## Revisión
2026-10-30 — **Aprobada** (supervisor).
- `npm run build` sin errores. Diff +116/-15 en 8 archivos, solo frontend.
- `ProtectedLayout` redirige toda ruta protegida a `/cambiar-contrasena` mientras `debe_cambiar_password`; tras el cambio, `useAuth.changePassword` actualiza `user` con la respuesta.
- `client.ts`: cambio mínimo; el manejador de 401 recibe el `detail` (misma condición, ahora después de leer el cuerpo). `LoginPage` muestra el aviso una vez.
- `Input.tsx` gana `aria-invalid`/`aria-describedby` (fuera de "Archivos probables", aceptado: lo exige el criterio de accesibilidad y solo agrega atributos).
- Verificado por el programador contra el backend local sin IA: redirección obligatoria, errores por campo, cambio desde Configuración y aviso de cuenta desactivada.
- Hallazgo previo (no causado por esta tarea): `/api/admin/*` responde **401** con contraseña de admin incorrecta y `adminApi` usa `req`, así que un error de contraseña del panel de prompts cierra la sesión del usuario. Anotado como deuda (backend: responder 403).
