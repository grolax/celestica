# T-026: Proyectos sin preguntas abiertas (pantalla)
Lado: frontend
Requerimientos: RF-24 (UI), RF-40 (parcial), RNF-13, RNF-14
Rama: tarea/T-026-pantalla-solo-cerradas
Depende de: T-025 (fusionada, PR #30)

## Objetivo
El asistente "Nuevo proyecto" permite crear un proyecto con solo preguntas cerradas, y ese proyecto se abre directamente en "Preguntas cerradas", mostrando solo las pestañas que sirven. "Mis proyectos" lo muestra con su número de personas y sin los indicadores de léxico ni codificación. Los proyectos con abiertas no cambian.

## Decisiones del usuario
- RF-24 en la iteración 3 (2026-10-30). El Excel de resultados para estos proyectos llega en T-027/T-028 (2026-10-31): no es parte de esta tarea.

## Alcance
- SÍ: tipos según el contrato **RF-24 · Proyectos sin preguntas abiertas (T-025)**: `Project.pregunta: string | null`; `ProjectSummary.n_abiertas: number`. TypeScript estricto sin errores, y **ninguna petición con `pregunta=null` ni a operaciones de abiertas** en estos proyectos.
- SÍ: **"Revisa las preguntas"** (`QuestionReview.tsx` y el botón "Continuar" de `NewProject.tsx`):
  - "Continuar" se habilita si hay al menos una pregunta **incluida** que sea abierta o cerrada (`escala`, `nps`, `si_no`, `seleccion_unica`, `seleccion_multiple`, `segmento`, `numerica`).
  - Sin abiertas pero con cerradas: aviso informativo (no de error) **"Esta encuesta no tiene preguntas abiertas: se analizarán solo las preguntas cerradas, sin libro de códigos ni IA."** El texto "…llegará pronto." desaparece.
  - Sin abiertas ni cerradas incluidas: aviso **"Marca al menos una pregunta abierta o cerrada para analizar."** y "Continuar" deshabilitado.
- SÍ: **paso 3** ("Datos del proyecto"):
  - Resumen: "Se analizarán <a> preguntas abiertas y <c> preguntas cerradas" (con singular y plural correctos; si `a` = 0: "Se analizarán <c> preguntas cerradas, sin IA."). La parte del contexto para la IA solo aparece si hay abiertas.
  - Sin abiertas, la tarjeta **"Marco teórico"** (y sus plantillas) **no se muestra**: solo sirve al análisis con IA.
- SÍ: **dentro del proyecto** (`ProjectView.tsx`) cuando `project.pregunta` es `null`:
  - Pestañas visibles: solo **"Preguntas cerradas"** y **"Auditoría"**.
  - Si la ruta es otra (el índice "Dashboard", `lexico`, `codigos`, `codificacion`, `trazabilidad`, `informe`, `exportar`), redirigir a `cerradas` (con `Navigate replace`), para que un enlace viejo o escrito a mano no muestre errores.
  - La línea bajo el nombre dice **"<n_responses> personas · Solo preguntas cerradas"** en vez de "… respuestas · Pregunta: …".
  - Al crear el proyecto, el asistente navega como hoy a `/proyectos/<id>` y la redirección lo lleva a "Preguntas cerradas".
- SÍ: **"Mis proyectos"** (`ProjectList.tsx`), para `n_abiertas === 0`: la columna "Respuestas" muestra `n_responses` (son personas); en "Análisis", una píldora **"Solo cerradas"** en vez de "Léxico" y "sin codificar"; en "Estado", "—" en vez de "0 categorías". Los demás proyectos, igual que hoy.
- NO: el Excel (T-027/T-028); cambios en el backend; cambiar la experiencia de proyectos con abiertas.

## Contrato de API
`docs/API_CONTRATOS.md`, sección **RF-24 · Proyectos sin preguntas abiertas (T-025)** (y la advertencia actualizada de la vista previa en la sección RF-22/RF-25). Solo se consume.

## Archivos probables
- Tocar: `src/features/projects/{types.ts,QuestionReview.tsx,NewProject.tsx,ProjectView.tsx,ProjectList.tsx}`, `questionGroups.ts` si conviene poner ahí la lista de tipos cerrados (y reutilizarla en `ProjectView`, que hoy la define aparte como `CERRADAS`), y los componentes de pestañas solo si TypeScript lo exige por el `string | null`.
- No tocar: `07_MVP/backend/**`, `docs/**`, `shared/api/client.ts`.

## Criterios de aceptación
- [ ] `npm run build` sin errores.
- [ ] Contra el backend local sin IA (cuenta `t012@prueba.cl` / `Prueba-T012-clave`), con la encuesta real `C:/Users/isral/Downloads/Encuesta proyecto de título (respuestas).xlsx` (datos personales: solo local):
  - en "Revisa las preguntas", al desmarcar las abiertas aparece el aviso informativo y "Continuar" sigue habilitado; al desmarcar también todas las cerradas, aparece el otro aviso y "Continuar" se deshabilita;
  - el paso 3 dice "Se analizarán <c> preguntas cerradas, sin IA." y no muestra "Marco teórico";
  - al crear, se abre directamente "Preguntas cerradas" con solo 2 pestañas, y la línea "500 personas · Solo preguntas cerradas";
  - escribir a mano `/proyectos/<id>/lexico` o `/proyectos/<id>` lleva a "Preguntas cerradas"; en la red no hay peticiones a `summary`, `lexical`, `codify`, `report` ni con `pregunta=null`;
  - "Ver por…" y juntar grupos funcionan en ese proyecto;
  - en "Mis proyectos" aparece con 500 y la píldora "Solo cerradas"; el proyecto ya creado por el supervisor (`proj_e3433aa031`) también.
- [ ] Un proyecto con abiertas (por ejemplo `proj_4df733d1c3`) se crea y se abre exactamente como antes: pestañas, selector de pregunta, "Dashboard".
- [ ] Un lector ve el proyecto solo con cerradas igual (sin botones de edición nuevos).
- [ ] Commits con el formato `T-026 RF-24: ...`.

## Notas
- El supervisor tomará capturas reales: al terminar, deja backend (8000) y frontend (5173) corriendo e indica el id del proyecto creado.
- Pon tus scripts y capturas en una subcarpeta propia de la carpeta temporal; no modifiques scripts ajenos.

## Revisión
2026-10-31 — **Aprobada** (supervisor).
- `npm run build` sin errores. Diff solo frontend (7 archivos, +57/−28); `CERRADAS` queda en un solo lugar (`questionGroups.ts`).
- Recorrido propio del supervisor con la encuesta real (cuenta analista), con capturas:
  - "Revisa las preguntas": al desmarcar las 2 abiertas aparece el aviso informativo y "Continuar" sigue habilitado; al desmarcar todo aparece "Marca al menos una pregunta abierta o cerrada para analizar." y "Continuar" se deshabilita.
  - Paso 3: "Se analizarán 44 preguntas cerradas, sin IA." sin "Marco teórico".
  - Al crear (`proj_08d77f74ba`): se abre `/cerradas` con 2 pestañas y "500 personas · Solo preguntas cerradas"; `/lexico`, `/`, `/codigos` e `/informe` redirigen a `/cerradas`; **ninguna** petición a `summary`, `lexical`, `codify`, `report`, `responses`, `categories` ni con `pregunta=null`.
  - "Mis proyectos": 500 y "Solo cerradas" con "—"; los demás proyectos igual.
  - Lector: llega a `/cerradas` con las mismas 2 pestañas. Proyecto con abiertas: 9 pestañas y "484 respuestas · Pregunta: …", como antes. Sin errores de JS.
- Deuda: el contexto de las pestañas se tipa como `ProjectAbierta` con un cast en `ProjectView` (una pestaña nueva que use `pregunta` en un proyecto sin abiertas no avisaría en TypeScript); un enlace viejo con `?pregunta=` a un proyecto sin abiertas muestra el error 404 con "Volver al proyecto".
