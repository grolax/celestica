# T-019: Una sola codificación a la vez por pregunta
Lado: backend
Requerimientos: RF-23, RNF-08 (costo de IA)
Rama: tarea/T-019-bloqueo-codificacion-doble
Depende de: T-013 (fusionada)

## Objetivo
`POST /api/projects/{id}/codify` no debe lanzar una segunda codificación con IA del mismo `(proyecto, pregunta)` mientras la primera siga en curso (dos pestañas o dos personas), igual que ya hace `POST .../report` con `already_running`. Así se evita pagar los tokens dos veces.

## Alcance
- SÍ: en `codify`, si `_codify_progress[(project_id, qid)]` está en `running`, responder `{"status": "already_running", "total": <total en curso>}` sin crear hilo ni llamar a la IA.
- SÍ: comprobación e inicio **atómicos** con un `threading.Lock` (los endpoints síncronos de FastAPI corren en un pool de hilos; dos llamadas simultáneas pueden pasar ambas la comprobación). Si sale barato, usar el mismo lock en la comprobación de `report` (reports.py:118-121), que tiene la misma carrera.
- NO: cambios en el frontend (ya es compatible: tras la respuesta empieza a consultar el progreso); persistir el progreso en Mongo; cancelar codificaciones.

## Contrato de API
`docs/API_CONTRATOS.md`, sección **RF-23 · Una sola codificación a la vez por pregunta (T-019)**.

## Archivos probables
- Tocar: `app/routers/analysis.py` (`codify`), `app/deps.py` (el lock, junto a `_codify_progress`), `app/routers/reports.py` (solo si usas el lock ahí), un test nuevo en `tests/`.
- No tocar: `07_MVP/frontend/**`, `docs/**`, `services/thematic.py`.

## Criterios de aceptación
- [ ] Prueba pytest (mongomock, IA simulada): con `codify_all` simulado que se bloquea hasta que el test lo libera (por ejemplo, un `threading.Event`), un segundo `POST codify` de la misma pregunta responde `already_running` y `codify_all` se llamó **una sola vez**; tras liberarlo y terminar, un nuevo `POST` vuelve a responder `started`.
- [ ] En la misma prueba o en otra: una segunda pregunta del mismo proyecto sí puede iniciar (`started`) mientras la primera corre.
- [ ] Si la codificación termina en `error`, se puede volver a lanzar.
- [ ] Sin regresiones: `python -m pytest tests -q` en verde (incluidas aislamiento y permisos).
- [ ] Commits con el formato `T-019 RF-23: ...`.

## Notas
- Modelo a imitar: `reports.py:118-121`.
- Limpia `_codify_progress` en la prueba (es un dict global) para no contaminar otras.

## Revisión
2026-10-30 — **Aprobada** (supervisor).
- `python -m pytest tests -q`: 197 passed. Diff de código +21/-6 en 3 archivos más una prueba nueva (65 líneas), solo backend.
- `codify` comprueba "en curso" y marca `running` dentro de `_progress_lock`; responde `{"status": "already_running", "total": <en curso>}` como dice el contrato. `report` usa el mismo lock (estaba en el alcance opcional), sin cambio de comportamiento.
- Las pruebas cubren: segundo POST de la misma pregunta sin llamar a la IA (`calls == 2` con q_1 + q_2), otra pregunta en paralelo, relanzar tras `done` y tras `error`.
- Deuda: el progreso y el lock viven en memoria de un solo proceso; con varios workers de uvicorn o tras un reinicio no se comparten (ya ocurría antes; ver RNF de despliegue).
