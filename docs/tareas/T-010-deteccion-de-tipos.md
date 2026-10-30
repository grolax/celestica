# T-010: Detección de tipos de pregunta y vista previa
Lado: backend
Requerimientos: RF-22, RF-25 (backend), RNF-07, RNF-10
Rama: tarea/T-010-deteccion-de-tipos
Depende de: T-008b (fusionada)

## Objetivo
Antes de crear un proyecto, la plataforma lee la encuesta y propone el tipo de cada columna (abierta, escala, NPS, sí/no, selección, numérica, fecha, identificador, segmento…) con una explicación en lenguaje simple. Es determinístico, **sin IA** y sin costo. En esta tarea **no se guarda nada**; la creación con preguntas confirmadas es T-011.

## Decisiones del usuario (2026-10-30)
- Proyectos solo con preguntas cerradas quedan para después (junto con RF-30): por ahora solo se advierte.
- Optimizar el gasto de tokens: esta detección no usa IA.

## Alcance
- SÍ: módulo nuevo `app/services/question_types.py` con una función pura `detectar(df) -> dict` que devuelve exactamente el cuerpo del contrato (`n_filas`, `preguntas`, `advertencias`). Reglas sugeridas (ajústalas si una prueba lo justifica y explícalo):
  1. Todo vacío → `sin_datos`. Un solo valor distinto en todas las filas → `constante`.
  2. Título que sugiere identificador (`id`, `rut`, `folio`, `email`, `correo`, `id_respuesta`…) o valores casi todos distintos, cortos y sin espacios → `identificador`.
  3. ≥ 90 % de los valores interpretables como fecha → `fecha`.
  4. Enteros entre 0 y 10 y título con `recomend`/`nps` → `nps` (`escala {0,10}`).
  5. Valores normalizados dentro de {sí, si, no, s, n, yes, true, false, 1, 0} con 2 distintos → `si_no`.
  6. Enteros con pocos valores distintos (≤ 11) en un rango 0–10 → `escala` (`min`/`max` observados, por ejemplo 1–5, 1–7). Si el título sugiere año, edad o curso, preferir `segmento`/`numerica`.
  7. Otros números → `numerica`.
  8. Valores con separador `;` o `,` cuyas partes forman un conjunto pequeño → `seleccion_multiple`.
  9. Texto con pocos valores distintos (≤ 20, o ≤ 30 % de las filas): si el título sugiere grupo (`tienda`, `sede`, `sucursal`, `comuna`, `región`, `carrera`, `área`, `cargo`, `sexo`, `género`, `edad`, `tramo`, `asignatura`…) → `segmento`; si no → `seleccion_unica`.
  10. Texto restante con promedio ≥ 3 palabras o mayoría de valores distintos → `abierta`; si no, `seleccion_unica`.
  - `motivo` en español simple, una frase. `ejemplos`, `opciones`, `escala` y `advertencias` según el contrato.
  - Debe tardar menos de 2 s con 10.000 filas × 30 columnas (RNF-10): usa operaciones vectorizadas de pandas.
