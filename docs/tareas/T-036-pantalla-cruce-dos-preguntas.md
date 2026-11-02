# T-036: Pantalla del cruce de 2 preguntas y pares sugeridos
Lado: frontend
Requerimientos: RF-31, RF-41, RNF-13, RNF-14
Rama: tarea/T-036-pantalla-cruce-dos-preguntas
Depende de: T-035

## Objetivo
En "Preguntas cerradas", al elegir un "Ver por…", el cliente elige **qué pregunta** quiere ver separada; también puede elegir "Todas". La tarjeta "Recomendaciones" sugiere **pares** y los abre directamente.

## Alcance
- SÍ: selector "Pregunta" en `ClosedResults.tsx`; `ver` en `closedQuery`, por lo que el Excel descarga lo mismo que se ve; la sección "Cruces sugeridos" de `Recommendations.tsx` pasa a usar `cruces`; `?ver=` en la dirección al entrar, junto a `?por=`.
- NO: backend; cambios en alertas o plantilla; vista sin "Ver por…" (sigue mostrando todas las preguntas, como hoy).

## Contrato de API
`docs/API_CONTRATOS.md` → sección T-035.

## Archivos probables
- Se tocan: `features/analysis/closed/ClosedResults.tsx`, `features/analysis/api.ts` (`closedQuery`), `features/analysis/types.ts`, `features/projects/Recommendations.tsx`, `features/projects/types.ts`.
- NO se tocan: `07_MVP/backend/**`, `GroupControls.tsx` (salvo lo imprescindible).

## Criterios de aceptación
- [ ] Sin "Ver por…", la pantalla es igual que hoy: todas las preguntas, sin selector "Pregunta".
- [ ] Con un "Ver por…" elegido, aparece el selector **"Pregunta"** (con `label`), junto al de "Ver por…". Opciones:
  - "Elige una pregunta…" (valor vacío, inicial);
  - "Todas las preguntas";
  - cada pregunta cerrada del proyecto, salvo la del "Ver por…", recortada a ~70 caracteres con el título completo en `title`.
- [ ] Mientras no se elija, no se piden resultados por grupo ni se muestra la lista. Se ve el texto "Elige qué pregunta quieres ver separada por «<título del Ver por>», o «Todas las preguntas»." Los controles de tramos y de unir grupos siguen disponibles.
- [ ] Al elegir una pregunta, se pide `closed-results` con `ver` y se muestra solo esa. Con "Todas las preguntas", se pide sin `ver`, como hoy. Cambiar el "Ver por…" vuelve el selector a "Elige una pregunta…".
- [ ] "Descargar Excel" envía también `ver` cuando hay una pregunta elegida. Sin pregunta elegida y con "Ver por…", el botón queda deshabilitado, con el `title` "Elige una pregunta para descargar".
- [ ] "Cruces sugeridos" en la tarjeta:
  - usa `cruces`: "<por_titulo> × <ver_titulo>" (recortados, con el título completo en `title`) y el `motivo`;
  - el botón "Ver este cruce" navega a `cerradas?por=<por>&ver=<ver>`, conservando `?pregunta=`; dentro de "Preguntas cerradas" aplica ambos en el acto (extender `onVerPor` a `(por, ver)`);
  - si `cruces` viene vacío, se usa `segmentos` como hoy, con "Ver por este grupo", que deja el selector "Pregunta" sin elegir.
- [ ] "Preguntas cerradas" acepta `?por=…&ver=…` al entrar. Un `ver` inválido deja el selector en "Elige una pregunta…".
- [ ] Usa los componentes de `shared/components` y `globals.css`; accesible con teclado; lenguaje simple.
- [ ] `cd 07_MVP/frontend && npm run build` sin errores.
- [ ] Verificación con la encuesta real local (`proj_4df733d1c3`, cuenta `t012@prueba.cl` / `Prueba-T012-clave`) y el proyecto sin abiertas (`proj_08d77f74ba`). Probar: elegir "Ver por" edad y luego una escala; "Todas"; un cruce sugerido desde "Resumen"; y el Excel con `ver`. Si usas puertos del usuario y están libres, apágalos al terminar; no detengas procesos del usuario. Sin IA real.

## Notas
- Decisión del usuario: el cliente elige la pregunta; "Todas" queda como opción.
- Mantener el patrón de `cargar` (contador `ultima`, estado solo tras una carga exitosa) y guardar también `ver` aplicado.
