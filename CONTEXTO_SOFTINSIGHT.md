# SoftInsight — Documento de contexto del producto

> **Para quién es este documento:** para los agentes de desarrollo (Claude Code) que trabajan sobre este repositorio y para cualquier persona que se sume al equipo. Describe qué es SoftInsight, a quién sirve, cómo funciona hoy, qué debe llegar a hacer y cómo se organiza el equipo de agentes que lo desarrolla.
>
> **Cómo usarlo:** léelo completo antes de la primera tarea. Para el detalle técnico de lo que ya existe, consulta `07_MVP/COMO_FUNCIONA.md` (arquitectura, decisiones y su porqué) y `07_MVP/README.md` (instalación). Si este documento y el código se contradicen, **el código manda sobre el estado actual** y **este documento manda sobre la dirección** del producto; avisa la contradicción en tu resumen final.
>
> Versión del documento: 1.0 — octubre 2026. Estado del código de referencia: `07_MVP/` v1.1.

---

## 1. Qué es SoftInsight

SoftInsight es una plataforma web que ayuda a las organizaciones a **convertir los resultados de sus encuestas en hallazgos claros, trazables y presentables**. Combina análisis automático (estadístico y léxico, sin IA), análisis temático asistido por IA (Claude) **siempre con validación humana**, y la generación de informes listos para entregar (PDF, Word, Excel, CSV).

Su promesa central se resume en tres ideas:

1. **De la encuesta al informe en horas, no semanas.** Lo que un equipo hace a mano en Excel durante días (leer cientos de comentarios, agruparlos, contar, redactar) se hace en la plataforma con apoyo de IA.
2. **Nada es caja negra.** Cada número y cada afirmación del informe se puede rastrear hasta las respuestas que lo sustentan, y cada decisión (humana o de la IA) queda en un registro de auditoría que no se puede borrar. Este es el diferenciador frente a usar ChatGPT directamente.
3. **La IA propone, el humano decide.** Las categorías y codificaciones que sugiere la IA entran como propuestas; la persona las valida, edita o descarta.

### 1.1 Dirección de esta etapa

El MVP v1.1 está centrado en **respuestas abiertas** y en un usuario analista experto. La siguiente etapa amplía el producto en tres direcciones, que son los requerimientos rectores de todo el trabajo:

| Eje | Qué significa | Ejemplo |
| --- | --- | --- |
| **Personalizable por tipo de cliente** | La plataforma se adapta a la industria, vocabulario, marca y metodología de cada organización sin tocar código. | Un municipio ve "vecinos" y "servicios municipales"; un retail ve "clientes", "tiendas" y NPS; una universidad ve "estudiantes" y criterios CNA. |
| **Asesorable** | La plataforma guía al usuario (recomendaciones, explicaciones, siguientes pasos) y además permite que un asesor/consultor de SoftInsight acompañe a varios clientes. | "Tu encuesta tiene 3 preguntas abiertas y 12 cerradas: te recomendamos la plantilla *Satisfacción de Clientes (NPS)*." Un consultor revisa y comenta el proyecto de un cliente. |
| **Amigable para el cliente** | Un usuario no experto (jefe de área, encargado municipal) puede llegar a un informe útil sin saber de análisis cualitativo. | Asistente paso a paso, lenguaje simple, valores por defecto sensatos, la complejidad metodológica queda disponible pero no estorba. |

Y una ampliación de alcance: **SoftInsight debe servir a toda organización que haga encuestas, incluyan o no preguntas de respuesta abierta.** Hoy el producto solo analiza una columna de texto abierto; debe pasar a analizar también preguntas cerradas (escalas, selección, NPS, sí/no) y cruzarlas con las abiertas.

---

## 2. Público objetivo

### 2.1 Organizaciones (clientes)

Toda organización que aplique encuestas de forma recurrente y necesite transformar los resultados en decisiones o en informes para terceros.

