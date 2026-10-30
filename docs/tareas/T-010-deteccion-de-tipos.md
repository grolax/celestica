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
