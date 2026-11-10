# T-043: Detectar NPS con todas las formas de "recomendar"
Lado: backend
Requerimientos: RF-22, RF-30, RF-43
Rama: tarea/T-043-deteccion-nps (ya creada desde `main`, con esta orden; trabaja en ella)
Depende de: —

## Objetivo
Una columna de 0 a 10 titulada "¿Qué tan probable es que nos recomiendes?" debe detectarse como `nps`. Hoy queda como `escala`, porque `recomend` no coincide con "recomiendes" ni "recomiendas", y el panel de Resultados muestra un promedio en vez del NPS.

## Alcance
- SÍ: la condición del paso "4. NPS" de `detectar` (`question_types.py`, línea 148), con dos cambios:
  1. Reconocer también las formas con "recomiend": `recom[ei]end|nps`.
  2. Exigir `num.max() > 7`, para que una escala 1–5 o 1–7 que mencione "recomendar" siga siendo `escala`. Sin este resguardo, el cambio 1 convertiría esas escalas en un NPS con cifras falsas.
- NO: frontend; cambiar los proyectos ya creados; las palabras clave de las plantillas (`templates.py`); revisar el `nps` suelto de la expresión; otros tipos de pregunta.

## Contrato de API
Sin cambios. La respuesta de la detección mantiene su forma; solo cambia el tipo que se propone en estos casos.

## Archivos probables
- Se toca: `07_MVP/backend/app/services/question_types.py` y `07_MVP/backend/tests/test_tipos_pregunta_pytest.py`.
- No se toca: `07_MVP/frontend/**`, `routers/`, `store`, `templates.py`.

## Criterios de aceptación
- [ ] Con valores de 0 a 10 son `nps`, con `escala` `{"min": 0, "max": 10}`: "¿Qué tan probable es que nos recomiendes?", "¿Nos recomiendas?", "¿Recomendarías este servicio?" y "RECOMIENDE".
- [ ] Con valores de 1 a 5 y de 1 a 7, "¿Qué tanto recomiendas este curso?" y "¿Recomendarías este curso?" son `escala`, con su rango real.
- [ ] Sigue igual: una columna de 0 a 10 sin la palabra clave es `escala` (`test_nps_con_palabra_clave_y_sin_ella`).
- [ ] Pruebas nuevas parametrizadas en `test_tipos_pregunta_pytest.py`, sin IA.
- [ ] `python -m pytest tests -q` en verde.
- [ ] Sin regresiones de aislamiento multi-tenant: la tarea no toca rutas ni consultas.

## Notas
- Sin migración: no cambia el esquema. La detección corre solo al importar, así que los proyectos ya creados conservan su tipo y se corrigen con "Cambiar tipo".
- Una encuesta NPS con muy pocas respuestas y ninguna sobre 7 quedará como `escala`. Se acepta: es poco probable y se corrige con "Cambiar tipo", mientras que el error contrario publicaría un NPS falso.
- La razón que acompaña al tipo ("el título menciona "recomendar"") sigue siendo correcta; no la cambies.

## Revisión
2026-11-10 · **Aprobada, con una desviación aceptada.**
- Commit `3b41c2f`: 2 archivos, 17 líneas agregadas y 1 quitada. No toca rutas, consultas, esquema ni frontend.
- `python -m pytest tests -q`: 414 pasan (8 nuevas). El supervisor comprobó `detectar` con 14 combinaciones de título y valores: 0 a 10 con cualquier forma de "recomendar" es `nps`; 1 a 5 y 1 a 7 ya no lo son; 0 a 10 sin palabra clave sigue siendo `escala`.
- **Error de la orden, corregido por el programador:** la expresión indicada, `recom[ei]end`, no coincide con "recomend" y habría roto "recomendarías". La implementada, `recomi?end`, cubre ambas formas.
- **Desviación aceptada:** "¿Recomendarías este curso?" con 1 a 5 o 1 a 7 da `segmento`, no `escala`. La causa es la regla previa `hint_anio` (título corto con "curso"), fuera del alcance. El criterio buscaba evitar un NPS falso, y eso se cumple. La prueba usa "¿Recomendarías este taller?". Anotado como deuda en `docs/ESTADO.md`.
- No probado: una importación completa desde la pantalla. El cambio está en una función que ya cubren las pruebas de detección.
