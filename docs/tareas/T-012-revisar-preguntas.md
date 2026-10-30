# T-012: Paso "Revisa las preguntas" al crear un proyecto
Lado: frontend
Requerimientos: RF-25, RF-22 (UI), RF-40 (parcial), RNF-13, RNF-14
Rama: tarea/T-012-revisar-preguntas
Depende de: T-010 y T-011a (fusionadas)

## Objetivo
"Nuevo proyecto" pasa a tres pasos: **① Sube tu encuesta → ② Revisa las preguntas → ③ Datos del proyecto**. En el paso 2 el usuario ve lo que la plataforma detectó en cada columna, corrige tipos, elige qué incluir y qué se envía a la IA como contexto, y une columnas ramificadas. Al crear, se envían las `preguntas` confirmadas.

## Decisiones del usuario (2026-10-30)
- Boceto aprobado (ver notas): abiertas primero, todas las preguntas visibles.
- Respuesta vacía = **N/A**; columnas ramificadas se ofrecen unir; contexto para la IA por defecto solo **género y edad**; identificadores nunca a la IA.

## Alcance
- SÍ: `projects/api.ts`: `preview(file)`, `previewQualtrics(survey_id)`, `previewGoogleForms(sheet_url)` y sus tipos (contrato **RF-22 / RF-25 · Vista previa (T-010)**). La creación (archivo, Qualtrics, Google Forms) envía `preguntas` según **RF-23 · Preguntas del proyecto (T-011a)**: en archivo como campo de formulario con JSON en texto; en las integraciones dentro del cuerpo JSON.
- SÍ: `NewProject` como asistente de 3 pasos, con indicador de paso arriba (paso actual marcado con algo más que color) y botones "← Volver" / "Continuar →":
  1. **Sube tu encuesta:** el selector de origen y los controles de hoy (archivo, Qualtrics, Google Forms). Botón **"Revisar preguntas →"** que llama a la vista previa correspondiente (muestra estado de carga y los errores del backend tal cual).
  2. **Revisa las preguntas** (componente nuevo, por ejemplo `projects/QuestionReview.tsx`):
     - Encabezado: "Revisa las preguntas detectadas" y la línea **"Encontramos N respuestas y M columnas. Revisa el tipo de cada una; puedes cambiarlo si no corresponde."**
     - Las `advertencias` del backend como alertas. Excepción: no repetir una advertencia por cada columna ramificada si se muestra el aviso de unión.
     - **Aviso de columnas ramificadas:** agrupar columnas cuyo título, sin espacios finales ni un número final (`"…actualmente?   2"`), es igual, cuando son 2 o más. Texto: **"«<título>» aparece en N columnas. Si las unes, cada persona queda con su respuesta en una sola pregunta."** con botón **"Unir en una"** (y "Deshacer"). Al unir: una sola fila con `columnas` = todas, título = el título base (editable), tipo = el de la mayoría, respuestas = suma de las del grupo.
     - Sección **"Preguntas abiertas"** con el subtítulo "Se analizan con IA, una por una, cuando tú lo pidas." y luego **"Otras preguntas"**. Cada fila: casilla **Incluir**, título (recortado con el completo en `title`), selector de **tipo** (etiquetas en español: Abierta, Escala, NPS, Sí / No, Selección única, Selección múltiple, Numérica, Fecha, Identificador, Segmento, Constante, Sin datos) con el `motivo` como texto de ayuda, **respuestas** y debajo **"N/A n"** si hay vacías, y casilla **Contexto para la IA**. En abiertas, mostrar hasta 3 ejemplos; en selección, segmento y sí/no, un desplegable **"Ver opciones"** con las `opciones` y su conteo, donde las de **1 mención** se agrupan como **"Otras respuestas (k)"**.
     - Valores por defecto: **Incluir** desmarcado en `constante` y `sin_datos`. **Contexto para la IA** marcado solo si el título menciona género, sexo o edad y el tipo es `segmento`, `numerica` o `seleccion_unica` (el mismo criterio del backend; si cambia el tipo, se recalcula); deshabilitado en `identificador`, `abierta`, `fecha`, `constante` y `sin_datos`, con texto alternativo "No se envía a la IA".
     - Nota al pie: **"Contexto para la IA: la IA solo recibe el texto de la pregunta abierta y lo que marques aquí. Los datos de identificación (nombre, RUT, email) nunca se envían."**
     - Si no queda ninguna abierta incluida, "Continuar" se deshabilita y se muestra: **"Necesitas al menos una pregunta abierta para analizar. El análisis de preguntas cerradas llegará pronto."**
  3. **Datos del proyecto:** nombre, marco teórico y plantillas, como hoy. Resumen breve ("Se analizarán 2 preguntas abiertas; 2 preguntas irán como contexto a la IA: edad y género."). Botón **"Crear proyecto"**. Errores 400/422 del backend tal cual; si el error es de preguntas, ofrecer volver al paso 2.
- SÍ: el estado del asistente vive en memoria del componente; volver atrás no pierde lo elegido.
- SÍ: accesible: tabla con encabezados; cada casilla y selector con etiqueta que incluya el título de la pregunta; recorrible con teclado.
- NO: cambios en el backend; el selector de pregunta en el análisis (T-013); análisis de cerradas; agregar preguntas a un proyecto existente.

