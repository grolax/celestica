# T-038: Cambiar el tipo de una pregunta cerrada (pantalla)
Lado: frontend
Requerimientos: RF-25, RF-30, RNF-13, RNF-14
Rama: tarea/T-038-pantalla-cambiar-tipo
Depende de: T-037

## Objetivo
En "Preguntas cerradas", un analista o admin puede corregir el tipo de una pregunta desde su propia tarjeta, y ver al instante el resultado con el tipo nuevo.

## Alcance
- SÍ: en el componente `Pregunta` de `ClosedResults.tsx`, un botón de texto pequeño "Cambiar tipo" junto a la línea de datos (solo con `puede(user, "analista")`). Al pulsarlo:
  - se muestra un `select` con los tipos cerrados (etiquetas de `TIPOS` en `questionGroups.ts`) y los botones "Guardar" y "Cancelar";
  - al guardar, se llama al `PATCH` y luego se recargan los resultados con los mismos `por`, `ver`, `cortes` y `unir` aplicados, más `refresh()` del proyecto.
- SÍ: `projectsApi.updatePreguntaTipo(id, preguntaId, tipo)` en `features/projects/api.ts`.
- NO: backend; cambiar abiertas; editar títulos o unir columnas.

## Contrato de API
`docs/API_CONTRATOS.md` → sección T-037.

## Archivos probables
- Se tocan: `features/analysis/closed/ClosedResults.tsx`, `features/projects/api.ts`.
- NO se tocan: `07_MVP/backend/**`, `QuestionReview.tsx`.

## Criterios de aceptación
- [ ] El lector no ve "Cambiar tipo".
- [ ] El `select` ofrece solo los 7 tipos cerrados, con el actual preseleccionado. "Guardar" queda deshabilitado si no cambió.
- [ ] Al guardar bien, la tarjeta muestra el tipo nuevo y sus cifras, por ejemplo promedio y notas altas al pasar a "Escala", sin recargar la página. El "Ver por…", la pregunta, los tramos y las uniones se mantienen.
- [ ] Si el servidor responde 400, el mensaje se muestra junto al `select` (usar el estilo de error de `Input` o `alert alert-error` pequeño dentro de la tarjeta). No se cierra el editor.
- [ ] Si la pregunta cambiada es la del "Ver por…" y deja de servir para separar (pasa a escala, NPS o selección múltiple), la pantalla vuelve a "Todas las personas (sin separar)" sin errores.
- [ ] Accesible con teclado: `label` en el `select` y foco en el `select` al abrir el editor.
- [ ] `cd 07_MVP/frontend && npm run build` sin errores.
- [ ] Verificación con la encuesta real local (`proj_4df733d1c3`, cuenta `t012@prueba.cl` / `Prueba-T012-clave`):
  - cambiar una pregunta a otro tipo cerrado compatible y devolverla a su tipo original, para dejar los datos como estaban;
  - provocar el error de "no son números".

  Reporta lo que viste. No dejes servidores ni archivos temporales. Sin IA real.

## Notas
- Decisión del usuario: solo entre cerradas.
- El cambio queda en la auditoría (lo registra el servidor).