| Segmento | Ejemplos | Encuestas típicas | Qué valoran más |
| --- | --- | --- | --- |
| **Retail y consumo masivo** | Tottus, supermercados, tiendas por departamento, cadenas de farmacias | Satisfacción post-compra, NPS por tienda, experiencia en caja/despacho, encuestas a colaboradores | Velocidad, comparar tiendas/zonas, tendencias entre periodos, NPS, volumen alto de respuestas |
| **Sector público** | Municipalidades, servicios públicos, gobiernos regionales | Consultas ciudadanas, PLADECO, satisfacción con servicios (aseo, seguridad, salud primaria), presupuestos participativos | Lenguaje simple, informes presentables al concejo/ciudadanía, trazabilidad para rendición de cuentas, bajo costo, soporte |
| **Educación superior** | Universidades, institutos, CFT | Evaluación docente, satisfacción estudiantil, procesos de acreditación (CNA) | Rigor metodológico, trazabilidad ante auditores, marcos teóricos formales |
| **Empresas (RR.HH. y B2B)** | Empresas medianas y grandes | Clima laboral, pulso, encuestas de salida, voz del cliente B2B | Confidencialidad, segmentación por área/cargo, comparativas entre ciclos |
| **Estudios de mercado** | Consultoras, agencias de investigación | Percepción de marca, prueba de concepto, NPS | Productividad del analista, exportables editables, marca propia en los informes |
| **Salud** | Clínicas, CESFAM, hospitales | Experiencia de pacientes | Confidencialidad de datos, lenguaje cuidadoso |

### 2.2 Usuarios (personas dentro de cada organización)

| Rol | Quién es | Qué necesita de SoftInsight |
| --- | --- | --- |
| **Administrador de la organización** | Encargado del contrato o del área de estudios | Invitar usuarios, asignar roles, configurar marca, plantillas y vocabulario de su organización, ver consumo. |
| **Analista** | Persona que trabaja los datos (sociólogo, analista de experiencia, RR.HH.) | Todo el flujo de análisis con control fino: validar categorías, re-codificar, revisar trazabilidad, editar informe. |
| **Usuario de negocio / lector** | Gerente de tienda, alcalde/concejal, director de carrera | Ver resultados y descargar informes sin tener que entender el método. Solo lectura y comentarios. |
| **Asesor SoftInsight** (interno) | Consultor del equipo SoftInsight | Acompañar a varias organizaciones: ver sus proyectos (con permiso), comentar, sugerir categorías, ajustar plantillas y prompts por cliente. |
| **Superadministrador SoftInsight** (interno) | Equipo de producto | Gestionar organizaciones, plantillas globales, prompts metodológicos base, consumo y costos de IA. |

---

## 3. Funcionamiento: cómo se usa el producto

### 3.1 Flujo actual (v1.1, ya implementado)

```
Importar datos ──► Análisis léxico ──► Libro de códigos ──► Codificación ──► Trazabilidad ──► Informe ──► Exportación
(CSV/XLSX,         (frecuencias,       (la IA propone       (IA por lotes,    (respuesta →     (rápido v1    (PDF, DOCX,
 Qualtrics,         bigramas,           categorías,          con justificación  categoría →     o profundo    CSV, XLSX)
 Google Forms)      sentimiento)        el humano valida)    y confianza)       justificación)   v2, streaming)
                                                  ▲
                                         Auditoría de todo el flujo
```

- **Stack:** backend Python + FastAPI + MongoDB (pymongo) + Claude API; frontend React 18 + TypeScript + Vite, CSS propio (`globals.css`, paleta crema + celeste `#0099CC`, tipografía Inter), organizado por features.
- **Multi-tenant hoy = por usuario:** cada proyecto pertenece a un `user_id`; la organización es solo un texto (`empresa`) en el perfil.
- **Proyecto = un documento Mongo** con respuestas, categorías, codificaciones, informe y log de auditoría; las operaciones puntuales usan `$set`/`$push`.
- **IA aislada en un solo archivo:** `backend/app/services/thematic.py`. Salidas JSON con tool use forzado + schema (`schemas_v2.py`). Toda llamada se registra con tokens y costo (`claude_log.py`).
- **12 plantillas de marcos teóricos** en 5 industrias, escritas en `backend/app/templates.py` (código, no datos).
- **4 prompts metodológicos** editables desde la UI con una contraseña global de administrador (`prompt_store.py`).
- **Una sola columna de texto por proyecto** (`text_column`); el resto de columnas se guarda como `meta` de cada respuesta y solo lo usa el informe profundo v2.

### 3.2 Flujo objetivo (hacia dónde va)

