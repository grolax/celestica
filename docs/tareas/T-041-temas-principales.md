# T-041: Temas principales con citas para el panel de resultados (servidor)
Lado: backend
Requerimientos: RF-43, RNF-01, RNF-02, RNF-05, RNF-06, RNF-07, RNF-10
Rama: tarea/T-041-temas-principales (ya creada desde `main`, con el contrato y esta orden; trabaja en ella)
Depende de: —

## Objetivo
Entregar, para cada pregunta abierta, sus temas validados más frecuentes, con conteo, porcentaje y citas textuales, sin IA. La pantalla llega en T-042.

## Alcance
- SÍ: `GET /api/projects/{id}/temas-principales`, tal como dice el contrato, con su cálculo en una función pura de un servicio nuevo.
- NO: frontend; temas por grupo; enmascarar o recortar citas; cambios en `/summary`, en `closed-results` o en las recomendaciones; caché; detectar nombres de personas.

## Contrato de API
`docs/API_CONTRATOS.md` → "RF-43 · Temas principales para el panel de resultados (T-041)".

## Archivos probables
- Se tocan: `07_MVP/backend/app/services/temas_principales.py` (nuevo), `app/routers/analysis.py` (la ruta, en "Resultados, trazabilidad e informe"), un archivo nuevo `tests/test_temas_principales_pytest.py`, `tests/test_aislamiento_pytest.py`, `tests/test_permisos_pytest.py` y `07_MVP/COMO_FUNCIONA.md` (un párrafo).
- NO se tocan: `services/thematic.py`, `store.py` (lee con `_get_or_404` y `store.vista_pregunta`), `07_MVP/frontend/**`.

## Criterios de aceptación
Cada punto lleva su prueba en pytest, con mongomock.

**Temas**
- [ ] El 200 tiene la forma exacta del contrato. Las preguntas salen en el orden del proyecto, con varias abiertas.
- [ ] Un proyecto sin abiertas devuelve `{"preguntas": []}`, y una pregunta sin codificar devuelve `temas: []`.
- [ ] Solo aparecen categorías `validada`. Una `propuesta`, una `descartada` y `SIN_CATEGORIA` nunca aparecen, aunque tengan codificaciones, y una respuesta `SIN_CATEGORIA` sí cuenta en `n_codificadas`.
- [ ] Máximo 5 temas, ordenados como dice el contrato (incluido el empate). `n_temas` conserva el total antes del máximo.
- [ ] Una asignación repetida a la misma categoría en una respuesta cuenta una vez. Las codificaciones de respuestas inexistentes se ignoran.
- [ ] Porcentaje con 1 decimal sobre `n_codificadas`. Una respuesta con 2 temas cuenta en ambos.
- [ ] Una asignación de baja confianza cuenta igual (RNF-06).

**Citas**
- [ ] Cada cita es **idéntica** al `text` de una respuesta asignada a ese tema. La prueba lo comprueba por igualdad exacta.
- [ ] No se eligen respuestas con correo, RUT (`12.345.678-9`, `12345678-K`, `1234567-8`) ni teléfono (`+56 9 1234 5678`, `912345678`). Esas respuestas sí cuentan en `personas`.
- [ ] Si todas las respuestas de un tema tienen datos personales: `citas: []`, y el tema se mantiene con su conteo.
- [ ] Se cumple el orden de preferencia completo. Dos llamadas seguidas dan el mismo resultado.
- [ ] Una respuesta no se repite en otro tema de la misma pregunta, salvo que ese tema no tenga otra elegible.

**Seguridad y costo**
- [ ] Permisos: el lector recibe 200. Agrega la ruta a `test_permisos_pytest.py` (rol mínimo lector).
- [ ] Aislamiento: otra organización recibe 404. Agrega la ruta a `test_aislamiento_pytest.py`.
- [ ] Una prueba confirma que la IA simulada no se llama y que el proyecto no cambia, incluido `audit_log`.
- [ ] La respuesta no incluye `meta`, `rationale` ni datos de quien respondió.

**Rendimiento y cierre**
- [ ] Con 10.000 respuestas codificadas, reporta en tu resumen cuánto tarda el cálculo. La meta es menos de 1 s (RNF-10). No agregues una prueba con límite de tiempo: esas pruebas ya fallaron con el equipo cargado (ver `docs/ESTADO.md`).
- [ ] Sin migración: el esquema no cambia. Confírmalo en tu resumen.
- [ ] `cd 07_MVP/backend && python -m pytest tests -q` en verde. Sin llamadas a la API real de Anthropic.

## Notas
- Decisiones del usuario (2026-11-03): ver el contrato. Los nombres de personas no se detectan con reglas, y eso queda para la anonimización de RNF-05.
- Forma de los datos: `vista["codings"]` es `{response_id: [{category_id, rationale, confidence, source, status}]}`. Las asignaciones de la IA llevan `source: "claude"` y `status: "propuesta"`, y las del analista `source: "analista"` y `status: "validada"`. **Filtra por el `status` de la categoría, no por el de la asignación:** casi todas las asignaciones de IA siguen en `propuesta`. Por eso T-042 marcará en pantalla que la IA clasificó las respuestas (RNF-06).
- Una respuesta recodificada a mano puede tener la lista vacía: cuenta en `n_codificadas`, pero en ningún tema.
- Una asignación puede venir sin `confidence`: trátala como la de menor prioridad, sin que falle.
- Ninguna pregunta de la base local tiene codificaciones, así que las pruebas usan datos armados a mano. No generes codificaciones en la base local.

## Revisión
2026-11-03 · **Aprobada.**
- Diff dentro del alcance: servicio nuevo (71 líneas), ruta en `analysis.py`, pruebas, y un párrafo en `COMO_FUNCIONA.md`. No toca `thematic.py`, `store.py` ni el frontend.
- `python -m pytest tests -q` con el equipo descargado: 406 pasan en 1 min 27 s.
- Contrato: forma del 200, máximo de temas y citas, orden de preferencia y exclusión de datos personales.
- Aislamiento y permisos: lee con `_get_or_404` (filtro por organización en `store`); otra organización recibe 404 y el lector, 200. Ruta agregada a ambas pruebas de cobertura.
- Principios: sin IA, cifras en Python, citas idénticas al texto, solo categorías validadas, la confianza no filtra conteos y no escribe en la auditoría.
- Verificación del supervisor sobre los 25 proyectos locales, solo en memoria: sin errores y base sin cambios. Con codificación simulada: 229 citas, todas textuales y sin datos personales. Ninguna respuesta local activó el filtro; ese caso lo cubren las pruebas.
- Decisión aceptada: si un tema tiene alguna respuesta aún sin citar, cita solo de esas, aunque quede con 1 cita.
- Rendimiento medido: 0,15 s con 10.000 respuestas codificadas. Sin migración: el esquema no cambia.
- No probado con codificaciones reales: no hay ninguna en la base local.
