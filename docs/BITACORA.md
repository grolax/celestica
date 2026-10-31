# Bitácora de desarrollo — SoftInsight

**Qué es este documento:** el registro, en orden, de cada cambio que se hace a la plataforma SoftInsight, con su motivo y su resultado. Está escrito para todo el equipo de SoftInsight: no hace falta saber programar para entenderlo.

**Quién lo actualiza:** el supervisor técnico (Claude), cada vez que se hace un cambio. El responsable del proyecto (Israel) aprueba qué se publica.

**Última actualización:** 31 de octubre de 2026

---

## Cómo leer esta bitácora

Cada entrada responde tres preguntas:

- **Qué se hizo:** el cambio, en lenguaje simple.
- **Por qué:** el problema que resuelve o la necesidad que cubre.
- **Resultado:** cómo quedó y qué falta, si algo falta.

Al final hay un **glosario** con los términos técnicos que aparecen.

### Cómo trabaja el equipo

| Quién | Qué hace |
| --- | --- |
| **Responsable del proyecto** (persona) | Toma las decisiones de producto y aprueba cada cambio antes de que pase a la versión oficial. |
| **Supervisor técnico** (Claude) | Planifica el trabajo, escribe las instrucciones de cada tarea, revisa lo que hacen los programadores y lleva esta bitácora. No programa. |
| **Programador backend** (Claude) | Construye la parte "interna": servidor, base de datos, cálculos e inteligencia artificial. |
| **Programador frontend** (Claude) | Construye la parte "visible": las pantallas que usa el cliente. |

Cada cambio sigue el mismo camino: **instrucción escrita → programación → revisión del supervisor → aprobación del responsable → incorporación a la versión oficial.** Ningún cambio llega a la versión oficial sin la aprobación del responsable del proyecto.

---

## Resumen del estado actual

