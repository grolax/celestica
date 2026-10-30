# T-005: Mostrar la organización y el rol en la interfaz
Lado: frontend
Requerimientos: RF-02 (UI), RNF-13
Rama: tarea/T-005-organizacion-en-ui
Depende de: T-004 (fusionada; el backend ya entrega `rol` y `organizacion`)

## Objetivo
El usuario ve a qué organización pertenece y con qué rol, usando los datos que el backend ya devuelve en signup, login y `/auth/me`. Tarea corta, sin lógica nueva.

## Alcance
- SÍ: `src/features/auth/api.ts`: el tipo `User` gana `rol: "admin" | "analista" | "lector"` y `organizacion: { id: string; nombre: string }`, exactamente como el objeto `user` del contrato.
- SÍ: `Header.tsx`: bajo el nombre del usuario se muestra `organizacion.nombre` (en lugar de `empresa`; si `organizacion.nombre` viniera vacío, usar `empresa`).
- SÍ: `Settings.tsx`, tarjeta "Mi cuenta": nombre y email como hoy, más dos líneas: "Organización: <nombre>" y "Rol: <rol en español>". Etiquetas del rol: `admin` → "Administrador", `analista` → "Analista", `lector` → "Lector" (un objeto de traducción en `auth/api.ts` o junto al tipo, reutilizable por RF-03).
- SÍ: en el registro (`SignupPage`), la etiqueta del campo "Institución / Empresa" pasa a **"Organización (institución o empresa)"**, porque ahora ese texto es el nombre de la organización. El placeholder no cambia.
- NO: pantallas de gestión de miembros, ocultar o mostrar acciones por rol (eso es RF-03), cambios en el backend.

## Contrato de API
`docs/API_CONTRATOS.md`, sección **RF-02 · Organizaciones (T-004)**, objeto `user`. Solo se consume; no hay endpoints nuevos.

## Archivos probables
- Tocar: `src/features/auth/api.ts`, `src/shared/layout/Header.tsx`, `src/features/settings/Settings.tsx`, `src/features/auth/LoginPage.tsx` (solo la etiqueta del campo).
- No tocar: `07_MVP/backend/**`, `docs/**`, `shared/api/client.ts`, la lógica de `useAuth`.

## Criterios de aceptación
- [ ] `npm run build` sin errores (tipado estricto con los campos nuevos).
- [ ] Con un usuario recién registrado, el encabezado muestra el nombre de su organización y Configuración muestra organización y "Rol: Administrador". Indica cómo lo verificaste (el backend local puede levantarse sin clave de Anthropic; no uses IA real).
- [ ] La etiqueta del registro dice "Organización (institución o empresa)".
- [ ] Diff pequeño (menos de unas 60 líneas).
- [ ] Commits con el formato `T-005 RF-02: ...`.
