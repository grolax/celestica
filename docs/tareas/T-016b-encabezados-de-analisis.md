# T-016b: Encabezado de página en las pestañas del proyecto
Lado: frontend
Requerimientos: RNF-13, RNF-16
Rama: tarea/T-016b-encabezados-de-analisis
Depende de: T-016a (usa `PageHeader`)

## Objetivo
Segunda mitad de T-016. Cada pestaña del proyecto abre con `PageHeader` en nivel 2 (el `h1` es el nombre del proyecto en `ProjectView`): título y una línea de ayuda en lenguaje simple.

## Alcance
- SÍ: aplicar `PageHeader level={2}` al inicio de cada pestaña, reemplazando el título actual si existe: Resumen (`ProjectDashboard`), Análisis léxico (`LexicalAnalysis`), Libro de códigos (`Codebook`), Codificación (`Coding`), Trazabilidad (`Traceability`), Informe (`ReportView`), Exportar (`ExportReport`) y Auditoría (`AuditLog`).
- SÍ: si una pantalla tiene un bloque de explicación que repite la línea de ayuda, se quita la repetición; si aporta más detalle, se deja.
- NO: cambiar flujos, lógica, endpoints, nombres de pestañas, textos metodológicos ni otros componentes internos de cada pantalla.

## Textos (aprobados por el usuario, 2026-10-30)
Úsalos tal cual.
- **Resumen del proyecto:** "Cómo va tu análisis y cuál es el siguiente paso."
- **Análisis léxico:** "Las palabras y frases que más se repiten y el tono de las respuestas, calculados sin IA."
- **Libro de códigos:** "Los temas para clasificar las respuestas. La IA los propone y tu equipo los revisa y valida."
- **Codificación:** "La IA asigna a cada respuesta sus temas validados, con el motivo y su nivel de confianza. Puedes corregir cualquier asignación."
- **Trazabilidad:** "Sigue cada respuesta hasta su categoría, el motivo y quién la asignó."
- **Informe:** "Genera el informe con los hallazgos y las citas textuales que los respaldan."
- **Exportar:** "Descarga el informe en PDF o Word, y los datos en Excel o CSV."
- **Auditoría:** "Registro de cada acción, de personas y de la IA. No se puede editar ni borrar."

## Contrato de API
No aplica.

## Archivos probables
- Tocar: `src/features/projects/ProjectDashboard.tsx`, `src/features/analysis/{lexical,codebook,coding,traceability,report,audit}/*.tsx` (solo el encabezado), `src/features/export/ExportReport.tsx`.
- No tocar: `07_MVP/backend/**`, `docs/**`, `shared/api/client.ts`, los `api.ts`, `PageHeader.tsx` (salvo un bug real; explícalo).

## Criterios de aceptación
- [ ] `npm run build` sin errores.
- [ ] Las 8 pestañas muestran título (h2) y su línea de ayuda exacta; un solo `h1` por pantalla.
- [ ] Sin cambios de comportamiento: ejecutar léxico, validar categorías, ver trazabilidad y exportar siguen funcionando. Indica cómo lo probaste.
- [ ] Diff de menos de unas 400 líneas.
- [ ] Commits con el formato `T-016b RNF-13: ...`.
