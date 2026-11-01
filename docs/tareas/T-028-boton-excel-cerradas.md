# T-028: Botón "Descargar Excel" en "Preguntas cerradas"
Lado: frontend
Requerimientos: RF-30, RF-31, RF-24, RF-52
Rama: tarea/T-028-boton-excel-cerradas
Depende de: T-027 (fusionada, PR #32)

## Objetivo
En la pestaña "Preguntas cerradas" aparece un botón "Descargar Excel" que baja el archivo de `export/closed-xlsx` con **exactamente lo que se está viendo**: sin separar o separado por el "Ver por…" elegido, con los tramos y los grupos unidos que estén aplicados. Así los proyectos con solo cerradas (que no tienen pestaña "Exportar") pueden entregar su Excel.

## Alcance
- SÍ: botón en el encabezado de `ClosedResults.tsx` (como `children` de `PageHeader`), función `downloadClosedXlsx` en `features/export/api.ts` usando `downloadFile`, estado de carga y error con `useDownload`.
- SÍ: guardar en el estado de la página los `cortes` **aplicados** (hoy solo se pasan a `cargar` y no quedan guardados), para enviarlos en la descarga. Se guardan solo cuando la carga resulta bien, igual que `por` y `unir`.
- NO: cambios en el backend, en la pestaña "Exportar" ni en otros archivos de exportación. Sin refactor de `getClosedResults`, salvo extraer la construcción de la query a una función compartida si así se evita duplicarla (recomendado, ver Notas).

## Contrato de API
`docs/API_CONTRATOS.md` → `GET /api/projects/{id}/export/closed-xlsx[?por=…&cortes=…&unir=<json>]` (T-027). Mismos parámetros y mensajes 400 que `closed-results`. Roles: lector, analista, admin (el botón se ve para todos).

## Archivos probables
- Se tocan: `07_MVP/frontend/src/features/analysis/closed/ClosedResults.tsx`, `07_MVP/frontend/src/features/export/api.ts`, quizá `07_MVP/frontend/src/features/analysis/api.ts` (query compartida).
- NO se tocan: `07_MVP/backend/**`, `ExportReport.tsx`, `GroupControls.tsx` (salvo que sea imprescindible), `globals.css` (salvo una clase mínima si hace falta).

## Criterios de aceptación
- [ ] Botón secundario con ícono `download` y texto "Descargar Excel", en el encabezado de la pestaña; usa `Button`/`Icon` de `shared/components`.
- [ ] Sin "Ver por…": llama a `/projects/{id}/export/closed-xlsx` sin parámetros.
- [ ] Con "Ver por…": envía `por`, y además `cortes` y `unir` **si están aplicados en pantalla**, con la misma codificación que `getClosedResults` (`encodeURIComponent`, `unir` como JSON).
- [ ] Si se escriben tramos y no se presiona "Aplicar", o la aplicación falla con 400, el Excel usa los últimos tramos **aplicados** (lo que se ve), no lo escrito en el campo.
- [ ] Mientras descarga, el botón muestra el estado ocupado (`busy`) y no se puede pulsar dos veces; también se deshabilita mientras se recalculan los resultados (`busy` de la página) o si aún no hay datos.
- [ ] Si falla, el mensaje del servidor se muestra en el `alert alert-error` de la página (texto simple, sin códigos).
- [ ] Accesible con teclado (es un `<button>` real); el nombre del archivo lo da el servidor (`Content-Disposition`).
- [ ] Proyecto con solo cerradas y proyecto con abiertas: el botón aparece y funciona en ambos.
- [ ] `cd 07_MVP/frontend && npm run build` sin errores.
- [ ] Verificación manual contra la encuesta real local (proyecto `proj_4df733d1c3`, cuenta `t012@prueba.cl` / `Prueba-T012-clave`): descargar (1) sin separar, (2) por género, (3) por edad uniendo tramos. Indica en el resumen las URLs pedidas (pestaña Network o equivalente) y confirma que coinciden con los parámetros de `closed-results` de la pantalla. Si guardas archivos, solo en la carpeta temporal de la sesión, nunca en el repo.
- [ ] Sin regresiones: el "Ver por…", los tramos y la unión de grupos siguen funcionando igual.

## Notas
- `downloadFile` (`shared/api/client.ts`) ya maneja el token, el nombre del archivo y los errores; no hace falta nada nuevo para HTTP.
- Patrón de referencia: `ExportReport.tsx` (`useDownload` + `busyKey`).
- Para no duplicar la query de `getClosedResults` (`features/analysis/api.ts`, líneas ~53-58), se recomienda extraer una función `closedQuery(o?: ClosedOpciones): string` y usarla en ambos lados. Mismo resultado, una sola fuente.
- Los proyectos con solo cerradas no tienen pestaña "Exportar" (T-026); por eso el botón vive en "Preguntas cerradas".
