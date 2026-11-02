# T-037: Cambiar el tipo de una pregunta cerrada (servidor)
Lado: backend
Requerimientos: RF-25, RF-30, RNF-01, RNF-02, RNF-07
Rama: tarea/T-037-cambiar-tipo-cerrada
Depende de: T-036 (PR #41; la rama sale de ella solo por los docs)

## Objetivo
Permitir que un analista corrija el tipo de una pregunta cerrada mal detectada en un proyecto ya creado (por ejemplo, de "Selección única" a "Escala"), con validación y registro en la auditoría.

## Alcance
- SÍ: `PATCH /api/projects/{id}/preguntas/{pregunta_id}` según el contrato; función en `store.py` que actualiza el `tipo` de esa pregunta filtrando por organización; evento de auditoría.
- NO: cambios entre abierta y cerrada; unir columnas o cambiar títulos después de crear; editar `contexto_ia`; frontend.

## Contrato de API
`docs/API_CONTRATOS.md` → "RF-25 · Cambiar el tipo de una pregunta cerrada después de crear el proyecto (T-037)".

## Archivos probables
- Se tocan: `07_MVP/backend/app/routers/projects.py`, `07_MVP/backend/app/store.py` (un `$set` puntual sobre `preguntas.$.tipo`, con filtro por `org_id`), pruebas nuevas.
- NO se tocan: `services/thematic.py`, `quantitative.py` (salvo exponer la lectura de números si hace falta reutilizarla), `07_MVP/frontend/**`.

## Criterios de aceptación
- [ ] El 200 devuelve la forma del contrato. Después, `closed-results` muestra la pregunta con el tipo nuevo; por ejemplo, de `seleccion_unica` a `escala` aparecen promedio, notas altas y bajas.
- [ ] Mismo tipo: 200, sin escritura ni evento de auditoría.
- [ ] Cada error del contrato tiene su prueba, con el mensaje exacto:
  - tipo inválido;
  - pregunta abierta → cerrada;
  - cerrada → `abierta`;
  - texto → `escala`;
  - números fuera de 0–10 → `nps`;
  - el borde del 90 %: 9 de 10 números pasa, 8 de 10 no.
- [ ] Evento `cambio_tipo_pregunta` con `antes`, `despues` y `usuario`. La auditoría solo crece.
- [ ] Permisos y aislamiento:
  - el lector recibe 403;
  - un proyecto de otra organización da 404 y no se modifica;
  - agregar la ruta a `test_aislamiento_pytest.py` y a `test_permisos_pytest.py` (rol mínimo analista).
- [ ] La escritura filtra por `org_id` en la capa `store`.
- [ ] No hace falta migración (el esquema no cambia). Confirmarlo en el resumen.
- [ ] `cd 07_MVP/backend && pytest tests -q` en verde. Sin llamadas a la API real de Anthropic.

## Notas
- Para leer números, reutilizar la lectura que ya usa `quantitative` (`_num`) para que el criterio sea el mismo que en los resultados.
- Decisión del usuario: solo entre cerradas.
- Fuera de alcance, pero relacionado: unir columnas ramificadas después de crear el proyecto (el caso de "¿En qué comuna vives?" repartida en 16 columnas). Si el usuario lo pide, va en otra tarea.
