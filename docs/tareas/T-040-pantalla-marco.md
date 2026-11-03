# T-040: Editar el marco teórico (pantalla)
Lado: frontend
Requerimientos: PED-01 (`docs/BACKLOG.md`), RF-41, RNF-13, RNF-14
Rama: tarea/T-040-pantalla-marco (ya creada desde `main`, con esta orden; trabaja en ella)
Depende de: T-039 (fusionada, PR #45)

## Objetivo
En el resumen del proyecto, cualquiera puede leer el marco teórico completo, y un analista o administrador puede editarlo sin recargar la página. Antes de guardar se avisa qué pasa con lo ya generado. En Auditoría, el cambio se ve completo.

## Alcance
- SÍ: una tarjeta "Marco teórico" en `ProjectDashboard.tsx`, justo después del bloque `grid-2`, como componente nuevo `features/projects/MarcoTeorico.tsx`.
- SÍ: `projectsApi.updateMarco(id, marco_teorico)` en `features/projects/api.ts`.
- SÍ: en `AuditLog.tsx`, mostrar completo el detalle de los eventos `cambio_marco_teorico`. Hoy `JSON.stringify(e.detail).slice(0, 300)` corta el texto, y `usuario`, que va al final, puede quedar oculto.
- SÍ: en `Recommendations.tsx`, agregar `project.marco_teorico` a las dependencias del `useEffect` de la línea 65. La plantilla sugerida depende del marco y, sin esto, queda desactualizada tras guardar.
- NO: backend; historial de versiones; bloquear la edición mientras corre un proceso de IA; cambiar la línea corta del marco en `ProjectView.tsx`; cambiar el detalle de otros eventos de auditoría; volver a aplicar el marco de una plantilla.

## Contrato de API
`docs/API_CONTRATOS.md` → "RF-41 · Editar el marco teórico después de crear el proyecto (T-039)". El contrato no cambia.

## Archivos probables
- Se tocan: `features/projects/MarcoTeorico.tsx` (nuevo), `features/projects/ProjectDashboard.tsx`, `features/projects/api.ts`, `features/projects/Recommendations.tsx`, `features/analysis/audit/AuditLog.tsx`.
- NO se tocan: `07_MVP/backend/**`, `shared/components/**`, `globals.css` salvo que falte algo imprescindible (explícalo en tu resumen).

## Criterios de aceptación
**Lectura**
- [ ] La tarjeta muestra el marco completo, respetando los saltos de línea (`white-space: pre-wrap`).
- [ ] Sin marco, muestra: "Este proyecto no tiene marco teórico. La IA busca los temas directamente en las respuestas."
- [ ] El lector ve la tarjeta, pero no el botón "Editar".
- [ ] En un proyecto sin preguntas abiertas no aparece: esos proyectos no montan el resumen. Confírmalo en la verificación, sin agregar código para esto.

**Edición (solo con `puede(user, "analista")`)**
- [ ] "Editar" abre un `TextArea` con etiqueta, con el marco actual y el foco puesto en él. El teclado basta para todo el flujo.
- [ ] Muestra un contador, por ejemplo "1.234 de 5.000 caracteres", sobre el texto sin espacios en los extremos. **No usa `maxLength`:** cortaría sin avisar un texto pegado.
- [ ] Antes de guardar, se ve este aviso: "Lo que ya se generó (categorías, codificación e informes) no cambia. El marco nuevo se usa desde el próximo trabajo con IA y vale para todas las preguntas abiertas del proyecto. El próximo informe profundo volverá a gastar IA, porque debe rehacer sus análisis con este marco."
- [ ] "Guardar" queda deshabilitado mientras guarda y si el texto no cambió (ignorando los espacios de los extremos). "Cancelar" cierra el editor sin guardar.
- [ ] Al guardar bien: se llama a `refresh()`, el editor se cierra y la tarjeta y la línea corta del encabezado muestran el marco nuevo, sin recargar la página. Se puede dejar vacío.
- [ ] Si el servidor responde con error (por ejemplo, más de 5.000 caracteres), se muestra su mensaje junto al editor, anunciado a lectores de pantalla (`role="alert"`). El editor sigue abierto y **el texto no se pierde**.

**Auditoría**
- [ ] Cada evento `cambio_marco_teorico` muestra completos, sin cortar y con saltos de línea, "Antes", "Después" y "Por" (`detail.antes`, `detail.despues`, `detail.usuario`). Un texto vacío se muestra como "(vacío)".
- [ ] Los demás eventos se ven igual que hoy.

**Recomendaciones**
- [ ] Tras guardar un marco, la tarjeta "Recomendaciones" se actualiza sin recargar la página.

**General**
- [ ] Usa `shared/api/client.ts`, los componentes `Card`, `Button` y `TextArea`, y las variables de `globals.css`.
- [ ] `cd 07_MVP/frontend && npm run build` sin errores.
- [ ] Verificación en el navegador, sobre una **base desechable**, para no sumar eventos permanentes a la auditoría de tu base local:
  - levanta el backend con `MONGODB_URI=mongodb://localhost:27017/softinsight_t040`, y confirma que realmente usa esa base;
  - crea ahí una cuenta admin, un miembro lector y dos proyectos con los datos de ejemplo: uno con abiertas y otro solo con cerradas;
  - recorre todos los criterios de arriba, incluidos un marco de 5.001 caracteres y uno vacío;
  - al terminar, borra la base `softinsight_t040` y apaga los servidores. No dejes archivos temporales.
  - **Sin IA real:** no pulses ningún botón que analice, codifique o genere informes.

  Reporta lo que viste, criterio por criterio.

## Notas
- Decisiones del usuario (2026-11-02): el marco es propio de cada proyecto; editarlo no toca lo ya generado; máximo 5.000 caracteres; no se edita en proyectos sin abiertas.
- El límite lo valida el servidor. No dupliques su mensaje en la pantalla.
- Si el texto no cambió, el servidor responde 200 sin registrar nada; por eso "Guardar" queda deshabilitado en ese caso.
- `TextArea` no asocia `error` con el campo mediante `aria-describedby`. No lo modifiques aquí: usa un `alert alert-error` con `role="alert"` dentro de la tarjeta.

## Revisión 1
2026-11-02 · **Con cambios (una observación).** El resto del diff está bien.

**`features/projects/MarcoTeorico.tsx`, línea de `abrir` y `disabled` de "Guardar": un marco con saltos de línea de Windows se ve como modificado sin estarlo.**
- **Causa:** al crear el proyecto, el marco viaja en un `FormData`, y el navegador convierte sus saltos de línea a `\r\n`. El servidor lo guarda así (comprobado: `'Linea uno\r\nLinea dos'`; también está en 1 de los 25 proyectos de la base local). El `textarea` entrega siempre `\n`, así que tras cualquier edición el texto ya no es igual a `project.marco_teorico`.
- **Cómo se reproduce:** crea un proyecto con un marco de dos líneas desde el formulario, pulsa "Editar" y agrega un espacio al final.
- **Qué falla:**
  - "Guardar" se habilita aunque el texto no cambió.
  - Al guardar, el servidor lo toma como distinto y registra un `cambio_marco_teorico` sin cambio real. La auditoría solo crece, así que ese evento no se puede quitar.
  - Antes de editar, el contador cuenta cada salto de línea como 2 caracteres.
- **Qué se espera:** normaliza `\r\n` a `\n` en un solo lugar de `MarcoTeorico.tsx`, tanto para el texto inicial del editor como para la comparación de "Guardar". El marco mostrado en la tarjeta y el evento de auditoría no cambian.
- **Verificación:** basta con `npm run build`. El supervisor repite la prueba en el navegador; los puertos 8000 y 5173 ya están ocupados por sus servidores, así que no levantes otros.

No toques el backend: guardar `\r\n` al crear queda como deuda técnica.