```
1. Organización y configuración
   El admin de la organización configura marca, industria, vocabulario y plantillas propias; invita a su equipo.

2. Importar encuesta
   Archivo / Qualtrics / Google Forms / (nuevos conectores). La plataforma DETECTA el tipo de cada pregunta
   (abierta, escala Likert, NPS, selección única/múltiple, sí/no, numérica, demográfica/segmento) y el usuario confirma.

3. Asistente de análisis (modo guiado)
   Según la industria y las preguntas detectadas, recomienda plantilla, segmentos para cruzar y tipo de informe.
   El usuario acepta los valores por defecto o los ajusta (modo experto).

4. Análisis
   a. Cuantitativo (preguntas cerradas): distribuciones, promedios, NPS, top-2-box, cruces por segmento.   ← NUEVO
   b. Léxico (preguntas abiertas): igual que hoy, con stopwords/lexicón configurables por organización.
   c. Temático con IA (preguntas abiertas): categorías → validación → codificación, para CADA pregunta abierta.
   d. Integración: temas de las abiertas cruzados con las cerradas ("quienes ponen NPS ≤ 6 mencionan X").

5. Resultados e informe
   Panel de resultados para lectores no expertos + informe con marca de la organización, editable, exportable.
   Comparación entre periodos/olas de la misma encuesta.

6. Acompañamiento
   Comentarios, recomendaciones de la plataforma y, si el cliente lo contrata, revisión de un asesor SoftInsight.
```

---

## 4. Requerimientos funcionales

**Convenciones.** Cada requerimiento tiene un ID estable (`RF-xx`) que se usa en commits, PR y resúmenes.
**Estado:** ✅ existe · 🟡 parcial · 🆕 nuevo. **Prioridad:** P0 = imprescindible para la próxima versión · P1 = importante · P2 = deseable.

### 4.1 Organizaciones, usuarios y roles

| ID | Requerimiento | Estado | Prioridad |
| --- | --- | --- | --- |
| RF-01 | Registro e inicio de sesión con email y contraseña (JWT). | ✅ | — |
| RF-02 | **Entidad Organización**: cada usuario pertenece a una organización y los proyectos pertenecen a la organización (no al usuario). El aislamiento multi-tenant pasa de `user_id` a `org_id`, manteniendo las pruebas de acceso cruzado. Incluye migración idempotente de los datos actuales (cada usuario existente → su propia organización). | 🆕 | P0 |
| RF-03 | **Roles por organización**: administrador, analista, lector. Permisos verificados en el backend, no solo ocultos en la UI. | 🆕 | P0 |
| RF-04 | Invitar usuarios a la organización por enlace o email, y quitarles acceso. | 🆕 | P1 |
| RF-05 | Recuperación de contraseña y verificación de email. | 🆕 | P1 |
| RF-06 | **Rol asesor SoftInsight**: usuario interno con acceso a varias organizaciones, solo cuando la organización lo autoriza; todo acceso del asesor queda en auditoría. | 🆕 | P1 |
| RF-07 | Panel de superadministración interno (organizaciones, plan, consumo de IA por organización). Reemplaza la contraseña global `ADMIN_PASSWORD`. | 🟡 (hoy panel con contraseña global) | P1 |

### 4.2 Personalización por cliente

| ID | Requerimiento | Estado | Prioridad |
| --- | --- | --- | --- |
| RF-10 | **Perfil de organización**: nombre, industria/segmento, logo, color principal. La industria define valores por defecto (plantillas sugeridas, vocabulario, tipo de informe). | 🆕 | P0 |
| RF-11 | **Marca en informes**: el logo, nombre y color de la organización aparecen en PDF y DOCX (portada, encabezados). | 🆕 | P0 |
| RF-12 | **Plantillas como datos, no como código**: mover las 12 plantillas de `templates.py` a MongoDB. Plantillas globales (SoftInsight) + plantillas propias de cada organización, creadas desde cero o duplicando una global. | 🟡 (12 plantillas fijas en código) | P0 |
| RF-13 | **Vocabulario configurable** por organización: cómo se llama a quien responde (cliente, vecino, estudiante, colaborador, paciente), a la unidad de análisis (tienda, sede, carrera, área) y términos de la UI que lo usen. | 🆕 | P1 |
| RF-14 | **Stopwords y lexicón de sentimiento por organización/industria.** Hoy `lexical.py` trae stopwords de jerga universitaria chilena fijas; deben ser una base general + listas por industria + ajustes de la organización. | 🟡 | P1 |
| RF-15 | **Prompts metodológicos por organización**: la organización (o su asesor) puede ajustar los prompts sobre la base global, con historial de versiones y opción de volver a la base. | 🟡 (prompts globales) | P2 |
| RF-16 | **Plantillas de informe** por tipo de cliente: secciones, extensión y tono (ejecutivo para retail/gerencia, rendición de cuentas para sector público, formal para acreditación). | 🆕 | P1 |
| RF-17 | Nuevas plantillas de marco para los segmentos objetivo que faltan: **Retail** (experiencia en tienda, post-compra/NPS, despacho y e-commerce, colaboradores de tienda) y **Municipal** (satisfacción con servicios municipales, consulta PLADECO, presupuesto participativo). | 🆕 | P0 |