| Tarea | De qué se trata | Estado |
| --- | --- | --- |
| Plan de la etapa | Hoja de ruta de las próximas mejoras | ✅ Aprobado por el responsable |
| T-000 | Actualizar herramientas de construcción de las pantallas | ✅ Incorporada a la versión oficial |
| T-001 | Reparar las pruebas automáticas del sistema | ✅ Incorporada a la versión oficial |
| T-014 | Nueva identidad visual: nombre Celestica, colores azul y blanco, iconos minimalistas | ✅ Incorporada a la versión oficial |
| T-015 | Página pública de presentación con acceso "Iniciar sesión" | ✅ Incorporada a la versión oficial |
| T-016 | Orden visual del área de trabajo (en dos partes: T-016a y T-016b) | ✅ Incorporada a la versión oficial (T-016a y T-016b) |
| T-017 | Nombre y colores Celestica en los informes PDF y Word | ✅ Incorporada a la versión oficial |
| T-002 | Hacer obligatorias las pruebas de seguridad entre clientes | ✅ Incorporada a la versión oficial |
| T-003 | Ordenar el código del servidor en archivos por tema (en dos partes: T-003a y T-003b) | ✅ Incorporada a la versión oficial (T-003a y T-003b) |
| T-004 | Organizaciones: los proyectos pasan a pertenecer a la organización | ✅ Incorporada a la versión oficial |
| T-005 | Mostrar la organización y el rol en pantalla | ✅ Incorporada a la versión oficial |
| T-006 a T-008 | Roles y gestión de miembros | ✅ Incorporadas a la versión oficial (T-006, T-007, T-008a y T-008b) |
| T-010 a T-013 | Encuestas completas: tipos de pregunta y varias preguntas abiertas | ✅ Incorporadas a la versión oficial (T-010, T-011a, T-012 y T-013) |
| T-019 | Arreglo: el servidor no permite codificar dos veces a la vez la misma pregunta | ✅ Incorporada a la versión oficial |
| T-020 | Números de las preguntas cerradas, calculados sin IA (servidor) | ✅ Incorporada a la versión oficial |
| T-021 | Pantalla "Preguntas cerradas" | ✅ Incorporada a la versión oficial |
| T-022 | Resultados de las cerradas separados por grupo (servidor) | 🟡 Aprobada; esperando la aprobación del responsable (PR #27) |
| T-009 | Arreglo: una contraseña mal escrita en el panel interno ya no cierra la sesión | ✅ Incorporada a la versión oficial |

---

## 14 de octubre de 2026

### 1. Diagnóstico inicial de la plataforma

- **Qué se hizo:** se revisó la documentación del producto y el código actual de SoftInsight (versión 1.1), y se ejecutaron todas las pruebas automáticas.
- **Por qué:** antes de planificar mejoras hay que saber en qué estado real está el sistema.
- **Resultado:** aparecieron tres problemas:
  1. **7 de las 14 pruebas automáticas fallaban.** Faltaba un archivo de configuración de los textos que guían a la IA. En el computador del desarrollador original existía, pero no se guardaba en el repositorio.
  2. **Las pruebas que verifican que un cliente no pueda ver los datos de otro no corrían de forma automática;** había que ejecutarlas a mano. Hoy pasan, pero nada impide que en el futuro se rompan sin que nadie lo note.
  3. **Había cambios sin registrar** en las herramientas de construcción de las pantallas. El responsable confirmó que eran suyos y que debían conservarse.

### 2. Plan de trabajo de la nueva etapa

- **Qué se hizo:** se escribió la hoja de ruta para llevar SoftInsight de su versión actual a una plataforma para organizaciones: varias personas por cliente con distintos permisos, encuestas con preguntas cerradas (escalas, NPS, sí/no) y no solo abiertas, y un asistente paso a paso para usuarios no expertos.
- **Por qué:** el documento de producto define estos objetivos. El plan los ordena por prioridad y por dependencia (por ejemplo, no se pueden crear permisos por rol antes de que exista la "organización").
- **Resultado:** plan organizado en 5 fases con puntos de control entre ellas. El responsable tomó cuatro decisiones:
  1. Conservar la actualización de herramientas que había hecho.
  2. **Cada usuario pertenece a una sola organización.** Más adelante, solo los asesores de SoftInsight podrán acompañar a varias.
  3. Incluir desde ya una **gestión básica de miembros:** el administrador de la organización podrá agregar y quitar personas, sin envío de correos por ahora.
  4. Aprobar los **permisos por rol:**
     - **Lector:** ve resultados, descarga informes y comenta.
     - **Analista:** hace todo el trabajo de análisis, incluido borrar proyectos.
     - **Administrador:** lo mismo que el analista, más la gestión de su organización y sus miembros.

### 3. T-000 · Actualización de las herramientas de construcción de las pantallas

- **Qué se hizo:** se actualizaron las herramientas con que se construyen las pantallas (Vite a la versión 8 y React Router a la 7). Además, se reemplazó un componente que no era compatible con la nueva versión.
- **Por qué:** el sistema funcionaba en el computador del desarrollador, pero **una instalación desde cero (por ejemplo, al publicar la plataforma en internet) podía fallar** por esa incompatibilidad.
- **Resultado:** se verificó que la plataforma se instala y se construye desde cero sin errores, y se cambió el requisito mínimo de instalación (Node.js 20.19 o superior). Las pantallas no cambiaron en nada visible. Fue aprobada por el responsable e incorporada a la versión oficial (cambio #1 en GitHub).
- **Pendiente menor:** abrir la plataforma en el navegador y confirmar que no aparecen avisos nuevos. Le corresponde al responsable.

### 4. T-001 · Reparación de las pruebas automáticas

- **Qué se hizo:** la plataforma ahora usa los textos de IA "de fábrica" cuando no encuentra la versión personalizada. Si existe una versión personalizada, esta tiene prioridad.
- **Por qué:** sin esto, 7 pruebas fallaban en cualquier computador nuevo. **No se puede aprobar ningún cambio futuro con pruebas fallando**, así que era la primera reparación necesaria.
- **Revisión del supervisor:** se pidió una corrección. Al "restaurar" un texto a su versión de fábrica, el sistema lo guardaba como copia fija, y ese texto ya no habría recibido las mejoras futuras. El programador lo corrigió en la primera ronda.
- **Resultado:** **las 18 pruebas pasan** (antes fallaban 7 de 14; se agregaron 4 nuevas). Las pruebas de seguridad entre clientes siguen pasando. Ningún texto de la IA cambió de contenido.
- **Estado:** aprobada por el supervisor y publicada para revisión del responsable (cambio #2 en GitHub). **Espera su aprobación.**

### 5. Creación de esta bitácora

- **Qué se hizo:** se creó este registro de cambios. Primero estaba dentro del código del proyecto. A pedido del responsable, se trasladó a esta carpeta compartida y se reescribió en lenguaje para todo el equipo.
- **Por qué:** para que cualquier persona de SoftInsight pueda seguir qué se cambió, cuándo y por qué, sin entrar al código.
- **Resultado:** este documento. Se actualiza con cada cambio.

---

## 15 de octubre de 2026

### 6. T-001 incorporada a la versión oficial

- **Qué se hizo:** el responsable aprobó e incorporó la reparación de las pruebas automáticas (cambio #2 en GitHub).
- **Resultado:** la versión oficial ya tiene todas sus pruebas en verde. Desde aquí se puede construir con seguridad.

### 7. Nueva prioridad: diseño de la experiencia (UX/UI)

- **Qué se hizo:** el responsable decidió priorizar el diseño, porque hoy es lo más débil para el usuario. Pidió:
  1. Una **página de presentación pública**, la carta de presentación para quien llega desde fuera: quiénes somos, nuestro objetivo y qué hace la plataforma.
  2. Una pestaña **"Iniciar sesión"** en la parte superior, que lleve al área de trabajo actual.
  3. Un diseño **sobrio, entendible y con separaciones claras**, en **azules (incluido el celeste) y blanco**.
- **Decisiones del responsable que quedan registradas:**
  - **El nombre oficial del programa es Celestica.** SoftInsight sigue como nombre del equipo detrás del producto. Esto cierra una de las preguntas abiertas del documento de producto.
  - **Cambio de colores:** sale el fondo crema y entran el blanco y los azules. La tipografía (Inter) se mantiene.
  - El diseño va **antes** que la siguiente tarea técnica (T-002), que queda pospuesta.
- **Cómo se organizó:** en cuatro tareas cortas, para revisar cada una por separado:
  - **T-014 · Identidad visual:** colores, nombre Celestica en todas las pantallas y separaciones más claras. Incluye una regla de accesibilidad: el texto debe leerse bien, con contraste suficiente según la norma internacional WCAG AA. Por eso el celeste se usa como acento y no para textos pequeños, porque sobre blanco se lee poco.
  - **T-015 · Página de presentación:** la portada pública, con el área de trabajo en una dirección propia (`/proyectos`) y una página de acceso más simple. Funciona también en celular.
  - **T-016 · Orden del área de trabajo:** cada pantalla con título y una línea de ayuda, menú lateral agrupado y pasos del análisis claramente marcados.
  - **T-017 · Informes PDF y Word:** que digan Celestica en vez de SoftInsight.
- **Pendiente del responsable:** revisar los **textos de la página de presentación**. El supervisor escribió un borrador, sobre todo el de "Quiénes somos", que debe validar alguien del equipo. La página solo menciona funciones que la plataforma **ya tiene**, para no prometer nada que aún no existe.
- **Estado:** T-014 en desarrollo.

### 8. Traslado de esta bitácora

- **Qué se hizo:** se retiró la versión antigua de la bitácora que estaba dentro del código del proyecto.
- **Por qué:** desde ahora vive solo aquí, para que haya una única versión.

### 9. T-014 · Nueva identidad visual Celestica

- **Qué se hizo:**
  - **Nombre:** toda la plataforma dice **Celestica**: título de la pestaña del navegador, logo (una "C"), menú, acceso, documentación, configuración e informe en pantalla.
  - **Colores:** fondo blanco con un gris azulado muy suave en lugar del crema. Los títulos van en azul marino, los botones y enlaces en azul, y el celeste como detalle decorativo.
  - **Separaciones:** tarjetas con borde visible y una línea bajo cada título, encabezado y menú lateral bien delimitados, y tablas con filas alternadas. Se quitaron los degradados para lograr un aspecto más sobrio.
  - **Colores de estado:** verde, naranja y rojo (aprobado, revisar, error) se oscurecieron levemente para que se lean bien.
  - **Teclado:** quien navega con la tecla Tab ve un contorno azul claro alrededor del elemento seleccionado.
- **Por qué:** es la base visual que pidió el responsable. Al cambiarla en un solo lugar, todas las pantallas existentes la heredan sin rehacerlas una por una.
- **Cómo se verificó:** el programador revisó a mano el acceso, la lista de proyectos, un proyecto y la configuración. El supervisor revisó todos los cambios, confirmó que la plataforma se construye sin errores y recalculó el contraste de los colores. **Todos los textos cumplen la norma de accesibilidad WCAG AA.** El celeste no la cumple como color de texto, por eso se usa solo como adorno.
- **Pendiente:**
  - Confirmar si el correo de soporte que aparece en Documentación (`soporte@softinsight.cl`) se mantiene o cambia.
  - Las pantallas internas de análisis se revisarán con detalle en T-016.
- **Estado:** aprobada por el supervisor. Espera que el responsable autorice publicarla (pull request).

---


### 10. T-014 · Ajustes pedidos por el responsable tras ver la plataforma

- **Qué se hizo:** el responsable revisó la plataforma en su navegador y pidió dos ajustes, recordando que el diseño debe ser sobrio:
  1. **Iconos minimalistas en lugar de emojis.** Los emojis del menú (📁, 📖, ⚙️), de los botones de descarga, de editar y de comentar, y de otros lugares, se cambiaron por iconos de línea fina, del mismo color que el texto: gris en reposo y azul en el elemento seleccionado. Los iconos se dibujan dentro del propio código, sin agregar programas externos.
  2. **Presentación más breve.** El bloque de bienvenida de la pantalla de acceso quedó en un título, una línea y tres puntos cortos con icono.
- **Además:** con el mismo criterio, se acortaron los textos de la futura **página de presentación pública** (T-015). Queda con cuatro secciones: portada, "Quiénes somos" y "Nuestro objetivo" lado a lado, cuatro tarjetas de "Qué hace Celestica" y el pie de página.
- **Cómo se verificó:** el supervisor revisó todos los cambios y confirmó que la plataforma se construye sin errores y que no se agregaron componentes externos.
- **Estado:** T-014 publicada para revisión del responsable en GitHub (PR #3: https://github.com/grolax/celestica/pull/3). **Espera su aprobación.**

---

## 30 de octubre de 2026

### 11. T-014 incorporada a la versión oficial

- **Qué se hizo:** el responsable aprobó e incorporó la nueva identidad visual Celestica (PR #3 en GitHub).
- **Resultado:** la versión oficial ya muestra el nombre Celestica, los colores azul y blanco y los iconos de línea.

### 12. Textos de la página de presentación aprobados

- **Qué se hizo:** el responsable revisó y ajustó los textos de la página pública (T-015):
  - **Frase principal:** "De la encuesta al informe en minutos".
  - **Quiénes somos:** "Somos Celestica: análisis social, metodología y tecnología al servicio de las organizaciones que escuchan a su gente."
  - **Nuestro objetivo:** "Que pasar de las respuestas a las decisiones tome minutos, no semanas, con cada objetivo respaldado por evidencia."
  - La línea bajo la frase principal y las cuatro tarjetas se mantienen como estaban en el borrador.
- **Otra decisión:** por ahora se mantiene el correo de soporte `soporte@softinsight.cl` en la Documentación.
- **Estado:** T-015 en desarrollo.

### 13. La bitácora pasa al repositorio

- **Qué se hizo:** a pedido del responsable, esta bitácora se trasladó a `docs/BITACORA.md`, dentro del repositorio del proyecto.
- **Por qué:** para que todo el equipo vea los avances en GitHub, junto con el código.

---

### 14. T-015 · Página pública de presentación

- **Qué se hizo:**
  - Al entrar a Celestica, ahora se ve primero una **página de presentación**: portada, "Quiénes somos" y "Nuestro objetivo", cuatro tarjetas de "Qué hace Celestica" y un pie de página. Arriba hay una barra con el botón **"Iniciar sesión"**. Si la persona ya inició sesión, el botón dice **"Ir a mi espacio"**.
  - La lista de proyectos se trasladó a la dirección `/proyectos`. Todos los enlaces internos se actualizaron.
  - Las pantallas de acceso y registro quedaron más simples: solo el formulario, con un enlace "Volver al inicio".
- **Por qué:** quien llega desde fuera necesita saber qué es Celestica antes de entrar.
- **Cómo se verificó:** la plataforma se construye sin errores y las 18 pruebas automáticas siguen pasando. Se revisó la página en computador, tablet y celular, y se recorrió completa con el teclado.
- **Pendiente:** que el responsable pruebe una vez el ingreso real con su cuenta.
- **Estado:** aprobada por el supervisor. Espera que el responsable autorice publicarla.

---

### 15. T-015 incorporada y decisiones para las siguientes tareas

- **T-015:** el responsable aprobó e incorporó la página de presentación (PR #4 en GitHub).
- **T-017 · Informes:** los PDF y Word dirán **Celestica** y usarán los mismos azules de la plataforma. El pie de página será "Análisis realizado con Celestica · Auditable y trazable" y los archivos descargados se llamarán `informe_celestica_...`.
- **Nombre interno:** por ahora, el nombre técnico interno (servidor, base de datos, registros) sigue siendo SoftInsight, para evitar confusiones. Nadie fuera del equipo técnico lo ve.
- **T-016 · Área de trabajo:** el responsable aprobó las líneas de ayuda de las 12 pantallas. La tarea se dividió en dos partes para revisarla mejor: T-016a (encabezados, menú lateral y lista vacía) y T-016b (pantallas de análisis).
- **Después del diseño:** se retoma el trabajo interno (backend): pruebas de seguridad entre clientes, orden del código del servidor, organizaciones y roles.

---

### 16. T-017 · Informes PDF y Word con el nombre Celestica

- **Qué se hizo:** los informes descargables ahora dicen **Celestica** en la portada, el título, el pie de página ("Análisis realizado con Celestica · Auditable y trazable") y la nota de metodología. Usan los mismos azules de la plataforma: azul marino para los títulos y azul para las tablas y los gráficos. Los archivos se descargan con el nombre `informe_celestica_...`.
- **Por qué:** para que lo que el cliente recibe tenga la misma identidad que la plataforma.
- **Cómo se verificó:** se agregó una prueba automática que genera un PDF y un Word y comprueba que digan Celestica y no SoftInsight. Las 19 pruebas pasan.
- **Pendiente menor:** en el Word, las tablas toman el azul propio de Word, que es parecido pero no igual al de Celestica.
- **Estado:** incorporada a la versión oficial por el responsable (PR #5 en GitHub).

---

### 17. T-016a · Encabezados, menú lateral y lista vacía

- **Qué se hizo:**
  - Las pantallas Mis proyectos, Nuevo proyecto, Configuración y Documentación muestran un **título con una línea de ayuda** en lenguaje simple, con los textos que aprobó el responsable.
  - El **menú lateral** se ordenó en dos grupos: "Trabajo" (Nuevo proyecto, Mis proyectos) y "Ayuda y configuración" (Documentación, Configuración).
  - El elemento seleccionado del menú y la pestaña activa de cada proyecto se marcan con **letra más gruesa y una barra o subrayado**, no solo con color, para que también los distingan quienes ven poco los colores.
  - Si alguien todavía no tiene proyectos, ve un mensaje que explica qué hacer y un botón "Crear proyecto".
- **Por qué:** para que cada pantalla diga para qué sirve y el área de trabajo se entienda sin ayuda externa.
- **Cómo se verificó:** la plataforma se construye sin errores y el supervisor revisó todos los cambios. Falta recorrerla en el navegador.
- **Estado:** incorporada a la versión oficial por el responsable (PR #6 en GitHub).

---

### 18. T-016b · Encabezados en las pantallas del análisis

- **Qué se hizo:** las 8 pestañas de cada proyecto (Resumen, Análisis léxico, Libro de códigos, Codificación, Trazabilidad, Informe, Exportar y Auditoría) empiezan ahora con su título y una línea de ayuda, con los textos que aprobó el responsable. Se quitaron las explicaciones que repetían esa línea y se dejaron las que dan más detalle.
- **Por qué:** para que quien no sabe de análisis entienda qué hace cada paso.
- **Cómo se verificó:** la plataforma se construye sin errores y el supervisor revisó todos los cambios. El informe en pantalla sigue indicando que es contenido generado por IA. Falta recorrerla en el navegador.
- **Estado:** incorporada a la versión oficial por el responsable (PR #7 en GitHub). Con esta tarea terminó la fase de diseño.

---

### 19. De vuelta al trabajo interno: T-002

- **Qué se hizo:** terminada la fase de diseño, se retomó el backend. La primera tarea es T-002.
- **De qué se trata:** hoy, las pruebas que verifican que **un cliente no pueda ver ni modificar los proyectos de otro** existen, pero hay que ejecutarlas a mano, y cubren solo 8 de las 25 operaciones que se pueden hacer sobre un proyecto. T-002 las incorpora a las pruebas automáticas y las extiende a las 25. Además, si en el futuro alguien agrega una operación nueva sin su prueba de seguridad, las pruebas fallarán y lo avisarán.
- **Por qué ahora:** la siguiente gran etapa cambia cómo se separan los datos de cada cliente (de "por usuario" a "por organización"). Antes de mover algo tan delicado, hay que tener una alarma que suene si algo se rompe.
- **Estado:** en desarrollo.

---

### 20. T-002 · Pruebas de seguridad entre clientes, ahora automáticas

- **Qué se hizo:**
  - Las pruebas que antes había que ejecutar a mano ahora corren solas, junto con todas las demás.
  - Se agregó una prueba que intenta, como un usuario ajeno, cada una de las **25 operaciones** posibles sobre un proyecto: verlo, borrarlo, editar categorías, comentar, codificar, exportar, generar el informe, etc. En todas, el sistema debe responder "no encontrado". Además, la prueba revisa que el proyecto original no haya cambiado y que la IA no se haya activado.
  - Si alguien agrega en el futuro una operación nueva sin su prueba de seguridad, las pruebas fallan y lo avisan.
- **Resultado:** **no se encontró ninguna fuga**: las 25 operaciones ya estaban protegidas. Ahora hay **51 pruebas automáticas** (antes 19) y todas pasan. Como control, se desactivó a propósito la protección de forma temporal y las pruebas lo detectaron de inmediato.
- **Por qué importa:** la siguiente etapa cambia la forma de separar los datos, de "por usuario" a "por organización". Esta alarma garantiza que ese cambio no abra una puerta sin que nadie lo note.
- **Estado:** incorporada a la versión oficial por el responsable (PR #8 en GitHub).

---

### 21. T-003 · Ordenar el código del servidor

- **Qué se hace:** casi todo el código del servidor vive hoy en un único archivo de unas 950 líneas. Se reparte en archivos por tema: proyectos, integraciones, análisis, informes y exportaciones, y administración.
- **Por qué:** es como ordenar una bodega antes de que llegue mercadería nueva. Las organizaciones y los roles tocan casi todas las operaciones. Con el código ordenado por tema, cada cambio será más fácil de hacer y de revisar, y habrá menos riesgo de error.
- **Qué NO cambia:** nada de lo que ve el usuario, ninguna dirección del servidor y ninguna respuesta. Para comprobarlo, el supervisor guardó una "huella digital" de la API antes del cambio. Después del cambio, la huella debe ser idéntica y las 51 pruebas deben pasar sin modificarlas.
- **Cómo se organizó:** en dos partes, para revisar cada una con calma. T-003a cubre la base común, los proyectos y las integraciones. T-003b cubre el análisis, los informes y la administración.
- **T-003a, resultado:** la base común, los proyectos y las integraciones ya viven en sus propios archivos. El archivo principal bajó de 948 a 639 líneas. La huella de la API quedó **idéntica** y las 51 pruebas pasan sin cambios.
- **T-003b, resultado:** el análisis, los informes y exportaciones y la administración también quedaron en sus propios archivos. El archivo principal pasó de 948 líneas al inicio a **88**, solo con la configuración. La huella de la API sigue idéntica y las 51 pruebas pasan sin cambios.
- **Estado:** incorporada a la versión oficial (PR #9 y PR #10 en GitHub).

---

### 22. T-004 · Organizaciones: decisiones y diseño

- **Qué se decidió (responsable, 30 de octubre):**
  1. Al registrarse, cada persona crea su organización y queda como su **administradora**. La organización toma el nombre escrito en "Institución / Empresa".
  2. Los usuarios actuales reciben **cada uno su propia organización**, con sus proyectos. No se unen automáticamente aunque hayan escrito la misma empresa: ese texto es libre y una unión por error mostraría datos de una persona a otra.
  3. Las credenciales de Qualtrics siguen siendo de cada persona.
  4. Para la etapa de roles: los nuevos miembros los crea el administrador con una contraseña temporal.
- **Qué cambia:** los proyectos dejan de pertenecer a una persona y pasan a pertenecer a su organización. Cada proyecto recuerda además quién lo creó. Por ahora cada organización tiene un solo miembro, así que **para el usuario todo se ve igual**. El cambio prepara el terreno para los equipos y los permisos.
- **Datos actuales:** un proceso de migración los reacomoda solo al iniciar el servidor. Está hecho para poder ejecutarse varias veces sin duplicar nada.
- **Estado:** el responsable aprobó el contrato de API y que la migración se ejecute sola al iniciar el servidor.

### 23. T-004 · Organizaciones, implementadas

- **Qué se hizo:**
  - Existe la **organización**. Cada persona que se registra crea la suya y queda como administradora.
  - Los proyectos ahora pertenecen a la organización, y la regla de seguridad pasó de "¿este proyecto es tuyo?" a **"¿este proyecto es de tu organización?"**.
  - Los datos existentes se migran solos al iniciar el servidor: cada usuario actual recibe su propia organización con sus proyectos.
- **Revisión del supervisor:** hubo una ronda de correcciones, con tres puntos:
  1. Una parte de la prueba de seguridad de T-002 había dejado de verificar que el proyecto quedara intacto. Se reparó y se agregó un control para que no vuelva a fallar en silencio.
  2. Se agregó un resguardo: si una cuenta llegara a quedar sin organización, no ve ningún proyecto.
  3. La migración automática se movió al núcleo de la aplicación, para que el servidor arranque igual cuando se publique en internet.
- **Cómo se verificó:** hay **59 pruebas automáticas** y todas pasan. Las 25 operaciones sobre proyectos se prueban ahora entre organizaciones distintas. Hay pruebas nuevas del registro, de dos personas de la misma organización que comparten proyectos y de la migración: no une a usuarios con la misma empresa y, si se ejecuta dos veces, no cambia nada.
- **Para el usuario:** todavía no cambia nada visible. Cada organización tiene un solo miembro hasta que lleguen los roles (RF-03).
- **Estado:** incorporada a la versión oficial por el responsable (PR #11 en GitHub).

---

### 24. Primera vista general y T-005

- **Qué se hizo:** el responsable levantó la plataforma en su computador para ver cómo se ve tras la fase de diseño. Se hizo sin clave de IA, así que no hubo ningún gasto.
- **T-005:** tarea corta de pantallas. El encabezado y Configuración mostrarán el nombre de la organización y el rol de la persona (Administrador, Analista o Lector). En el registro, el campo "Institución / Empresa" pasa a llamarse "Organización (institución o empresa)", porque ese texto es ahora el nombre de la organización.
- **Resultado:** el encabezado muestra la organización bajo el nombre de la persona, y Configuración muestra "Organización" y "Rol: Administrador". Se verificó registrando una cuenta de prueba en la plataforma local, sin usar IA.
- **Estado:** incorporada a la versión oficial por el responsable (PR #12 en GitHub).

### 25. Roles y miembros: decisiones y diseño

- **Qué se decidió (responsable, 30 de octubre):**
  1. Quien recibe una contraseña temporal **debe cambiarla** en su primer ingreso. Cualquier persona podrá cambiar su contraseña.
  2. "Quitar" a un miembro significa **desactivarlo**: no puede volver a entrar, pero su nombre se conserva en la auditoría y en los proyectos que creó.
  3. Una organización **nunca puede quedar sin un administrador activo**.
  4. El administrador puede **cambiar el rol** de cualquier miembro.
  5. El lector solo puede **borrar sus propios comentarios**.
- **Cómo se organizó:** en tres tareas:
  - **T-006:** el servidor verifica en cada operación que el rol de la persona la permita.
  - **T-007:** las operaciones para gestionar miembros.
  - **T-008:** la pantalla "Miembros" y ocultar los botones que cada rol no puede usar.
- **Un detalle de diseño:** la contraseña temporal la **genera el sistema**, no el administrador, y se muestra **una sola vez** al crear al miembro. Así no se usan contraseñas fáciles de adivinar, y nadie puede consultarla después.
- **Estado:** el responsable aprobó los contratos, incluida la contraseña temporal generada por el sistema. T-006 en desarrollo.

---

### 26. T-006 · Permisos por rol

- **Qué se hizo:** el servidor ahora revisa, en cada operación, que el rol de la persona la permita:
  - **Lector:** ver, descargar y comentar.
  - **Analista y administrador:** además crear, analizar y borrar proyectos.
  - Si alguien intenta algo que su rol no permite, ve: *"Tu rol (Lector) no permite esta acción."*
  - El lector solo puede borrar sus propios comentarios.
- **Hallazgo en la revisión:** el programador descubrió que una de las pruebas de seguridad de T-002 había dejado de vigilar sin avisar. Era la que alerta si se agrega una operación nueva sin su prueba de acceso cruzado, y se rompió cuando se ordenó el código del servidor (T-003). **No hubo ninguna fuga:** las pruebas que verifican que un ajeno no ve nada siguieron funcionando, y hoy todas las operaciones están cubiertas. El supervisor debió detectarlo en la revisión de T-003 y no lo hizo. Se corrigió en esta tarea, y la prueba ahora falla si no encuentra operaciones que revisar.
- **Cómo se verificó:** hay **99 pruebas automáticas** (antes 59) y todas pasan. Las nuevas cubren cada operación con cada rol, comprueban que la IA no se active cuando un lector intenta analizar, y fallan si se agrega una operación sin declarar quién puede usarla.
- **Estado:** incorporada a la versión oficial por el responsable (PR #13 en GitHub). T-007 (gestión de miembros) en desarrollo.

---

### 27. T-007 · Gestión de miembros

- **Qué se hizo** (en el servidor; la pantalla llega con T-008):
  - El administrador puede ver los miembros de su organización, **crear** uno nuevo (email, nombre y rol), **cambiarle el rol**, **desactivarlo** y **reactivarlo**.
  - Al crear un miembro, el sistema genera una **contraseña temporal** de 12 caracteres, sin letras que se confundan como la "O" y el "0". Se muestra **una sola vez**: en la base de datos solo queda cifrada, y no aparece en la auditoría ni en los registros.
  - Quien entra con una contraseña temporal **solo puede cambiarla**. Hasta hacerlo, todo lo demás está bloqueado.
  - Cualquier persona puede cambiar su contraseña.
  - Un miembro desactivado no puede entrar, y si tenía la sesión abierta, se le corta en ese momento. Sus proyectos siguen en la organización con su nombre como creador.
  - La organización **nunca queda sin un administrador activo**, y nadie puede desactivarse a sí mismo.
  - Cada alta, cambio de rol, desactivación y cambio de contraseña queda en la auditoría.
- **Cómo se verificó:** hay **113 pruebas automáticas** y todas pasan. Una de ellas recorre todas las operaciones de la plataforma con una cuenta que aún tiene la contraseña temporal y confirma que ninguna la deja pasar.
- **Pendientes menores:**
  - Cambiar la contraseña todavía no cierra las otras sesiones abiertas de esa persona. Se resolverá con la seguridad de producción.
  - Si dos administradores se quitaran el rol mutuamente en el mismo instante, la organización podría quedar sin administrador. Es muy improbable.
- **Estado:** incorporada a la versión oficial por el responsable (PR #14 en GitHub).

### 28. T-008 · Las pantallas de roles y miembros

- **Cómo se organizó:** en dos partes.
  - **T-008a, la cuenta:** la pantalla para cambiar la contraseña, que es obligatoria después del primer ingreso con contraseña temporal y también está disponible desde Configuración. Además, un aviso claro cuando la cuenta fue desactivada.
  - **T-008b, el equipo:** la pantalla "Miembros" para el administrador, y que cada persona vea solo los botones que su rol permite. El lector verá una marca de **"Solo lectura"** en cada proyecto.
- **Textos propuestos por el supervisor**, que el responsable puede ajustar:
  - El aviso de contraseña temporal: "Por seguridad, cambia la contraseña temporal que te entregó tu administrador antes de continuar."
  - La explicación de cada rol en la pantalla Miembros.
- **T-008a, resultado:** quien entra con una contraseña temporal es llevado a cambiarla antes de seguir. En Configuración hay un botón para cambiar la contraseña. Si alguien es desactivado con la sesión abierta, vuelve al inicio de sesión y ve el aviso. Se verificó en la plataforma local con cuentas de prueba, sin usar IA.
- **Hallazgo:** ya existía un error. Si alguien escribe mal la contraseña del panel interno de prompts, la plataforma le cierra la sesión. Quedó anotado para corregirlo en una tarea corta.
- **Estado:** T-008a aprobada por el supervisor; espera que el responsable autorice publicarla. T-008b en cola.

---

### 29. T-009 · Arreglo del panel interno

- **Qué se hizo:** si alguien escribe mal la contraseña del panel interno de prompts, el servidor ahora responde "no tienes permiso" en vez de "tu sesión venció". Así la persona **no pierde su sesión** y sigue viendo "Contraseña incorrecta.".
- **Por qué:** el error lo encontró el programador durante T-008a, y el responsable pidió corregirlo cuanto antes.
- **Cómo se verificó:** hay **128 pruebas automáticas** y todas pasan. Las nuevas prueban las 5 operaciones del panel con la contraseña correcta, con una incorrecta y sin contraseña.
- **Estado:** incorporada a la versión oficial por el responsable (PR #16 en GitHub).

---

### 30. T-008b · Pantalla de miembros y botones según el rol

- **Qué se hizo:**
  - **Grupo "Organización"** en el menú, visible solo para el administrador, con la pantalla **"Miembros"**. Ahí se ve el equipo, se agregan personas, se cambia su rol y se las desactiva o reactiva. Al agregar a alguien aparece la contraseña temporal una sola vez, con un botón "Copiar".
  - Cada persona **ve solo los botones que su rol permite**. El lector ve todas las pestañas, descarga y comenta, pero no ve los botones para crear, analizar ni borrar, y cada proyecto le muestra la marca **"Solo lectura"**. Donde se ocultó un botón importante, el lector ve un aviso breve: "Un analista de tu organización puede…".
- **Cómo se verificó:** el programador creó tres cuentas de prueba (administrador, analista y lector) en la plataforma local, sin IA. Recorrió el ciclo completo: crear al lector, entrar con su contraseña temporal y cambiarla, comentar, ascenderlo a analista, desactivarlo y reactivarlo. El supervisor revisó todos los cambios.
- **Con esto quedan completos RF-02 (organizaciones) y RF-03 (roles y miembros).**
- **Estado:** incorporada a la versión oficial por el responsable (PR #17 en GitHub).

### 31. Iteración 2: encuestas completas — decisiones y plan

- **Qué se busca:** hoy cada proyecto analiza una sola columna de texto. Ahora Celestica va a reconocer cada pregunta de la encuesta y va a poder analizar **varias preguntas abiertas** en un mismo proyecto.
- **Decisiones del responsable (30 de octubre):**
  1. **El foco es pulir lo que ya existe.** Los proyectos que solo tienen preguntas cerradas (escalas, NPS, sí/no) se dejan para después, junto con el análisis cuantitativo. Por ahora, la plataforma solo avisa.
  2. **Cuidar el gasto en IA sin perder calidad.** La IA trabaja una pregunta a la vez, solo cuando el usuario lo pide.
  3. **Un informe por pregunta abierta,** hasta que exista el informe integrado.
  4. **Los proyectos actuales siguen igual,** con su única pregunta abierta.
- **Plan en cuatro tareas:**
  - **T-010:** reconocer el tipo de cada pregunta y mostrar una vista previa. Se hace con reglas fijas, sin IA y sin costo.
  - **T-011:** guardar las preguntas en el proyecto y permitir varias preguntas abiertas.
  - **T-012:** el paso "Revisa las preguntas detectadas" al crear un proyecto, donde el usuario puede corregir cada tipo.
  - **T-013:** elegir qué pregunta abierta analizar en cada pestaña.
- **Estado:** T-010 en desarrollo.

---

### 32. Requerimiento nuevo: comparar preguntas abiertas entre sí

- **Qué se decidió:** el responsable pidió que el informe integrado (RF-51) también **compare los temas entre preguntas abiertas** de una misma encuesta. Por ejemplo, qué temas aparecen tanto en "¿qué destacarías?" como en "¿qué mejorarías?", o quiénes mencionan un tema en una pregunta y otro tema distinto en la otra.
- **Cómo se hará, cuidando el gasto:** los cruces se calculan a partir de las codificaciones que el equipo ya validó, **sin volver a llamar a la IA**. La IA solo redacta la lectura de conjunto sobre los números ya calculados.
- **Dónde quedó anotado:** en el estado del proyecto (`docs/ESTADO.md`). Falta agregarlo al documento de producto.

### 33. T-010 · La plataforma reconoce el tipo de cada pregunta

- **Qué se hizo:** antes de crear un proyecto, Celestica lee la encuesta y propone el tipo de cada columna, con una frase que explica por qué. Los tipos son: abierta, escala, NPS, sí/no, selección única o múltiple, numérica, fecha, identificador, segmento (como carrera o comuna), constante (el mismo valor en todas las filas) o vacía. También avisa si no hay preguntas abiertas, si hay muy pocas respuestas o si una columna está casi vacía.
- **Sin IA y sin costo:** la detección usa reglas fijas y **no guarda nada**. Guardar las preguntas en el proyecto es la tarea siguiente (T-011). Con una encuesta de 10.000 respuestas y 30 preguntas tarda menos de un segundo.
- **Prueba con los datos de ejemplo:** en la encuesta de evaluación docente reconoció bien la respuesta como abierta; la carrera, la asignatura, el año y el género como segmentos; el enunciado repetido como constante, y el código de respuesta como identificador.
- **Cómo se verificó:** hay **156 pruebas automáticas** y todas pasan.
- **Estado:** aprobada por el supervisor. Espera que el responsable autorice publicarla.

---

### 34. T-010 · Prueba con una encuesta real y correcciones

- **Qué se hizo:** a pedido del responsable, se probó la detección con una encuesta real sobre vivienda (500 respuestas, 47 preguntas, hecha en Google Forms). Se leyó solo en el computador del responsable: **no se subió al repositorio**, porque contiene datos de personas.
- **Qué se encontró:** la primera versión tomaba como "abiertas" **9 preguntas que en realidad eran de selección múltiple**, con opciones largas como "Comprar una vivienda propia, Viajar…". Esto habría hecho que la IA trabajara de más y **gastara sin necesidad**. Además, edad, género, región y comuna no quedaban como segmentos para cruzar resultados.
- **Resultado tras la corrección:** ahora solo quedan como abiertas las **2 preguntas que de verdad lo son**. Las de selección múltiple y los segmentos se reconocen bien. Quedan dos detalles menores, que el usuario podrá corregir en la pantalla de revisión, sin costo. Hay **168 pruebas automáticas** y todas pasan.
- **Decisiones del responsable:**
  - Las 16 columnas de comuna que Google Forms separó por región se ofrecerán unir en una sola columna "Comuna".
  - Cuando una persona **no respondió** una pregunta, la plataforma mostrará **"N/A"**. Así no parece que eligió alguna opción. "N/A" se cuenta aparte y no como una respuesta más.
- **Estado:** aprobada por el supervisor. Espera que el responsable autorice publicarla.

---

### 35. T-010 · Segunda prueba con la encuesta real: opciones con comas

- **Qué se encontró:** al revisar de nuevo la encuesta de vivienda, apareció otro error. Google Forms separa con comas las opciones marcadas, y algunas opciones **tienen comas dentro**, como "Subsidios habitacionales (DS1, DS19, DS49)" o "Invertir en depósitos a plazo, fondos mutuos, acciones…". La plataforma las cortaba en trozos falsos. Más adelante, eso habría dado **conteos y porcentajes equivocados**.
- **Qué se hizo:** en dos rondas de corrección, la plataforma aprendió a rearmar esas opciones:
  - no corta dentro de un paréntesis;
  - une los trozos que siempre aparecen juntos;
  - une al anterior todo trozo que empieza con minúscula, como "pero todavía no he buscado".
- **Resultado:** en la encuesta real, todas las opciones quedan completas y con sus conteos correctos. La pregunta "¿Cuál de estas alternativas describe mejor…?" quedó bien reconocida como selección única. Hay **176 pruebas automáticas** y todas pasan.
- **Para la pantalla de revisión (T-012):** las respuestas escritas a mano en la opción "Otro" de Google Forms se agruparán bajo "Otro".
- **Estado:** incorporada a la versión oficial por el responsable (PR #18 en GitHub).

### 36. T-011 · Guardar la encuesta completa y ordenada

- **Qué es, en simple:** hasta ahora, cada proyecto giraba en torno a **una sola columna** de texto, y el resto de la encuesta quedaba guardada sin orden. Con T-011, el proyecto guarda **la encuesta completa y ordenada**:
  - todas las preguntas, cada una con su tipo;
  - las columnas repetidas unidas en una sola, como la comuna;
  - las respuestas vacías como "N/A";
  - **un análisis separado por cada pregunta abierta**, con su propio libro de códigos, su codificación y su informe.
- **Hallazgo importante:** el informe profundo enviaba a la IA, por cada persona, **todas** las demás columnas del archivo. Eso gastaba tokens de más y, si el archivo tenía email o RUT, también los enviaba.
- **Decisión del responsable:** para el análisis, a la IA solo le importan **el género y la edad**. Desde ahora, la IA recibe solo el texto de la pregunta abierta y las columnas marcadas como contexto, que por defecto son solo género y edad. **Nombre, RUT y email nunca se envían.** Una prueba automática lo vigila. Así los informes deberían salir más baratos, sin perder calidad.
- **Proyectos existentes:** se reacomodan solos y se verán igual que hoy.
- **Para el usuario:** todavía no cambia nada visible. Las pantallas que aprovechan este orden vienen en T-012 (revisar las preguntas al crear el proyecto) y T-013 (elegir qué pregunta analizar).
- **Estado:** T-011a en desarrollo.

### 37. T-011a · Resultado y una revisión que evitó un problema grave

- **Qué quedó hecho:** el proyecto guarda la encuesta completa y ordenada, con un análisis separado por cada pregunta abierta. A la IA solo le llega el texto de la pregunta y, como contexto, **edad y género**, incluso cuando la edad viene como número. Nombre, RUT y email nunca se envían.
- **El problema que se encontró en la revisión:** las pruebas automáticas usan una base de datos simulada. El supervisor hizo **una copia de la base de datos real** del responsable, con 11 proyectos, entre ellos la encuesta de vivienda, y probó ahí. Descubrió que **la migración no se ejecutaba al iniciar el servidor**. Si se hubiera publicado así, los proyectos existentes no se habrían podido abrir.
- **Correcciones:**
  - La migración ahora se ejecuta al arrancar.
  - Si un proyecto viejo tiene datos raros, ese se deja intacto y se avisa, sin tumbar el servidor.
  - Se borró una copia antigua del informe profundo que ya no servía y guardaba columnas con posibles datos personales.
- **Verificación final:** sobre una nueva copia de la base real, se arrancó la aplicación tal como lo haría el servidor. Los 11 proyectos se abren con los mismos datos de antes. La copia se borró y la base original quedó intacta. Hay **195 pruebas automáticas** y todas pasan.
- **Estado:** incorporada a la versión oficial por el responsable (PR #19 en GitHub).

### 38. T-012 · Pantalla "Revisa las preguntas": boceto aprobado

- **Qué se hace:** "Nuevo proyecto" pasa a tener tres pasos:
  1. **Sube tu encuesta.**
  2. **Revisa las preguntas.** Una tabla con lo que la plataforma detectó en cada columna: el tipo, que se puede cambiar; cuántas respuestas tiene y cuántas quedaron como N/A; si se incluye; y si se envía a la IA como contexto. Ofrece **unir las columnas ramificadas**, como la comuna, y agrupa las respuestas escritas en "Otro".
  3. **Datos del proyecto.**
- **Decisión del responsable:** aprobó el boceto, con las preguntas abiertas primero y todas visibles, y pidió **ver capturas reales** del resultado antes de aprobarlo.
- **Estado:** en desarrollo.

### 39. T-012 · Resultado, verificado con capturas reales

- **Qué quedó:** "Nuevo proyecto" ahora tiene tres pasos, con una barra que marca el paso actual.
  - El paso 2, "Revisa las preguntas", muestra todas las preguntas con su tipo, cuántas respuestas tienen y cuántas son N/A, y si van a la IA como contexto.
  - Las preguntas abiertas aparecen primero, con ejemplos de respuestas.
  - Ofrece **unir las 16 columnas de comuna** en una sola, con opción de deshacer.
  - En las preguntas de selección se pueden ver las opciones con su conteo. Las respuestas escritas en "Otro" se agrupan.
  - El paso 3 resume qué se va a analizar y qué se va a enviar a la IA.
- **Cómo se verificó:** el supervisor sacó **capturas reales** con la encuesta de vivienda (500 respuestas, 47 columnas). En ellas encontró tres detalles visuales:
  - un campo sin el estilo de Celestica;
  - una explicación que no calzaba en la comuna unida;
  - opciones largas que ocultaban su número.

  Se corrigieron y se confirmaron con capturas nuevas. Las capturas quedaron en el computador del responsable.
- **Estado:** incorporada a la versión oficial por el responsable (PR #20 en GitHub).

### 40. T-018 · Arreglo de campos sin estilo

- **Qué se hace:** algunos campos de texto se veían como un recuadro simple del navegador, sin el estilo de Celestica. Pasaba en el registro (Nombre y Organización), en la categoría manual y en Qualtrics. La causa está en un solo componente y se corrige con una línea.
- **Por qué ahora:** el responsable pidió arreglarlo antes de seguir con T-013.
- **Resultado:** se cambió una línea. Una captura de la pantalla de registro confirma que todos los campos se ven iguales, con el estilo de Celestica.
- **Estado:** incorporada a la versión oficial por el responsable (PR #21 en GitHub).

---

### 41. T-013 · Elegir qué pregunta abierta analizar

- **Qué se hace:** en los proyectos con varias preguntas abiertas, aparece arriba de las pestañas un selector, **"Pregunta que estás analizando"**. Todas las pestañas trabajan sobre la pregunta elegida: resumen, léxico, libro de códigos, codificación, trazabilidad, informe y exportar. Si el proyecto tiene una sola pregunta abierta, no aparece nada nuevo.
- **Por qué:** es la última pieza para analizar encuestas con varias preguntas abiertas. Cada una tiene su propio análisis, y la IA trabaja solo sobre la elegida y solo cuando se lo piden.
- **Estado:** en desarrollo.

### 42. T-013 · Resultado y un riesgo de gasto que se corrigió

- **Qué quedó:** en los proyectos con varias preguntas abiertas, el selector "Pregunta que estás analizando" cambia todas las pestañas a la pregunta elegida. Cada una tiene su propio análisis, y la elección se mantiene al recargar o al cambiar de pestaña. Se verificó con capturas reales.
- **Riesgo que se encontró:** si alguien cambiaba de pregunta mientras otra se estaba codificando con IA y luego volvía, la pantalla no mostraba que el proceso seguía en curso y ofrecía de nuevo el botón "Codificar". Apretarlo **habría pagado la codificación dos veces**.
- **Corrección en las pantallas:** ahora Codificación e Informe detectan si hay un proceso en curso y muestran su avance en vez del botón.
- **Corrección pendiente en el servidor (T-019):** bloquear una segunda codificación de la misma pregunta mientras la primera no termine, como ya se hace con el informe.
- **Con T-013 se completa la iteración de "encuestas completas".**
- **Estado:** incorporada a la versión oficial (PR #22).

### 43. T-019 · Plan: que el servidor no gaste la IA dos veces

- **Problema:** las pantallas ya evitan lanzar dos veces la codificación de una pregunta, pero con dos pestañas abiertas o dos personas trabajando a la vez todavía se podía lanzar dos veces y pagar el doble.
- **Arreglo:** si ya hay una codificación en curso para esa pregunta, el servidor responde "ya está en curso" y no llama a la IA. Otra pregunta del mismo proyecto sí puede codificarse al mismo tiempo.
- **Resultado:** funciona. Las pruebas confirman que un segundo pedido de la misma pregunta no llama a la IA, que otra pregunta sí puede codificarse en paralelo y que tras terminar (o tras un error) se puede volver a lanzar. De paso se reforzó el mismo bloqueo del informe. 197 pruebas en verde.
- **Estado:** incorporada a la versión oficial (PR #23).

### 44. Iteración 3 · Plan: los números de las preguntas cerradas

- **Qué viene:** la plataforma mostrará los resultados de las preguntas cerradas (escalas, NPS, sí/no, selección) y permitirá verlos por grupo (género, edad, región…). Todos los números los calcula la plataforma, sin IA.
- **Orden:** T-020 cálculos (servidor) → T-021 pantalla → T-022 cruces (servidor) → T-023 cruces (pantalla) → T-024/25 proyectos solo con preguntas cerradas.
- **Decisiones del responsable:**
  - los porcentajes se calculan sobre quienes respondieron y los N/A se muestran aparte;
  - el aviso de pocos datos aparece con menos de 10 personas por grupo;
  - la edad se agrupa en tramos de 18–24 a 65+, que el cliente podrá cambiar;
  - las escalas con palabras ("Muy de acuerdo…") se convertirán a 1–5 más adelante.
- **Estado:** T-020 aprobada (ver entrada 45).

### 45. T-020 · Resultado: los números de las preguntas cerradas

- **Qué quedó:** el servidor calcula, sin IA, los resultados de todas las preguntas cerradas: conteos y %, promedio y desviación en escalas, % de notas altas y bajas, NPS y cuántos respondieron. La pantalla llega en T-021.
- **Probado con la encuesta real:** "importancia de ser propietario" tiene promedio 4,31 y 79,4 % de notas 4 o 5. "Capacidad de ahorro": Sí 56,5 %. Los tramos de ingreso salen en su orden natural, de menor a mayor.
- **Error encontrado y corregido:** en una escala de 1 a 5 donde nadie eligió el 1, la plataforma creía que la escala empezaba en 2 y contaba el 3 (neutral) entre las notas bajas. Ahora la escala empieza siempre en 1, o en 0 si alguien respondió 0.
- **Pendiente:** si nadie elige la nota máxima, la escala se acorta. Se resolverá cuando el usuario confirme el rango al revisar las preguntas.
- **Estado:** incorporada a la versión oficial (PR #24).

### 46. T-021 · Pantalla "Preguntas cerradas"

- **Qué quedó:** una pestaña nueva, **"Preguntas cerradas"**, muestra los resultados de cada pregunta cerrada en una tarjeta:
  - barras con el % y el número de personas escritos;
  - las personas que no respondieron (N/A), aparte;
  - en las escalas, el promedio y el % de notas altas y bajas;
  - en NPS, los promotores, pasivos y detractores, con una explicación simple;
  - en las preguntas numéricas, el promedio, la mediana, el mínimo y el máximo.
- **Quién la ve:** aparece solo en los proyectos con preguntas cerradas. La ven todos los roles, también el lector. Los números los calcula el servidor, sin IA.
- **Cómo se verificó:** con capturas reales de la encuesta de vivienda. "Importancia de ser propietario" muestra 4,31 de 5 y 79,4 % de notas altas, los mismos números de T-020.
- **Corrección en la revisión:** en el celular, los nombres de los tramos de ingreso se cortaban y no se distinguían entre sí. Ahora el nombre va completo en su propia línea, con la barra debajo.
- **Estado:** incorporada a la versión oficial (PR #26).

### 47. T-022 · Resultados separados por grupo

- **Qué quedó:** el servidor ahora entrega los resultados de las preguntas cerradas separados por grupo: género, comuna, nivel educacional, tramo de edad… Cada grupo trae los mismos números que el total, calculados de la misma forma y sin IA. Los grupos de menos de 10 personas llevan un aviso de pocos datos. La pantalla llega en T-023.
- **Probado con la encuesta real:**
  - En "importancia de ser propietario", las mujeres dan un promedio de 4,36 (81,5 % de notas altas) y los hombres 4,24 (76,6 %).
  - Por edad, la importancia sube de 4,06 entre los 20 y 24 años a 4,74 entre los 55 y 59.
  - En todas las preguntas, la suma de los grupos da exactamente el total.
- **Decisiones del responsable:**
  - los tramos de edad que elige el cliente sirven solo para ese análisis y no se guardan;
  - cruzar los temas de las preguntas abiertas por grupo queda para más adelante.
- **Algo a tener en cuenta:** en la encuesta de vivienda la edad ya viene en tramos (20-24, 25-29…). Ahí la plataforma usa esos tramos tal cual. Los tramos 18–24 … 65+ se aplican cuando la edad viene como número.
- **Estado:** subida a GitHub (PR #27), esperando la aprobación del responsable.

---

## Glosario

| Término | Significado |
| --- | --- |
| **Backend** | La parte interna de la plataforma: guarda los datos, hace los cálculos y conversa con la IA. El usuario no la ve. |
| **Frontend** | La parte visible: las pantallas, botones y formularios que usa el cliente. |
| **Pruebas automáticas** | Programas que revisan solos que la plataforma funcione bien. Se ejecutan antes de aprobar cada cambio. |
| **Aislamiento entre clientes (multi-tenant)** | Garantía de que una organización nunca pueda ver los datos de otra. |
| **Repositorio / GitHub** | Lugar donde se guarda el código y su historial completo de cambios. |
| **Rama** | Copia de trabajo donde se prepara un cambio sin afectar la versión oficial. |
| **Versión oficial (`main`)** | El código aprobado. Solo el responsable del proyecto autoriza qué entra. |
| **Pull request (PR)** | Solicitud formal para incorporar un cambio a la versión oficial. El responsable la revisa y la aprueba. |
| **Textos de IA (prompts)** | Instrucciones metodológicas que guían a la IA al proponer categorías, codificar respuestas y redactar informes. |
| **Tarea (T-000, T-001…)** | Unidad de trabajo con instrucciones escritas, criterios de aceptación y revisión. |
| **RF / RNF** | Códigos de los requerimientos del producto: funcionales (qué hace la plataforma) y no funcionales (seguridad, calidad, rendimiento). |
