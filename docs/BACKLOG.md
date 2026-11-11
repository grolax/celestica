# Backlog de Celestica

Archivo mantenido por el agente `supervisor`. **Última revisión:** 2026-11-02, contra `main` en el PR #45.

## Cómo usar este documento

| Documento | Qué responde |
| --- | --- |
| `CONTEXTO_SOFTINSIGHT.md` §4 y §5 | Qué dice cada requerimiento (RF/RNF) |
| **`docs/BACKLOG.md`** | Qué falta, en qué orden, para quién y cómo se valida |
| `docs/ESTADO.md` | Qué tareas están hechas, en curso o bloqueadas |
| `docs/tareas/T-*.md` | Cómo se construye cada tarea y sus criterios técnicos |

- **Estado de los requerimientos:** este documento manda sobre las marcas ✅ 🟡 🆕 de `CONTEXTO_SOFTINSIGHT.md` §4, que están desactualizadas.
- **Estados:** ✅ hecho · 🟡 parcial · ⬜ pendiente. Las marcas se revisaron buscando en el código y en `docs/ESTADO.md`, sin probar cada función de nuevo.
- **Pedidos surgidos en revisión (`PED-xx`):** lo que pide el responsable y no tiene un requerimiento propio.
- **Validación:** "técnica" significa pruebas y revisión del supervisor. El merge aprueba el cambio, pero no equivale a una validación funcional. **Ningún cliente real ha validado todavía el producto.**
- **Orden:** el orden de la sección 2 lo aprobó el responsable el 2026-11-02.

## 1. Épicas y avance

El avance cuenta solo requerimientos funcionales: hechos / total.

| ID | Épica | Objetivo | Requerimientos | Avance |
| --- | --- | --- | --- | --- |
| E1 | Organizaciones y roles | Que cada organización trabaje en equipo, con permisos y datos aislados | RF-01 a RF-07 | 3/7 |
| E2 | Personalización por cliente | Adaptar la plataforma a cada rubro sin tocar código | RF-10 a RF-17 | 1/8 |
| E3 | Importación de encuestas | Traer cualquier encuesta y reconocer sus preguntas | RF-20 a RF-28 | 6/9 |
| E4 | Análisis | Obtener resultados trazables de preguntas abiertas y cerradas | RF-30 a RF-38 | 5/9 |
| E5 | Experiencia guiada y asesoría | Que un usuario no experto llegue solo a un resultado útil | RF-40 a RF-47 | 1/8 |
| E6 | Informe y colaboración | Entregar informes presentables y compartibles | RF-50 a RF-57 | 4/8 |
| E7 | Plataforma y calidad | Dejar el producto seguro y confiable para publicarlo | RNF-01 a RNF-21 | Ver sección 5 |

## 2. Backlog priorizado

| # | ID | Qué | Prioridad | Épica | Lado | Depende de | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PED-01 | Pantalla para editar el marco teórico | Pedido | E2 | Frontend (T-040) | T-039 | ✅ Fusionado (PR #47); falta tu validación funcional |
| 2 | RF-43 | Panel de resultados para lectores | P0 | E5 | Ambos (T-041, T-042) | RF-30, RF-31 | 🟡 En curso |
| 3 | RF-40 | Terminar el asistente de creación (plantilla sugerida al crear) | P0 | E5 | Ambos | RF-41 | ✅ Fusionado (T-044, T-045) |
| 4 | RF-10 | Perfil de organización | P0 | E2 | Ambos | RF-02 | 🟡 T-046 y T-047 fusionadas; T-048 en PR #55 |
| 5 | RF-11 | Marca de la organización en PDF y Word | P0 | E2 | Backend | RF-10 | ⬜ |
| 6 | RF-12 | Plantillas como datos, globales y propias | P0 | E2 | Ambos | RF-02 | ⬜ |
| 7 | RF-51 | Informe integrado de abiertas y cerradas | P0 | E6 | Ambos | RF-30, RF-31 | ⬜ |

**Después de los P0:** se ordenan los P1 de la sección 4 con el responsable.