### 4.3 Importación de encuestas

| ID | Requerimiento | Estado | Prioridad |
| --- | --- | --- | --- |
| RF-20 | Subir CSV o XLSX. | ✅ | — |
| RF-21 | Importar desde Qualtrics (token cifrado) y Google Forms (planilla pública). | ✅ | — |
| RF-22 | **Detección del tipo de cada pregunta/columna**: abierta, escala (Likert 1–5/1–7), NPS (0–10), selección única, selección múltiple, sí/no, numérica, fecha, identificador, segmento/demográfica. El usuario revisa y corrige antes de crear el proyecto. | 🆕 | P0 |
| RF-23 | **Varias preguntas abiertas por proyecto** (hoy solo una `text_column`). Cada pregunta abierta tiene su propio libro de códigos, codificación y sección de informe. | 🆕 | P0 |
| RF-24 | **Proyectos sin preguntas abiertas**: si la encuesta solo tiene cerradas, el flujo omite léxico y codificación y entrega análisis cuantitativo + informe. | 🆕 | P0 |
| RF-25 | Vista previa de los datos antes de importar (primeras filas, tipos detectados, n° de respuestas, respuestas vacías). | 🆕 | P1 |
| RF-26 | Nuevos conectores priorizados: Microsoft Forms, SurveyMonkey; evaluar KoboToolbox/LimeSurvey para sector público. Todos deben respetar el contrato `fetch_responses(config) -> DataFrame` de `services/integrations/base.py`. | 🆕 | P2 |
| RF-27 | **Olas/periodos**: importar una nueva medición de la misma encuesta dentro de un proyecto existente, reutilizando el libro de códigos validado. | 🆕 | P1 |
| RF-28 | Sincronización continua con Qualtrics y OAuth de Google. | 🆕 | P2 |

### 4.4 Análisis

| ID | Requerimiento | Estado | Prioridad |
| --- | --- | --- | --- |
| RF-30 | **Análisis cuantitativo de preguntas cerradas** (sin IA, determinístico): frecuencias y porcentajes, promedio y desviación para escalas, top-2-box/bottom-2-box, cálculo de NPS (promotores/pasivos/detractores), tasa de respuesta por pregunta. | 🆕 | P0 |
| RF-31 | **Cruces por segmento**: cualquier métrica cerrada o tema abierto desglosado por una variable de segmento (tienda, comuna, carrera, área, sexo, tramo de edad), con advertencia cuando un grupo tiene muy pocas respuestas (umbral configurable, por defecto n < 10). | 🆕 | P0 |
| RF-32 | Análisis léxico (frecuencias, bigramas, co-ocurrencias, sentimiento con evidencia). | ✅ | — |
| RF-33 | Libro de códigos: la IA propone, el humano valida; plantillas; categorías manuales; comentarios. | ✅ | — |
| RF-34 | Codificación por lotes con justificación y confianza; re-codificación manual auditada. | ✅ | — |
| RF-35 | **Integración abiertas × cerradas** en la vista de resultados: por ejemplo, prevalencia de cada tema entre detractores vs promotores, o entre comunas. | 🟡 (solo dentro del informe v2) | P1 |
| RF-36 | Trazabilidad respuesta → categoría → justificación → confianza → fuente. | ✅ | — |
| RF-37 | **Comparación entre olas/periodos**: variación de métricas y de prevalencia de temas, con significancia simple cuando aplique. | 🆕 | P1 |
| RF-38 | Estimación de costo de IA **antes** de lanzar codificación o informe profundo, con confirmación del usuario. | 🟡 (hoy se ve después, en el panel admin) | P1 |

### 4.5 Experiencia guiada y asesoría

