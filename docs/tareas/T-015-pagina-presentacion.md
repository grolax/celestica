# T-015: Página pública de presentación y nueva estructura de rutas
Lado: frontend
Requerimientos: RNF-13, RNF-14, RNF-15, RNF-16
Rama: tarea/T-015-pagina-presentacion
Depende de: T-014 (usa su paleta, su nombre y su componente `Icon`)

## Objetivo
Quien entra a Celestica desde fuera ve primero una **carta de presentación**: quiénes somos, nuestro objetivo y qué hace la plataforma. Arriba hay una barra con la pestaña **"Iniciar sesión"**, que lleva al acceso y desde ahí al área de trabajo actual. La página es pública, estática y no usa la API.

## Alcance
- SÍ: rutas nuevas
  - `/` → página de presentación, **pública** y visible también con sesión iniciada.
  - `/login`, `/signup` → igual que hoy.
  - `/proyectos` → lista de proyectos, que hoy está en `/`, protegida.
  - `/proyectos/nuevo`, `/proyectos/:id/*`, `/configuracion` y `/documentacion` → sin cambios.
  - Después del login o del signup se va a `/proyectos`. Si el usuario ya tiene sesión y entra a `/login` o `/signup`, también va a `/proyectos`. La ruta `*` lleva a `/`.
  - Actualizar todos los destinos que hoy apuntan a `/` como área de trabajo: `App.tsx` (`PublicOnly`), `LoginPage.tsx` (2 `navigate("/")`), `NewProject.tsx` (Cancelar), el logo del `Header` (dentro del área de trabajo lleva a `/proyectos`) y `Sidebar` ("Mis proyectos"). Busca cualquier otro con `grep`.
- SÍ: barra superior pública, propia de esta página: logo "Celestica" a la izquierda; a la derecha, enlaces de ancla a las secciones y la pestaña/botón **"Iniciar sesión"** (`/login`). Si ya hay sesión, ese botón dice **"Ir a mi espacio"** (`/proyectos`).
- SÍ: **página resumida** (pedido del usuario del 2026-10-15: "más resumida", diseño sobrio). Se lee completa en dos o tres pantallas de escritorio. Secciones, en este orden, separadas con claridad (alternar fondo blanco y `--bg-alt`, títulos en navy):
  1. **Portada:** nombre, frase principal, una línea, botón primario "Iniciar sesión" y botón secundario "Crear cuenta" (`/signup`).
  2. **Quiénes somos / Nuestro objetivo:** dos columnas lado a lado (una sola columna en móvil), con un párrafo corto cada una.
  3. **Qué hace Celestica:** 4 tarjetas con un icono de línea (el componente `Icon` de T-014), un título y una línea.
  4. **Pie:** "Celestica es un producto de SoftInsight", año y enlace "Iniciar sesión".
- SÍ: simplificar `LoginPage`/`SignupPage`. El bloque `AuthHero` duplica la presentación: se reemplaza por un formulario centrado con el logo y un enlace "← Volver al inicio" (`/`).
- SÍ: responsive (RNF-15). En móvil, la barra pública colapsa los enlaces de ancla y deja visible "Iniciar sesión", y las tarjetas pasan a una columna.
- NO: formularios de contacto, solicitud de demo, ni nada que llame al backend; imágenes externas o de stock; librerías nuevas (ilustraciones simples con CSS o SVG inline, si acaso); cambiar el área de trabajo (eso es T-016).

## Contrato de API
No aplica: la página es estática.

## Textos (versión resumida, 2026-10-15)
Usa estos textos tal cual. Si alguno no calza con el diseño, propón el cambio en tu resumen en vez de inventar. **No agregues funciones que la plataforma aún no tiene.** Por ejemplo, NPS y preguntas cerradas todavía no existen.

- **Frase principal:** "De la encuesta al informe, con evidencia en cada paso."
- **Línea:** "Análisis de encuestas con IA y validación de tu equipo."
- **Quiénes somos:** "Somos SoftInsight: análisis social, metodología y tecnología al servicio de las organizaciones que escuchan a su gente."
- **Nuestro objetivo:** "Que pasar de las respuestas a las decisiones tome horas, no semanas, con cada hallazgo respaldado por evidencia."
- **Qué hace Celestica:** 4 tarjetas.
  - *Importa tus datos:* "CSV, Excel, Qualtrics o Google Forms."
  - *La IA propone, tu equipo decide:* "Temas sugeridos que tu equipo valida."
  - *Trazabilidad total:* "Cada decisión queda registrada."
  - *Informes listos:* "PDF, Word, Excel y CSV."

## Archivos probables
- Crear: `07_MVP/frontend/src/features/landing/LandingPage.tsx` (y, si hace falta, un componente de barra pública en esa misma carpeta).
- Tocar: `src/App.tsx`, `src/features/auth/LoginPage.tsx`, `src/features/projects/NewProject.tsx`, `src/shared/layout/Header.tsx`, `Sidebar.tsx` y `src/styles/globals.css` (sección nueva `/* ---------- Landing ---------- */`, con las variables de T-014).
- No tocar: `07_MVP/backend/**`, `docs/**`, la lógica de `useAuth` ni `shared/api/client.ts`.

## Criterios de aceptación
- [ ] `npm run build` sin errores.
- [ ] Sin sesión: `/` muestra la presentación; "Iniciar sesión" lleva a `/login`; después del login se llega a `/proyectos` con la lista de siempre.
- [ ] Con sesión: `/` muestra la presentación con "Ir a mi espacio"; `/login` redirige a `/proyectos`.
- [ ] Una URL protegida sin sesión (por ejemplo `/proyectos`) sigue mandando a `/login`, como hoy.
- [ ] Ningún enlace interno del área de trabajo lleva por error a la presentación. Lista en tu resumen los destinos que cambiaste.
- [ ] Accesible: la página se recorre completa con teclado (Tab) y con foco visible; landmarks semánticos (`header`, `nav`, `main`, `section` con encabezado, `footer`); un solo `h1`; contraste AA con la paleta de T-014.
- [ ] Responsive: se ve bien en 375 px, 768 px y 1280 px de ancho. Indica cómo lo verificaste.
- [ ] Los textos coinciden con la sección "Textos" (o el resumen explica cada diferencia).
- [ ] Commits con el formato `T-015 RNF-13: ...`.

## Notas
- La URL de la lista de proyectos cambia de `/` a `/proyectos`. Quien tenga marcada la URL vieja llegará a la presentación y desde ahí entra con un clic, así que es aceptable.
- Diseño sobrio: aire generoso entre secciones, ancho máximo de contenido de unos 1100 px, una acción primaria por sección.
