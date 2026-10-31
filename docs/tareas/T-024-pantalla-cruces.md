# T-024: Pantalla de cruces por grupo
Lado: frontend
Requerimientos: RF-31 (UI), RNF-07, RNF-13, RNF-14, RNF-15
Rama: tarea/T-024-pantalla-cruces
Depende de: T-021, T-022 y T-023 (fusionadas)

## Objetivo
En la pestaña "Preguntas cerradas", el usuario elige **"Ver por…"** un grupo (género, edad, comuna…) y cada pregunta muestra una tabla compacta que compara los grupos, con aviso de pocos datos. Si el grupo es una numérica (edad como número), puede editar los tramos. Si es una pregunta de grupos, puede **juntar grupos** con un nombre propio. Nada se guarda: vale solo para ese análisis.

## Decisiones del usuario (2026-10-31)
- Disposición aprobada: selector "Ver por…" arriba; tabla por pregunta con los grupos como filas; aviso visible en grupos con pocos datos; tramos editables si la edad es numérica; juntar grupos marcando, nombrando y aplicando, con deshacer.
- Los tramos y las uniones valen solo para ese análisis (no se guardan).
- Umbral de pocos datos: el que manda el backend (`umbral_pocos_datos`, hoy 10).

## Alcance
- SÍ: `analysisApi.getClosedResults(id, opciones?)` con `por`, `cortes` y `unir` opcionales (`unir` = `JSON.stringify` de la lista, codificado con `encodeURIComponent`). Tipos nuevos según el contrato: `por`, `umbral_pocos_datos`, `n_sin_grupo`, `grupos[]` (con `unidos?`), y `por_grupo[]` en cada pregunta.
- SÍ: **selector "Ver por"** (un `<select>` con etiqueta) arriba de las tarjetas, con la opción **"Todas las personas (sin separar)"**, que es la de por defecto, y las preguntas del proyecto de tipo `segmento`, `seleccion_unica`, `si_no` y `numerica` (de `project.preguntas`, título recortado y completo en `title`). Sin grupo elegido, la pantalla queda **exactamente como hoy**. El estado vive en el componente (no en la URL ni en el almacenamiento).
- SÍ: con un grupo elegido, bajo el selector:
  - "Separado por: <título>. <N> grupos." y, si `n_sin_grupo` > 0: **"<n> personas no respondieron esta pregunta y no aparecen en ningún grupo."**
  - Si algún grupo tiene `pocos_datos`: **"Los grupos marcados con «Pocos datos» tienen menos de <umbral> personas: tómalos con cautela."**
- SÍ: con un grupo elegido, cada tarjeta muestra la línea de respuestas de siempre y, en vez de las barras, una **tabla** (`Table` de `shared/components`) con una fila **"Todas las personas"** (los valores del total) y una fila por grupo, en el orden de `grupos`. En los grupos con `pocos_datos`, junto al nombre va una píldora **"Pocos datos"** (texto, no solo color). Los grupos unidos muestran sus `unidos` en `title` o en texto pequeño. Columnas según el tipo:
  - `escala`: Grupo · Respondieron · Promedio · Notas altas (x y y) · Notas bajas (x y y).
  - `nps`: Grupo · Respondieron · NPS (con signo) · Promotores · Detractores.
  - `numerica`: Grupo · Respondieron · Promedio · Mediana · Mínimo · Máximo.
  - Categóricas (`si_no`, `seleccion_unica`, `segmento`, `seleccion_multiple`): Grupo · Respondieron · una columna por opción, en el orden de las opciones del total, con "<pct> % (<n>)". Si hay más de 6 opciones, mostrar las 6 primeras y el botón "Ver todas las opciones (<total>)" / "Ver menos"; la tabla puede desplazarse a lo ancho. La `nota` de la selección múltiple, debajo.
  - Un grupo sin respuestas en esa pregunta muestra "—" en las celdas sin dato (no "0" ni "NaN").