- SÍ: lectura de datos reutilizable: extraer de `routers/projects.py` la lectura del archivo (CSV/XLSX) a una función compartida, y en `routers/integrations.py` reutilizar `fetch_responses` de cada integración. Tope de 20 MB para el archivo (413).
- SÍ: los 3 endpoints del contrato con `require_role("analista")`, en los routers que correspondan. **No** guardan nada en Mongo ni registran eventos de proyecto (no hay proyecto). Cuidado con el orden de rutas: `POST /api/projects/preview` no debe chocar con rutas con `{project_id}`.
- SÍ: agregar las 3 rutas nuevas a `tests/test_permisos_pytest.py` (rol mínimo `analista`); es la única modificación permitida en pruebas existentes.
- SÍ: pruebas nuevas `tests/test_tipos_pregunta_pytest.py`:
  - Unitarias de `detectar` con un DataFrame por tipo (los 12 tipos), incluidos casos ambiguos: escala 1–5 vs. año cursado 1–5 con título "anio_cursado"; NPS sin palabra clave (debe quedar `escala`); sí/no con mayúsculas y tildes; columna constante.
  - El dataset demo `07_MVP/data/dataset_demo_evaluacion_docente.csv` produce: `respuesta` → `abierta`, `pregunta` → `constante`, `id_respuesta` → `identificador`, `carrera`/`asignatura`/`genero` → `segmento`.
  - Advertencias: sin abiertas, pocas filas y columna mayormente vacía.
  - Endpoint de archivo: 200 con la forma del contrato; archivo ilegible 400; > 20 MB 413; lector 403; **no se crea ningún proyecto ni evento** (conteo de `projects` y `audit_events` igual antes y después).
  - Qualtrics y Google Forms con `requests` simulado (como `test_fase5.py`), sin internet.
  - Rendimiento: 10.000 × 30 en menos de 2 s.
- NO: guardar preguntas en el proyecto, cambiar `POST /api/projects` ni la codificación (T-011); frontend (T-012); usar IA.

## Contrato de API
`docs/API_CONTRATOS.md`, sección **RF-22 / RF-25 · Vista previa con tipos de pregunta detectados (T-010)**.

## Archivos probables
- Crear: `app/services/question_types.py`, `tests/test_tipos_pregunta_pytest.py`.
- Tocar: `app/routers/projects.py` (lectura compartida + endpoint de archivo), `app/routers/integrations.py` (2 endpoints de vista previa), `tests/test_permisos_pytest.py` (solo agregar rutas), `07_MVP/COMO_FUNCIONA.md`.
- No tocar: `07_MVP/frontend/**`, `docs/**`, `services/thematic.py`, el resto de las pruebas existentes.

## Criterios de aceptación
- [ ] `pytest tests -q` en verde (hoy 128 + las nuevas).
- [ ] Respuesta exactamente con la forma del contrato.
- [ ] Ninguna llamada a IA ni a internet en pruebas; ningún dato persistido por los endpoints de vista previa.
- [ ] Las pruebas de cobertura de rutas (T-002, T-006) siguen afirmando que encontraron rutas y cubren las nuevas.
- [ ] `COMO_FUNCIONA.md` documenta las reglas de detección.
- [ ] Commits con el formato `T-010 RF-22: ...`.

## Revisión
2026-10-30 — **Aprobada** (supervisor).
- `pytest tests -q`: 156 pasan. En `test_permisos_pytest.py` solo se agregaron las 3 rutas.
- `services/question_types.py`: función pura, solo `re`, `unicodedata` y `pandas` (sin IA). El supervisor corrió `detectar` sobre el dataset demo: `id_respuesta` identificador, `carrera`/`asignatura`/`anio_cursado`/`genero` segmento, `pregunta` constante, `respuesta` abierta; sin advertencias.
- Vista previa no persiste nada (conteos de `projects` y `audit_events` verificados en las pruebas); 403 antes de leer el archivo; tope de 20 MB también en `POST /api/projects` (aceptado: comparten lector).
- Rutas nuevas sin colisión con las de `{project_id}`. Rendimiento 10.000×30 entre 0,3 y 1 s.
- Ajustes de reglas aceptados (pistas de título solo en títulos cortos, umbrales de "pocos valores", identificador por valores, coma decimal, `ResponseId`). Atajos marcados con `shortcut:` (muestra de 1.000 valores para pruebas de texto; enteros casi todos distintos → identificador).
- Detalle menor: el `motivo` repite la palabra del título tal cual (por ejemplo "genero" sin tilde). Deuda.

## Revisión 2
2026-10-30 — **Con cambios** (supervisor). Se reabre la aprobación anterior (la rama no se había subido): a pedido del usuario se probó `detectar` con una encuesta real de Google Forms (500 filas, 47 columnas, sobre vivienda) y aparecieron errores de clasificación que importan para el costo de IA. **Los datos reales no se suben al repositorio** (contienen datos personales): reproduce cada patrón con datos sintéticos en las pruebas.