**Antes de publicar en internet:** RNF-03, RNF-04 y RNF-05 de la sección 5, sin importar el orden anterior.

## 3. Historias de usuario y criterios de validación (próximas 7)

Son criterios de producto, escritos desde quien usa la plataforma. Cada orden de trabajo los traduce a criterios técnicos. Valida el responsable del proyecto, en la plataforma y con una encuesta real cuando sea posible.

### PED-01 · Editar el marco teórico

**Como** analista, **quiero** corregir el marco teórico de un proyecto ya creado, **para** adaptar el análisis a lo que necesita ese cliente sin crear el proyecto de nuevo.

- [ ] Puedo ver el marco completo, editarlo y guardarlo sin recargar la página.
- [ ] Antes de guardar me avisan que lo ya generado no cambia y que el siguiente informe profundo vuelve a gastar IA.
- [ ] Si me paso de 5.000 caracteres, veo qué pasó y puedo corregirlo sin perder mi texto.
- [ ] Como lector, veo el marco, pero no puedo editarlo.
- [ ] En un proyecto solo con preguntas cerradas, no se me ofrece editarlo.
- [ ] El cambio aparece en Auditoría, con el texto anterior, el nuevo y quién lo hizo.

### RF-43 · Panel de resultados para lectores

**Como** gerente, alcalde o director, **quiero** ver los resultados de una encuesta en una sola pantalla, **para** entenderlos y decidir sin saber de análisis.

- [ ] Sin ayuda, puedo contar los resultados principales después de leer el panel una vez, porque no tiene jerga.
- [ ] Veo las métricas clave, los temas principales con citas y las alertas importantes.
- [ ] Cada cita aparece textual en las respuestas, y lo generado por IA está marcado como tal.
- [ ] Solo aparecen temas validados por una persona.
- [ ] Los grupos con pocas respuestas llevan su advertencia.
- [ ] Puedo imprimir el panel y leerlo en tablet y móvil.
- [ ] Funciona en proyectos con solo preguntas cerradas, sin secciones vacías.

### RF-40 · Terminar el asistente de creación

**Como** encargado sin experiencia en análisis, **quiero** que el asistente me sugiera una plantilla al crear el proyecto, **para** empezar bien sin conocer los marcos teóricos.

- [ ] Después de revisar las preguntas, veo la plantilla sugerida y por qué se sugiere.
- [ ] Puedo aceptarla, elegir otra o seguir sin plantilla.
- [ ] Si la encuesta no tiene preguntas abiertas, no se me sugiere plantilla.
- [ ] Cada paso se entiende con su propio texto de ayuda.
- [ ] Puedo llegar de subir el archivo a ver el proyecto creado sin ayuda externa.

### RF-10 · Perfil de organización

**Como** administrador, **quiero** configurar nombre, rubro, logo y color de mi organización, **para** que la plataforma refleje a quién pertenece.

- [ ] Puedo editar esos datos desde la configuración, y un analista o lector no puede.
- [ ] Si el logo o el color no sirven, me explican qué hacer.
- [ ] Un color con poco contraste no vuelve ilegible la plataforma.
- [ ] Otra organización no ve mis datos ni mi logo.
- [ ] El rubro cambia lo que se sugiere por defecto, como las plantillas.

### RF-11 · Marca en los informes

**Como** administrador, **quiero** que los informes lleven mi logo, nombre y color, **para** entregarlos como propios.

- [ ] El PDF y el Word muestran el logo, el nombre y el color en la portada y en los encabezados.
- [ ] Sin logo, el informe se ve bien y conserva la marca por defecto.
- [ ] Un logo grande o de formato poco común no descuadra el informe.
- [ ] El informe de una organización nunca muestra la marca de otra.

### RF-12 · Plantillas propias

**Como** administrador o analista, **quiero** crear plantillas o duplicar una global, **para** reutilizar la metodología de mi organización.

