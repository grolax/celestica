# T-035: Cruce de 2 preguntas y pares sugeridos (servidor)
Lado: backend
Requerimientos: RF-31, RF-41, RF-30, RNF-10
Rama: tarea/T-035-cruce-dos-preguntas
Depende de: T-034 (PR #39; la rama sale de ella solo por los docs)

## Objetivo
Que `closed-results` y su Excel puedan entregar **una sola pregunta** (`ver`), y que las recomendaciones sugieran **pares** "Ver por × pregunta" (`cruces`). Lo consumirá la pantalla en T-036.

## Alcance
- SÍ: parámetro `ver` en `closed-results` y `export/closed-xlsx`; campo `cruces` en `recommendations`.
- NO: frontend; quitar `segmentos`; cambiar las reglas de `segmentos`, alertas o plantilla; cambiar cifras.

## Contrato de API
`docs/API_CONTRATOS.md` → "RF-31 / RF-41 · Cruce de 2 preguntas y pares sugeridos (T-035)".

## Archivos probables
- Se tocan: `07_MVP/backend/app/services/quantitative.py` (`calcular` con `ver`), `07_MVP/backend/app/routers/projects.py` y `routers/reports.py` (parámetro), `07_MVP/backend/app/services/export_closed.py` (línea "Pregunta:" en Resumen, si hace falta), `07_MVP/backend/app/services/recommendations.py` (`cruces`), pruebas.
- NO se tocan: `07_MVP/frontend/**`, `thematic.py`.

## Criterios de aceptación
- [ ] Con `ver`, `preguntas` trae un solo elemento, **idéntico** al que trae la respuesta sin `ver`, con y sin `por`, `cortes` y `unir`. Probarlo con todos los tipos cerrados, incluida la selección múltiple.
- [ ] Los dos 400 nuevos con los mensajes exactos del contrato. Los 400 existentes no cambian.
- [ ] `calcular` con `ver` no calcula las otras preguntas.
- [ ] Excel con `ver`:
  - solo esa pregunta en "Totales" y "Por grupo";
  - la línea "Pregunta: <título>" en "Resumen";
  - nombre de archivo con el sufijo del contrato.

  Las cifras coinciden con `closed-results` con los mismos parámetros, igual que la prueba de T-027.
- [ ] `cruces`:
  - el orden, el máximo de 5 y el recorte del motivo, según el contrato;
  - lista vacía sin escalas ni NPS y sin segmentos;
  - `segmentos` sigue idéntico.
- [ ] Aislamiento sin cambios: las rutas ya están en las pruebas de acceso cruzado. Agregar un caso con `ver` sobre un proyecto de otra organización, que debe responder 404.
- [ ] Con la encuesta real local (`proj_4df733d1c3`):
  - `closed-results?por=<comuna>&ver=<una escala>` responde mucho más rápido que sin `ver`; reporta los dos tiempos;
  - reporta los `cruces` que devuelve.
- [ ] `cd 07_MVP/backend && pytest tests -q` en verde. Sin llamadas a la API real de Anthropic.

## Notas
- Decisiones del usuario (2026-11-01):
  - el cliente debe elegir la pregunta (el selector de T-036 empieza sin elegir, con la opción "Todas");
  - pares sugeridos de grupos × escalas y NPS, máximo 5;
  - el cliente puede armar cualquier par.
- El nombre `ver` evita confundirse con `pregunta`, que ya identifica la pregunta abierta en otras rutas.
- Reutilizar la lógica de `_segmentos` para los candidatos (sin el corte a 3) en vez de duplicarla.
