# T-032: Recomendaciones automáticas (servidor)
Lado: backend
Requerimientos: RF-41, RF-17, RNF-01, RNF-02
Rama: tarea/T-032-recomendaciones
Depende de: T-031 (PR #36; la rama sale de ella porque usa las plantillas nuevas)

## Objetivo
Un endpoint que, con reglas fijas y sin IA, entrega tres cosas para un proyecto:
- alertas de calidad de datos;
- hasta 3 segmentos sugeridos para cruzar;
- una plantilla de marco sugerida.

Lo consumirá la tarjeta "Recomendaciones" del panel del proyecto (T-033).

## Alcance
- SÍ: `GET /api/projects/{id}/recommendations` según el contrato; un servicio nuevo con las reglas; `palabras_clave` en cada una de las 19 plantillas.
- NO: frontend; cambios en `closed-results`, en `preview`/`detectar` ni en las alertas de la vista previa; guardar recomendaciones en la base; IA.

## Contrato de API
`docs/API_CONTRATOS.md` → "RF-41 · Recomendaciones automáticas (T-032)".

## Archivos probables
- Se tocan: `07_MVP/backend/app/services/recommendations.py` (nuevo), `07_MVP/backend/app/routers/projects.py` (ruta), `07_MVP/backend/app/templates.py` (solo agregar `palabras_clave`), pruebas nuevas.
- NO se tocan: `services/thematic.py`, `prompts_default.json`, el texto y las categorías de las plantillas, `07_MVP/frontend/**`.

## Criterios de aceptación
- [ ] La respuesta tiene la forma exacta del contrato, y los mensajes de alerta son **idénticos** a los de la tabla.
- [ ] Cada regla de alerta tiene prueba con datos mínimos: un caso que la activa y uno en el borde que no (por ejemplo, n = 9 y n = 10; n = 29 y n = 30; `n_na` justo en la mitad).
- [ ] Segmentos: se arman reutilizando `quantitative._grupos` (o una función pública equivalente del mismo módulo), sin duplicar la lógica. Probar:
  - el orden (título "Género" antes que otra pregunta con más grupos);
  - el máximo de 3;
  - la exclusión por más de 15 grupos, por menos de 2 grupos con datos suficientes y por menos de la mitad de respuestas;
  - una `numerica` agrupada en tramos.
- [ ] Plantilla:
  - `palabras_clave` en las 19 plantillas;
  - la prueba de estructura de `test_plantillas_pytest.py` exige entre 6 y 15 palabras clave, sin tildes;
  - probar que un proyecto con preguntas sobre "profesor" y "clase" sugiere `evaluacion_docente_cna`, y que uno con "despacho" y "pedido" sugiere `retail_despacho_ecommerce`;
  - probar que se devuelve `null` sin abiertas, con menos de 2 coincidencias y cuando el marco es el de una plantilla.
- [ ] El endpoint no escribe nada: la auditoría no cambia tras llamarlo.
- [ ] Aislamiento: un proyecto de otra organización responde 404. Agregar la ruta a `test_aislamiento_pytest.py` y a `test_permisos_pytest.py` (rol mínimo lector).
- [ ] Con la encuesta real local (`proj_4df733d1c3`, 500 personas) responde en menos de 1 s. Indica en el resumen qué alertas, segmentos y plantilla devuelve.
- [ ] `cd 07_MVP/backend && pytest tests -q` en verde. Sin llamadas a la API real de Anthropic.

## Notas
- Decisiones del usuario (2026-11-01):
  - la plantilla se sugiere por palabras clave, sin pedir el rubro;
  - el aviso de menos de 30 respuestas se suma al de menos de 10;
  - el cliente puede modificar todo lo que trae la plantilla.
- Para quitar tildes ya existe `_sin_tildes` en `services/question_types.py`; reutilizarla.
- Las palabras clave se buscan como **raíces al inicio de palabra** (por ejemplo, `profesor` coincide con "profesores"), no como subcadenas en cualquier posición.
- Las reglas de `cerrada_dispersa` y de abiertas usan los valores guardados en `respondentes`. Si la encuesta tiene preguntas ramificadas unidas, se usan los valores ya unidos, igual que en `closed-results`.

## Revisión
2026-11-01 · **Aprobada.**
- Diff (+391): servicio `recommendations.py` (94 líneas), ruta de una línea con `_get_or_404` (filtra por organización), `palabras_clave` en las 19 plantillas, pruebas y una sección de `COMO_FUNCIONA.md`. Sin cambios en frontend, IA ni texto de las plantillas.
- Contrato: forma y mensajes idénticos; segmentos con `quantitative._grupos` (los mismos grupos que `closed-results`); plantilla `null` en los tres casos pedidos; solo lectura.
- Decisiones del programador donde el contrato no decía, aceptadas:
  - las alertas se agrupan por regla;
  - el recorte a 80 caracteres aplica solo a los mensajes;
  - "entre 2 y 15 grupos" cuenta todos los grupos;
  - "responden la mitad" cuenta a quienes quedan en un grupo.
- `python -m pytest tests -q`: 334 pasan. 28 pruebas nuevas con los bordes de cada regla.
- Encuesta real (500 personas), 37 ms:
  - alertas `muchas_vacias` y `abierta_corta` en `q_32`;
  - segmentos edad, género e ingreso;
  - plantilla `percepcion_marca` ("marca", "asocia").
- Deuda:
  - Algunas palabras clave son genéricas ("comuna", "producto", "cliente", "proyecto", "desarrollo", "usuario") y pueden dar sugerencias equivocadas; hay que afinarlas con encuestas reales.
  - Un marco editado a partir de una plantilla puede volver a sugerirla.
- Para T-033: los títulos reales traen saltos de línea; en HTML se ven como un espacio (no usar `white-space: pre`).
