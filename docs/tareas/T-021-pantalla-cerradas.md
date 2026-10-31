# T-021: Pantalla "Preguntas cerradas"
Lado: frontend
Requerimientos: RF-30 (UI), RNF-07, RNF-13, RNF-14, RNF-16
Rama: tarea/T-021-pantalla-cerradas
Depende de: T-020 (fusionada, PR #24)

## Objetivo
Una pestaña nueva del proyecto, **"Preguntas cerradas"**, muestra los resultados de todas las preguntas cerradas (escalas, NPS, sí/no, selección, segmentos, numéricas) que entrega `GET /api/projects/{id}/closed-results`. Lenguaje simple, números con formato chileno, sin IA y sin librerías de gráficos.

## Decisiones del usuario (2026-10-30)
- % sobre quienes respondieron; los N/A se muestran aparte, nunca como una opción más.
- Selección múltiple: % de personas (puede sumar más de 100 %); el backend manda `nota`, mostrarla.
- Orden de opciones: el que manda el backend (no reordenar).

## Alcance
- SÍ: tipos en `src/features/analysis/types.ts` (o un archivo nuevo de la feature) exactamente según el contrato; función `getClosedResults(id)` en `analysisApi` (sin `pregunta`: este endpoint no la recibe).
- SÍ: componente nuevo `src/features/analysis/closed/ClosedResults.tsx`, ruta `cerradas` bajo `/proyectos/:id` en `App.tsx`, y pestaña **"Preguntas cerradas"** en `ProjectView` justo después de "Dashboard". La pestaña se muestra **solo si** el proyecto tiene al menos una pregunta de tipo `escala`, `nps`, `si_no`, `seleccion_unica`, `seleccion_multiple`, `segmento` o `numerica` (de `project.preguntas`). Visible para todos los roles (lector incluido).
- SÍ: encabezado con `PageHeader` (como las otras pestañas) y una línea: **"Estos números los calcula la plataforma directamente desde las respuestas, sin IA. Los porcentajes son sobre quienes respondieron cada pregunta; quienes no respondieron aparecen como N/A."** Debajo: "<n_personas> personas respondieron la encuesta".
- SÍ: una `Card` por pregunta, en el orden del backend:
  - Título completo, tipo con la etiqueta de `TIPOS` (de `projects/questionGroups.ts`, no duplicar) y la línea **"<n_respuestas> respondieron · <n_na> N/A (<tasa_respuesta> % de respuesta)"**.
  - Si viene `n_invalidas`: **"<n> respuestas no se pudieron leer como número y no se cuentan."**
  - **Opciones** con las clases existentes `.bar-row`/`.bar`: etiqueta, barra con ancho = `pct`, y texto visible **"<pct> % (<n>)"**. El valor y el n son texto, no solo la barra (RNF-14); la barra lleva `aria-hidden`. Si hay más de 10 opciones, mostrar 10 y un botón "Ver todas (<total>)" / "Ver menos". Etiquetas largas recortadas con el título completo en `title`.
  - **`escala`:** con `StatCard`: **Promedio** "4,23 de 5" (de `escala.max`), **Notas altas (4 y 5)** "80,3 %", **Notas bajas (1 y 2)** "5,6 %" (los valores salen de `top2.valores`/`bottom2.valores`); desviación en texto pequeño: "Desviación: 0,98".
  - **`nps`:** `StatCard` destacado **NPS** con el valor (con signo, "+32,5" / "−4"), y tres más: **Promotores (9–10)**, **Pasivos (7–8)**, **Detractores (0–6)** con "% (n)". Una línea de ayuda: **"NPS = % de promotores − % de detractores. Va de −100 a +100."** Luego la distribución 0–10 con barras.
  - **`seleccion_multiple`:** la `nota` del backend bajo las barras.
  - **`numerica`:** sin barras; `StatCard` con Promedio, Mediana, Mínimo y Máximo; desviación en texto pequeño.
  - Sin `opciones` ni bloque extra para tipos desconocidos: mostrar solo el título y la línea de respuestas (no romper).
- SÍ: formato de números con `toLocaleString("es-CL")` (coma decimal; 1 decimal en %, hasta 2 en promedio/desviación/NPS, como los manda el backend).
- SÍ: estados: cargando ("Calculando resultados…"), error con el mensaje del backend (vía `shared/api/client.ts`), y vacío (`preguntas: []`): **"Este proyecto no tiene preguntas cerradas."**
- SÍ: CSS mínimo en `globals.css` solo si hace falta (por ejemplo una grilla de `StatCard`); reutilizar clases y variables existentes. Responsive: las tarjetas se apilan en móvil (RNF-15).
- NO: cruces por segmento (T-022/T-023), elegir qué preguntas ver, exportar, gráficos con librerías, cambios en el backend, editar rangos de escala.

## Contrato de API
`docs/API_CONTRATOS.md`, sección **RF-30 · Resultados de preguntas cerradas (T-020)**, `GET /api/projects/{id}/closed-results`. Solo se consume.

## Archivos probables
- Tocar: `src/App.tsx` (ruta), `src/features/projects/ProjectView.tsx` (pestaña), `src/features/analysis/{api.ts,types.ts}`, `src/features/analysis/closed/ClosedResults.tsx` (nuevo), `src/styles/globals.css` si hace falta.
- No tocar: `07_MVP/backend/**`, `docs/**`, `shared/api/client.ts`.

## Criterios de aceptación
- [ ] `npm run build` sin errores.
- [ ] Contra el backend local **sin IA**, con un proyecto creado desde `C:/Users/isral/Downloads/Encuesta proyecto de título (respuestas).xlsx` (datos personales: solo local, no commitear ni copiar al repo) en la cuenta `t012@prueba.cl` / `Prueba-T012-clave` (créala si no existe): la pestaña aparece; "importancia de ser propietario" muestra promedio 4,31 y 79,4 % de notas altas; "capacidad de ahorro" muestra Sí 56,5 %; los tramos de ingreso salen de menor a mayor; la comuna unida muestra 10 opciones y "Ver todas".
- [ ] Con el dataset demo (`07_MVP/data/dataset_demo_evaluacion_docente.csv`) o un proyecto antiguo sin cerradas: la pestaña no aparece; y entrando a `/proyectos/<id>/cerradas` a mano se ve el mensaje de vacío.
- [ ] Un usuario lector ve la pestaña y los resultados.
- [ ] Ningún número calculado en el frontend salvo el ancho de las barras (todo viene del backend).
- [ ] Accesible: botón "Ver todas" con teclado; valores visibles como texto.
- [ ] Commits con el formato `T-021 RF-30: ...`.

## Notas
- El supervisor tomará capturas reales para el usuario: al terminar deja backend (8000) y frontend (5173) corriendo con ese proyecto creado, e indica su id en el resumen.
- NPS: la encuesta real puede no tener NPS; verifica ese bloque con la respuesta simulada en el navegador (interceptando la petición, como en T-013) o con un CSV sintético pequeño con una columna 0–10.

## Revisión 1
2026-10-31 — **Con cambios** (supervisor).

Verificado y correcto: `npm run build` sin errores; diff solo frontend (6 archivos, ~150 líneas); tipos y `getClosedResults` según el contrato; pestaña visible solo con cerradas (el demo sin cerradas no la muestra, `/cerradas` a mano da el mensaje de vacío); lector la ve; en escritorio, "importancia de ser propietario" 4,31 de 5 · 79,4 % · 5,6 %, "capacidad de ahorro" Sí 56,5 %, comuna con "Ver todas (120)"; NPS con signo "−4" y nota de `n_invalidas` (respuesta simulada); el frontend no calcula nada salvo el ancho de la barra. El orden de los tramos de ingreso ("Menos de $500.000" en medio) es el que manda el backend según el contrato: no se toca aquí.

Cambio pedido (RNF-15, el panel de resultados debe leerse en móvil):

1. **`globals.css`, regla `@media (max-width: 640px) { .bar-row.closed … }` (línea ~367):** a 390 px de ancho las etiquetas quedan recortadas a ~120 px y los tramos no se distinguen entre sí ("$361.000 – $640…", "$1.500.001 – $1.8…"); en un teléfono el `title` no se puede ver. Además, en las escalas ("1"…"5") la barra queda de ~50 px. Lo que se espera: en móvil, **la etiqueta ocupa su propia línea completa y puede ocupar varias líneas** (sin recorte), y debajo van la barra y el valor en una fila (por ejemplo, `grid-template-columns: 1fr auto` con la etiqueta en `grid-column: 1 / -1` y `white-space: normal`). Solo CSS; en escritorio queda como está.
2. Verifícalo a 390 px con la tarjeta de ingreso (12.) y la de comuna, y deja los servidores corriendo como antes.

## Revisión 2
2026-10-31 — **Aprobada** (supervisor).
- Cambio solo CSS (`globals.css`, media query de `.bar-row.closed`, +5/−1). `npm run build` sin errores.
- Capturas del supervisor a 390 px (cuenta lectora): tramos de ingreso completos ("$361.000 – $640.000", "$1.500.001 – $1.800.000"), barra y valor debajo; escala y NPS (simulado) correctos; `scrollWidth` = 390 (sin scroll horizontal). Escritorio sin cambios.
- Deuda: en móvil el nombre de la organización se desborda en la barra superior (preexistente); con 29 preguntas la página es larga y no hay índice; las barras en móvil son cortas (el valor en texto siempre está visible).