## Contrato de API
`docs/API_CONTRATOS.md`: **RF-22 / RF-25 · Vista previa (T-010)** y **RF-23 · Preguntas del proyecto (T-011a)**. Solo se consumen.

## Archivos probables
- Crear: `src/features/projects/QuestionReview.tsx` (y, si ayuda, `questionGroups.ts` con la agrupación de ramificadas y los valores por defecto).
- Tocar: `src/features/projects/NewProject.tsx`, `src/features/projects/api.ts`, `src/features/projects/types.ts`, `src/features/integrations/QualtricsSection.tsx` (solo si hace falta para el paso 1), `src/styles/globals.css` (sección propia).
- No tocar: `07_MVP/backend/**`, `docs/**`, `shared/api/client.ts`.

## Criterios de aceptación
- [ ] `npm run build` sin errores.
- [ ] Con el dataset demo (`07_MVP/data/dataset_demo_evaluacion_docente.csv`) contra el backend local sin IA: el paso 2 muestra 1 abierta (`respuesta`), `pregunta` como Constante desmarcada, `id_respuesta` como Identificador sin contexto; crear el proyecto funciona y queda con sus preguntas (`GET /api/projects/{id}` → `preguntas`).
- [ ] Con un CSV sintético con columnas ramificadas (por ejemplo "¿En qué comuna vives?", "¿En qué comuna vives? 2", "… 3") el aviso aparece, "Unir en una" crea una sola pregunta y el proyecto se crea con `columnas` de 3 elementos.
- [ ] Sin abiertas incluidas, no se puede continuar y se ve el mensaje.
- [ ] Volver del paso 3 al 2 conserva los cambios.
- [ ] Diff de menos de unas 450 líneas; si se pasa, avísalo y divide en commits lógicos.
- [ ] Commits con el formato `T-012 RF-25: ...`.

## Notas
- Boceto aprobado por el usuario (2026-10-30), resumido: indicador de 3 pasos; aviso amarillo de columnas ramificadas con botón; tabla "Preguntas abiertas" y luego "Otras preguntas" con Incluir · título · [Tipo ▾] · respuestas (y N/A) · Contexto para la IA; "▸ Ver opciones" en preguntas de selección; nota de contexto al pie; "← Volver" / "Continuar →".
- El supervisor tomará capturas reales del resultado para mostrárselas al usuario: deja el flujo funcionando con backend y frontend locales.

## Revisión 1
2026-10-30 — **Con cambios** (supervisor).

Revisado el código (`questionGroups.ts` replica el criterio de contexto del backend; unión con N/A = filas − suma; `aPreguntas` nunca manda contexto en tipos excluidos) y `npm run build` OK. El supervisor tomó capturas reales con la encuesta real de 500 respuestas y 47 columnas (paso 1, paso 2 antes y después de unir, opciones, paso 3). El flujo funciona: aviso de 16 columnas de comuna, unión con "Deshacer", abiertas primero, edad y género con contexto marcado, resumen del paso 3 correcto. Pendientes visuales:

1. **Paso 3: el campo "Nombre del proyecto" aparece sin estilo** (borde y relleno nativos del navegador). Es la deuda conocida de `Input` sin `type`: pasa `type="text"` en ese campo y revisa los demás `Input` del asistente.
2. **Fila unida: el `motivo` no corresponde a la unión.** Muestra el de la primera columna ("10 valores distintos en 24 respuestas…") junto a "500" respuestas. Para filas unidas, recalcular un motivo coherente con los números unidos, por ejemplo: "<k> valores distintos en <n> respuestas, unidas desde <m> columnas." (k = opciones distintas tras unir).
3. **"Ver opciones": las opciones largas se cortan y ocultan su conteo** (por ejemplo, "Subsidios habitacionales (DS1, DS19, DS49) · …" sin el 264). Las opciones deben ajustarse en varias líneas (sin `text-overflow: ellipsis`) para que siempre se vea el número.

## Revisión 2
2026-10-30 — **Aprobada** (supervisor).
- `npm run build` sin errores. Diff de código ~440 líneas en 7 archivos (incluye `integrations/api.ts` por el campo `preguntas`, aceptado).
- Capturas repetidas con la encuesta real: el campo "Nombre del proyecto" ya tiene el estilo de Celestica; la fila unida de comuna dice "109 valores distintos en 500 respuestas, unidas desde 16 columnas."; "Ver opciones" muestra cada opción completa con su conteo (Subsidios habitacionales (DS1, DS19, DS49) · 264).
- Deuda: `Input` sin `type` por defecto deja sin estilo campos en `ManualCategoryForm`, `LoginPage` (2) y `QualtricsSection` — corregir en el componente (`type="text"` por defecto). `.main-content { min-width: 0 }` global (aceptado). Cambiar el tipo de una fila recalcula "Incluir" y "Contexto" (pisa lo marcado a mano). El botón "Volver a revisar las preguntas" del paso 3 se decide por el texto del error.