- [ ] Sigo viendo las 19 plantillas actuales, con el mismo contenido.
- [ ] Puedo crear una plantilla desde cero o duplicar una global y editar la copia.
- [ ] Editar mi copia no cambia la plantilla global ni los proyectos ya creados.
- [ ] Otra organización no ve mis plantillas.
- [ ] Las categorías de una plantilla siguen entrando como propuesta y yo las valido.

### RF-51 · Informe integrado

**Como** analista, **quiero** un solo informe con preguntas cerradas y abiertas, **para** entregar todos los resultados de la encuesta sin armarlos a mano.

- [ ] El informe trae gráficos de cerradas, NPS, cruces, temas y citas.
- [ ] Cada número coincide con la pantalla de resultados y se puede rastrear a sus respuestas.
- [ ] Toda cita es textual, y solo se usan categorías validadas.
- [ ] Veo temas comparados entre preguntas abiertas: los que se repiten y quiénes mencionan uno y otro.
- [ ] Esa comparación se calcula sin nuevas llamadas a la IA; la IA solo redacta sobre números ya calculados.
- [ ] Las recomendaciones van en su propia sección, marcadas como sugerencia.
- [ ] Veo el costo estimado antes de generarlo, si usa IA.
- [ ] Un proyecto solo con cerradas también obtiene un informe, sin secciones vacías.

## 4. Resto del backlog

Las historias son de una línea. Los criterios de validación se escriben cuando entran a la lista priorizada.

### P1

| ID | Épica | Historia | Estado | Falta |
| --- | --- | --- | --- | --- |
| RF-04 | E1 | Como administrador, quiero invitar personas por enlace o correo para sumarlas sin entregar contraseñas temporales. | 🟡 | Enlace o correo; ya se crean y desactivan miembros |
| RF-05 | E1 | Como usuario, quiero recuperar mi contraseña y verificar mi correo para no depender del administrador. | ⬜ | Todo |
| RF-06 | E1 | Como asesor, quiero entrar a las organizaciones que me autoricen para acompañarlas, con mis accesos auditados. | ⬜ | Todo |
| RF-07 | E1 | Como superadministrador, quiero un panel interno para gestionar organizaciones y consumo sin una contraseña global. | 🟡 | Sigue con `ADMIN_PASSWORD` y sin vista por organización |
| RF-13 | E2 | Como administrador, quiero definir cómo se llama a quien responde y a la unidad de análisis para que la plataforma hable como mi rubro. | ⬜ | Todo |
| RF-14 | E2 | Como analista, quiero stopwords y lexicón según mi rubro para que el léxico no arrastre términos universitarios. | 🟡 | Hoy son listas fijas |
| RF-16 | E2 | Como administrador, quiero plantillas de informe por tipo de cliente para ajustar secciones, extensión y tono. | ⬜ | Todo |
| RF-27 | E3 | Como analista, quiero importar una nueva medición en el mismo proyecto para reutilizar el libro de códigos validado. | ⬜ | Todo |
| RF-31 | E4 | Como analista, quiero ver también los temas abiertos por grupo para saber quién menciona qué. | 🟡 | Temas por grupo. RF-31 es P0, pero el usuario dejó esta parte para después (2026-10-31); las cerradas ya están hechas |
| RF-35 | E4 | Como analista, quiero cruzar temas con preguntas cerradas en resultados para ver, por ejemplo, qué mencionan los detractores. | 🟡 | Hoy solo dentro del informe profundo |
| RF-37 | E4 | Como analista, quiero comparar olas para ver qué mejoró o empeoró. | ⬜ | Depende de RF-27 |
| RF-38 | E4 | Como analista, quiero ver el costo estimado antes de lanzar IA para decidir con la información a la vista. | 🟡 | Hoy el costo se ve después |
| RF-42 | E5 | Como usuario no experto, quiero un modo guiado para no enfrentar pasos metodológicos avanzados. | ⬜ | Todo |
| RF-44 | E5 | Como gerente, quiero siguientes pasos sugeridos, separados de los hallazgos, para pasar a la acción. | ⬜ | Todo |
| RF-45 | E5 | Como usuario, quiero explicaciones breves donde aparece cada concepto para entenderlo sin salir de la pantalla. | 🟡 | Hay ayudas puntuales, no en toda la plataforma |
| RF-47 | E5 | Como cliente nuevo, quiero datos de demostración de mi rubro para probar el flujo antes de subir los míos. | 🟡 | Solo hay evaluación docente |
| RF-53 | E6 | Como analista, quiero editar el informe antes de exportarlo, distinguiendo lo humano de lo generado por IA. | ⬜ | Todo |