1. **Selección múltiple con opciones largas clasificada como `abierta`.** Patrón de Google Forms: el valor es una lista de opciones separadas por `, ` donde cada opción es una frase de varias palabras (por ejemplo `"Comprar una vivienda propia, Viajar, Emprender un negocio"`), y el título suele decir "Puedes seleccionar más de una", "Selecciona hasta N" o "Selecciona". Hay 30–240 combinaciones distintas en 500 filas, pero las **partes** se repiten mucho. Regla esperada: si al separar por `, ` (y `;`) las partes distintas son pocas (por ejemplo ≤ 40) y las más frecuentes cubren la gran mayoría de las menciones, es `seleccion_multiple` aunque cada parte sea larga; una pista de título ("seleccionar", "selecciona", "más de una", "hasta") refuerza la decisión. Prueba: lista de 6–10 opciones largas combinadas al azar en 500 filas → `seleccion_multiple`; texto libre real con comas (oraciones distintas) → sigue `abierta`.
2. **Selección única con muchas filas y opciones largas clasificada como `abierta`.** 21 valores distintos que se repiten en 500 filas (4 %), cada uno de ~7 palabras. Regla esperada: si los valores distintos son ≤ 10 % de las respuestas (con al menos ~30 respuestas), es categórica (`seleccion_unica` o `segmento`) sin importar el largo. Prueba con ese patrón.
3. **Pista de grupo ignorada en títulos largos.** "1. ¿Cuál es tu edad?", "2. ¿Con qué género te identificas?", "3. ¿En qué región de Chile vives actualmente?", "¿En qué comuna vives actualmente?", "4. ¿Cuál es tu nivel educacional alcanzado?" quedaron `seleccion_unica`; deben ser `segmento`. Mantén la restricción de título corto **solo** para columnas numéricas (para que "¿Cómo evalúa el curso?" 1–5 siga siendo `escala`); en columnas de texto categóricas, la pista de grupo vale con cualquier largo de título. Agrega `nivel educacional`/`educación`/`región`/`comuna` si faltan. Pruebas con esos títulos.
4. **Columnas con muy pocas respuestas.** Con 2 y 6 respuestas no vacías iguales salió `constante` ("Tiene el mismo valor en todas las filas" es falso: 498 filas están vacías); con 5–7 respuestas de 2 palabras salió `abierta` con el motivo contradictorio "Textos largos y casi todos distintos (promedio 2 palabras)". Esperado: `constante` solo si **todas** las filas tienen ese valor (o al menos la gran mayoría tienen respuesta); con pocas respuestas y valores cortos, `seleccion_unica`/`segmento`; `abierta` exige promedio ≥ 3 palabras, y el `motivo` debe ser coherente con los números que muestra.

La única modificación permitida en pruebas existentes sigue siendo la de `test_permisos_pytest.py` (ya hecha). Los casos del dataset demo deben seguir dando lo mismo.

## Revisión 3
2026-10-30 — **Aprobada** (supervisor).
- `pytest tests -q`: 168 pasan; dataset demo con los mismos tipos.
- El supervisor repitió la detección sobre la encuesta real (solo lectura local): de 11 columnas `abierta` (9 falsas) se pasó a **2, las correctas**; las de selección múltiple con opciones largas quedan `seleccion_multiple`; edad, género, región, nivel educacional y las 16 columnas de comuna quedan `segmento`; escalas, sí/no y fecha sin cambios.
- Pendientes menores aceptados (el usuario los corrige en la revisión de preguntas, sin costo de IA): una selección única con comas dentro de las alternativas sale `seleccion_multiple`; "educación financiera" sale `segmento` por la pista de título; "1 valores distintos" (gramática del motivo).
- Excepción aceptada: la pista de grupo no aplica a títulos que evalúan (`evalu|calific|satisf|opin`).

