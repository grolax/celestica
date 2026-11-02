# T-039: Editar el marco teórico después de crear el proyecto (servidor)
Lado: backend
Requerimientos: RF-41, RNF-01, RNF-02, RNF-06
Rama: tarea/T-039-editar-marco (ya creada desde `main`, con el contrato y esta orden; trabaja en ella)
Depende de: —

## Objetivo
Permitir que un analista o administrador cambie el marco teórico de un proyecto ya creado, sin alterar lo que ya se generó y dejando el cambio en la auditoría.

## Alcance
- SÍ: `PATCH /api/projects/{id}` según el contrato, validación y evento de auditoría.
- NO: frontend; recalcular o invalidar categorías, codificaciones o informes; límite de largo al crear el proyecto; versiones del marco; bloquear la edición mientras corre un proceso de IA; cambiar la sugerencia de plantilla.

## Contrato de API
`docs/API_CONTRATOS.md` → "RF-41 · Editar el marco teórico después de crear el proyecto (T-039)".

## Archivos probables
- Se tocan: `07_MVP/backend/app/routers/projects.py`, pruebas nuevas, `test_aislamiento_pytest.py`, `test_permisos_pytest.py` y `07_MVP/COMO_FUNCIONA.md` (un párrafo).
- NO se tocan: `services/thematic.py`, `07_MVP/frontend/**`. `store.py` no debería cambiar: `set_project_field` ya hace el `$set` con filtro de organización.

## Criterios de aceptación
- [ ] El 200 devuelve la forma del contrato y `GET /api/projects/{id}` muestra el marco nuevo, sin espacios en los extremos.
- [ ] El marco puede quedar vacío.
- [ ] Mismo texto (también si solo difiere en los espacios de los extremos): 200, sin escritura ni evento de auditoría.
- [ ] Cada error del contrato tiene su prueba, con el mensaje exacto:
  - 5.000 caracteres pasa y 5.001 no;
  - proyecto sin preguntas abiertas: 400 y el marco no cambia.
- [ ] Evento `cambio_marco_teorico` con `antes`, `despues` y `usuario`. La auditoría solo crece.
- [ ] Una prueba confirma que categorías, codificaciones, léxico e informe siguen iguales después del cambio, y que la IA simulada no se llama.
- [ ] Una prueba confirma que `_v2_analyses_fingerprint` cambia con el marco: el informe profundo no reutiliza análisis hechos con el marco anterior.
- [ ] Permisos y aislamiento:
  - el lector recibe 403;
  - un proyecto de otra organización da 404 y no se modifica;
  - agregar la ruta a `test_aislamiento_pytest.py` y a `test_permisos_pytest.py` (rol mínimo analista).
- [ ] No hace falta migración (el esquema no cambia). Confirmarlo en el resumen.
- [ ] `cd 07_MVP/backend && pytest tests -q` en verde. Sin llamadas a la API real de Anthropic.

## Notas
- Reutilizar `store.set_project_field(project_id, user.org_id, "marco_teorico", ...)`, `store.pregunta_abierta(project)` y `store.log_event`, como las rutas vecinas.
- El límite de 5.000 caracteres se valida después de quitar los espacios. El marco entra en cada llamada a la IA; el más largo guardado hoy tiene 1.566 caracteres.
- No hace falta bloqueo: los procesos en curso ya recibieron su marco como parámetro al empezar.
