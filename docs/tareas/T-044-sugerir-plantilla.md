# T-044: Sugerir la plantilla antes de crear el proyecto (servidor)
Lado: backend
Requerimientos: RF-40, RF-41, RNF-02, RNF-18
Rama: tarea/T-044-sugerir-plantilla (ya creada desde `main`, con el contrato y esta orden; trabaja en ella)
Depende de: —

## Objetivo
Exponer la sugerencia de plantilla de RF-41 para una encuesta que todavía no es proyecto, usando las preguntas que la persona confirmó. Sin IA y sin guardar nada. La pantalla llega en T-045.

## Alcance
- SÍ: `POST /api/projects/suggest-template`, tal como dice el contrato.
- SÍ: hacer pública la función `_plantilla` de `services/recommendations.py` (por ejemplo, `plantilla_sugerida`) y reutilizarla. No dupliques la regla.
- SÍ: agregar la raíz `"recomiend"` a `palabras_clave` de las dos plantillas que ya tienen `"recomend"` en `templates.py`, para que un título con "recomiendes" también cuente.
- NO: frontend; cambios en `GET .../recommendations`, en las vistas previas o en la creación del proyecto; plantillas en MongoDB; cambiar otras palabras clave ni la regla de coincidencias.

## Contrato de API
`docs/API_CONTRATOS.md`, sección "RF-40 · Plantilla sugerida al crear el proyecto (T-044)".

## Archivos probables
- Se tocan: `07_MVP/backend/app/routers/projects.py`, `07_MVP/backend/app/services/recommendations.py`, `07_MVP/backend/app/templates.py` y `07_MVP/backend/tests/` (`test_permisos_pytest.py` y las pruebas de la sugerencia).
- No se tocan: `07_MVP/frontend/**`, `store.py`, `services/thematic.py`.

## Criterios de aceptación
- [ ] Con títulos que coinciden en 2 o más palabras clave y al menos una `abierta`, devuelve `plantilla` con `key`, `nombre`, `industria` y `motivo`.
- [ ] Para las mismas preguntas, el resultado coincide con el de `recommendations` en un proyecto con esos títulos, sin nombre ni marco.
- [ ] `plantilla` es `null` sin preguntas `abierta` (aunque los títulos coincidan), con menos de 2 coincidencias y con la lista vacía.
- [ ] Un título con "recomiendes" cuenta como coincidencia en las dos plantillas ajustadas.
- [ ] Más de 1.000 preguntas o un `titulo` de más de 2.000 caracteres responde 422.
- [ ] Sin sesión responde 401 y con rol lector 403; analista y admin responden 200. La ruta queda declarada en la tabla de `test_permisos_pytest.py`.
- [ ] Prueba de que no escribe: la cantidad de proyectos y de eventos de auditoría no cambia.
- [ ] Las pruebas de `test_plantillas_pytest.py` siguen en verde con la raíz nueva.
- [ ] `python -m pytest tests -q` en verde, con mongomock y sin IA real.
- [ ] Sin regresiones de aislamiento multi-tenant: la ruta no lee proyectos, y las plantillas son globales.

## Notas
- Declara la ruta sin conflicto con `/api/projects/{project_id}`: es un POST de dos segmentos, igual que `/api/projects/preview`.
- La función solo usa `preguntas`, `name` y `marco_teorico` del diccionario, así que basta pasarle `{"preguntas": [...]}`.
- Valida los límites con el modelo Pydantic del cuerpo, como las demás rutas.
- No hace falta migración: no cambia el esquema.
