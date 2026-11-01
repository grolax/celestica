# T-029: Léxico y propuesta de categorías: una sola vez a la vez y estado consultable
Lado: backend
Requerimientos: RF-23, RNF-08, RNF-01
Rama: tarea/T-029-analisis-en-curso
Depende de: — (la rama sale de `tarea/T-028-boton-excel-cerradas`, PR #33, solo por los docs; no hay dependencia de código)

## Objetivo
Que el léxico y la propuesta de categorías no se puedan lanzar dos veces a la vez para la misma pregunta. Así se evitan el doble gasto de IA y las categorías duplicadas. Además, la pantalla podrá preguntar si hay uno en curso, para retomarlo al volver a la pestaña.

## Alcance
- SÍ: marca "en curso" por `(proyecto, pregunta, operación)` con lock, 409 al repetir, endpoint `GET analysis-status`.
- NO: volverlos asíncronos con hilos ni barra de progreso; no cambiar la respuesta 200 de los POST; no tocar codificación ni informe; no tocar frontend.

## Contrato de API
`docs/API_CONTRATOS.md` → "Léxico y propuesta de categorías: una sola vez a la vez y estado consultable (T-029)".

## Archivos probables
- Se tocan: `07_MVP/backend/app/routers/analysis.py`, `07_MVP/backend/app/deps.py` (junto a `_codify_progress` y `_progress_lock`), pruebas nuevas en `07_MVP/backend/tests/`.
- NO se tocan: `services/thematic.py`, `store.py` (salvo que sea imprescindible), `07_MVP/frontend/**`.

## Criterios de aceptación
- [ ] Una segunda llamada a `POST lexical` mientras la primera corre, para la misma pregunta, responde 409 con el mensaje del contrato. No llama a la IA ni escribe en la base ni en la auditoría. Igual para `categories/propose`.
- [ ] Otra pregunta del mismo proyecto, o la otra operación, sí corre en paralelo.
- [ ] La marca se libera al terminar bien **y** al fallar. Prueba: la IA simulada lanza `RuntimeError` y responde 503; después, una nueva llamada funciona.
- [ ] `GET analysis-status` devuelve `running`/`idle` correcto antes, durante y después; lector puede consultarlo.
- [ ] Aislamiento: `analysis-status` de un proyecto de otra organización → 404. Agregarlo a la prueba de acceso cruzado (`test_aislamiento_pytest.py`) y a la de permisos (`test_permisos_pytest.py`).
- [ ] Prueba de concurrencia, como `test_codify_lock_pytest.py`: con la IA simulada bloqueada, dos llamadas simultáneas dan una 200 y una 409, y la IA se llama una sola vez.
- [ ] `cd 07_MVP/backend && pytest tests -q` en verde. Las pruebas existentes de léxico y propuesta siguen pasando sin cambiar su forma de uso.
- [ ] Sin llamadas a la API real de Anthropic.

## Notas
- Patrón de referencia: `codify` en `routers/analysis.py` (lock atómico con `_progress_lock`) y `tests/test_codify_lock_pytest.py`.
- Un `def` síncrono de FastAPI sigue ejecutándose aunque el cliente se desconecte, por eso basta con la marca: el resultado se guarda igual.
- Usar `try/finally` para liberar la marca.
- Limpiar el estado en memoria entre pruebas (como se hace con `_codify_progress.clear()`).