| ID | Requerimiento | Estado | Prioridad |
| --- | --- | --- | --- |
| RF-40 | **Asistente de creación de proyecto** en pasos cortos: (1) subir/importar, (2) revisar preguntas detectadas, (3) elegir objetivo y plantilla recomendada, (4) confirmar y analizar. Cada paso con texto de ayuda en lenguaje simple. | 🟡 (formulario único) | P0 |
| RF-41 | **Recomendaciones automáticas** basadas en reglas (no requieren IA): plantilla sugerida según industria y preguntas, segmentos sugeridos para cruzar, alertas de calidad de datos (muchas respuestas vacías, pocas respuestas, columna mal detectada). | 🆕 | P0 |
| RF-42 | **Modo guiado / modo experto**: el modo guiado oculta pasos metodológicos avanzados y usa valores por defecto; el modo experto muestra todo (como hoy). Se elige por usuario. | 🆕 | P1 |
| RF-43 | **Panel de resultados para lectores**: resumen en una pantalla (métricas clave, top temas con citas, alertas), sin jerga, imprimible. | 🆕 | P0 |
| RF-44 | **"Siguientes pasos" en el informe**: sección opcional con acciones sugeridas a partir de los hallazgos, marcada claramente como sugerencia generada por IA y separada de los hallazgos. | 🆕 | P1 |
| RF-45 | Ayuda contextual: explicaciones breves de cada concepto (confianza, categoría validada, NPS, top-2-box) en el lugar donde aparecen. | 🟡 (existe página de documentación) | P1 |
| RF-46 | Solicitud de asesoría desde la plataforma: el cliente pide revisión de un asesor sobre un proyecto; el asesor comenta y sugiere; todo queda auditado. | 🆕 | P2 |
| RF-47 | Datos de demostración por segmento (retail, municipal, universidad) para que un cliente nuevo pruebe el flujo completo antes de subir sus datos. | 🟡 (solo dataset de evaluación docente) | P1 |

### 4.6 Informe, exportación y colaboración

| ID | Requerimiento | Estado | Prioridad |
| --- | --- | --- | --- |
| RF-50 | Informe cualitativo rápido (v1) y profundo (v2) con progreso real por streaming. | ✅ | — |
| RF-51 | **Informe integrado** que combine sección cuantitativa (gráficos de cerradas, NPS, cruces) y cualitativa (temas, citas) según la plantilla de informe (RF-16). | 🆕 | P0 |
| RF-52 | Exportación PDF, DOCX, CSV y XLSX. | ✅ | — |
| RF-53 | **Edición del informe en la plataforma** antes de exportar (texto por sección), con registro en auditoría de lo editado por humanos vs lo generado por IA. | 🆕 | P1 |
| RF-54 | Exportar a PowerPoint (resumen ejecutivo para presentar a gerencia/concejo). | 🆕 | P2 |
| RF-55 | Enlace de solo lectura para compartir resultados con personas sin cuenta (con expiración y revocable). | 🆕 | P2 |
| RF-56 | Comentarios en categorías. | ✅ | — |
| RF-57 | Auditoría inmutable de toda acción humana y de IA. | ✅ | — |

---

## 5. Requerimientos no funcionales

