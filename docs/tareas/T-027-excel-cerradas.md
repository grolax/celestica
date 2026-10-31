# T-027: Excel de resultados de preguntas cerradas (con grupos y gráficos)
Lado: backend
Requerimientos: RF-30, RF-31, RF-24 (entrega), RF-52, RNF-07, RNF-14, RNF-01
Rama: tarea/T-027-excel-cerradas
Depende de: T-020 a T-026 (fusionadas)

## Objetivo
`GET /api/projects/{id}/export/closed-xlsx` descarga un Excel con los resultados de las preguntas cerradas (totales y, si se pide, por grupo) con gráficos nativos de Excel que tengan sentido: barras para comparar opciones o grupos sin orden, y líneas de tendencia cuando los grupos tienen un orden natural (tramos de edad, de ingreso…). Cifras idénticas a la pantalla. Sin IA.

## Decisiones del usuario (2026-10-31)
- Excel para los proyectos con solo cerradas (y disponible en todos), con los grupos de "Ver por…" y gráficos "que hagan sentido, de tendencia".
- Nota del supervisor: una tendencia en el tiempo necesita varias mediciones (olas, RF-27/RF-37, aún no existen). Por eso, la línea de tendencia se usa a lo largo de grupos **ordenados** (tramos), y las barras en grupos sin orden.

## Alcance
- SÍ: implementar el contrato **RF-30 / RF-31 · Excel de resultados de preguntas cerradas (T-027)** de `docs/API_CONTRATOS.md`, al pie de la letra.
- SÍ: las cifras salen de `quantitative.calcular(...)` con los mismos parámetros (una sola fuente de verdad); el Excel solo las ordena y grafica. Nada se recalcula aparte.
- SÍ: gráficos nativos con `openpyxl.chart` (`BarChart`, `LineChart`), con etiquetas de datos visibles, colores de la marca Celestica que ya usa `services/export.py` (sin inventar colores nuevos) y textos en español.
- SÍ: la regla de "orden natural" de los grupos se reutiliza de `quantitative.py` (no duplicarla): expón lo mínimo necesario para saber si los grupos de `por` quedaron en orden natural.
- NO: cambios en el frontend (el botón llega en T-028); informe con IA; guardar nada; dependencias nuevas.

## Contrato de API
`docs/API_CONTRATOS.md`, sección **RF-30 / RF-31 · Excel de resultados de preguntas cerradas (T-027)**.

## Archivos probables
- Tocar: `app/services/export.py` (o un módulo nuevo `app/services/export_closed.py` si `export.py` crece mucho); `app/services/quantitative.py` (solo para exponer el orden natural, sin cambiar cálculos); `app/routers/reports.py` (endpoint nuevo, junto a las demás exportaciones); pruebas nuevas en `tests/`; una línea en `07_MVP/COMO_FUNCIONA.md`.
- No tocar: `07_MVP/frontend/**`, `docs/**`, `services/thematic.py`.

## Criterios de aceptación
- [ ] `pytest tests -q` en verde.
- [ ] Pruebas nuevas (mongomock, sin IA), abriendo el archivo con `openpyxl.load_workbook`:
  - hojas "Resumen" y "Totales" sin `por`, y además "Por grupo" con `por`;
  - **las cifras de las celdas coinciden con `closed-results`** con los mismos parámetros, con y sin `por`, y con `unir` y `cortes`. Cubrir al menos una escala, una selección única, una selección múltiple, un sí/no, un NPS y una numérica;
  - tipos de gráfico:
    - líneas en una escala con `por` numérica (tramos);
    - barras con `por` sin orden (por ejemplo, género);
    - barras agrupadas en una categórica por grupo;
    - ningún gráfico, y el texto del contrato, con más de 15 grupos;
    - "10 opciones más frecuentes de <n>" con más de 10 opciones;
  - columna "Pocos datos" = "Sí" en un grupo de menos de 10 personas, y la nota en "Resumen";
  - casos de borde:
    - los 400 de `closed-results` (por ejemplo, `por` inválido y `unir` inválido) con el mismo mensaje;
    - lector → 200; otra organización → 404;
    - proyecto sin cerradas → Excel con la nota;
  - nombre del archivo según el contrato (encabezado `Content-Disposition`).
- [ ] Contra la encuesta real local (proyecto `proj_4df733d1c3`, cuenta `t012@prueba.cl` / `Prueba-T012-clave`), descarga tres archivos: sin `por`; por género; y por edad uniendo "20-24" + "25-29" y "50-54" + "55-59" + "60-64" + "Mayor a 65". Guárdalos **en la carpeta temporal de la sesión** (nunca en el repo: tienen datos de la encuesta) e indica las rutas en el resumen, para que el supervisor los revise.
- [ ] Informa el tiempo de generación con la encuesta real por comuna (120 grupos).
- [ ] Commits con el formato `T-027 RF-30: ...` o `T-027 RF-31: ...`.

## Notas
- Al terminar, deja el backend (8000) corriendo con el código nuevo (`SECRET_KEY=dev-local-secret-t021`).
