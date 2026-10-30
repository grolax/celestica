# T-016a: Encabezado de página, menú lateral agrupado y estado vacío
Lado: frontend
Requerimientos: RNF-13, RNF-14, RNF-16
Rama: tarea/T-016a-encabezados-y-navegacion
Depende de: T-015 (fusionada)

## Objetivo
Primera mitad de T-016 (`docs/tareas/T-016-area-de-trabajo.md`, que queda como referencia general). Se crea un encabezado de página común (título + una línea de ayuda), se aplica a las pantallas de primer nivel, se agrupa el menú lateral, se marca la pestaña activa del proyecto sin depender solo del color y la lista de proyectos vacía explica qué hacer.

## Alcance
- SÍ: componente `shared/components/PageHeader.tsx` con props `title`, `help` y `level` opcional (`1` por defecto, `2` para pestañas de proyecto, que usará T-016b). Renderiza el encabezado y la línea de ayuda con clase `muted`. Estilos en `globals.css` con las variables existentes.
- SÍ: aplicar `PageHeader` (nivel 1) en: Mis proyectos (`ProjectList`), Nuevo proyecto (`NewProject`), Configuración (`Settings`) y Documentación (`Documentation`). Reemplaza el `h1` actual de cada una.
- SÍ: `Sidebar` agrupado en dos secciones con título: **"Trabajo"** (Nuevo proyecto, Mis proyectos) y **"Ayuda y configuración"** (Documentación, Configuración). El elemento activo se distingue además del color (peso de texto y una barra/borde lateral).
- SÍ: pestañas de `ProjectView`: la activa se marca con algo más que color (subrayado grueso o borde) y `aria-current="page"` (NavLink ya lo pone; verificar). No cambiar nombres ni orden de las pestañas.
- SÍ: estado vacío en `ProjectList` cuando no hay proyectos: un texto corto ("Todavía no tienes proyectos. Crea el primero subiendo tu encuesta.") y un botón "Crear proyecto" a `/proyectos/nuevo`.
- NO: tocar las pantallas de las pestañas del proyecto (eso es T-016b), cambiar flujos, endpoints, lógica o textos metodológicos.

## Textos (aprobados por el usuario, 2026-10-30)
Úsalos tal cual.
- **Mis proyectos:** "Aquí están tus encuestas en análisis. Abre una para continuar o crea un proyecto nuevo."
- **Nuevo proyecto:** "Sube tu archivo o conecta Qualtrics o Google Forms, y elige la pregunta abierta que quieres analizar."
- **Configuración:** "Ajusta los textos que guían a la IA y revisa el consumo."
- **Documentación:** "Guía de uso y explicación de cada concepto de la plataforma."

## Contrato de API
No aplica.

## Archivos probables
- Crear: `src/shared/components/PageHeader.tsx`.
- Tocar: `src/features/projects/ProjectList.tsx`, `NewProject.tsx`, `ProjectView.tsx` (solo estilos de pestañas), `src/features/settings/Settings.tsx`, `src/features/docs/Documentation.tsx`, `src/shared/layout/Sidebar.tsx`, `src/styles/globals.css`.
- No tocar: `07_MVP/backend/**`, `docs/**`, `shared/api/client.ts`, los `api.ts`, `src/features/analysis/**`.

## Criterios de aceptación
- [ ] `npm run build` sin errores.
- [ ] Las 4 pantallas muestran título y su línea de ayuda exacta.
- [ ] Sidebar con dos secciones con título; activo marcado con algo más que color; recorrible con Tab y foco visible.
- [ ] Pestaña activa del proyecto marcada con algo más que color y con `aria-current="page"`.
- [ ] Estado vacío visible cuando no hay proyectos, con botón que lleva a `/proyectos/nuevo`.
- [ ] Sin cambios de comportamiento: crear proyecto y abrir uno siguen funcionando. Indica cómo lo probaste.
- [ ] Diff de menos de unas 400 líneas.
- [ ] Commits con el formato `T-016a RNF-13: ...`.