| ID | Categoría | Requerimiento |
| --- | --- | --- |
| RNF-01 | **Seguridad — aislamiento** | Ninguna consulta a datos de proyecto puede ejecutarse sin filtro de organización. El filtro vive en la capa `store`, no en los routers. Toda nueva ruta debe tener prueba de acceso cruzado (otra organización → 404). |
| RNF-02 | **Seguridad — autorización** | Los permisos por rol se validan en el backend con una dependencia común (análoga a `get_current_user`). La UI solo refleja permisos; nunca es la única barrera. |
| RNF-03 | **Seguridad — secretos** | Ningún secreto en el repositorio ni en el navegador. `SECRET_KEY` y `ADMIN_PASSWORD` sin valores por defecto utilizables en producción (el servidor no arranca en modo producción con valores de desarrollo). Credenciales de integraciones cifradas como hoy. |
| RNF-04 | **Seguridad — producción** | HTTPS, rate-limiting de login, revocación de sesiones, cabeceras de seguridad, CORS restringido al dominio del frontend. |
| RNF-05 | **Privacidad de datos** | Cumplir la Ley 19.628 de protección de datos personales de Chile y preparar la adecuación a la Ley 21.719 (nueva ley de datos personales). Las respuestas pueden contener datos personales o sensibles (salud, RR.HH.): opción de **anonimizar** (enmascarar nombres, RUT, emails, teléfonos) antes de enviar textos a la IA; política de retención y borrado de proyectos por organización. |
| RNF-06 | **Transparencia de IA** | Toda salida de IA se marca como tal en la UI y en los informes. La confianza se usa para priorizar revisión, nunca para filtrar datos. Ninguna categoría de IA se usa en codificación sin validación humana. |
| RNF-07 | **Trazabilidad** | Todo número del informe debe poder rastrearse a las respuestas que lo producen. Los cálculos cuantitativos se hacen en Python (determinísticos), nunca se le pide a la IA que cuente o calcule porcentajes. |
| RNF-08 | **Costos de IA** | Toda llamada a Claude pasa por `services/thematic.py` y queda registrada (tokens, costo, paso, proyecto, organización). Debe existir un tope de gasto configurable por organización con aviso al acercarse. Los resultados caros se cachean (como el Prompt 1 del informe v2). |
| RNF-09 | **Robustez de IA** | Ningún paso depende de que la salida del modelo "quepa": la entrada se acota por tokens y el trabajo se divide si se trunca (principio ya aplicado en el informe v2, ver `COMO_FUNCIONA.md` §5). Salidas estructuradas siempre con tool use + schema. |
| RNF-10 | **Rendimiento** | Análisis cuantitativo y léxico de 10.000 respuestas en menos de 10 s. Páginas de la UI interactivas en menos de 2 s con proyectos de ese tamaño (paginación en tablas de respuestas y trazabilidad). Operaciones puntuales con `$set`/`$push`, nunca reescribir el proyecto completo. |
| RNF-11 | **Escalabilidad** | Soportar proyectos de hasta 50.000 respuestas (retail). Si el documento del proyecto se acerca al límite de 16 MB de MongoDB, mover respuestas y codificaciones a colecciones propias indexadas por `project_id` (decisión ya anticipada en `COMO_FUNCIONA.md` §15). |
| RNF-12 | **Procesos largos** | Codificación e informe sobreviven a un reinicio del servidor (hoy el progreso vive en memoria): estado del trabajo persistido en Mongo y reanudable. |
| RNF-13 | **Usabilidad** | Un usuario no experto debe llegar de "subir archivo" a "descargar informe" en el modo guiado sin ayuda externa. Lenguaje en español neutro-chileno, sin jerga técnica en el modo guiado. Todos los errores muestran qué pasó y qué hacer (principio de "errores hablables" ya aplicado en integraciones). |
| RNF-14 | **Accesibilidad** | WCAG 2.1 nivel AA en contraste, navegación por teclado y etiquetas de formularios. Los gráficos no dependen solo del color. |
| RNF-15 | **Responsive** | El panel de resultados y la lectura del informe funcionan en tablet y móvil; el trabajo de análisis puede limitarse a escritorio. |
| RNF-16 | **Identidad visual** | Mantener el sistema de diseño actual (`globals.css`, variables CSS, componentes de `shared/components`). Sin frameworks CSS nuevos. La marca de cada organización se aplica en informes y como acento en su espacio, sin romper la paleta base ni el contraste. |
| RNF-17 | **Mantenibilidad** | Backend: separar `main.py` (hoy ~950 líneas) en routers por dominio (`auth`, `orgs`, `projects`, `analysis`, `reports`, `integrations`, `admin`). Frontend: mantener la organización por features y el cliente HTTP único (`shared/api/client.ts`). Tipado estricto en TypeScript. |
| RNF-18 | **Pruebas** | Toda funcionalidad nueva con pruebas en `backend/tests/` (mongomock + IA simulada, sin gastar API). Agregar suite Playwright para los flujos críticos de UI (login, crear proyecto con asistente, ver resultados, exportar). |
| RNF-19 | **Portabilidad** | Despliegue en la nube cambiando solo variables de entorno (MongoDB Atlas, backend en Render/Railway, frontend en Vercel). El proveedor de IA sigue siendo intercambiable porque todo pasa por un solo módulo. |
| RNF-20 | **Observabilidad** | Logs estructurados por petición con `org_id` y `project_id`; registro de llamadas a IA como hoy; endpoint de salud. |
| RNF-21 | **Compatibilidad hacia atrás** | Los proyectos existentes deben seguir abriéndose. Todo cambio de esquema viene con un script de migración idempotente en `backend/scripts/`. |

