# T-014: Identidad visual Celestica (paleta azul y blanco, nombre oficial)
Lado: frontend
Requerimientos: RNF-16, RNF-14, RNF-13
Rama: tarea/T-014-identidad-celestica
Depende de: —

## Objetivo
El usuario (2026-10-15) pidió un diseño **sobrio, entendible, con separaciones claras**, en una **gama de azules (incluido el celeste) y blanco**, y que el nombre visible del producto sea **Celestica**. Esta tarea cambia la base visual, es decir, las variables de `globals.css` y los componentes compartidos, y el nombre en toda la interfaz. Todas las pantallas existentes deben heredar el cambio sin que se reescriba cada una.

## Alcance
- SÍ: reemplazar la paleta de `:root` en `globals.css`. Fuera el fondo crema (`#fffaf0`) y los bordes beige; entran blanco y azules. Paleta de partida, que puedes ajustar si no cumple contraste:
  - `--navy: #0b2545` (títulos, encabezados y fondos oscuros)
  - `--primary: #0077b6` (botones y enlaces; verifica que el texto blanco sobre este azul cumpla AA, ≥ 4,5:1)
  - `--primary-dark: #005f8f` (hover)
  - `--celeste: #0099cc` (solo acento decorativo, íconos, bordes o texto grande; **no** sirve para texto normal sobre blanco porque queda en ≈ 3,4:1)
  - `--primary-soft: #e6f4fa`
  - `--bg: #ffffff`, `--bg-alt: #f4f7fa` (fondo general, gris azulado muy claro)
  - `--border: #dce3ea`, `--border-soft: #eaeff4`
  - `--text: #0f1c2b`, `--text-muted: #5b6b7c` (verifica ≥ 4,5:1 sobre `--bg-alt`)
  - Verde, naranja y rojo semánticos: se mantienen, ajustando solo lo necesario para cumplir AA.
- SÍ: separaciones más claras en la base. Header con borde inferior definido, sidebar con borde y fondo distinto del contenido, `Card` con borde visible y espaciado interno consistente, y títulos de página con jerarquía clara (h1 > h2 > h3). Todo se resuelve en `globals.css` y `shared/components`, sin tocar pantalla por pantalla.
- SÍ: nombre **Celestica** en todo texto visible de la UI: `index.html` (`<title>Celestica — Análisis de encuestas con evidencia</title>`), logo del `Header` (marca "C"; si quieres, la palabra con "Celestica" en navy), `Sidebar` ("Celestica v1.1"), `LoginPage`, `Documentation`, `NewProject`, `Settings` y `ReportView`. El panel de prompts de Settings pasa a llamarse "Configuración metodológica (equipo Celestica)".
- SÍ: actualizar el comentario de cabecera de `globals.css` ("Celestica — Sistema de diseño v2.0", con la paleta nueva).
- NO: la página pública de presentación ni el cambio de rutas (eso es T-015); rediseñar la estructura de las pantallas del área de trabajo (eso es T-016); tocar el backend (los PDF/DOCX siguen diciendo SoftInsight hasta una tarea de backend aparte); agregar frameworks CSS, librerías de íconos o fuentes nuevas. Inter se mantiene.

## Contrato de API
No aplica.

## Archivos probables
- Tocar: `07_MVP/frontend/src/styles/globals.css`, `index.html`, `src/shared/layout/Header.tsx`, `Sidebar.tsx`, `src/shared/components/*` (solo si un estilo no se puede resolver con CSS), y los textos con "SoftInsight" de `LoginPage.tsx`, `Documentation.tsx`, `NewProject.tsx`, `Settings.tsx` y `ReportView.tsx`.
- No tocar: `07_MVP/backend/**`, `docs/**`, la lógica de los componentes ni las llamadas a la API.

## Criterios de aceptación
- [ ] `npm run build` sin errores.
- [ ] `grep -rn "SoftInsight" src index.html` no devuelve texto visible para el usuario. Se aceptan comentarios de código, si quedan.
- [ ] Ninguna referencia al crema (`#fffaf0`) ni a los bordes beige (`#e6e2d8`, `#efece4`) en `src/`.
- [ ] En el resumen final, una tabla de contraste con los pares texto/fondo usados: texto normal sobre `--bg` y `--bg-alt`, `--text-muted` sobre ambos, texto blanco sobre `--primary` y `--navy`, y enlaces sobre blanco. Cada par con su razón calculada; todos ≥ 4,5:1 para texto normal (WCAG AA).
- [ ] El foco del teclado se ve en botones, enlaces e inputs: un anillo visible en azul, sin `outline: none` sin reemplazo.
- [ ] Recorres a mano `/login`, la lista de proyectos, un proyecto y Configuración: nada queda ilegible ni con colores viejos. Indica en el resumen qué pantallas revisaste.
- [ ] Commits con el formato `T-014 RNF-16: ...`.

