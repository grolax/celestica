# T-016: Orden visual del área de trabajo
Lado: frontend
Requerimientos: RNF-13, RNF-14, RNF-16
Rama: tarea/T-016-area-de-trabajo
Depende de: T-015

## Objetivo
Con la nueva paleta y el nombre Celestica ya aplicados (T-014), y con las rutas nuevas (T-015), el área de trabajo debe sentirse **sobria, entendible y con separaciones claras**: cada pantalla con un título, una breve explicación de para qué sirve y bloques bien delimitados.

## Alcance
- SÍ: encabezado de página consistente en cada pantalla del área de trabajo: título y una línea de ayuda en lenguaje simple. Las pantallas son: lista de proyectos, nuevo proyecto, dashboard, léxico, libro de códigos, codificación, trazabilidad, informe, exportar, auditoría, configuración y documentación. Si hace falta, se crea un componente compartido `PageHeader` en `shared/components`.
- SÍ: la navegación del proyecto (`ProjectView`) muestra con claridad en qué pestaña se está y el orden del flujo (léxico → códigos → codificación → trazabilidad → informe → exportar).
- SÍ: el sidebar se agrupa en secciones con título ("Trabajo", "Ayuda y configuración") y el elemento activo se distingue sin depender solo del color (RNF-14).
- SÍ: la lista de proyectos vacía tiene un estado vacío que explica qué hacer y ofrece un botón "Crear proyecto".
- NO: cambiar flujos, endpoints, lógica, textos metodológicos, ni agregar funciones; rehacer el asistente de creación (eso es RF-40, T-008).

## Contrato de API
No aplica.

## Archivos probables
- Tocar: `src/features/projects/*.tsx`, `src/features/analysis/**/` (solo el encabezado y el envoltorio de cada pantalla), `src/features/settings/Settings.tsx`, `src/features/docs/Documentation.tsx`, `src/shared/layout/*`, `src/shared/components/*` y `globals.css`.
- No tocar: `07_MVP/backend/**`, `docs/**`, `shared/api/client.ts` y los archivos `api.ts` de cada feature.

## Criterios de aceptación
- [ ] `npm run build` sin errores.
- [ ] Cada pantalla de la lista tiene título y una línea de ayuda.
- [ ] El sidebar y las pestañas del proyecto marcan el elemento activo con algo más que color (peso de texto, borde o indicador) y se pueden recorrer con teclado.
- [ ] El estado vacío de la lista de proyectos funciona.
- [ ] No hay cambios de comportamiento: crear proyecto, ejecutar léxico, validar categorías y exportar siguen funcionando. Indica en el resumen cómo lo probaste.
- [ ] Diff de menos de unas 400 líneas. Si se pasa, divide en dos commits lógicos y avísalo.
- [ ] Commits con el formato `T-016 RNF-13: ...`.

## Notas
- Las líneas de ayuda van en español neutro-chileno y sin jerga. Por ejemplo, en Trazabilidad: "Sigue cada respuesta hasta su categoría, el motivo y quién la asignó."
