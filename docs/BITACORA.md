# Bitácora del supervisor

Cada cambio que hace el supervisor (archivos, ramas, commits, pushes, PR, delegaciones) con su motivo. La entrada más nueva va al final.
Formato: `fecha · qué hice · por qué`.

## 2026-10-14

- Leí `CONTEXTO_SOFTINSIGHT.md`, `COMO_FUNCIONA.md`, `docs/ESTADO.md` y `docs/API_CONTRATOS.md`, y revisé el código (`store.py`, `auth.py`, `main.py`, `App.tsx`) · Para planificar sobre el estado real del código.
- Corrí `pytest tests -q` en `main`: 7 de 14 en rojo por falta de `app/prompts.json` · Para conocer la línea base antes de planificar. No se puede aprobar ninguna tarea con pruebas en rojo.
- Corrí a mano los scripts `test_e2e` y `test_fase1/3/5`: todos pasan · Para confirmar que el aislamiento multi-tenant está bien hoy, aunque pytest no lo ejecute.
- Creé `tasks/plan.md` y `tasks/todo.md` · El usuario pidió el plan de la etapa (comando `/plan`).
- Anoté en `docs/ESTADO.md` las pruebas en rojo, los scripts fuera de pytest y las decisiones pendientes · Es la fuente de verdad del avance.
- Corrí `npm run build` con Vite 8 y React Router 7 (cambios del usuario sin commitear): compila, pero `npm ls` marca `vite invalid` · El usuario decidió mantener esos cambios y había que confirmar que funcionaran.
- Creé la rama `tarea/T-000-deps-frontend` desde `main` · Para que esos cambios queden en una rama propia y no se mezclen con las tareas de backend.
- Registré en `plan.md`, `todo.md` y `ESTADO.md` las decisiones D-1 a D-4 del usuario · Para que queden por escrito antes de delegar.
- Escribí `docs/tareas/T-000-deps-frontend.md` y lo commiteé con los docs (`65c4fc2`) · Porque `@vitejs/plugin-react` 4.x no admite Vite 8 y una instalación limpia (`npm ci`, Vercel) podía fallar.
- Delegué T-000 a `programador-frontend` · Una tarea por programador y por lado, según el ciclo de trabajo.
- Revisé T-000: diff, `npm ls` y `npm run build` en verde · La revisión del supervisor es obligatoria; no basta con el resumen del programador.
- Aprobé T-000, agregué `## Revisión` a la orden y actualicé `ESTADO.md` y `todo.md` (`646c729`) · Todos los criterios se cumplen. La consola del navegador quedó como verificación manual del usuario.
- `git push -u origin tarea/T-000-deps-frontend` · El usuario lo autorizó explícitamente.
- Abrí el PR #1 (https://github.com/grolax/celestica/pull/1) con `gh` desde `C:\Program Files\GitHub CLI\gh.exe` · El usuario instaló `gh` y lo pidió. La ruta completa fue necesaria porque mi terminal aún no tenía `gh` en el PATH.
- `git switch main && git pull` y creé la rama `tarea/T-001-prompts-fallback` · El usuario fusionó el PR #1 y pidió seguir con T-001.
- Escribí `docs/tareas/T-001-prompts-fallback.md`, marqué T-000 como fusionada y T-001 en curso en `ESTADO.md`/`todo.md` (`be63e25`) · Para que el programador tenga la orden y el avance quede registrado.
- Delegué T-001 a `programador-backend` · Es la siguiente tarea del plan: sin pruebas en verde no se puede revisar nada más.
- Creé esta bitácora (`docs/BITACORA.md`) · El usuario pidió un registro de cada cambio y su motivo. La commitearé junto con la revisión de T-001, para no hacer commits mientras el programador trabaja en la misma rama.
- Revisé T-001: diff, `pytest tests -q` (18 passed sin `prompts.json`) y los 4 scripts (TODO OK) · Revisión obligatoria antes de aprobar.
- Agregué `## Revisión 1` a `docs/tareas/T-001-prompts-fallback.md` (con cambios) y devolví la tarea a `programador-backend` · `reset_prompt` copia el default en `prompts.json` y lo congela, así que futuras mejoras de los defaults no llegarían a ese prompt. Es una corrección de una línea más su prueba.
- Revisé la corrección de T-001 (`7042c7f`): diff de 2 líneas, `pytest tests -q` 18 passed sin `prompts.json` y los 4 scripts en TODO OK · Revisión obligatoria de la ronda 1.
- Aprobé T-001: `## Revisión 2` en la orden, T-001 en "Hecho" en `ESTADO.md`, la deuda de pruebas en rojo reemplazada por la de docs de prompts desactualizados, `todo.md` marcado · Todos los criterios se cumplen.
- Commit de los docs de T-001 y de esta bitácora en `tarea/T-001-prompts-fallback` · Los cambios de `docs/` van en la rama de la tarea; esperé a que el programador terminara para no mezclar commits.
