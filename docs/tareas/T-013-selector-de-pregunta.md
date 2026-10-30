# T-013: Selector de pregunta abierta en el análisis
Lado: frontend
Requerimientos: RF-23 (UI), RNF-08, RNF-13, RNF-14
Rama: tarea/T-013-selector-de-pregunta
Depende de: T-011a y T-012 (fusionadas)

## Objetivo
En un proyecto con varias preguntas abiertas, el usuario elige cuál analizar y todas las pestañas (resumen, léxico, libro de códigos, codificación, trazabilidad, informe, exportar) trabajan sobre esa pregunta. Con una sola pregunta abierta no cambia nada visible.

## Decisiones del usuario (2026-10-30)
- Un análisis por pregunta abierta; la IA corre solo a pedido y pregunta por pregunta (cuidar tokens).
- Un informe por pregunta abierta hasta RF-51.

## Alcance
- SÍ: tipos: `Project` gana `preguntas: Pregunta[]` y `pregunta: string` (contrato **RF-23 · Preguntas del proyecto (T-011a)**, `GET /api/projects/{id}`). Reutiliza el tipo de pregunta de T-012 si encaja.
- SÍ: la pregunta elegida vive en la URL como `?pregunta=<id>` (se conserva al recargar y al cambiar de pestaña: los enlaces de las pestañas de `ProjectView` mantienen la query). Sin `?pregunta`, se usa la que devuelva el backend (la primera abierta).
- SÍ: `useProjectData` / `ProjectContext` exponen `pregunta` (id) y cargan `GET /api/projects/{id}?pregunta=<id>`; al cambiar de pregunta se recarga.
- SÍ: **toda** llamada de `analysisApi`, `exportApi` y `projectsApi.applyTemplate` que el contrato lista con `?pregunta` recibe la pregunta como parámetro y la agrega a la URL. Ninguna llamada de análisis debe quedar sin ella (revísalo con `grep` y cuéntalo).
- SÍ: **selector** en `ProjectView`, bajo el nombre del proyecto y sobre las pestañas, **solo si hay 2 o más preguntas abiertas**:
  - Etiqueta: **"Pregunta que estás analizando"**; un `<select>` (o grupo de botones si son pocas) con el título de cada pregunta abierta (recortado, completo en `title`) y su número de respuestas: "28. ¿Qué tendría que cambiar…? · 484 respuestas".
  - Debajo, una línea: **"Cada pregunta abierta tiene su propio libro de códigos, codificación e informe. La IA solo trabaja sobre la pregunta elegida y solo cuando tú se lo pides."**
  - La línea actual de `ProjectView` que dice "columna de texto: …" pasa a decir **"Pregunta: <título>"** (también con una sola abierta).
- SÍ: los **progresos** (codificación e informe) que se consultan por sondeo usan la pregunta activa; si el usuario cambia de pregunta mientras otra se codifica, la pantalla muestra el estado de la nueva y no mezcla.
- SÍ: el **resumen** (`ProjectDashboard`) muestra los números de la pregunta elegida.
- NO: cambios en el backend; comparar preguntas entre sí (RF-51 ampliado); mostrar resultados de preguntas cerradas.

## Contrato de API
`docs/API_CONTRATOS.md`, sección **RF-23 · Preguntas del proyecto y varias preguntas abiertas (T-011a)** (parámetro `pregunta` y `GET /api/projects/{id}`). Solo se consume.

## Archivos probables
- Tocar: `src/features/projects/{types.ts,api.ts,useProjectData.ts,ProjectView.tsx,ProjectDashboard.tsx}`, `src/features/analysis/api.ts` y las pantallas de `src/features/analysis/**` y `src/features/export/**` que llaman a la API (solo para pasar la pregunta), `src/styles/globals.css` si hace falta.
- No tocar: `07_MVP/backend/**`, `docs/**`, `shared/api/client.ts`.

## Criterios de aceptación
- [ ] `npm run build` sin errores.
- [ ] Contra el backend local **sin IA**: un proyecto con 2 preguntas abiertas (créalo con el asistente de T-012) muestra el selector; crear una categoría manual en la pregunta A no la muestra en B; ejecutar el léxico en A (no usa IA salvo la interpretación, que fallará sin clave: es esperado) deja B sin léxico; la URL lleva `?pregunta` y se conserva al cambiar de pestaña y al recargar.
- [ ] Un proyecto con una sola pregunta abierta no muestra el selector y funciona igual que antes.
- [ ] `grep`: ninguna llamada de análisis o exportación sin la pregunta.
- [ ] Selector accesible (etiqueta asociada, recorrible con teclado).
- [ ] Commits con el formato `T-013 RF-23: ...`.

## Notas
- El supervisor tomará capturas reales: deja backend (8000) y frontend (5173) corriendo y un proyecto de prueba con 2 abiertas en la cuenta `t012@prueba.cl` (contraseña `Prueba-T012-clave`).

## Revisión 1
2026-10-30 — **Con cambios** (supervisor).

Lo de T-013 está bien: la pregunta es parámetro obligatorio en las funciones de API (TypeScript impide omitirla); `?pregunta` en la URL y en las pestañas; `Outlet` con `key` por pregunta; selector solo con 2+ abiertas; textos de la orden; `npm run build` OK. `audit` y `usage` sin pregunta es correcto (el contrato no los incluye).

Cambio pedido (riesgo de gasto doble de IA, señalado por el programador como preexistente pero que el selector vuelve frecuente):

1. **Codificación e Informe deben retomar un proceso en curso al montarse.** Hoy, si el usuario cambia de pregunta mientras otra se codifica y vuelve, `Coding` no consulta el progreso y vuelve a ofrecer "Codificar corpus con IA"; el backend no bloquea una segunda codificación de la misma pregunta, así que se pagarían los tokens dos veces. Al montarse (y al cambiar de pregunta), `Coding` y `ReportView` deben llamar una vez a `getCodifyProgress` / `getReportProgress`; si el estado es `running`, mostrar la barra de progreso, ocultar o deshabilitar el botón de lanzar y reanudar el sondeo hasta que termine. Si es `done` o `idle`, comportarse como hoy. Verifícalo contra el backend local sin IA: puedes simular un estado `running` interceptando la respuesta de progreso en el navegador (como en tus scripts), sin lanzar IA real.

El supervisor agrega por separado el bloqueo en el backend (T-019).
