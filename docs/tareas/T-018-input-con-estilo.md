# T-018: Campos de texto sin estilo
Lado: frontend
Requerimientos: RNF-16, RNF-14
Rama: tarea/T-018-input-con-estilo
Depende de: T-012 (fusionada)

## Objetivo
El estilo de los campos en `globals.css` se aplica por tipo (`input[type=...]`). `shared/components/Input.tsx` no pone `type` por defecto, así que un `<Input>` sin `type` se ve como un recuadro nativo del navegador. Hoy pasa en el registro (Nombre y Organización), en la categoría manual del libro de códigos y en el Datacenter de Qualtrics.

## Alcance
- SÍ: en `Input.tsx`, `type` por defecto `"text"` (sin cambiar nada más del componente; un `type` explícito sigue mandando).
- SÍ: quitar los `type="text"` agregados en T-012 en `NewProject.tsx` solo si quedan redundantes (opcional).
- NO: cambiar estilos, otros componentes ni el backend.

## Archivos probables
- Tocar: `src/shared/components/Input.tsx` (y opcionalmente `src/features/projects/NewProject.tsx`).
- No tocar: `07_MVP/backend/**`, `docs/**`.

## Criterios de aceptación
- [ ] `npm run build` sin errores.
- [ ] Los 4 campos (registro: Nombre y Organización; categoría manual: Nombre; Qualtrics: Datacenter ID) se ven con el mismo estilo que los demás. Indica cómo lo verificaste.
- [ ] Commits con el formato `T-018 RNF-16: ...`.

## Revisión
2026-10-30 — **Aprobada** (supervisor).
- Diff de 1 línea en `Input.tsx` (`type="text"` antes de `{...rest}`, un `type` explícito sigue mandando). `npm run build` sin errores.
- Captura del supervisor de `/signup`: los 5 campos con el mismo estilo (Nombre y Organización ahora `type=text`, radio 8 px). El programador verificó además categoría manual y Datacenter de Qualtrics por estilo calculado.
