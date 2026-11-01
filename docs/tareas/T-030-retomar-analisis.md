# T-030: Retomar el léxico y la propuesta de categorías al volver a la pestaña
Lado: frontend
Requerimientos: RF-23, RNF-08, RNF-13
Rama: tarea/T-030-retomar-analisis
Depende de: T-029

## Objetivo
Si el usuario sale de "Análisis léxico" o "Libro de códigos" mientras corre el análisis y vuelve, la pantalla muestra que sigue en curso: el botón queda ocupado y no se puede relanzar. Al terminar, muestra el resultado sin recargar la página.

## Alcance
- SÍ: `LexicalAnalysis.tsx` y `Codebook.tsx`; función `getAnalysisStatus` en `features/analysis/api.ts` y su tipo en `types.ts`.
- NO: Codificación, Informe (ya retoman), Preguntas cerradas, backend.

## Contrato de API
`docs/API_CONTRATOS.md` → sección T-029 (`GET analysis-status` y el 409 de los POST).

## Archivos probables
- Se tocan: `07_MVP/frontend/src/features/analysis/lexical/LexicalAnalysis.tsx`, `07_MVP/frontend/src/features/analysis/codebook/Codebook.tsx`, `07_MVP/frontend/src/features/analysis/api.ts`, `07_MVP/frontend/src/features/analysis/types.ts`.
- NO se tocan: `07_MVP/backend/**`, `Coding.tsx`, `ReportView.tsx`.

## Criterios de aceptación
- [ ] Al entrar a cada pestaña, se consulta `analysis-status`. Si su operación está `running`, el botón queda ocupado con su texto de espera y se consulta cada 2 s (`usePolling`) hasta `idle`.
- [ ] Al pasar a `idle`: léxico → `GET lexical` y `refresh()`; códigos → `refresh()` (el proyecto trae las categorías nuevas).
- [ ] Si al pulsar el botón el servidor responde 409, no se muestra como error: se pasa a la misma espera.
- [ ] Al salir de la pestaña, el polling se detiene, sin fugas ni avisos de React. Al cambiar de pregunta se reinicia el estado (patrón de `Coding.tsx`: efecto con `off`).
- [ ] La ejecución normal (sin salir de la pestaña) se ve y funciona igual que hoy.
- [ ] `cd 07_MVP/frontend && npm run build` sin errores.
- [ ] Verificación manual **sin llamar a la API real de Anthropic**: con el backend local y la IA simulada o sin clave, o forzando la respuesta de `analysis-status`. Describe en el resumen cómo lo verificaste.

## Notas
- Patrón de referencia: el efecto "Retoma una codificación en curso" de `Coding.tsx` (líneas ~55-65) y `usePolling`.
- `req` lanza `Error` con el `detail`. Para distinguir el 409 puede hacer falta conocer el código HTTP. Si `shared/api/client.ts` no lo expone, hacer el cambio mínimo (por ejemplo, adjuntar `status` al error) sin afectar al resto de las llamadas que usan `req`.