---

## 6. Reglas de negocio y principios metodológicos (no negociables)

1. **La IA propone, el humano decide.** Categorías de IA o de plantilla entran como `propuesta`; solo las `validada` se usan para codificar.
2. **La IA no calcula.** Conteos, porcentajes, promedios, NPS y cruces se calculan en Python. La IA redacta e interpreta sobre números ya calculados.
3. **Citas textuales, nunca inventadas.** Toda cita del informe debe existir literalmente en las respuestas; validar en código antes de mostrarla.
4. **Neutralidad.** Los informes describen hechos con números y evidencia; las recomendaciones van en su propia sección, marcadas como sugerencia.
5. **El log de auditoría solo crece.** No existe endpoint para editar ni borrar eventos.
6. **Grupos pequeños.** No mostrar desgloses por segmento con menos respuestas que el umbral de la organización (por confidencialidad, especialmente en RR.HH.), o mostrarlos con advertencia según configuración.

---

## 7. Arquitectura objetivo (resumen de cambios)

```
MongoDB
├── organizations     🆕 {_id, nombre, industria, branding{logo, color}, vocabulario, config{umbral_n, tope_gasto, modo_por_defecto}}
├── users             🟡 + org_id, rol (admin | analista | lector), preferencias (modo guiado/experto)
├── memberships       🆕 (solo si se permite un usuario en varias organizaciones, ej. asesores)
├── projects          🟡 user_id → org_id (+ created_by), questions[] con tipo detectado, varias preguntas abiertas
├── templates         🆕 plantillas de marco (globales + por organización)
├── report_templates  🆕 estructura de informe por segmento/organización
├── jobs              🆕 estado persistente de codificación/informe (reanudable)
└── audit_events      ✅ + org_id
```

Detalle de lo que existe hoy: `07_MVP/COMO_FUNCIONA.md`.

---

## 8. Equipo de agentes

El desarrollo lo hace un equipo de tres agentes de Claude Code (definidos en `.claude/agents/`): un **supervisor** que planifica y revisa, y dos **programadores** especializados. Se trabaja iniciando Claude Code como supervisor (`claude --agent supervisor`); él delega a los programadores.

### 8.1 Roles

| | **supervisor** | **programador-backend** | **programador-frontend** |
| --- | --- | --- | --- |
| Hace | Elige requerimientos, escribe órdenes de trabajo, define contratos de API, delega, revisa diffs, ejecuta pruebas, aprueba o pide cambios | Implementa órdenes de backend con pruebas | Implementa órdenes de frontend con build verificado |
| Escribe en | Solo `docs/` | `07_MVP/backend/**` | `07_MVP/frontend/**` |
| Foco | Calidad, alcance, coherencia con este documento | Organizaciones y roles, migraciones, modelo de preguntas, análisis cuantitativo, IA, informes, exportaciones, seguridad | Asistente guiado, modo guiado/experto, panel de resultados, personalización visual, ayuda contextual, accesibilidad, Playwright |
| Requerimientos principales | Todos (revisión) | RF-02, 03, 06, 07, 10 (modelo), 11, 12, 14, 15, 17, 22–24, 27, 30, 31, 35, 37, 38, 51; RNF-01–12, 17 (backend), 19–21 | RF-10 (UI), 13, 25, 40–45, 47, 53; RNF-13–16, 17 (frontend), 18 (UI) |

### 8.2 Reglas de coordinación

1. **Contrato primero.** Ningún endpoint nuevo se implementa ni se consume sin estar definido en `docs/API_CONTRATOS.md` (lo escribe el supervisor).
2. **Una tarea, un lado, un programador a la vez.** Cada orden de trabajo (`docs/tareas/T-<n>-<slug>.md`) es solo de backend o solo de frontend. Los programadores comparten directorio y git, por eso no trabajan en paralelo.
3. **Orden en funcionalidades completas:** contrato → backend → revisión → frontend → revisión.
4. **Ramas por tarea** (`tarea/T-<n>-<slug>`) y commits que citan tarea y requerimiento (`T-003 RF-22: ...`). Al aprobar una tarea, el supervisor pregunta al responsable humano si sube la rama y abre un pull request; el merge a `main` siempre lo aprueba el responsable humano.
5. **Revisión obligatoria** del supervisor antes de aprobar; máximo 3 rondas de corrección por tarea, luego se escala al responsable humano.
6. **Cambios de esquema** solo en backend y siempre con script de migración idempotente.
7. **No cambiar** sin acuerdo explícito del responsable humano: el stack, la paleta/tipografía base, los principios de la sección 6, el modelo de IA por defecto ni los prompts metodológicos base.
8. **Avance** registrado por el supervisor en `docs/ESTADO.md`.

