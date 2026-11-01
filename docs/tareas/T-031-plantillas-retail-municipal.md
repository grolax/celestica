# T-031: Plantillas de marco para Retail y Municipal
Lado: backend
Requerimientos: RF-17
Rama: tarea/T-031-plantillas-retail-municipal
Depende de: —

## Objetivo
Agregar las plantillas de marco teórico de los dos segmentos objetivo que faltan, **Retail** y **Municipal**, con la misma calidad que las existentes. Así la recomendación de plantillas (RF-41) tendrá algo apropiado que sugerir a esos clientes.

## Alcance
- SÍ: 7 plantillas nuevas en `07_MVP/backend/app/templates.py`, con la estructura de siempre (`nombre`, `industria`, `descripcion`, `marco_teorico`, `categorias_default`).
  - **Retail** (`"industria": "Retail"`):
    1. Experiencia en tienda.
    2. Post-compra y NPS.
    3. Despacho y e-commerce.
    4. Colaboradores de tienda (encuesta interna al personal de tiendas).
  - **Municipal** (`"industria": "Municipal"`):
    1. Satisfacción con servicios municipales.
    2. Consulta PLADECO (Plan de Desarrollo Comunal).
    3. Presupuesto participativo.
- SÍ: prueba pytest que valide **todas** las plantillas, nuevas y existentes (ver criterios).
- NO: cambiar ni borrar las plantillas existentes (incluidas "Consultas Ciudadanas" y "Evaluación de Servicios Públicos" del Sector Público); cambiar `list_templates`, `get_template` ni el endpoint; tocar prompts; tocar frontend (las pantallas agrupan por `industria` automáticamente).

## Contrato de API
Sin cambios: `GET /api/framework-templates` devuelve la misma forma, con 7 elementos más. `POST /api/projects/{id}/apply-template?template=<key>` acepta las claves nuevas.

## Archivos probables
- Se tocan: `07_MVP/backend/app/templates.py`, una prueba nueva en `07_MVP/backend/tests/`.
- NO se tocan: `routers/**`, `services/**`, `prompts_default.json`, `07_MVP/frontend/**`.

## Criterios de aceptación
- [ ] 7 plantillas nuevas, con claves en minúsculas y guion bajo (por ejemplo `retail_experiencia_tienda`, `municipal_pladeco`), agrupadas en el archivo bajo comentarios `# ===== RETAIL =====` y `# ===== MUNICIPAL =====`.
- [ ] Cada plantilla tiene entre 4 y 6 categorías. Cada categoría tiene `nombre`, `definicion`, `criterios_inclusion` y `criterios_exclusion` no vacíos. La exclusión **nombra la categoría vecina** a la que corresponde lo excluido, como en las existentes.
- [ ] Nombres de categoría únicos dentro de cada plantilla. `marco_teorico` y `descripcion` en lenguaje simple, en español de Chile y sin jerga innecesaria. La descripción dice para qué encuesta sirve, en una o dos oraciones.
- [ ] Contenido coherente con su uso real:
  - Retail: atención, disponibilidad de productos, tiempos de caja, precio y promociones, cambios y devoluciones, cumplimiento del plazo de despacho, estado del producto, seguimiento del pedido, clima y carga laboral del personal.
  - Municipal: atención y trámites, aseo y ornato, seguridad, áreas verdes, prioridades por ámbito del PLADECO (desarrollo social, territorial, económico…), propuestas de proyectos, reglas y confianza en el proceso participativo.
  - Se aceptan ajustes razonables.
- [ ] Prueba nueva (pytest, sin IA) que recorra `FRAMEWORK_TEMPLATES` y verifique la estructura de **todas** las plantillas: campos obligatorios no vacíos, entre 4 y 6 categorías, nombres únicos y criterios de exclusión presentes. Además:
  - `GET /api/framework-templates` incluye las industrias "Retail" (4 plantillas) y "Municipal" (3 plantillas);
  - aplicar una plantilla nueva a un proyecto crea sus categorías como `propuesta`, con `origen: "plantilla"`.
- [ ] `cd 07_MVP/backend && pytest tests -q` en verde. Si alguna plantilla existente no cumple la validación, **no la corrijas**: repórtalo en tu resumen y excluye esa plantilla puntual de la prueba, con un comentario.
- [ ] Sin llamadas a la API real de Anthropic.

## Notas
- Estándar de calidad: lo dice el docstring de `templates.py`. Las exclusiones bien escritas son lo que hace precisa la codificación de la IA.
- Las categorías de plantilla siguen requiriendo validación humana (principio de la sección 6): `apply_template` ya las crea como `propuesta`, no cambiar eso.
- El cliente puede modificar las categorías después de aplicarlas (editar, descartar, agregar). Editar el marco teórico después de crear el proyecto llega en una tarea posterior.

## Revisión
2026-11-01 · **Aprobada.**
- Diff: `templates.py` (+242, solo plantillas nuevas bajo `RETAIL` y `MUNICIPAL`), prueba nueva `test_plantillas_pytest.py` y una línea de `test_e2e.py`, que tenía fijo "12 plantillas / 5 industrias". El cambio es necesario y está justificado.
- 7 plantillas con 5 o 6 categorías cada una. Las exclusiones nombran a la categoría vecina y el lenguaje es simple; revisé el detalle de Retail.
- La prueba de estructura recorre las 19 plantillas y no falló ninguna existente. La regla de "exclusión que nombra a la vecina" se aplica solo a las 7 nuevas, porque `feedback_empleados` y `percepcion_marca` no la cumplen del todo (deuda menor).
- `python -m pytest tests -q`: 304 pasan.
- El contenido es un primer borrador. Conviene afinarlo con encuestas reales de Retail y municipios, y no se ha probado cómo codifica la IA con estas exclusiones.
