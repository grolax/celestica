# T-036: Pantalla del cruce de 2 preguntas y pares sugeridos
Lado: frontend
Requerimientos: RF-31, RF-41, RNF-13, RNF-14
Rama: tarea/T-036-pantalla-cruce-dos-preguntas
Depende de: T-035 (PR #40; la rama sale de ella)

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

## Revisión 1
2026-11-01 · **Con cambios.**

Lo demás está bien:
- `ver` en `closedQuery`, compartido con el Excel;
- el Excel queda deshabilitado sin pregunta elegida;
- `?ver=` inválido se ignora;
- los cruces sugeridos y el respaldo con `segmentos` funcionan;
- `npm run build` sin errores.

Se acepta la decisión de pedir una pregunta "sonda" con `ver` para obtener los grupos sin mostrar la lista: calcula una sola pregunta y mantiene disponibles los tramos y "Juntar grupos".

**Falla: cambiar "Pregunta" borra los tramos y grupos unidos aplicados.**
- `ClosedResults.tsx`: el `onChange` de `#ver_pregunta` llama a `aplicar(por, e.target.value)`, que hace `cargar(p, v)` sin `cortes` ni `unir`.
- Si el cliente junta "20-24" con "25-29", o cambia los tramos, y luego elige una pregunta (o pasa a "Todas"), los grupos vuelven a los originales.
- Además, `GroupControls` (con `key={por}`) sigue mostrando la unión anterior, así que la pantalla queda incoherente.

**Se espera:**
- Al cambiar solo "Pregunta", se mantienen los `cortes` y `unir` aplicados, es decir, `cargar(por, v, cortes, unir)`.
- Al cambiar "Ver por…", se reinician, como hoy.
- El Excel sigue reflejando lo que se ve.
- Verificar: con "Ver por" edad, juntar dos tramos, elegir una escala, luego "Todas", luego otra pregunta. Los grupos unidos deben mantenerse en los tres pasos, igual en la pantalla y en la URL del Excel. Lo mismo con tramos de una pregunta numérica, si la hay.
- `npm run build` sin errores. No dejar servidores ni archivos temporales.

## Revisión 2
2026-11-01 · **Aprobada.**
- Corrección mínima: `cambiarPregunta(v)` llama `cargar(por, v, cortes, unir)`; "Ver por…" sigue reiniciando.
- Verificación del supervisor en Chrome, con la encuesta real local (`proj_4df733d1c3`), los servidores levantados en 8000/5173 y apagados al terminar:
  - **Dashboard:** 5 botones "Ver este cruce". El tercero abre `cerradas?por=q_3&ver=q_12` con ambos selectores aplicados y 1 tarjeta.
  - **Ver por edad:** "Elige una pregunta…", 0 tarjetas, el mensaje de ayuda y el Excel deshabilitado.
  - **Juntar "20-24" y "25-29" como "Jóvenes"** y pasar por q_12, "Todas" y q_23: 1, 28 y 1 tarjetas, con la unión intacta en pantalla y en cada petición.
  - **Excel:** pide `closed-xlsx?por=q_2&ver=q_23&unir=[…]` y el nombre incluye la pregunta.
  - Sin errores de JS.
- Para más adelante (UX, no bloquea): con "Juntar grupos" abierto, los controles ocupan mucho espacio antes de los resultados.
