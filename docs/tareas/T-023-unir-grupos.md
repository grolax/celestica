# T-023: Unir grupos en los cruces
Lado: backend
Requerimientos: RF-31, RNF-01, RNF-02, RNF-07
Rama: tarea/T-023-unir-grupos
Depende de: T-022 (fusionada, PR #27)

## Objetivo
`closed-results` acepta `unir` para juntar opciones de la pregunta `por` en grupos con un nombre elegido por el cliente (por ejemplo, tramos de edad de 5 años en tramos de 10, o comunas en zonas). Solo para esa consulta: no se guarda nada. Sin IA.

## Decisiones del usuario (2026-10-31)
- Juntar grupos ya hechos es una preferencia del cliente, válida solo para ese análisis (no se guarda, ni por proyecto ni por organización).

## Alcance
- SÍ: implementar el contrato **RF-31 · Unir grupos en los cruces (T-023)** de `docs/API_CONTRATOS.md`, al pie de la letra, con los mensajes 400 exactos.
- SÍ: hacerlo en `services/quantitative.py` sobre los grupos que ya arma `_grupos` (juntar las listas de personas), sin tocar las reglas de cálculo: `por_grupo` y `pocos_datos` salen solos del cálculo existente.
- NO: guardar uniones; unir con `por` numérica; unir opciones de las preguntas cruzadas (solo de `por`); cambios en el frontend o en el esquema.

## Contrato de API
`docs/API_CONTRATOS.md`, sección **RF-31 · Unir grupos en los cruces (T-023)**.

## Archivos probables
- Tocar: `app/services/quantitative.py`, `app/routers/projects.py` (solo el parámetro `unir` de `closed-results`), `tests/test_quantitative_pytest.py`, una línea en `07_MVP/COMO_FUNCIONA.md`.
- No tocar: `07_MVP/frontend/**`, `docs/**`, `services/thematic.py`.

## Criterios de aceptación
- [ ] `pytest tests -q` en verde; las pruebas de T-020 y T-022 pasan sin tocarlas.
- [ ] Pruebas nuevas (mongomock, sin IA):
  - unión de dos opciones: `n_personas` del grupo = la suma de ambas; `por_grupo` del grupo unido igual a calcular a mano sobre esas personas; `unidos` en el orden de T-022; posición = la de la primera opción;
  - opciones no mencionadas intactas; la suma de los grupos + `n_sin_grupo` sigue siendo `n_personas`;
  - `pocos_datos` se recalcula: dos grupos de 6 personas unidos dan 12 personas → `false`;
  - cada error 400 del contrato con su mensaje exacto (incluido «<x>» con el valor);
  - lector con `unir` → 200; otra organización con `unir` → 404.
- [ ] Contra la encuesta real local (proyecto `proj_4df733d1c3`, cuenta `t012@prueba.cl` / `Prueba-T012-clave`): por edad (`q_2`) uniendo "20-24" + "25-29" y "50-54" + "55-59" + "60-64" + "Mayor a 65", informa los grupos y el promedio de "importancia de ser propietario" (`q_12`) por grupo.
- [ ] Commits con el formato `T-023 RF-31: ...`.

## Notas
- `unir` llega como JSON codificado en la URL; FastAPI lo recibe como texto: parsealo con `json.loads` y valida la estructura antes de usarlo.
- Al terminar, deja el backend (8000) corriendo con el código nuevo.

## Revisión 1
2026-10-31 — **Con cambios** (supervisor).

Lo de T-023 está bien: `pytest tests -q` 243 en verde; `_unir` solo junta listas de personas; los 6 mensajes 400 son exactos (verificados por la API); con la encuesta real, por edad, 20-29 (216 personas, 4,09) y "50 o más" (151, 4,57) con `unidos`, sin problemas de codificación en la respuesta (la "á" llega bien; lo que se veía mal era la consola).

Cambio pedido (error de T-022, ya en `main`, que salió al revisar esta tarea):

1. **`services/quantitative.py`, `_categorica` en `seleccion_multiple` dentro de un grupo:** `separar_opciones` deduce el separador (umbral del 5 % de `;`) y reconstruye las opciones con comas **a partir del conjunto de valores que recibe**. En un grupo chico la deducción sale distinta que en el total, y algunas respuestas no se cuentan en la opción que corresponde. Con la encuesta real, por género (`por=q_3`) la suma de los grupos no da el total en 53 opciones de 10 preguntas de selección múltiple. Ejemplos: q_22 "Ubicación": total 368, suma de los grupos 366; q_21 "Encontrar una propiedad en una ubicación conv…" con `por=q_2`: total 65, suma 61. Se espera que **la separación de cada respuesta en opciones dependa solo del conjunto completo de respuestas de la pregunta**, la misma en el total y en todos los grupos: por ejemplo, separar una vez sobre todos los respondentes y contar en cada grupo con ese resultado. Así, para cualquier tipo de pregunta, incluida la selección múltiple, **la suma de `n` de una opción entre los grupos (más los sin grupo) es igual al `n` del total**.
2. **Prueba nueva:** un caso de selección múltiple donde el grupo chico separaría distinto si se separara solo (por ejemplo, una opción con coma adentro que en el grupo aparece una sola vez, o un grupo donde el `;` no llega al 5 %), y que verifique que la suma de los grupos es igual al total. Además, una prueba general sobre los datos de alguna prueba existente: para todas las preguntas con `opciones`, la suma de los grupos más los sin grupo es igual al total.
3. Verifica con la encuesta real que, con `por=q_3` y con `por=q_2` (con y sin `unir`), no queda ningún descuadre, e informa la cuenta.

Commit `T-023 RF-31: ...` en la misma rama.
