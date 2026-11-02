# T-034: Alertas compactas y etiqueta "Poco respondida"
Lado: frontend
Requerimientos: RF-41, RF-30, RNF-13, RNF-14
Rama: tarea/T-034-alertas-compactas
Depende de: T-033 (fusionada)

## Objetivo
Comentario del usuario tras revisar la encuesta real: la tarjeta "Recomendaciones" se llena de alertas, una por pregunta, y tapa las funciones de la pantalla.
- La tarjeta mostrará **una línea por tipo de alerta**, con la lista desplegable.
- En "Preguntas cerradas", cada pregunta poco respondida llevará una etiqueta pequeña, del mismo estilo que "Pocos datos".

## Alcance
- SÍ: agrupar las alertas en `Recommendations.tsx`; etiqueta "Poco respondida" en el encabezado de cada pregunta de `ClosedResults.tsx` (componente `Pregunta`).
- NO: backend (las alertas siguen llegando una por una desde `GET /recommendations`); cambios en segmentos o plantilla de la tarjeta (los cruces cambian en una tarea posterior); otras pantallas.

## Contrato de API
Sin cambios. Consume `GET /api/projects/{id}/recommendations` (T-032) y `closed-results` (T-020) tal como están.

## Archivos probables
- Se tocan: `07_MVP/frontend/src/features/projects/Recommendations.tsx`, `07_MVP/frontend/src/features/analysis/closed/ClosedResults.tsx`.
- NO se tocan: `07_MVP/backend/**`, `GroupTable.tsx`, `globals.css` (salvo una regla mínima si fuera imprescindible).

## Criterios de aceptación
- [ ] **Alertas generales** (`pocas_respuestas`, `pocas_respuestas_30`): se muestran como hoy, con su `mensaje`.
- [ ] **Alertas por pregunta** (`muchas_vacias`, `abierta_repetida`, `abierta_corta`, `cerrada_dispersa`): se agrupan por `id`.
  - Si el tipo tiene **1** alerta, se muestra su `mensaje` tal cual.
  - Si tiene **2 o más**, se muestra **una sola** alerta con un resumen y un botón de texto "Ver cuáles (k)" / "Ocultar" que despliega la lista de los `mensaje` originales. La lista empieza cerrada.
  - Textos del resumen (k = cantidad):
    - `muchas_vacias`: "{k} preguntas tienen más de la mitad sin responder."
    - `abierta_repetida`: "{k} preguntas abiertas tienen respuestas muy repetidas: quizás son cerradas."
    - `abierta_corta`: "{k} preguntas abiertas tienen respuestas muy cortas: el análisis de temas tendrá poco material."
    - `cerrada_dispersa`: "{k} preguntas cerradas tienen casi tantas opciones como respuestas: quizás son abiertas."
  - Mismo color que hoy según `nivel`; un `id` desconocido se muestra como hoy, uno por uno.
  - El botón es un `<button>` real (accesible con teclado, con `aria-expanded`).
- [ ] **Etiqueta "Poco respondida"** en "Preguntas cerradas":
  - Cuando `n_na * 2 > n_respuestas + n_na`, que es la misma regla que `muchas_vacias`, se muestra junto al título o en la línea de datos de la pregunta.
  - Clase `pill propuesta`, igual que "Pocos datos", con `title` "Más de la mitad de las personas no respondió esta pregunta".
  - Se ve con y sin "Ver por…".
- [ ] Con la encuesta real local (`proj_4df733d1c3`, cuenta `t012@prueba.cl` / `Prueba-T012-clave`): la tarjeta queda corta, y las preguntas poco respondidas muestran la etiqueta. Si existe localmente un proyecto **sin abiertas** creado desde esa encuesta, revisarlo también (ahí se ven muchas alertas). Si no existe, créalo como en T-026, desmarcando las abiertas.
- [ ] `cd 07_MVP/frontend && npm run build` sin errores. Sin llamadas a la API real de Anthropic.

## Notas
- Decisiones del usuario (2026-11-01):
  - una alerta por tipo, con la lista desplegable;
  - una etiqueta pequeña por pregunta, como "Pocos datos";
  - los cruces de a 2 y el cambio de tipo de las cerradas llegan en tareas posteriores.
- El backend local debe estar en `main` actualizado (incluye `GET /recommendations`). Si el puerto 8000 está ocupado por otro proceso, usa otro puerto para tu verificación y no detengas procesos del usuario.

## Revisión
2026-11-01 · **Aprobada.**
- La primera ejecución se cortó por el límite de uso con el código sin commit. Un segundo programador la revisó, la verificó, limpió los temporales (configuración de Vite y servidores en 8001 y 5181) e hizo el commit, sin cambios en el código.
- Diff: 2 archivos de frontend, +57/−5, dentro del alcance.
  - Agrupación por `id` con los textos exactos de la orden.
  - Botón accesible con `aria-expanded`; la lista empieza cerrada.
  - Etiqueta con la misma regla que `muchas_vacias`.
- `npm run build` sin errores.
- Verificación en Chrome sin interfaz:
  - En el proyecto sin abiertas (`proj_08d77f74ba`), las 15 alertas quedan en una sola línea, con "Ver cuáles (15)", y hay 15 etiquetas "Poco respondida", también con "Ver por…".
  - En la encuesta con abiertas, las 2 alertas son de tipos distintos y se ven sin agrupar.
- Decisión aceptada: el grupo se pinta de rojo si alguna alerta del grupo es "importante".
