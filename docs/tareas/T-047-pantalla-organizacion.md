# T-047: Sección "Organización" en Configuración y logo en la barra superior
Lado: frontend
Requerimientos: RF-10, RNF-13, RNF-14
Rama: tarea/T-047-pantalla-organizacion (ya creada desde `main`, con esta orden; trabaja en ella)
Depende de: T-046 (fusionada, PR #53)

## Objetivo
El administrador edita el nombre, el rubro y el color de su organización, y sube, reemplaza o quita el logo, desde Configuración. Todos los miembros ven esos datos, y el logo aparece en la barra superior junto al nombre de la organización, sin recargar la página.

## Alcance
- SÍ: tipos y llamadas en `features/org/api.ts` y `features/auth/api.ts`; la tarjeta "Organización" en `Settings.tsx`; el logo y el acento de color en `Header.tsx`; una forma de actualizar `user.organizacion` en `useAuth.tsx`; estilos mínimos en `globals.css`.
- NO: backend; cambiar la paleta, los botones ni los enlaces con el color de la organización; la marca en PDF y Word (RF-11); el rubro en el registro; recortar o redimensionar imágenes; tocar `Members.tsx`, `NewProject.tsx` ni `shared/components`.

## Contrato de API
`docs/API_CONTRATOS.md`, sección "RF-10 · Perfil de organización (T-046)". Las rutas ya existen en `main`. La lista de rubros se copia con el texto exacto a una constante `RUBROS` en `features/org/api.ts`.

## Archivos probables
- Se tocan: `07_MVP/frontend/src/features/org/api.ts`, `features/auth/api.ts` (tipo `User.organizacion`), `features/auth/useAuth.tsx`, `features/settings/Settings.tsx`, `shared/layout/Header.tsx`, `styles/globals.css`.
- No se tocan: `07_MVP/backend/**`, `shared/components/**`, `shared/api/client.ts` (ya admite `FormData` como `body`: mira `projectsApi.createProject`).

## Comportamiento

**Tipos.** `User.organizacion` pasa a `{ id, nombre, rubro: string | null, color: string | null, tiene_logo: boolean }`. En `orgApi`: `getProfile` no existe, los datos vienen en `user.organizacion`; agrega `updateProfile(body)`, `uploadLogo(file)` (con `FormData`, campo `file`), `getLogo()` y `deleteLogo()`.

**Tarjeta "Organización"** en Configuración, debajo de "Mi cuenta" y visible para todos los roles. Cambia el texto de ayuda de la página a: "Los datos de tu organización, tu cuenta y los ajustes del equipo."
- **Administrador:** un formulario con:
  - "Nombre de la organización" (`Input`, obligatorio, hasta 100 caracteres).
  - "Rubro" (`<select>` con `id` y `<label>`, como en Miembros): primera opción "Sin rubro" (valor vacío → se envía `null`) y luego `RUBROS`. Nota bajo el campo: "El rubro ordena las plantillas que te sugerimos."
  - "Color de la organización": un `<input type="color">` y un campo de texto sincronizados, con un botón "Sin color" que lo deja vacío (se envía `null`). Nota: "Se usa como acento junto al logo y, más adelante, en los informes. No cambia los colores de la plataforma."
  - Botón "Guardar" ocupado mientras guarda y deshabilitado si no hay cambios. Al guardar bien: aviso "Los datos de la organización se guardaron." Al fallar: el mensaje del servidor tal cual, en `alert alert-error`.
  - **Logo:** si hay logo, se muestra (desde `getLogo`) con `alt` "Logo de <nombre>", junto a "Reemplazar logo" y "Quitar logo". Si no hay, "Subir logo". El `<input type="file">` lleva `accept="image/png,image/jpeg"` y una nota: "PNG o JPG de hasta 500 KB." Antes de enviar, si el archivo pesa más de 512.000 bytes muestra "El logo pesa más de 500 KB. Usa una imagen más liviana." sin llamar al servidor. Cualquier otro error, el mensaje del servidor. Se sube al elegir el archivo, sin botón aparte. "Quitar logo" pide confirmación con `confirm`.
- **Analista y lector:** los mismos datos en solo lectura (nombre, rubro o "Sin rubro", color como muestra con su código o "Sin color", y el logo si existe) más la línea "Solo un administrador puede cambiar estos datos."
- La línea "Organización: …" de "Mi cuenta" se quita, porque ahora está en su tarjeta.

**Sesión al día.** `useAuth` expone una función para reemplazar `user.organizacion` con el objeto que devuelve el servidor (`PUT /api/org/profile`, `PUT`/`DELETE /api/org/logo` devuelven ese objeto). No hace falta volver a pedir `/auth/me`.

**Barra superior.** En `header-user`, antes del avatar: si `tiene_logo`, un `<img>` con el logo (alto máximo 28 px, ancho máximo 90 px, `alt` igual al nombre de la organización). Si hay `color`, un punto redondo de 10 px con ese color (`aria-hidden`), junto al nombre de la organización. El logo se pide una sola vez por sesión y se vuelve a pedir cuando cambia: para eso guarda el data URL en el estado de `AuthProvider` y recárgalo cuando Configuración sube, reemplaza o quita el logo. Bajo 640 px de ancho, el logo no se muestra (`display: none`), para no empeorar el desborde ya anotado de la barra.

**Accesibilidad:** todos los campos con `<label>`; errores en `alert`; la muestra de color no es el único indicador (lleva el código al lado); todo operable con teclado; el foco visible viene de `globals.css`.

## Criterios de aceptación
- [ ] Un administrador guarda nombre, rubro y color, y la tarjeta y la barra superior se actualizan sin recargar.
- [ ] Un analista o lector ve los datos en solo lectura y no ve el formulario ni los botones del logo.
- [ ] Nombre vacío, rubro fuera de la lista y color mal escrito muestran el mensaje del servidor; el nombre vacío también se puede frenar en la pantalla con el mismo texto del contrato.
- [ ] Subir un PNG o JPG muestra el logo en la tarjeta y en la barra; reemplazarlo cambia la imagen en ambos; quitarlo las borra en ambos.
- [ ] Un archivo de más de 500 KB se frena en la pantalla con el mensaje del contrato; un SVG renombrado muestra el mensaje del servidor.
- [ ] "Sin color" deja la organización sin color y el punto desaparece de la barra.
- [ ] Las demás pantallas no cambian de colores por el color de la organización.
- [ ] Al recargar, el logo y el punto siguen en la barra (con `/auth/me` y `getLogo`).
- [ ] Usa `shared/api/client.ts`, los componentes de `shared/components` y las variables de `globals.css`.
- [ ] `npm run build` sin errores.
- [ ] Sin regresiones de aislamiento multi-tenant: no cambia el backend.

## Notas
- Decisiones del usuario (2026-11-10): rubro de lista cerrada; el color es solo un acento, nunca cambia la paleta; logo PNG o JPG hasta 500 KB.
- No levantes servidores ni corras Playwright: el supervisor recorre la pantalla con un backend y una base desechables. A ti te basta con `npm run build`.
- El desborde de la barra superior a 375 px es una deuda anterior (T-021): no la arregles aquí, solo no la empeores.
