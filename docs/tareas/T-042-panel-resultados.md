# T-042: Pantalla "Resultados" para lectores
Lado: frontend
Requerimientos: RF-43, RNF-06, RNF-13, RNF-14, RNF-15
Rama: tarea/T-042-panel-resultados (ya creada desde `main`, con esta orden; trabaja en ella)
Depende de: T-041 (fusionada, PR #48)

## Objetivo
Una pestaña "Resultados" que un gerente, alcalde o director entienda sin saber de análisis: métricas clave, temas principales con citas y alertas de la encuesta, en una sola pantalla, imprimible y legible en tablet y móvil. El lector entra ahí desde la lista de proyectos.

## Alcance
- SÍ: componente nuevo `features/analysis/results/ResultsPanel.tsx` (divídelo si crece), con la ruta `resultados`.
- SÍ: `analysisApi.getTemasPrincipales(id)` y sus tipos.
- SÍ: reglas `@media print` en `globals.css`.
- NO: backend; temas por grupo; tramos o unión de grupos en esta pantalla; descargar Excel desde aquí; cambios en Dashboard, Preguntas cerradas o `Recommendations.tsx`; detectar u ocultar nombres en las citas; Playwright; arreglar deudas de otras pantallas.

## Contrato de API
Sin cambios. Consume:
- `docs/API_CONTRATOS.md` → "RF-43 · Temas principales para el panel de resultados (T-041)".
- `GET /closed-results`, con y sin `por` (T-020, T-022), con `analysisApi.getClosedResults`. No envíes `ver`: sin `ver` llegan todas las preguntas.
- `GET /recommendations` (T-032), con `projectsApi.getRecommendations`.

## Archivos probables
- Se tocan: `features/analysis/results/ResultsPanel.tsx` (nuevo), `features/analysis/api.ts`, `features/analysis/types.ts`, `App.tsx`, `features/projects/ProjectView.tsx`, `features/projects/ProjectList.tsx`, `styles/globals.css`.
- NO se tocan: `07_MVP/backend/**`, `shared/components/**`, `features/analysis/closed/**` (se importan `GroupTable` y `format.ts` sin modificarlos).

## Criterios de aceptación
**Entrada y pestaña**
- [ ] "Resultados" es la primera pestaña para todos los roles, también en proyectos sin abiertas (`SOLO_CERRADAS`).
- [ ] En `ProjectList.tsx`, el lector (`!puede(user, "analista")`) abre `/proyectos/<id>/resultados`, en la fila y en "Abrir". Analista y admin abren `/proyectos/<id>`, como hoy.
- [ ] **No redirijas la ruta índice:** el lector debe poder seguir abriendo la pestaña Dashboard.
- [ ] Un analista que entra a un proyecto con abiertas sigue llegando al Dashboard, y uno sin abiertas a Preguntas cerradas.
- [ ] En esta pestaña no se muestran el selector "Pregunta que estás analizando" ni la línea "Pregunta: … · Marco: …": la pantalla cubre todas las preguntas. El nombre del proyecto y "Solo lectura" se mantienen. Las demás pestañas se ven igual que hoy.

**Encabezado y alertas**
- [ ] `PageHeader` con título "Resultados", una línea de ayuda simple y un botón "Imprimir" (`window.print()`). Debajo, "N personas respondieron la encuesta" (`n_personas`).
- [ ] Solo se muestran las alertas generales de la encuesta (`pregunta_id` nulo): `alert-error` si `nivel` es `importante`, si no `alert-warning`. Las de cada pregunta quedan en el Dashboard.

**Métricas**
- [ ] Se muestran todas las preguntas `nps` y las 6 primeras de tipo `escala` o `si_no`, en el orden que entrega la API. Otros tipos no aparecen aquí.
- [ ] NPS: valor con signo, y "Promotores: recomiendan (9–10)", "Pasivos: neutrales (7–8)" y "Detractores: no recomiendan (0–6)", con % y personas. Una línea explica que va de −100 a +100.
- [ ] Escala: "Promedio X de Y" y "Notas altas (4 y 5)" con su %.
- [ ] Sí/no: una barra por opción, con % y personas escritos. La barra lleva `aria-hidden`: la información no depende del color.
- [ ] Cada pregunta dice cuántas personas respondieron. No aparecen "desviación", "N/A", "tasa de respuesta" ni "Cambiar tipo".
- [ ] Si quedan preguntas cerradas sin mostrar, un enlace "Ver las otras N preguntas" lleva a la pestaña Preguntas cerradas, conservando `?pregunta=` si está en la dirección.
- [ ] Sin preguntas para mostrar, la sección no aparece, ni siquiera su título.

**Ver por…**
- [ ] Selector con etiqueta "Ver por…": "Todas las personas (sin separar)" más `rec.segmentos` (máximo 3, con `titulo`). Por defecto, sin separar. Solo aparece si hay segmentos y métricas.
- [ ] Al elegir un grupo, cada métrica usa `GroupTable`, que ya trae la etiqueta "Pocos datos". Se explica "Los grupos marcados con «Pocos datos» tienen menos de N personas: tómalos con cautela." (si hay alguno, con `umbral_pocos_datos`) y se avisa `n_sin_grupo` (si es mayor que 0).
- [ ] Los temas no cambian al separar.
- [ ] Una respuesta lenta anterior no pisa a la última elegida (patrón `ultima` de `ClosedResults.tsx`). Si falla, se muestra el error y sigue visible lo anterior.

**Temas principales**
- [ ] Una tarjeta por cada pregunta abierta, en el orden de la API, todas en la misma pantalla. En un proyecto sin abiertas la sección no aparece.
- [ ] Cada tema: nombre, "120 personas · 25,0 %", barra con `aria-hidden`, definición y citas.
- [ ] Las citas se muestran **idénticas** a como llegan, sin recortar ni corregir, en `blockquote`. Un tema sin citas se muestra igual, sin texto de relleno.
- [ ] Una nota visible en la sección dice: "Temas revisados y validados por tu equipo. La IA ayudó a clasificar las respuestas; las cifras las calcula la plataforma." (RNF-06).
- [ ] Debajo de cada pregunta: "Porcentajes sobre N respuestas analizadas. Una persona puede mencionar más de un tema."
- [ ] Si `n_codificadas < n_respuestas`: "Se han analizado N de M respuestas."
- [ ] Si `n_temas > temas.length`: "Se muestran los K temas más mencionados de T."
- [ ] Con `temas: []`: "Esta pregunta todavía no tiene temas listos para mostrar."

**Errores y carga**
- [ ] Mientras carga, un texto de espera.
- [ ] Si falla `closed-results` o `temas-principales`, se muestra el mensaje del servidor y sigue visible la parte que sí cargó.
- [ ] Si falla `recommendations`, la pantalla funciona sin alertas ni "Ver por…", y sin mensaje (igual que `Recommendations.tsx`).

**Impresión, móvil y accesibilidad**
- [ ] Al imprimir no salen el encabezado de la app, el menú lateral, las pestañas, "Imprimir", "Ver por…" ni el enlace a otras preguntas, y el contenido usa todo el ancho. Una tarjeta no se corta entre páginas (`break-inside: avoid`). El separado elegido sí se imprime.
- [ ] Se lee sin desbordes a 768 px y a 375 px. Las tablas se desplazan dentro de su tarjeta, como ya ocurre en `GroupTable`.
- [ ] Todo se opera con teclado y el selector tiene etiqueta asociada.

**General**
- [ ] Usa `shared/api/client.ts`, `Card`, `StatCard`, `Button`, `PageHeader` y las variables de `globals.css`.
- [ ] `cd 07_MVP/frontend && npm run build` sin errores.
- [ ] Verificación en el navegador sobre una **base desechable**:
  - levanta el backend con `MONGODB_URI=mongodb://localhost:27017/softinsight_t042`, y confirma que realmente usa esa base;
  - crea una cuenta admin, un miembro lector, un proyecto con abiertas y cerradas, y otro solo con cerradas;
  - para tener temas **sin IA**: crea categorías manuales (`POST /categories`, nacen `validada`) y asigna respuestas con `PUT /responses/{id}/codings`, por API;
  - recorre todos los criterios con admin y con lector, incluidas la vista de impresión y los dos anchos;
  - al terminar, borra la base `softinsight_t042`, apaga los servidores y no dejes archivos temporales.
  - **Sin IA real:** no pulses ningún botón que analice, codifique o genere informes.

  Reporta lo que viste, criterio por criterio.

## Notas
- Decisiones del usuario (2026-11-03): pestaña "Resultados", la primera, donde entra el lector; NPS y hasta 6 escalas o sí/no, en el orden de la encuesta, con enlace al resto; sin separar por defecto, con "Ver por…" limitado a los grupos sugeridos (máximo 3) y etiqueta "Pocos datos"; un resumen por pregunta abierta en la misma pantalla.
- `Recommendations.tsx` navega con `cerradas?…` desde la ruta índice. Desde `resultados`, una ruta relativa simple apuntaría a otro lugar: usa `../cerradas` o una ruta absoluta y compruébalo en el navegador.
- En los proyectos sin abiertas `project.pregunta` es `null`: esta pantalla no debe usarla.
- El diff debería quedar bajo unas 400 líneas. Si se pasa, explica por qué en tu resumen.
- `graphify-out/` está sin seguimiento y **no debe entrar en ningún commit**: agrega solo tus archivos, por ruta, sin `git add .`.
- Los nombres de personas pueden aparecer en las citas hasta RNF-05. Es un límite conocido y aceptado.
