# Bitácora de desarrollo — SoftInsight

**Qué es este documento:** el registro, en orden, de cada cambio que se hace a la plataforma SoftInsight, con su motivo y su resultado. Está escrito para todo el equipo de SoftInsight: no hace falta saber programar para entenderlo.

**Quién lo actualiza:** el supervisor técnico (Claude), cada vez que se hace un cambio. El responsable del proyecto (Israel) aprueba qué se publica.

**Última actualización:** 30 de octubre de 2026

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
| T-003 | Ordenar el código del servidor en archivos por tema (en dos partes: T-003a y T-003b) | 🟡 T-003a incorporada; T-003b aprobada por el supervisor, espera autorización |

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
- **Estado:** T-003a incorporada a la versión oficial (PR #9 en GitHub). T-003b aprobada por el supervisor; espera que el responsable autorice publicarla.

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
