# T-045: Paso "Elige una plantilla" en el asistente de creación
Lado: frontend
Requerimientos: RF-40, RF-41, RNF-13, RNF-14
Rama: tarea/T-045-paso-plantilla (ya creada desde `main`, con esta orden; trabaja en ella)
Depende de: T-044 (fusionada, PR #51)

## Objetivo
"Nuevo proyecto" pasa a tener 4 pasos. El tercero, "Elige una plantilla", muestra la plantilla sugerida y su motivo, y permite usarla, elegir otra o seguir sin plantilla. Cada paso se explica con su propio texto de ayuda.

## Alcance
- SÍ: el paso nuevo, la llamada a `suggest-template`, los textos de ayuda, el arreglo del marco al cambiar de plantilla y las tarjetas de plantilla operables con teclado.
- NO: backend; cambios en `QuestionReview`; pedir el "objetivo" de la encuesta; marcar la plantilla sugerida por defecto; crear plantillas propias; aplicar categorías a más de una pregunta abierta; refactors de otros archivos.

## Contrato de API
`docs/API_CONTRATOS.md`, sección "RF-40 · Plantilla sugerida al crear el proyecto (T-044)". El cuerpo lleva solo `titulo` y `tipo`.

## Archivos probables
- Se tocan: `07_MVP/frontend/src/features/projects/NewProject.tsx`, `07_MVP/frontend/src/features/projects/api.ts`, `07_MVP/frontend/src/styles/globals.css` (solo `.template-option`).
- No se tocan: `07_MVP/backend/**`, `QuestionReview.tsx`, `questionGroups.ts`, `shared/components`.

## Comportamiento

**Pasos:** 1 "Sube tu encuesta", 2 "Revisa las preguntas", 3 "Elige una plantilla", 4 "Datos del proyecto".
- Si ya se revisaron las preguntas y ninguna abierta quedó incluida (`hayAbierta(filas)` falso), el paso 3 no aparece en la barra y no se pasa por él: "Continuar" y "Volver" saltan entre 2 y 4. En el paso 1, la barra muestra los 4.
- Solo el último paso crea el proyecto. Enter nunca crea desde el paso 3.

**Texto de ayuda por paso** (`help` de `PageHeader`):
1. "Sube el archivo de tu encuesta o impórtala desde Qualtrics o Google Forms."
2. "Revisa qué detectamos en cada pregunta y corrige lo que no calce."
3. "Una plantilla trae un enfoque de análisis y categorías de partida, que tu equipo revisa antes de usarlas."
4. "Ponle nombre a tu proyecto y confirma qué se va a analizar."

**Sugerencia:** al apretar "Continuar" en el paso 2 con alguna abierta incluida, se llama a `projectsApi.suggestTemplate` con las preguntas incluidas (`aPreguntas(filas)`, solo `titulo` y `tipo`) y el botón queda ocupado mientras tanto. Se llama cada vez, porque las preguntas pudieron cambiar. Si falla, se sigue sin sugerencia y sin mostrar error.

**Contenido del paso 3:** se mueve aquí la tarjeta "Marco teórico" completa; "Datos del proyecto" queda con el nombre y el resumen.
- **Con sugerencia:** tarjeta "Te sugerimos esta plantilla" con nombre, industria, `motivo`, y descripción y número de categorías si la plantilla está en la lista. **No viene marcada.** Botón "Usar esta plantilla"; una vez usada, indica que está elegida y ofrece "Quitar plantilla".
- **Sin sugerencia:** "No encontramos una plantilla que calce claramente con tu encuesta. Puedes elegir una de la lista o continuar sin plantilla."
- **Lista de las demás:** con sugerencia queda plegada tras un botón "Ver otras plantillas" (`aria-expanded`); sin sugerencia queda abierta. Sigue agrupada por industria.
- Bajo la lista queda el campo del marco teórico, con esta nota: "Elegir otra plantilla cambia este texto, salvo que lo hayas editado."
- Se puede avanzar con "Continuar →" sin elegir plantilla, y volver con "← Volver".

**Arreglo del marco:** al elegir, cambiar o quitar una plantilla:
- Si el marco está vacío o es idéntico al de la plantilla elegida hasta ese momento, pasa a ser el de la nueva plantilla (o queda vacío al quitarla).
- Si la persona lo editó, no se toca.

**Teclado:** cada tarjeta de plantilla es un `<button type="button">` con `aria-pressed`, no un `div` con `onClick`. Adentro solo puede haber contenido válido para un botón: usa `span` con `display: block` en vez de `p` y `div`. Conserva el aspecto actual, con texto a la izquierda y ancho completo.

## Criterios de aceptación
- [ ] Encuesta con abiertas: se ven 4 pasos y la sugerencia con su motivo, sin marcar.
- [ ] "Usar esta plantilla" la marca y carga su marco; "Quitar plantilla" deja todo como antes.
- [ ] Elegir otra plantilla cambia el marco si no se editó, y lo respeta si se editó.
- [ ] Sin plantilla, el proyecto se crea sin categorías de plantilla. Con plantilla, se envía `template` como hoy.
- [ ] Encuesta sin abiertas: no se ve el paso 3, no se llama a `suggest-template`, y Continuar y Volver saltan de 2 a 4 y de 4 a 2.
- [ ] Si la pregunta cambia de tipo tras volver al paso 2, la sugerencia se recalcula.
- [ ] Si `suggest-template` falla, se puede seguir y crear el proyecto.
- [ ] El error "Volver a revisar las preguntas" sigue funcionando desde el último paso (hoy depende de `step === 3`).
- [ ] Las tarjetas se eligen con Tab y Enter o Espacio, y muestran el foco.
- [ ] Usa `shared/api/client.ts`, los componentes de `shared/components` y las variables de `globals.css`.
- [ ] `npm run build` sin errores.
- [ ] Sin regresiones de aislamiento multi-tenant: no cambia el backend.

## Notas
- Decisiones del usuario (2026-11-10): paso propio y plantilla sin marcar.
- `crear()` ya no envía `template` ni marco sin abiertas: mantenlo.
- Los servidores locales de desarrollo están corriendo en los puertos 8000 y 5173: no los detengas ni levantes otros. El supervisor recorre la pantalla en el navegador; a ti te basta con `npm run build`.
- Limitación existente, no la cambies: el servidor aplica las categorías de la plantilla solo a la primera pregunta abierta.

## Revisión
2026-11-10 · **Aprobada.**
- Commit `885acbf`: 3 archivos de frontend, 131 líneas agregadas y 56 quitadas. No toca backend ni `shared/components`.
- `npm run build` sin errores. `python -m pytest tests -q`: 423 pasan.
- Verificación del supervisor en Chrome headless, con backend y base desechables ya borrados y sin IA: 44 de 45 comprobaciones. Cubren los 4 pasos y sus textos, sugerencia sin marcar, usar y quitar, teclado (Tab, Enter y Espacio con foco visible), marco editado respetado, recálculo, falla de `suggest-template`, creación con y sin plantilla (revisada en la API), "Volver a revisar las preguntas" y encuesta sin abiertas.
- **La comprobación que falló no es de esta tarea:** a 375 px solo se sale de la pantalla el usuario de la barra superior, también en "Mis proyectos" (deuda ya anotada desde T-021). El contenido del paso cabe.
- Contrato: el cuerpo lleva solo `titulo` y `tipo`. Usa `shared/api/client.ts`.
- Decisiones del programador aceptadas: la sugerida no se repite en la lista; la lista se abre sola si la plantilla elegida deja de ser la sugerida; "Quitar plantilla" va solo en la tarjeta sugerida, y las de la lista se quitan con otro clic. La sugerencia no se marca como IA porque sale de reglas fijas.
- No probado: una encuesta real, Qualtrics y Google Forms (comparten el mismo flujo desde el paso 2) y tablet física.