### P2

| ID | Épica | Historia | Estado |
| --- | --- | --- | --- |
| RF-15 | E2 | Como asesor, quiero ajustar prompts por organización, con historial, para adaptar el método sin afectar a otros. | ⬜ |
| RF-26 | E3 | Como analista, quiero importar desde Microsoft Forms y SurveyMonkey para no pasar por un archivo. | ⬜ |
| RF-28 | E3 | Como analista, quiero sincronizar Qualtrics y usar OAuth de Google para traer datos sin hacerlo a mano. | ⬜ |
| RF-46 | E5 | Como cliente, quiero pedir la revisión de un asesor desde la plataforma para recibir acompañamiento auditado. Depende de la decisión abierta §10.4. | ⬜ |
| RF-54 | E6 | Como gerente, quiero un PowerPoint ejecutivo para presentar los resultados. | ⬜ |
| RF-55 | E6 | Como analista, quiero un enlace de solo lectura, revocable y con expiración, para compartir con personas sin cuenta. | ⬜ |

### Pedidos sin prioridad asignada

| ID | Épica | Historia | Origen |
| --- | --- | --- | --- |
| PED-08 | E3 | Como analista, quiero convertir escalas con palabras a 1–5, ordenando las etiquetas, para obtener promedios y notas altas. | Pendiente posterior del usuario (`ESTADO.md`) |
| PED-09 | E3 | Como analista, quiero unir columnas ramificadas en un proyecto ya creado para corregir lo que no uní al crearlo. | Candidata; solo si el usuario la pide (`ESTADO.md`) |

## 5. Requerimientos no funcionales pendientes

`CONTEXTO_SOFTINSIGHT.md` no les asigna prioridad. La columna "Cuándo" es una propuesta. No se listan los RNF sin falta detectada.

| ID | Tema | Estado | Falta | Cuándo |
| --- | --- | --- | --- | --- |
| RNF-03 | Secretos | 🟡 | `SECRET_KEY` y `ADMIN_PASSWORD` tienen valores por defecto, y el servidor no se niega a arrancar con ellos | Antes de publicar |
| RNF-04 | Producción | 🟡 | Límite de intentos de login, revocar sesiones, cabeceras de seguridad, y CORS configurable (hoy fijo a localhost) | Antes de publicar |
| RNF-05 | Privacidad | 🟡 | A la IA ya solo va el contexto marcado; falta enmascarar datos en el texto, y la política de retención y borrado | Antes de publicar |
| RNF-08 | Costos de IA | 🟡 | El consumo se registra; falta el tope por organización con aviso | Antes de abrir a clientes |
| RNF-12 | Procesos largos | ⬜ | El avance vive en memoria y se pierde al reiniciar | Junto con RF-51 |
| RNF-10 | Rendimiento | 🟡 | Cruce con 120 grupos en 3,5 s (meta: 2 s) | Con encuestas de mayor volumen |
| RNF-11 | Escalabilidad | ⬜ | Respuestas fuera del documento del proyecto, sin validar con 50.000 | Con el primer cliente grande |
| RNF-14 | Accesibilidad | 🟡 | `select` sin etiqueta en Auditoría y Libro de códigos; sin auditoría AA completa | Con RF-43 |
| RNF-18 | Pruebas | 🟡 | Suite Playwright para los flujos críticos | Con RF-42 |
| RNF-20 | Observabilidad | 🟡 | Logs por petición con `org_id` y `project_id`, y salud pública (hoy solo `/api/admin/health`) | Antes de publicar |

## 6. Lo ya hecho y su trazabilidad

### Requerimientos

