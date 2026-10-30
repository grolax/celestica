# T-008b: Pantalla de miembros y acciones según el rol
Lado: frontend
Requerimientos: RF-03, RNF-02 (reflejo en UI), RNF-13, RNF-14
Rama: tarea/T-008b-miembros-y-acciones-por-rol
Depende de: T-008a

## Objetivo
El admin gestiona a su equipo desde una pantalla "Miembros". Cada persona ve solo las acciones que su rol permite, según la matriz del contrato. La UI solo refleja permisos: el backend sigue siendo la barrera.

## Alcance
- SÍ: helper único en `auth/api.ts`, por ejemplo `puede(user, "analista" | "admin")`, con el orden `lector < analista < admin` (un rol desconocido cuenta como lector, como en el backend). Nada de comparar strings de rol sueltos en los componentes.
- SÍ: **pantalla `/miembros`** (`src/features/org/Members.tsx` y `api.ts` con `GET/POST /api/org/members` y `PATCH /api/org/members/{user_id}`):
  - Solo admin: el sidebar gana un grupo nuevo **"Organización"** (entre "Trabajo" y "Ayuda y configuración"), visible solo para admin, con el ítem **"Miembros"** (icono de personas, `users` de `Icon`). La ruta redirige a `/proyectos` a otros roles. El grupo quedará también para el perfil de organización (RF-10).
  - `PageHeader`: título "Miembros", ayuda **"Las personas de tu organización y lo que puede hacer cada una."**
  - Tabla: nombre, email, rol (selector), estado ("Activo" / "Desactivado") y acción "Desactivar"/"Reactivar". El usuario actual se marca "(tú)".
  - Leyenda breve de roles, con estos textos: **Lector:** "Ve resultados, descarga informes y comenta." · **Analista:** "Hace todo el análisis, incluido crear y borrar proyectos." · **Administrador:** "Lo mismo que el analista, más la gestión de miembros."
  - Formulario "Agregar miembro": email, nombre, rol. Al crearlo, una alerta muestra la contraseña temporal con botón **"Copiar"** y el texto: **"Entrega esta contraseña temporal a <nombre>. Por seguridad no se volverá a mostrar; al entrar, deberá cambiarla."** La contraseña no se guarda en ningún estado persistente (ni localStorage) y desaparece al salir de la pantalla.
  - Cambiar rol y desactivar piden confirmación (`confirm` basta). Los errores del backend (409 último admin, 400, 404) se muestran tal cual.
- SÍ: **acciones por rol** (ocultar, no solo deshabilitar):
  - Lector no ve: "Nuevo proyecto" (sidebar y Mis proyectos), "Eliminar" proyecto, ejecutar léxico, proponer/crear/validar/descartar/editar categorías, aplicar plantilla, codificar, recodificar respuestas, generar informe, importar proyectos antiguos (Configuración) ni Qualtrics. La ruta `/proyectos/nuevo` lo redirige a `/proyectos`.
  - Lector sí ve: todas las pestañas, descargas y exportaciones, y el formulario de comentarios.
  - Borrar comentario: el botón aparece si `puede(user, "analista")` o si `comentario.author_id === user.id`. El tipo del comentario gana `author_id?: string`.
  - En `ProjectView`, para el lector, una píldora junto al nombre del proyecto: **"Solo lectura"**.
- NO: cambios en el backend, renombrar la organización, invitar por correo.

## Decisiones del usuario (2026-10-30)
- Ocultar (no deshabilitar) las acciones que el rol no permite.
- Textos de esta orden aprobados tal cual.
- "Miembros" va en un grupo nuevo "Organización" del menú.

## Contrato de API
`docs/API_CONTRATOS.md`: **RF-03 · Permisos por rol (T-006)** (matriz y `author_id`) y **RF-03 · Gestión de miembros (T-007)** (objeto `member`, endpoints y errores).

## Archivos probables
- Crear: `src/features/org/Members.tsx`, `src/features/org/api.ts`.
- Tocar: `src/features/auth/api.ts`, `src/App.tsx`, `src/shared/layout/Sidebar.tsx`, `src/features/projects/{ProjectList,ProjectView}.tsx`, `src/features/analysis/**` (solo condicionar botones), `src/features/analysis/types.ts` (`author_id`), `src/features/settings/Settings.tsx`.
- No tocar: `07_MVP/backend/**`, `docs/**`, `shared/api/client.ts`, la lógica de cada pantalla más allá de mostrar u ocultar.

## Criterios de aceptación
- [ ] `npm run build` sin errores.
- [ ] Probado contra el backend local sin IA, con tres cuentas de la misma organización (admin, analista, lector creados desde la pantalla Miembros): cada una ve exactamente lo que dice la matriz. Lista en tu resumen qué se ocultó y dónde.
- [ ] Flujo completo: el admin crea un lector, copia la contraseña, el lector entra, la cambia (T-008a), ve "Solo lectura", comenta y borra solo su comentario; el admin lo asciende a analista y, tras recargar, el ex lector ve las acciones de análisis; el admin lo desactiva y no puede entrar.
- [ ] Intentar quitar el rol al único admin muestra el mensaje 409 del backend.
- [ ] Accesible: tabla con encabezados, selector de rol con etiqueta, botones con texto claro, recorrible con Tab.
- [ ] Diff de menos de unas 400 líneas; si se pasa, divide en commits lógicos y avísalo.
- [ ] Commits con el formato `T-008b RF-03: ...`.

## Revisión
2026-10-30 — **Aprobada** (supervisor).
- `npm run build` sin errores. Diff +275/-54 en 17 archivos, solo frontend, 2 commits; `client.ts` intacto.
- `puede(user, minimo)` único (rol desconocido o usuario nulo = lector); `RequireRole` protege `/proyectos/nuevo` (analista) y `/miembros` (admin). Sin comparaciones de rol sueltas.
- Grupo "Organización" con "Miembros" solo para admin. Pantalla con los textos de la orden; contraseña temporal solo en `useState`; confirmación al cambiar rol y desactivar; errores del backend tal cual.
- Lector: acciones ocultas según la matriz (lista en el informe del programador); "Solo lectura" en `ProjectView`; borrar comentario solo si `author_id === user.id`.
- Verificado por el programador con 3 cuentas `@prueba.cl` contra el backend local sin IA (66 comprobaciones del flujo completo).
- Fuera de la orden, aceptado y señalado al usuario: avisos para el lector ("Un analista de tu organización puede…") en 4 pantallas; "Nombre" obligatorio en el alta (el contrato lo admite vacío, pero la alerta lo usa).
- Deuda: `Input` sin `type` explícito pierde el estilo del campo; el rol en la UI se refresca solo al recargar (el backend valida siempre).