- SÍ: **tramos** (solo si el grupo elegido es `numerica`): campo **"Tramos"** con valor inicial `18, 25, 35, 45, 55, 65`, ayuda **"Cada número inicia un tramo. Por ejemplo, 18, 25, 35 da 18–24, 25–34 y 35 o más."**, botón "Aplicar" y "Volver a los tramos por defecto". Se envía como `cortes` (sin espacios). Si el backend responde 400, se muestra su mensaje junto al campo.
- SÍ: **juntar grupos** (solo si el grupo elegido no es `numerica`), en una sección plegable **"Juntar grupos"** (cerrada por defecto):
  - Lista de casillas con los grupos **originales** (los de la consulta sin `unir`), con su número de personas; las que ya están en una unión aparecen deshabilitadas. Lista con altura máxima y desplazamiento si son muchos (por ejemplo, 120 comunas).
  - Campo "Nombre del grupo nuevo" y botón "Juntar" (habilitado con 2 o más casillas y un nombre).
  - Debajo, las uniones aplicadas: "<nombre>: <opciones>" con botón "Deshacer" cada una, y "Quitar todas".
  - Cada cambio vuelve a pedir los resultados con la lista completa en `unir`. Si el backend responde 400, se muestra su mensaje y la unión no se agrega.
  - Al cambiar el grupo elegido en "Ver por", los tramos y las uniones vuelven a cero.
- SÍ: CSS mínimo en `globals.css` solo si hace falta (por ejemplo, la lista de casillas con desplazamiento y la fila con pocos datos). Reutilizar `.pill`, `.table-wrap`, `table.si` y las variables existentes. Responsive: la tabla se desplaza a lo ancho en el celular (RNF-15).
- NO: guardar tramos o uniones; cruzar temas de las abiertas; exportar; gráficos; calcular cualquier número en el frontend (todo viene del backend); cambios en el backend.

## Contrato de API
`docs/API_CONTRATOS.md`, secciones **RF-31 · Cruces por grupo de las preguntas cerradas (T-022)** y **RF-31 · Unir grupos en los cruces (T-023)**. Solo se consume.

## Archivos probables
- Tocar: `src/features/analysis/{api.ts,types.ts}`, `src/features/analysis/closed/ClosedResults.tsx` y, si crece mucho, componentes nuevos en `src/features/analysis/closed/` (por ejemplo `GroupTable.tsx` y `GroupControls.tsx`), `src/styles/globals.css` si hace falta.
- No tocar: `07_MVP/backend/**`, `docs/**`, `shared/api/client.ts`.

## Criterios de aceptación
- [ ] `npm run build` sin errores.
- [ ] Contra el backend local sin IA, proyecto `proj_4df733d1c3` (cuenta `t012@prueba.cl` / `Prueba-T012-clave`):
  - sin grupo elegido, la pantalla es igual que en T-021;
  - **por género**: en "importancia de ser propietario", Todas las personas 4,31 · 79,4 %; Femenino 4,36 · 81,5 %; Masculino 4,24 · 76,6 %; "no binario" y "Prefiero no decirlo" con "Pocos datos";
  - **por edad**, juntando "20-24" + "25-29" en "20-29" y "50-54" + "55-59" + "60-64" + "Mayor a 65" en "50 o más": 20-29 con 216 personas y promedio 4,09; 50 o más con 151 y 4,57; "Deshacer" vuelve a los tramos originales;
  - un error de unión (por ejemplo, un nombre igual a una opción que queda sin unir) muestra el mensaje del backend.
- [ ] **Tramos**: con un proyecto pequeño sintético con una columna de edad numérica (créalo en la misma cuenta con un CSV en la carpeta temporal, nunca en el repo), los tramos por defecto y otros (por ejemplo `30, 50`) muestran las etiquetas que manda el backend; un valor inválido (`50, 30`) muestra el mensaje 400.
- [ ] Un usuario lector (`lector-t021@prueba.cl` / `Lector-T021-clave`) puede usar "Ver por", los tramos y juntar grupos (son consultas, no cambian datos).
- [ ] Accesible con teclado: selector, casillas, campos y botones con etiqueta; la píldora "Pocos datos" es texto.
- [ ] A 390 px de ancho la tabla se desplaza a lo ancho sin romper la página.
- [ ] Commits con el formato `T-024 RF-31: ...`.