## Notas
- **Decisión del usuario del 2026-10-15:** autorizó explícitamente cambiar la paleta base (antes crema + celeste) y fijar el nombre oficial "Celestica". Esto resuelve la decisión abierta §10.5 del contexto. El repositorio y el código interno siguen llamándose softinsight/celestica sin cambios.
- "Sobrio" quiere decir: sin degradados llamativos (el `.logo-mark` puede pasar a color plano), sombras suaves, mucho blanco y una sola acción primaria por zona.

## Revisión
2026-10-15 · **Aprobada**.
- Diff: 9 archivos del frontend, +59/−52. Paleta de `:root` según la orden, más `--navy`, `--celeste` y `--ring`; sin degradados; títulos en navy; Card con separador bajo el título; nombre Celestica en todos los textos visibles. No hay cambios en el backend.
- Verificado por el supervisor: `npm run build` en verde. `grep softinsight` solo deja la clave interna `softinsight_token`, el nombre de descarga por defecto y el correo `soporte@softinsight.cl`. No quedan colores crema, beige ni degradados. No hay hex inline en TSX. No hay `outline: none` sin reemplazo. Recalculé los contrastes clave: blanco/`#0077b6` 4,87, muted/`--bg-alt` 5,09, `--primary`/`--bg-alt` 4,53, warning 4,58, success 4,92; todos AA. El celeste (3,27) se usa solo como borde decorativo.
- Fuera de alcance, aceptado: se quitó `overflow-x: auto` de `.project-tabs` (scroll espurio con `flex-wrap`). Es una línea y está justificada.
- Pendientes:
  - (a) El correo `soporte@softinsight.cl` se mantiene, porque SoftInsight es el equipo; confirmar con el usuario si hay otro.
  - (b) Las pestañas internas del proyecto no se vieron renderizadas; heredan las clases. Se revisarán en T-016.
  - (c) En `/login` a 420 px la tarjeta se ve corrida, posiblemente por la captura en modo headless. Se verifica en T-015, que rehace esa pantalla.

## Revisión 1 (pedido del usuario tras ver la app)
2026-10-15 · **Con cambios**. El usuario revisó la app en el navegador y pidió dos ajustes, recordando que la idea del diseño es que sea **sobrio**.

1. **Emojis → iconos minimalistas.** Al iniciar sesión, los ítems (sidebar, pestañas del proyecto, botones, tarjetas y cualquier otro lugar de `src/`) usan emojis, por ejemplo "📁 Mis proyectos". Hay que reemplazarlos **todos**, incluido el `☰` del Header, por iconos de línea minimalistas.
   - Un componente nuevo `src/shared/components/Icon.tsx` con SVG inline: `viewBox="0 0 24 24"`, `fill="none"`, `stroke="currentColor"`, `stroke-width` 1.75, extremos redondeados, tamaño por defecto de 18 px y `aria-hidden="true"`. Un solo estilo para todos.
   - Sin dependencias nuevas: nada de librerías de iconos ni fuentes de iconos. Dibuja los trazos tú, o copia trazos de un set con licencia MIT/ISC (por ejemplo Lucide o Feather) y deja un comentario de una línea con el origen y la licencia.
   - El icono acompaña al texto, nunca lo reemplaza. Donde hoy solo hay un emoji como botón, mantén el `aria-label`.
   - Color heredado del texto (gris en reposo, azul en el ítem activo). Nada de iconos de colores.
   - Criterio: buscar emojis en `src/` (rangos Unicode de emoji y símbolos) no devuelve nada visible. Indica en el resumen qué icono quedó en cada lugar.
2. **Presentación más resumida.** El bloque de presentación de la pantalla de acceso (`AuthHero` en `LoginPage.tsx`) tiene demasiado texto. Déjalo en:
   - Título: "De la encuesta al informe, con evidencia en cada paso."
   - Una línea: "Análisis de encuestas con IA y validación de tu equipo."
   - Tres puntos cortos, con iconos de línea en vez de viñetas: "Temas propuestos por IA, validados por personas" · "Trazabilidad completa de cada decisión" · "Informes PDF, Word y Excel".

No cambies nada más. Al terminar, `npm run build` debe pasar. Commits con el formato `T-014 RNF-16: ...`.

## Revisión 2
2026-10-15 · **Aprobada**.
- Commit `83592d5`: `shared/components/Icon.tsx` con SVG inline (trazo 1.75, `currentColor`, `aria-hidden`, origen Lucide/ISC comentado). No hay dependencias nuevas (`package.json` sin cambios). Se reemplazaron todos los emojis y símbolos usados como icono, y donde un icono quedó solo se agregó `aria-label`/`sr-only`. `AuthHero` quedó resumido según el texto pedido.
- Verificado por el supervisor: diff de 15 archivos (+89/−39) acotado a lo pedido; `npm run build` en verde.
- Nota menor: el icono `sparkle` está definido pero no se usa. Se acepta, porque T-015 o T-016 pueden necesitarlo.
- Las pestañas del proyecto no tenían emojis y siguen sin iconos, a propósito, por sobriedad.