## Revisión 4
2026-10-30 — **Con cambios** (supervisor, a pedido del usuario; segunda ronda de corrección). Se reabre la aprobación de la revisión 3 (la rama no se había subido).

1. **Opciones con comas internas partidas en `seleccion_multiple`.** Google Forms une las opciones marcadas con `", "`; si una opción contiene una coma, hoy se corta en trozos falsos. Ejemplos reales: `"Invertir en depósitos a plazo, fondos mutuos, acciones u otros instrumentos"` → 3 opciones; `"Subsidios habitacionales (DS1, DS19, DS49)"` → `"…(DS1"`, `"DS19"`, `"DS49)"`; `"Transparencia en los precios, condiciones de compra y financiamiento"` → 2. Esperado: reconstruir las opciones uniendo trozos que **siempre** aparecen juntos, contiguos y en el mismo orden (si el trozo B solo aparece inmediatamente después de A, y A siempre va seguido de B, son una sola opción `"A, B"`); además, no cortar dentro de paréntesis sin cerrar. Los conteos de `opciones` deben salir sobre las opciones reconstruidas. Si un caso queda ambiguo (A aparece a veces sin B), se dejan separadas: el usuario corregirá en T-012.
2. **Selección única con comas dentro de las alternativas detectada como `seleccion_multiple`.** Caso real: 21 valores distintos en 500 filas (≈4 %), cada uno una frase con coma interna (`"Me interesa comprar, pero todavía no he buscado"`). Esperado: si tras reconstruir (punto 1) casi todas las respuestas contienen **una sola** opción, o si los valores completos ya son ≤ 10 % de las respuestas y cada valor completo se repite, es `seleccion_unica` (o `segmento` con pista de grupo).
3. **Redacción del `motivo`.** Concordancia de número ("1 valor distinto", "1 respuesta") y la palabra del grupo con su forma escrita correcta en español (género, región, educación, área, etc.), no la versión normalizada sin tildes.

Pruebas con datos sintéticos que reproduzcan cada patrón (opciones con coma interna y con paréntesis, mezcla ambigua que debe quedar separada, selección única con comas). Los casos anteriores (demo y revisión 2) deben seguir igual.

## Revisión 5
2026-10-30 — **Con cambios** (supervisor; tercera y última ronda de corrección).

El supervisor repitió la detección sobre la encuesta real: las opciones con coma interna de las preguntas de ahorro, subsidios (DS1, DS19, DS49) y transparencia quedan **completas y con conteos correctos**; la redacción del `motivo` quedó bien. Pendiente:

1. **Trozo final compartido por varias alternativas.** Caso real (selección única): `"Me interesa comprar para vivir, pero todavía no he buscado."` y `"Me interesa comprar como inversión, pero todavía no he buscado."`. El trozo `"pero todavía no he buscado."` sigue a dos prefijos distintos, así que la regla de "siempre juntos" no lo une, y la pregunta sale `seleccion_multiple` con una opción falsa de 186 menciones. Regla adicional: **un trozo que empieza con minúscula** (tras quitar espacios) se une al trozo anterior, salvo que ese mismo trozo aparezca también como respuesta completa por sí solo (entonces es una opción real). Las alternativas de Google Forms empiezan con mayúscula; las continuaciones ("pero…", "fondos mutuos…", "condiciones de compra…") con minúscula. Tras reconstruir, si casi todas las respuestas tienen una sola opción, la pregunta es `seleccion_unica` (ya implementado).
2. **`COMO_FUNCIONA.md`** (está en `07_MVP/`, no en `docs/`: sí te corresponde): documenta la reconstrucción de opciones (paréntesis, trozos siempre juntos, continuación en minúscula) y la regla de selección única con comas.

Pruebas sintéticas: dos prefijos con el mismo final en minúscula → `seleccion_unica` con las alternativas completas; un trozo en minúscula que también aparece solo → se mantiene separado. Lo demás debe seguir igual.
