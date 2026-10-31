# T-022: Cruces por grupo de las preguntas cerradas
Lado: backend
Requerimientos: RF-31 (cerradas), RNF-01, RNF-02, RNF-07, RNF-10
Rama: tarea/T-022-cruces-por-grupo
Depende de: T-020 (fusionada)

## Objetivo
`GET /api/projects/{id}/closed-results?por=<pregunta_id>` devuelve, además del total, los resultados de cada pregunta cerrada separados por los grupos de la pregunta elegida (género, comuna, tramo de edad…), con aviso de pocos datos (< 10 personas). Sin IA.

## Decisiones del usuario (2026-10-30)
- Umbral de pocos datos fijo: n < 10 (configurable por organización en la iteración 4).
- Tramos de edad por defecto 18–24 … 65+, modificables por el cliente: en esta tarea llegan como parámetro `cortes` y no se guardan.
- % sobre quienes respondieron; N/A aparte.

## Alcance
- SÍ: implementar el contrato **RF-31 · Cruces por grupo de las preguntas cerradas (T-022)** de `docs/API_CONTRATOS.md`, al pie de la letra.
- SÍ: **reutilizar** `services/quantitative.py`: cada grupo se calcula con la misma lógica de T-020 sobre el subconjunto de respondentes. Lo único nuevo es armar los grupos y forzar en cada grupo el rango de escala y la lista de opciones del total. No dupliques las reglas de cálculo.
- SÍ: validaciones de `por` y `cortes` con los mensajes 400 exactos del contrato.
- SÍ: sin `por`, respuesta idéntica a la actual (las pruebas de T-020 siguen pasando sin tocarlas).
- NO: cruzar temas de preguntas abiertas (codificaciones) por grupo (va en una tarea posterior); guardar tramos ni umbral; selección múltiple, escala o NPS como `por`; cambios en el frontend; caché.

## Contrato de API
`docs/API_CONTRATOS.md`, sección **RF-31 · Cruces por grupo de las preguntas cerradas (T-022)**.

## Archivos probables
- Tocar: `app/services/quantitative.py`, `app/routers/projects.py` (solo el endpoint `closed-results`), `tests/test_quantitative_pytest.py` (o un archivo nuevo de pruebas), y las pruebas de aislamiento/permisos si hace falta agregar el caso con `por`.
- No tocar: `07_MVP/frontend/**`, `docs/**`, `services/thematic.py`, el esquema de Mongo (no hay migración).

## Criterios de aceptación
- [ ] `pytest tests -q` en verde.
- [ ] Pruebas nuevas (mongomock, sin IA) que verifiquen:
  - grupos categóricos en el orden de T-020; `n_sin_grupo` cuenta a quienes no respondieron `por`;
  - en cada grupo, `n_respuestas + n_na` = `n_personas` del grupo, y la suma de `n_personas` de los grupos + `n_sin_grupo` = `n_personas`;
  - un caso con números conocidos: promedio, top2 y % de una escala en un grupo, calculados a mano;
  - en escala, el rango del grupo es el del total aunque el grupo no use el máximo; en categóricas, las opciones del grupo son las del total con `n: 0`;
  - `pocos_datos` true con 9 personas y false con 10;
  - `numerica` como `por`: tramos por defecto con etiquetas `"18–24"`…`"65+"` y `"Menos de 18"`; con `cortes=30,50` dan `"Menos de 30"`, `"30–49"`, `"50+"`; los valores no numéricos van a `n_sin_grupo`;
  - la pregunta `por` no aparece en `preguntas`;
  - los errores 400 del contrato (`por` inexistente, `por` de tipo `abierta` o `seleccion_multiple`, `cortes` inválidos o sin `por` numérica);
  - el lector puede consultar con `por`; un proyecto de otra organización con `por` responde 404.
- [ ] Rendimiento: con un proyecto sintético de 10.000 respondentes, 20 cerradas y `por` con 50 grupos, la respuesta tarda menos de 10 s (RNF-10). Informa el tiempo medido; no hace falta dejarlo como prueba si tarda mucho en la suite.
- [ ] Contra la encuesta real local (`C:/Users/isral/Downloads/Encuesta proyecto de título (respuestas).xlsx`, proyecto `proj_4df733d1c3` en el Mongo local, cuenta `t012@prueba.cl` / `Prueba-T012-clave`): informa en el resumen el resultado por género de "importancia de ser propietario" (promedio y % de notas altas por grupo) y los tramos de la edad.
- [ ] `COMO_FUNCIONA.md`: una línea sobre los cruces si describe `closed-results`.
- [ ] Commits con el formato `T-022 RF-31: ...`.

## Notas
- No hay cambio de esquema: no hace falta migración.
- El supervisor revisará los números con la encuesta real.
