# T-033: Tarjeta "Recomendaciones" en el proyecto
Lado: frontend
Requerimientos: RF-41, RNF-13, RNF-14
Rama: tarea/T-033-tarjeta-recomendaciones
Depende de: T-032 (PR #37; la rama sale de ella)

## Objetivo
Mostrar las recomendaciones de `GET /recommendations` en una tarjeta clara, en lenguaje simple y con una acción por recomendación:
- las alertas de calidad;
- los grupos sugeridos para cruzar, cada uno con su botón "Ver por…";
- la plantilla sugerida.

## Alcance
- SÍ: componente `Recommendations` nuevo (en `features/projects/`), que se muestra:
  - en "Resumen del proyecto" (`ProjectDashboard.tsx`), arriba de la grilla `grid-2`;
  - en "Preguntas cerradas" (`ClosedResults.tsx`), arriba del selector "Ver por…", **solo en proyectos sin preguntas abiertas**, porque esos proyectos no tienen "Resumen" (T-026).
- SÍ: que "Preguntas cerradas" acepte `?por=<pregunta_id>` en la dirección al cargar, para que el botón "Ver por…" de un segmento llegue con ese grupo aplicado.
- SÍ: `getRecommendations` en `features/projects/api.ts` y sus tipos en `types.ts`.
- NO: backend; editar el marco teórico (tarea siguiente); aplicar la plantilla desde la tarjeta (se aplica en "Libro de códigos", que ya tiene el selector); guardar `por` en la dirección al cambiar el selector a mano.

## Contrato de API
`docs/API_CONTRATOS.md` → "RF-41 · Recomendaciones automáticas (T-032)".

## Archivos probables
- Se tocan: `07_MVP/frontend/src/features/projects/Recommendations.tsx` (nuevo), `ProjectDashboard.tsx`, `features/projects/api.ts`, `features/projects/types.ts`, `features/analysis/closed/ClosedResults.tsx`.
- NO se tocan: `07_MVP/backend/**`, `Codebook.tsx`, `NewProject.tsx`.

## Criterios de aceptación
- [ ] Tarjeta `Card` con título "Recomendaciones". Si no hay alertas, ni segmentos, ni plantilla, **no se muestra**. Si la consulta falla, tampoco se muestra (no bloquea la pantalla ni muestra un error).
- [ ] **Alertas:**
  - `importante` usa `alert alert-error`; `aviso` usa `alert alert-warning` (o la clase de aviso que exista en `globals.css`; no crear colores nuevos).
  - El texto es el `mensaje` tal cual, sin `white-space: pre`: los títulos con saltos de línea deben verse en una sola línea.
- [ ] **Segmentos:**
  - Bloque "Cruces sugeridos": el `titulo` (recortado a ~60 caracteres con "…" y el título completo en `title`) y el `motivo`.
  - Botón secundario "Ver por este grupo", que navega a `cerradas?por=<pregunta_id>`, conservando el `?pregunta=` actual si lo hay.
- [ ] **Plantilla:**
  - Bloque "Plantilla sugerida": el nombre, la industria en un `pill` y el `motivo`.
  - Texto: "Puedes aplicarla en «Libro de códigos» y luego modificar sus categorías." Solo para analista y admin (`puede(user, "analista")`), con un botón que lleva a `codigos` conservando `?pregunta=`.
  - El lector no ve el bloque de plantilla.
- [ ] **"Preguntas cerradas" con `?por=`:**
  - Al entrar con `?por=<id>` válido (un id que esté entre las preguntas separables), la primera carga ya viene separada por ese grupo y el selector lo muestra.
  - Con un id inválido o ausente, carga sin separar, como hoy.
  - Cambiar el selector después no necesita tocar la dirección.
- [ ] Usa `Card`, `Button`, `Icon` y las clases de `globals.css`; nada de HTTP fuera de `shared/api/client.ts`. Botones accesibles con teclado. Lenguaje simple, sin jerga.
- [ ] Proyectos con abiertas: la tarjeta en "Resumen". Proyectos sin abiertas: en "Preguntas cerradas". Nunca dos veces en la misma pantalla.
- [ ] `cd 07_MVP/frontend && npm run build` sin errores.
- [ ] Verificación manual con la encuesta real local (`proj_4df733d1c3`, cuenta `t012@prueba.cl` / `Prueba-T012-clave`): la tarjeta muestra 2 alertas, 3 cruces (edad, género, ingreso) y Percepción de Marca, y "Ver por este grupo" en edad abre "Preguntas cerradas" separada por edad. Describe en el resumen lo que viste (capturas en el scratchpad si las tomas, nunca en el repo).

## Notas
- Las recomendaciones son de todo el proyecto, no de una pregunta: `GET /api/projects/{id}/recommendations` no lleva `?pregunta=`.
- Recargar las recomendaciones cuando cambie `project.id`. No hace falta recargarlas al codificar.
- `ProjectView.tsx` ya maneja `useSearchParams` para `pregunta`; en `ClosedResults` basta con leer `por` una vez al montar.

## Revisión 1
2026-11-01 · **Con cambios.**

Lo demás está bien: diff dentro del alcance, contrato respetado, `alert-warning` existente, lector sin plantilla, `?por=` al entrar desde "Resumen" y la línea "(sin IA)", que se acepta.

**Falla: "Ver por este grupo" en proyectos sin preguntas abiertas.**
- `Recommendations.tsx`, `verPor` (líneas ~32-36) navega a `cerradas?…` con una **ruta relativa**.
  - Desde "Resumen" (ruta índice) funciona.
  - Pero en un proyecto sin abiertas la tarjeta se monta **dentro** de `ClosedResults` (ruta `cerradas`), y la ruta relativa resuelve a `/proyectos/<id>/cerradas/cerradas`. Esa ruta no existe y cae en el `*` de `App.tsx`, que redirige a `/`.
- Aunque la dirección fuera correcta, `ClosedResults` solo lee `?por=` al montar (`porUrl` + efecto sobre `project.id`), así que, al estar ya montada, no aplicaría el grupo.

**Se espera:**
- `Recommendations` acepta una prop opcional `onVerPor?: (preguntaId: string) => void`.
  - Si viene, el botón la llama en vez de navegar.
  - `ClosedResults` la pasa con `cambiarPor`, que ya existe, y el resultado se separa en el acto, con el selector actualizado.
- Desde "Resumen" se mantiene la navegación actual.
- Verificación: describe en el resumen cómo comprobaste el botón en un proyecto **sin** abiertas. Puedes crear uno local desde la encuesta real desmarcando las abiertas, como en T-026, o, si ya existe uno, usarlo. No llames a la API real de Anthropic.
- `npm run build` sin errores.