| ID | Épica | Qué | Tareas | Validación |
| --- | --- | --- | --- | --- |
| RF-01 | E1 | Registro e inicio de sesión | MVP v1.1 | Línea base |
| RF-02 | E1 | Organizaciones | T-004, T-005 | Técnica |
| RF-03 | E1 | Roles y permisos | T-006, T-007, T-008a, T-008b | Técnica, con cuentas de prueba |
| RF-17 | E2 | Plantillas Retail y Municipal | T-031 | Técnica; contenido en borrador, sin validar con encuestas reales |
| RF-20, RF-21 | E3 | Archivos, Qualtrics y Google Forms | MVP v1.1 | Línea base |
| RF-22 | E3 | Detección de tipos | T-010, T-012 | Técnica, con encuesta real |
| RF-23 | E3 | Varias preguntas abiertas | T-011a, T-013, T-019 | Técnica, con encuesta real |
| RF-24 | E3 | Proyectos sin abiertas | T-025, T-026 | Técnica, con encuesta real |
| RF-25 | E3 | Vista previa y corrección de tipos | T-010, T-012, T-037, T-038 | Técnica; boceto de T-012 aprobado por el responsable |
| RF-30 | E4 | Resultados de cerradas | T-020, T-021 | Técnica, con encuesta real |
| RF-32, RF-33, RF-34, RF-36 | E4 | Léxico, libro de códigos, codificación y trazabilidad | MVP v1.1 (ajustes en T-029, T-030) | Línea base |
| RF-41 | E5 | Recomendaciones automáticas | T-032, T-033, T-034, T-035, T-036 | Técnica; el responsable revisó la pantalla y pidió T-034 a T-038 |
| RF-50, RF-52, RF-56, RF-57 | E6 | Informes, exportación, comentarios y auditoría | MVP v1.1 (ajustes en T-017, T-011a) | Línea base |

**Parciales con parte hecha:** RF-04 (T-007, T-008b), RF-31 (cerradas: T-022, T-023, T-024, T-035, T-036) y RF-40 (T-012, T-026).

### Pedidos surgidos en revisión

| ID | Qué | Tareas | Estado |
| --- | --- | --- | --- |
| PED-01 | Editar el marco teórico después de crear el proyecto | T-039, T-040 | ✅ Fusionado; falta la validación del responsable |
| PED-02 | Excel de cerradas con grupos y gráficos | T-027, T-028 | ✅ Visual aprobada por el responsable (T-027) |
| PED-03 | No lanzar dos veces el léxico ni la propuesta, y retomarlos al volver | T-029, T-030 | ✅ |
| PED-04 | Alertas agrupadas y etiqueta "Poco respondida" | T-034 | ✅ |
| PED-05 | Cruce de 2 preguntas con pares sugeridos | T-035, T-036 | ✅ |
| PED-06 | Corregir el tipo de una pregunta cerrada ya creada | T-037, T-038 | ✅ |
| PED-07 | Identidad Celestica, página de presentación y orden visual | T-014, T-015, T-016a, T-016b, T-017, T-018 | ✅ |

### Trabajo técnico

| Tema | Tareas |
| --- | --- |
| Herramientas y pruebas base | T-000, T-001 |
| Pruebas de aislamiento (RNF-01) | T-002 |
| Código por routers (RNF-17, backend) | T-003a, T-003b |
| Arreglo del panel interno | T-009 |

## 7. Decisiones

**Tomadas por el responsable (2026-11-02):**
1. Se aprueba el orden de la sección 2.
2. RF-51 se hace con una estructura única, sin esperar a RF-16.
3. En RF-43, con varias preguntas abiertas, el lector ve un resumen por pregunta en la misma pantalla.

**Decisiones abiertas de `CONTEXTO_SOFTINSIGHT.md` §10 que frenan requerimientos:**
- §10.2, planes y límites: RNF-08.
- §10.3, despliegue y región de datos: RNF-04, RNF-05 y RNF-19.
- §10.4, asesoría dentro del producto o externa: RF-06 y RF-46.
