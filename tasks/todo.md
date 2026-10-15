# Lista de tareas

Detalle y criterios en `tasks/plan.md`. Cada tarea, al delegarse, se convierte en `docs/tareas/T-<n>-<slug>.md`.

## Decisiones (resueltas 2026-10-14)
- [x] D-1 Mantener Vite 8 / React Router 7 → T-000
- [x] D-2 Un usuario = una organización
- [x] D-3 Sí a T-006
- [x] D-4 Matriz de permisos aprobada

## Fase 0 — Línea base en verde
- [x] T-000 frontend · consolidar Vite 8 + React Router 7 (plugin-react compatible, `npm ci` limpio) — aprobada
- [x] T-001 backend · `prompt_store` funciona sin `prompts.json` (suite 18/18 en clon limpio) — aprobada
- [ ] T-002 backend · scripts `test_e2e`/`test_fase*` corren dentro de pytest
- [ ] **Checkpoint 0** — suite completa en verde en `main`

## Fase 1 — Organizaciones, roles y asistente
- [ ] T-003 backend · separar `main.py` en routers (RNF-17), sin cambios de comportamiento
- [ ] C-01 supervisor · contrato de auth con `org`/`rol`, `GET /api/org`, 403 y matriz de permisos
- [ ] T-004 backend · organizaciones y tenant por `org_id` + `migrate_orgs.py` (RF-02)
- [ ] T-005 backend · roles y `require_role` (RF-03)
- [ ] T-006 backend · gestión mínima de miembros (RF-04 parcial) 
- [ ] T-007 frontend · navegación y acciones según rol
- [ ] T-008 frontend · asistente de creación en 4 pasos contra la API actual (RF-40)
- [ ] **Checkpoint 1** — migración probada sobre copia de base real; re-planificar Fase 2 y diseñar RF-23

## Fase 2 — Modelo de preguntas
- [ ] C-02 supervisor · contrato de vista previa y `questions[]`
- [ ] T-009 backend · detector de tipos + `POST /api/imports/preview` (RF-22, RF-25)
- [ ] T-010 backend · `projects.questions[]`, proyectos sin abiertas, migración (RF-22, RF-24)
- [ ] T-011 backend · varias preguntas abiertas por proyecto (RF-23) — diseño previo
- [ ] T-012 frontend · paso "revisar preguntas detectadas" con API real (RF-25)
- [ ] T-013 frontend · selector de pregunta en pestañas de análisis (RF-23, RF-24)
- [ ] **Checkpoint 2** — re-planificar Fase 3

## Fases 3–5 (se detallan en su checkpoint)
- [ ] Fase 3: RF-30, RF-31, RF-17 · RF-43, RF-41
- [ ] Fase 4: RF-10, RF-11, RF-12 · RF-10/RF-13 UI
- [ ] Fase 5: RF-51, RNF-12 · RF-42, RF-45, Playwright
