# T-020: Resultados de preguntas cerradas
Lado: backend
Requerimientos: RF-30, RNF-01, RNF-02
Rama: tarea/T-020-resultados-cerradas
Depende de: T-011a, T-019 (fusionadas)

## Objetivo
Un endpoint de solo lectura que calcula, sin IA, los resultados de todas las preguntas cerradas de un proyecto: conteos y porcentajes, estadísticos de escalas, top-2/bottom-2, NPS, estadísticos numéricos y tasa de respuesta. La pantalla vendrá en T-021.

## Decisiones del usuario (2026-10-30)
- % sobre quienes respondieron; N/A aparte. Selección múltiple: % de personas.
- Escalas con palabras ("Muy de acuerdo…") quedan como selección única por ahora.
- Opciones de más a menos respuestas; escalas y tramos en orden natural.

## Alcance
- SÍ: `GET /api/projects/{id}/closed-results` exactamente como el contrato.
- SÍ: el cálculo en un servicio nuevo y puro (por ejemplo `app/services/quantitative.py`: recibe las preguntas y los respondentes, devuelve el dict), probado de forma unitaria. El router solo obtiene el proyecto con el filtro de organización y llama al servicio.
- SÍ: para separar las opciones de `seleccion_multiple`, reutilizar la lógica de `question_types.py` (separador y `_reconstruir`); si hace falta exponer una función pequeña, hacerlo ahí sin cambiar el comportamiento de `detectar`.
- SÍ: agregar el endpoint a las listas de `test_aislamiento_pytest.py` y `test_permisos_pytest.py` (lector ve).
- NO: cruces por segmento (T-022), tramos de edad, guardar resultados en Mongo, proyectos sin abiertas (T-024), cambios en el informe o las exportaciones, frontend.

## Contrato de API
`docs/API_CONTRATOS.md`, sección **RF-30 · Resultados de preguntas cerradas (T-020)**.

## Archivos probables
- Crear: `app/services/quantitative.py`, `tests/test_quantitative_pytest.py`.
- Tocar: un router (`app/routers/analysis.py` o `projects.py`, el que agrupe mejor), `app/services/question_types.py` (solo si expones el separador), las dos pruebas de cobertura.
- No tocar: `07_MVP/frontend/**`, `docs/**`, `services/thematic.py`, el esquema de Mongo.

## Criterios de aceptación
- [ ] Pruebas unitarias del servicio con números verificables a mano:
  - escala 1–5 con un valor sin elegir (aparece con `n: 0`), promedio, desviación muestral, top2/bottom2;
  - NPS con los tres grupos y el valor;
  - selección múltiple con una opción que trae una coma adentro, % de personas que suma más de 100;
  - orden natural de tramos ("Menos de $360.000", "$360.001 - $700.000", "Prefiero no responder" al final) y orden por frecuencia con empate alfabético;
  - numérica con un valor no numérico (`n_invalidas`);
  - N/A (`null`) fuera de los %, y `n_respuestas + n_na = n_personas`.
- [ ] Prueba del endpoint (mongomock): un proyecto de otra organización da 404; un lector obtiene 200; un proyecto sin cerradas da `"preguntas": []`.
- [ ] Probado contra una copia local de la encuesta real (no la subas al repo): el resultado de las preguntas 10, 15 y 5 tiene sentido (en el resumen, cópialo abreviado).
- [ ] `python -m pytest tests -q` en verde.
- [ ] Commits con el formato `T-020 RF-30: ...`.

## Notas
- Principio no negociable: la IA no calcula números. Aquí no hay IA.
- `respondentes[].valores[q_id]` es `str | null`; en preguntas con varias columnas ya viene unido (primer no vacío).
- Desviación muestral: `statistics.stdev` (0 si hay una sola respuesta).
- El archivo de la encuesta real está en `C:/Users/isral/Downloads/Encuesta proyecto de título (respuestas).xlsx` (datos personales: solo local).

## Revisión 1
2026-10-30 — **Con cambios** (supervisor).

Bien: servicio puro y legible, `separar_opciones` reutiliza `_reconstruir` sin tocar `detectar`, endpoint con `_get_or_404` (filtro de organización), cobertura de aislamiento y permisos, 209 pruebas en verde. Los números de la encuesta real (P10, P15, P5) cuadran. La base de los % sobre respuestas válidas en escala/NPS queda aceptada; el contrato ya se actualizó.

Un cambio:

1. **`quantitative.py` `_escala`: el mínimo de la escala no puede salir del menor valor respondido.** Con una escala 1–5 donde nadie eligió 1 (frecuente en muestras chicas y satisfechas), hoy queda `min: 2` y `bottom2: [2, 3]`, que mete a los neutrales (3) en "las dos notas más bajas": un error metodológico que el usuario vería como dato. Esperado (contrato actualizado): `min` = 0 si alguien respondió 0, y 1 si no; `max` = el mayor valor respondido (sin cambio). Ajusta el `shortcut:` del comentario y agrega una prueba: escala con valores 2–5 → `opciones` desde "1" (n: 0), `bottom2.valores == [1, 2]`.
