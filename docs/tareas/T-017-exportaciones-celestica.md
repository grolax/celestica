# T-017: Nombre y colores Celestica en los informes PDF y Word
Lado: backend
Requerimientos: RNF-16
Rama: tarea/T-017-exportaciones-celestica
Depende de: T-014 (paleta), ya fusionada

## Objetivo
Los informes descargables (PDF y DOCX) dicen **Celestica** en vez de SoftInsight y usan la paleta de la plataforma (T-014): azul marino para títulos y azul para acentos. Es un cambio de presentación, sin tocar contenido ni cálculos.

## Alcance
- SÍ, en `app/services/export.py`:
  - Portada PDF y DOCX: "SoftInsight" → "Celestica".
  - Título del documento PDF: `Informe Celestica — {nombre}`.
  - Pie PDF y DOCX: "Análisis realizado con Celestica · Auditable y trazable".
  - Nota de metodología (línea ~128): "El análisis se realizó con Celestica en dos capas…".
  - Paleta: reemplazar `PRIMARY = "#0099CC"` por constantes de la paleta T-014: `NAVY = "#0b2545"` (portada y títulos h1/h2) y `PRIMARY = "#0077b6"` (encabezado de tablas, barras del gráfico, acentos). Quitar el turquesa `#00688B` de los h2 (pasa a `NAVY`). En DOCX, `primary_rgb` y el color de los títulos siguen la misma regla. Eliminar `CREAM` si no se usa.
- SÍ, en `app/main.py`: nombre del archivo descargado `informe_softinsight_<slug>.pdf/.docx` → `informe_celestica_<slug>.pdf/.docx`.
- NO (decisión del usuario 2026-10-30: dejar SoftInsight internamente "para evitar confusiones"):
  - `FastAPI(title="SoftInsight")` y el docstring de `main.py`.
  - Nombre de la base de datos, logs (`softinsight.log`, logger `softinsight.claude`).
  - **Nunca** la sal de `services/integrations/credentials.py` (`"softinsight-credentials:"`): cambiarla impide descifrar los tokens de Qualtrics guardados.
- NO: cambiar textos de contenido del informe, estructura, CSV/XLSX (no llevan marca), ni el frontend.

## Contrato de API
Sin cambios de rutas ni de cuerpos. Solo cambia el nombre de archivo en `Content-Disposition` de `/export/pdf` y `/export/docx`; el frontend lo toma de la cabecera, no lo construye.

## Archivos probables
- Tocar: `07_MVP/backend/app/services/export.py`, `07_MVP/backend/app/main.py` (solo las 2 líneas de nombre de archivo), una prueba nueva en `07_MVP/backend/tests/`.
- No tocar: `07_MVP/frontend/**`, `docs/**`, `database.py`, `claude_log.py`, `integrations/credentials.py`.

## Criterios de aceptación
- [ ] `pytest tests -q` en verde (hoy 18).
- [ ] Prueba nueva (pytest, mongomock, sin IA real): el PDF y el DOCX de un proyecto de prueba contienen "Celestica" y no contienen "SoftInsight"; la cabecera de descarga es `informe_celestica_...`. (Para el PDF basta comprobar el texto extraído o el título del documento; para DOCX, leer los párrafos con `python-docx`.)
- [ ] No queda `#0099CC` ni `#00688B` en `export.py`.
- [ ] Sin cambios de aislamiento: los endpoints de exportación siguen usando `_get_or_404`.
- [ ] Commits con el formato `T-017 RNF-16: ...`.

## Notas
- La marca por organización (logo y color propios, RF-11) es otra tarea; aquí solo la marca base Celestica.

## Revisión
2026-10-30 — **Aprobada** (supervisor).
- `pytest tests -q`: 19 pasan (18 + `test_export_marca_pytest.py`).
- Portada, título, pie y nota metodológica dicen Celestica en PDF y DOCX; `NAVY #0b2545` en títulos y portada, `PRIMARY #0077b6` en tablas y gráfico; sin `#0099CC`/`#00688B`; `CREAM` eliminado.
- `main.py`: solo los 2 nombres de archivo; título FastAPI, logs, base de datos y sal de `credentials.py` intactos. Endpoints siguen con `_get_or_404`.
- Pendiente menor: las tablas del DOCX usan el estilo de Word "Light Grid Accent 1" (azul del tema de Word), no `PRIMARY`. Aceptado; anotado como deuda.