### 8.3 Orden sugerido (primeras iteraciones)

| Iteración | Backend | Frontend |
| --- | --- | --- |
| 1 | RF-02 y RF-03 (organizaciones + roles + migración), separar `main.py` en routers | Asistente de creación (RF-40) con datos simulados; ajustes de navegación por rol |
| 2 | RF-22, RF-23, RF-24 (tipos de pregunta, varias abiertas, proyectos sin abiertas) | Paso "revisar preguntas detectadas" (RF-25) conectado a la API real |
| 3 | RF-30 y RF-31 (cuantitativo y cruces) + RF-17 (plantillas retail y municipal) | Panel de resultados para lectores (RF-43) y recomendaciones (RF-41) |
| 4 | RF-10/11/12 (perfil de organización, marca en informes, plantillas en Mongo) | Configuración de organización, marca y vocabulario (RF-10, RF-13) |
| 5 | RF-51 (informe integrado) + RNF-12 (procesos reanudables) | Modo guiado/experto (RF-42), ayuda contextual (RF-45), Playwright |

### 8.4 Definición de terminado (para cada tarea)

- El requerimiento se cumple tal como está descrito, o la desviación queda explicada.
- Pruebas nuevas en verde y las existentes siguen en verde (`cd 07_MVP/backend && pytest tests -q`; `npm run build` sin errores en el frontend).
- Sin regresiones en aislamiento multi-tenant.
- `COMO_FUNCIONA.md` y `README.md` actualizados si cambió la arquitectura, el esquema o la configuración.
- Resumen final con: requerimientos tocados, archivos principales, decisiones tomadas y lo que quedó pendiente.

---

## 9. Fuera de alcance por ahora

- Crear o aplicar encuestas dentro de SoftInsight (la plataforma analiza encuestas hechas en otras herramientas).
- Facturación y cobro automático de planes.
- Aplicación móvil nativa.
- Idiomas distintos al español (dejar los textos de la UI preparados para internacionalización, sin traducir todavía).

---

## 10. Decisiones abiertas (a definir por el equipo)

Estas preguntas no tienen respuesta aún; los agentes deben **no** asumirlas y consultarlas si una tarea depende de ellas:

1. ¿Un usuario puede pertenecer a más de una organización, o solo los asesores?
2. Planes y límites comerciales (n° de usuarios, respuestas, proyectos, gasto de IA por plan).
3. Dónde se desplegará en producción y en qué región de datos (relevante para clientes públicos y de salud).
4. ¿El servicio de asesoría es parte del producto (con flujo en la plataforma, RF-46) o un servicio externo?
5. Nombre comercial definitivo (el repositorio se llama `celestica`; el producto, SoftInsight).

---

## 11. Glosario

| Término | Significado |
| --- | --- |
| **Pregunta abierta** | Pregunta donde la persona escribe libremente (texto). |
| **Pregunta cerrada** | Pregunta con opciones predefinidas: escala, selección, sí/no, NPS. |
| **NPS** | Net Promoter Score: % de promotores (9–10) menos % de detractores (0–6) en la pregunta "¿Qué tan probable es que nos recomiendes?". |
| **Top-2-box** | % de respuestas en las dos opciones más altas de una escala (ej. 4 y 5 en una escala 1–5). |
| **Marco teórico** | Texto que explica desde qué enfoque se analiza la encuesta; orienta a la IA al proponer y codificar. |
| **Libro de códigos** | Lista de categorías (temas) con definición y criterios de inclusión y exclusión. |
| **Codificación** | Asignar a cada respuesta abierta una o más categorías, con justificación y confianza. |
| **Trazabilidad** | Poder seguir el camino respuesta → categoría → justificación → informe. |
| **Ola / periodo** | Una aplicación de la misma encuesta en un momento distinto (ej. semestre, trimestre). |
| **Segmento** | Variable para desglosar resultados (tienda, comuna, carrera, área). |
| **Organización (tenant)** | Cliente de SoftInsight; sus datos están aislados de los de otros clientes. |
