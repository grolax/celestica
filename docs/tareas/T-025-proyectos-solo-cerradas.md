# T-025: Proyectos sin preguntas abiertas (servidor)
Lado: backend
Requerimientos: RF-24, RNF-01, RNF-02, RNF-21
Rama: tarea/T-025-proyectos-solo-cerradas
Depende de: T-020 a T-024 (fusionadas)

## Objetivo
Se puede crear un proyecto con solo preguntas cerradas, abrirlo (`GET /api/projects/{id}`) y verlo en la lista con su número de personas. Las operaciones de análisis de preguntas abiertas responden 404 en esos proyectos, sin llamar a la IA. Los proyectos con abiertas no cambian.

## Decisiones del usuario
- RF-24 va en la iteración 3 junto con RF-30 (2026-10-30).

## Alcance
- SÍ: implementar el contrato **RF-24 · Proyectos sin preguntas abiertas (T-025)** de `docs/API_CONTRATOS.md`, al pie de la letra (mensaje de error exacto incluido).
- SÍ: `_armar_preguntas` / `_create_project_from_df` en `routers/projects.py`; `get_project` (sin `?pregunta` y sin abiertas, responde la forma del contrato en vez de 404); `store.list_projects` (`n_abiertas`, y `n_responses` = personas cuando no hay abiertas, calculado en el pipeline de Mongo como hoy).
- SÍ: que `routers/integrations.py` (Qualtrics y Google Forms) herede el cambio por el camino común, sin duplicar lógica.
- NO: informe o exportación de cerradas (decisión pendiente del usuario); cambiar el camino de compatibilidad sin `preguntas`; cambios en el frontend; migración (los proyectos existentes tienen abiertas).

## Contrato de API
`docs/API_CONTRATOS.md`, sección **RF-24 · Proyectos sin preguntas abiertas (T-025)**.

## Archivos probables
- Tocar: `app/routers/projects.py`, `app/store.py` (solo `list_projects` y lo mínimo para la vista sin abiertas), pruebas en `tests/` (nuevo archivo o los existentes de creación), y una línea en `07_MVP/COMO_FUNCIONA.md`.
- No tocar: `07_MVP/frontend/**`, `docs/**`, `services/thematic.py`, `services/quantitative.py`.

## Criterios de aceptación
- [ ] `pytest tests -q` en verde. Las pruebas existentes que esperaban el 400 "no tiene preguntas abiertas" se actualizan al nuevo comportamiento (y se explica cuáles en el resumen).
- [ ] Pruebas nuevas (mongomock, sin IA):
  - crear con `preguntas` sin abiertas (archivo, y al menos uno de Qualtrics o Google Forms con la integración simulada como en las pruebas existentes) → 200 con la forma del contrato; el evento de auditoría con `n_respuestas` y `columna_texto: null`;
  - con `template` y sin abiertas → marco guardado, sin categorías;
  - sin abiertas ni cerradas (por ejemplo, solo `identificador` y `fecha`) → 400 con el mensaje exacto;
  - `GET /api/projects/{id}` sin abiertas → forma del contrato con `pregunta: null`; con `?pregunta=q_1` → 404;
  - `GET /api/projects` → `n_abiertas` correcto en proyectos con 0, 1 y 2 abiertas; `n_responses` = personas sin abiertas;
  - en un proyecto sin abiertas, al menos léxico, codificación (con la IA simulada que falle la prueba si se llama), informe, resumen y una exportación → 404 "Pregunta no encontrada";
  - `closed-results` con y sin `por` funciona en ese proyecto; lector puede abrirlo; otra organización → 404.
- [ ] Un proyecto con abiertas se crea y se abre exactamente como antes (las pruebas existentes lo cubren).
- [ ] Commits con el formato `T-025 RF-24: ...`.

## Notas
- Al terminar, deja el backend (8000) corriendo con el código nuevo (usa `SECRET_KEY=dev-local-secret-t021` para que las cuentas de prueba sigan valiendo).