## Notas
- El supervisor tomará capturas reales: al terminar, deja el backend (8000) y el frontend (5173) corriendo, e indica en el resumen el id del proyecto sintético con edad numérica.
- Las cifras de referencia de arriba son las que el supervisor verificó en el backend (T-022 y T-023).

## Revisión 1
2026-10-31 — **Con cambios** (supervisor).

Verificado con capturas propias (cuenta lectora y analista): `npm run build` sin errores; sin grupo la pantalla es igual que en T-021; por género "importancia de ser propietario" 4,31 · 79,4 % / Femenino 4,36 · 81,5 % / Masculino 4,24 · 76,6 %, con "Pocos datos" en los dos grupos de 1 persona; por edad con uniones, 20-29 (216, 4,09, "Junta: 20-24, 25-29") y 50 o más (151, 4,57); tramos por defecto 18–24 … 65+, con `30, 50` → Menos de 30 / 30–49 / 50+, y el 400 junto al campo; a 390 px la tabla se desplaza dentro de la tarjeta (`scrollWidth` 390); sin errores de JS; el frontend no calcula cifras.

Cambio pedido (RNF-13, los errores deben dejar claro qué hacer sin perder lo hecho):

1. **`GroupControls.tsx`, `juntar` (líneas 42-46):** limpia `marcados` y `nombre` **antes** de saber si el backend aceptó la unión. Si responde 400 (por ejemplo, "Cada grupo unido necesita un nombre distinto."), el mensaje aparece pero las casillas y el nombre quedan vacíos, y la persona tiene que volver a marcar y escribir todo. Se espera que **solo se limpien si la unión se aplicó**, y que ante un error queden marcadas las casillas y escrito el nombre, para corregir solo lo que falló. Por ejemplo, `onUnir` puede devolver una promesa que indique si se aplicó; `cambiarControl` en `ClosedResults.tsx` ya distingue el éxito del error.
2. Verifícalo: marcar 30-34 y 35-39 con el nombre "40-44" → aparece el error, las dos casillas siguen marcadas y el nombre sigue escrito; cambiar el nombre a "30-39" y "Juntar" → se aplica y se limpia.

Commit `T-024 RF-31: ...` en la misma rama. Deja los servidores corriendo como antes.

## Revisión 2
2026-10-31 — **Aprobada** (supervisor).
- Corrección +5/−6 en `ClosedResults.tsx` y `GroupControls.tsx`: `onUnir` devuelve si se aplicó y `juntar` solo limpia en ese caso. `npm run build` sin errores.
- Verificado por el supervisor en el navegador (cuenta lectora): 30-34 + 35-39 con el nombre "40-44" → error del backend, las 2 casillas siguen marcadas y el nombre escrito, sin unión agregada; con el nombre "30-39" → se aplica y se limpia. Sin errores de JS.
- Deuda: con un grupo elegido, las escalas muestran las tarjetas del total y además la fila "Todas las personas" en la tabla (redundante, pero da contexto); la lista de casillas no se probó con 120 comunas; sin suite Playwright.

### Chequeo final antes de subir (2026-10-31, pedido por el usuario)
- `npm run build` y `tsc --noEmit` sin errores; `pytest tests -q` 246 en verde; `main` remoto sin cambios; la rama solo toca `07_MVP/frontend/` y `docs/`.
- Recorrido automático de **todas las pestañas** de los 9 proyectos de la cuenta de prueba, más **cada opción de "Ver por"** de cada proyecto con cerradas (16 en la encuesta real): sin errores de JS, sin errores 5xx, sin alertas de error y sin textos "NaN", "undefined" ni "Infinity".
- Tiempos en la encuesta real (500 personas, 29 cerradas): la mayoría de los grupos carga en 0,25–0,7 s; nivel educacional 2,3 s; comuna (120 grupos) 3,5 s.
- Comuna a 390 px: las 120 casillas en una lista con desplazamiento, sin desplazamiento horizontal de la página.
- Deuda: con 120 grupos la pantalla tarda 3,5 s (la meta de RNF-10 es 2 s para páginas interactivas); si molesta, mostrar las tablas por partes o limitar los grupos visibles.
