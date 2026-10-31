# SoftInsight v1.1 — Cómo funciona, por dentro y por fuera

Este documento explica en detalle la arquitectura de SoftInsight v1.1: qué hace cada pieza, qué decisiones técnicas se tomaron y por qué, dónde viven los datos, y cómo fluye la información desde que un usuario importa sus datos hasta que descarga un PDF de auditoría. Está pensado para que cualquiera del equipo (técnico o no) entienda el producto de forma cabal.

**Qué cambió respecto de v1.0:** la base de datos ahora es MongoDB (antes SQLite), el frontend está organizado por features con hooks reutilizables, el informe cualitativo muestra progreso real durante su generación (streaming), hay 12 plantillas de marcos teóricos en 5 industrias (antes 3, solo educación), y se puede crear un proyecto importando directamente desde Qualtrics o Google Forms.

---

## 1. Visión general en un párrafo

SoftInsight es una aplicación web con dos partes: un **backend** en Python (FastAPI) que expone una API REST y hace todo el trabajo pesado (guardar datos, analizar texto, hablar con Claude, generar reportes), y un **frontend** en React/TypeScript que es la interfaz que ve el usuario en su navegador. El navegador nunca habla directamente con Claude ni toca la base de datos: todo pasa por la API del backend, y cada petición viaja con un token que identifica al usuario. Esa separación es la que permite auditar todo: cualquier decisión —humana o de IA— pasa por un punto central que la registra.

```
Navegador (React)  ⇄  API REST (FastAPI)  ⇄  MongoDB (datos)
                              ⇅                    ⇅
                       Claude API (Anthropic)   Qualtrics / Google Sheets
                                                (importación puntual)
```

---

## 2. El stack y por qué se eligió cada pieza

| Pieza | Tecnología | Por qué |
| --- | --- | --- |
| Backend | Python + FastAPI | FastAPI valida datos automáticamente y genera documentación de la API en `/docs`. Python es el lenguaje natural para análisis de texto. |
| Base de datos | **MongoDB vía pymongo** | El modelo de datos ya era documental (cada proyecto es un documento). Mongo es su hogar natural: actualizaciones parciales (`$set`/`$push`), índices en campos anidados, y sin el workaround de "JSON en columna relacional". Local hoy, **Atlas mañana cambiando solo `MONGODB_URI`**. |
| Autenticación | JWT propio (PyJWT) + PBKDF2 | Sin dependencias de servicios externos para la beta. Estándar de la industria. |
| IA | Claude API (Anthropic) | Todo el contacto con la IA pasa por **un solo archivo** (`services/thematic.py`), así el proveedor es intercambiable. El informe usa la **API de streaming** para reportar progreso real. |
| Integraciones | `services/integrations/` | Interfaz común: cada fuente entrega un DataFrame de pandas, el mismo formato que un archivo subido. Agregar fuentes futuras es trivial. |
| Cifrado de credenciales | Fernet (cryptography) | El API Token de Qualtrics se guarda cifrado (clave derivada de `SECRET_KEY`); nunca viaja al navegador. |
| Reportes PDF | reportlab + matplotlib | Control total del layout (portada, tablas, pie de página); matplotlib genera el gráfico de frecuencias. |
| Reportes Word | python-docx | Genera un .docx real y editable, para que la organización agregue sus conclusiones. |
| Frontend | React 18 + TypeScript + Vite | TypeScript detecta errores antes de ejecutar; Vite recarga al instante. Se evaluó Next.js y se descartó: es una SPA detrás de login, sin SEO ni SSR que lo justifique. |
| Rutas | react-router-dom | URLs reales, botón atrás del navegador, protección de páginas por sesión. |
| Estilos | CSS propio (sin framework) | Un solo archivo (`globals.css`) define la paleta y los componentes; coherente y liviano. |

---

## 3. Dónde viven los datos (esto es lo más importante)

Todos los datos están **en tu computador**, en el MongoDB local (`mongodb://localhost:27017/softinsight`). Nada se sube a servidores externos, salvo (a) los textos que se envían a la API de Claude cuando pides análisis temático, y (b) las llamadas a Qualtrics/Google cuando importas datos.

```
MongoDB (base "softinsight")
├── users            ← cuentas: email, hash de contraseña, credenciales cifradas de integraciones
├── projects         ← EL DOCUMENTO COMPLETO de cada proyecto (respuestas, categorías,
│                       codificaciones, audit_log, informe...)
└── audit_events     ← copia plana del log de auditoría, consultable por proyecto/actor

07_MVP/backend/
├── .env                     ← Secretos: API key de Anthropic, SECRET_KEY. NUNCA subir a git.
├── app/main.py              ← Solo configuración de la app: `FastAPI`, `init_db`, manejador de errores, sink de costo de Claude, CORS e `include_router`. No define endpoints.
├── app/deps.py              ← Lo que comparten los routers: `_get_or_404`, `require_role` (permisos por rol), `_check_admin`, `ADMIN_PASSWORD`, `_slug` y el progreso en memoria de codificación/informe.
├── app/routers/projects.py  ← Plantillas, proyectos (crear, listar, obtener, borrar, importar), respuestas y consumo de API.
├── app/routers/integrations.py ← Credenciales y encuestas de Qualtrics; crear proyecto desde Qualtrics o Google Forms.
├── app/routers/analysis.py  ← Léxico, categorías y comentarios, codificación (con progreso), re-codificación, resumen y auditoría.
├── app/routers/reports.py   ← Trazabilidad, exportaciones PDF/DOCX/CSV/XLSX e informe cualitativo (con progreso).
├── app/routers/admin.py     ← Panel admin (X-Admin-Password): consumo, salud y prompts.
├── app/prompts.json         ← Cambios locales a los prompts (editables desde la UI). Ignorado por git; se crea al primer guardado.
├── app/prompts_default.json ← Prompts de fábrica: se usan cuando falta `prompts.json` o alguna clave, y para restaurar.
├── softinsight.db           ← Base SQLite de la v1.0 (solo como fuente de migración).
└── scripts/migrate_sqlite_to_mongo.py  ← migración v1.0 → v1.1, idempotente.
```

### 3.1 Las colecciones por dentro

**`users`** — un documento por cuenta:

| campo | contenido |
| --- | --- |
| _id | identificador tipo `usr_a1b2c3d4e5` |
| email | único (índice único en Mongo), en minúsculas |
| password_hash | la contraseña **nunca se guarda en texto plano** (ver sección 4) |
| nombre, empresa | datos de perfil |
| org_id, rol | organización a la que pertenece (una sola) y su rol (`admin`, `analista` o `lector`; ver sección 4.1) |
| activo, debe_cambiar_password | estado de la cuenta (ver sección 4.2); si faltan, se leen como `true` / `false`, así que las cuentas anteriores a T-007 no necesitaron migración |
| integrations | credenciales de integraciones **cifradas** (ej: `integrations.qualtrics.token_enc`) |

**`organizations`** — `{_id: "org_<10 hex>", nombre, created_at}`. Al registrarse se crea una organización nueva (nombre = `empresa`, o "Organización de <nombre|email>") y el usuario queda como `admin`. Los proyectos pertenecen a la organización, no al usuario.

**`projects`** — un documento por proyecto, con `_id` = id del proyecto y `org_id` como clave del multi-tenant (indexado). `user_id` se conserva con el significado "creado por" y **no** se usa para filtrar acceso. El documento es el proyecto completo:

```json
{
  "_id": "proj_...", "id": "proj_...", "org_id": "org_...", "user_id": "usr_...",
  "name": "Evaluación Docente 2026-1",
  "marco_teorico": "Modelo de competencias docentes...",
  "columns": ["id_respuesta", "Género", "Comentario", ...],   // solo dato de origen
  "text_column": "Comentario",                                 // solo dato de origen
  "preguntas": [ {"id": "q_1", "titulo": "Comentario", "columnas": ["Comentario"],
                  "tipo": "abierta", "contexto_ia": false},
                 {"id": "q_2", "titulo": "Género", "columnas": ["Género"],
                  "tipo": "segmento", "contexto_ia": true}, ... ],
  "respondentes": [ {"id": "R0001", "valores": {"q_1": "texto...", "q_2": "F", "q_3": null}}, ... ],
  "analisis": { "q_1": {                                       // uno por pregunta ABIERTA
      "lexical":    { "top_terms": [...], "sentiment_by_response": {...} },
      "lexical_interpretation": "...",
      "categories": [ {"id": "cat_...", "nombre": "...", "status": "validada",
                       "criterios_inclusion": "...", "comments": [...]}, ... ],
      "codings":    { "R0001": [ {"category_id": "cat_...", "rationale": "...",
                                  "confidence": 0.88, "source": "claude"} ], ... },
      "qualitative_report": "RESUMEN INTERPRETATIVO\n\n...",
      "v2_analyses_cache": {...} } },
  "audit_log":  [ {"timestamp": "...", "actor": "claude", "action": "...", "detail": {...}} ]
}
```

**Preguntas y respondentes (RF-23, T-011a).** El proyecto guarda **todas** las preguntas confirmadas (con su tipo de T-010) y **una fila por persona** en `respondentes`; `valores` tiene una clave por pregunta (`q_<n>`) y **respuesta vacía = `null` (N/A), nunca una opción**. Las columnas ramificadas (ej. comuna por región) se unen en una sola pregunta (`columnas` con varias): el valor de cada persona es el primero no vacío. El `id` de la persona es `id_respuesta` si la fuente lo trae, o `R0001`…. Cada pregunta **abierta** tiene su propio análisis independiente en `analisis.<id>`: léxico, categorías, codificaciones, informe y caché del informe v2. Las preguntas cerradas solo se guardan (su análisis cuantitativo llega con RF-30).

**Vista única por pregunta.** Ningún router, exportador ni función de IA lee `respondentes`/`analisis` directamente: todo pasa por `store.vista_pregunta(project, pregunta_id)`, que arma para esa pregunta abierta un diccionario con la forma de siempre (`responses` = `[{id, text, meta}]` solo de personas con texto, más `categories`, `codings`, `lexical`, `lexical_interpretation`, `qualitative_report`, `v2_analyses_cache`, `audit_log`…). Los routers la piden con `_get_vista(project_id, user, pregunta)` (en `deps.py`): el 404 de proyecto va primero, y una pregunta inexistente o que no es abierta da 404 "Pregunta no encontrada"; sin `?pregunta=` se usa la primera abierta, así que el frontend anterior sigue funcionando sin cambios. Las escrituras (`push_category`, `update_category_fields`, `push_comment`, `pull_comment`, `set_codings_*`, `set_project_field(..., pregunta_id)`) reciben el id de la pregunta y escriben con `$set`/`$push` puntuales en `analisis.<id>.…`. El progreso de codificación y de informe se indexa por `(proyecto, pregunta)`: dos preguntas del mismo proyecto pueden tener estados distintos, y los hilos de fondo capturan la pregunta al lanzarse.

**Qué se le envía a la IA (privacidad y tokens).** `meta` de cada respuesta en la vista lleva **solo** las preguntas con `contexto_ia: true` (clave = título) y **jamás** las de tipo `identificador`, aunque alguien las haya marcado; una respuesta N/A de contexto no se envía. Por defecto solo van **género y edad** (en la creación sin `preguntas` y en la migración: preguntas `segmento`, `numerica` o `seleccion_unica` cuyo título menciona género/sexo o edad; la edad puede detectarse como número). El texto enviado es solo el de la pregunta elegida: la otra pregunta abierta, los identificadores y el resto de las columnas no salen del servidor. Una prueba (`tests/test_preguntas_pytest.py`) captura lo que recibiría Anthropic en propuesta, codificación, léxico e informe v1/v2 y verifica que nada de eso aparezca. La IA solo corre a pedido y pregunta por pregunta.

**Migración a preguntas (RF-23).** `app/migrations.py::migrate_preguntas(db)` (envoltorio: `scripts/migrate_preguntas.py`; `init_db()` la corre en cada arranque) convierte todo proyecto sin `preguntas`: la columna de texto de siempre pasa a ser la pregunta `abierta` `q_1`; cada otra columna original pasa a una pregunta (`q_2`…) con el tipo que da `detectar()` sobre los valores guardados en `meta` (`contexto_ia: true` solo para género/sexo/edad); `responses` pasa a `respondentes` (`""` → `null`); y `categories`, `codings`, `lexical`, `lexical_interpretation` y `qualitative_report` se mueven a `analisis.q_1` y se quitan de la raíz; `v2_analyses_cache` se **descarta**. Es idempotente (el filtro exige `preguntas` ausente, también en el update) y el proyecto se ve igual por la API, salvo que `meta` ahora solo trae el contexto marcado. El caché del informe v2 antiguo se elimina (su huella ya no coincide y su snapshot guardaba las columnas antiguas, incluidos posibles identificadores): el primer informe después de migrar vuelve a analizar a cada respondente. La conversión de **cada** proyecto va en `try/except`: si uno falla, se registra en el log (id y tipo de error, sin datos de respuestas), queda sin tocar (se reintenta en el siguiente arranque) y se cuenta en `{"proyectos": n, "fallidos": m}`; el arranque nunca se cae por eso. `import_legacy_projects` convierte igual los proyectos pre-auth.

**`audit_events`** — copia plana del audit log (consultable por `project_id`, indexado; cada evento lleva también `org_id`), además del registro canónico que vive dentro del proyecto.

**Migración a organizaciones (RF-02).** `app/migrations.py` (`migrate_orgs(db) -> dict`; `scripts/migrate_orgs.py` es solo el envoltorio de línea de comandos) convierte datos anteriores: cada usuario sin `org_id` recibe su propia organización y `rol="admin"` (usuarios con la misma `empresa` **no** se unen); cada proyecto sin `org_id` hereda el de su `user_id`; cada `audit_event` sin `org_id` hereda el de su proyecto. Un proyecto cuyo usuario ya no existe queda con `org_id: null` (inaccesible) y se cuenta como huérfano. Es idempotente: solo toca documentos con `org_id` ausente, y `init_db()` la corre en cada arranque (barata si no hay nada pendiente).

### 3.2 Decisión clave: documento + actualizaciones parciales

En v1.0 el proyecto vivía como JSON dentro de una columna de SQLite y **cada guardado reescribía el documento completo**. En v1.1 el documento es nativo de Mongo y las operaciones puntuales son quirúrgicas:

| Operación | Antes (v1.0) | Ahora (v1.1) |
| --- | --- | --- |
| Validar/editar una categoría | reescribir todo el proyecto | `$set` sobre esa categoría (operador posicional) |
| Agregar categoría o comentario | reescribir todo | `$push` al array correspondiente |
| Re-codificar una respuesta | reescribir todo | `$set` de `analisis.q_1.codings.R0001` |
| Evento de auditoría | reescribir todo | `$push` a `audit_log` + insert en `audit_events` |
| Resultado de la codificación masiva | reescribir todo | un `$set` con todas las claves de `analisis.<pregunta>.codings` |
| Guardar informe | reescribir todo | `$set` de `analisis.<pregunta>.qualitative_report` |

Beneficio concreto: agregar un comentario ya no reescribe las 320 respuestas, y la codificación (que corre en un hilo durante minutos) ya no pisa los comentarios o categorías que el analista agregue mientras tanto.

`save_project` (documento completo) sigue existiendo para lo que corresponde: creación del proyecto e importación de proyectos antiguos.

### 3.3 Aislamiento entre cuentas (multi-tenant)

Cada consulta a Mongo filtra por la organización dueña. El filtro central es:

```python
def _tenant_filter(project_id, org_id):
    return {"_id": project_id, "org_id": org_id}
```

Los routers pasan `user.org_id`; todos los miembros de una organización ven y editan los mismos proyectos. Si un usuario de otra organización intenta abrir un proyecto (aunque adivine la URL), recibe "Proyecto no encontrado" — el sistema ni confirma que exista. Verificado con pruebas automáticas de acceso cruzado sobre lectura, escritura, exportación, borrado y progreso (`backend/tests/`).

---

## 4. Autenticación paso a paso

### Registro (signup)

1. El usuario llena el formulario (email, contraseña ≥ 8 caracteres, nombre, organización).
2. El backend verifica que el email no exista (más un índice **único** en Mongo que cubre cualquier carrera).
3. La contraseña se transforma con **PBKDF2-HMAC-SHA256**: sal aleatoria única y 200.000 iteraciones. El resultado (`pbkdf2$200000$sal$hash`) es lo único que se guarda.
4. Se crea el documento en `users` y se emite un **token JWT**.

### El token JWT

Texto firmado criptográficamente que dice "soy el usuario `usr_xyz`, válido hasta tal fecha". Se firma con la `SECRET_KEY` del `.env` y **expira a los 7 días**. El frontend lo guarda en `localStorage` y lo adjunta en cada petición como header `Authorization: Bearer <token>`.

### En cada petición

Todos los endpoints de proyectos declaran la dependencia `get_current_user`, que verifica firma y expiración (si falla → 401 y el frontend redirige a `/login`) y carga el usuario desde Mongo. No hay forma de llegar a datos de proyecto sin pasar por esta puerta.

### 4.1 Permisos por rol (RF-03)

El rol se verifica **en el backend**; la UI solo lo refleja. `app/deps.py` tiene una única tabla de niveles (`lector < analista < admin`) y etiquetas en español, y la dependencia `require_role("analista")`: llama a `get_current_user` (401) y, si el rol no alcanza, responde **403** `"Tu rol (Lector) no permite esta acción."`. Un rol desconocido en la base se trata como lector, nunca como admin. Como es una dependencia, corre antes de `_get_or_404`: el orden es siempre **401 → 403 → 404**, y el 403 no depende de que el proyecto exista (no revela proyectos de otras organizaciones).

| Operación | Lector | Analista | Admin |
| --- | --- | --- | --- |
| Ver proyectos, resultados, auditoría, informe, uso; descargar exportaciones | sí | sí | sí |
| Comentar categorías | sí | sí | sí |
| Borrar comentario | solo los suyos (`author_id`) | todos | todos |
| Crear proyecto (archivo, Qualtrics, Google Forms, import-legacy) | no | sí | sí |
| Analizar (plantilla, léxico, categorías, codificar, recodificar, generar informe) | no | sí | sí |
| Borrar proyecto | no | sí | sí |
| Credenciales y encuestas de Qualtrics | no | sí | sí |

Los comentarios guardan `author_id` (id del usuario); los antiguos no lo tienen y un lector no puede borrarlos. `/api/admin/*` sigue protegido solo por `X-Admin-Password`. La prueba `tests/test_permisos_pytest.py` declara el rol mínimo de cada operación `/api/` en la tabla `PERMISOS` y falla si aparece una ruta sin declarar.

### 4.2 Miembros y estados de cuenta (RF-03, T-007)

El admin gestiona su organización en `app/routers/org.py` (`require_role("admin")`, persistencia en `store.py`): `GET /api/org/members`, `POST /api/org/members` y `PATCH /api/org/members/{user_id}`. Un miembro de otra organización responde 404 "Miembro no encontrado".

- **Alta.** El servidor genera una contraseña temporal con `secrets` (12 caracteres sin `0 O o 1 l I`, formato `xxxx-xxxx-xxxx`), guarda **solo su hash** (PBKDF2, igual que cualquier contraseña) y la devuelve **una sola vez** en la respuesta 201. El usuario nace con `debe_cambiar_password: true`.
- **Quitar = desactivar** (`activo: false`): se conservan sus proyectos (`user_id`), comentarios y auditoría. Reactivar es `activo: true`.
- **Reglas del PATCH.** La organización nunca queda sin admin **activo** (409; se evalúa primero, por eso con un solo admin quitarse el rol o desactivarse da 409); nadie se desactiva a sí mismo (400, aplica cuando hay otro admin); cuerpo vacío o rol inválido, 422. La comprobación del último admin no es atómica (ver `shortcut:` en el código).
- **Dos bloqueos en la misma puerta.** `get_current_user_pendiente` (en `auth.py`) valida el token, carga al usuario desde la base **en cada petición** y responde 401 "Tu cuenta fue desactivada..." si `activo` es falso (el token vigente de un desactivado deja de servir al instante). `get_current_user` depende de ella y además responde 403 "Debes cambiar tu contraseña temporal antes de continuar." si hay temporal pendiente. Todas las rutas protegidas (incluido `require_role`) usan `get_current_user`; solo `GET /auth/me` y `POST /auth/change-password` usan la variante `_pendiente`. `login` también rechaza a un desactivado, pero solo después de verificar la contraseña. Una prueba recorre OpenAPI y exige el 403 en toda ruta `/api/` (salvo `/api/admin/*`) con una cuenta pendiente.
- **Cambio de contraseña** (`POST /auth/change-password`, cualquier usuario autenticado): exige la actual (400), nueva de al menos 8 caracteres (422) y distinta de la actual (400); apaga `debe_cambiar_password`. El token anterior sigue valiendo hasta su expiración (no hay revocación, ver Logout).

### Logout

Se borra el token del navegador. (Sin lista de revocación en servidor; suficiente para la beta.)

---

## 5. El flujo de análisis completo, de principio a fin

### Paso 0 — Crear proyecto (tres orígenes)

El proyecto nace de un **DataFrame de pandas**, venga de donde venga — esa es la decisión de diseño que hizo triviales las integraciones:

1. **Subir archivo** (CSV/XLSX): el backend lo lee con pandas.
2. **Qualtrics**: con las credenciales cifradas del usuario, el backend usa la API oficial de exportación (iniciar export → poll → descargar ZIP con CSV) y produce el mismo DataFrame.
3. **Google Forms**: el usuario pega la URL de la planilla de respuestas (compartida como "cualquiera con el enlace puede ver"); el backend la descarga como CSV. *Decisión documentada: OAuth completo de Google queda para el futuro; esta vía cubre la importación puntual sin fricción de configuración.*

En los tres casos: el usuario puede enviar `preguntas` (lo confirmado en la vista previa; ver sección 3.1); sin ellas se detectan con T-010 y, si no se indica columna de texto, se usa la heurística de **mayor largo promedio** (esa columna fuerza `abierta`). Errores: 422 si una columna no existe, está en dos preguntas, el tipo no es válido o se marca `contexto_ia` en un identificador; 400 si no hay ninguna pregunta abierta. Cada fila es una persona (`respondentes`) con ID estable; la plantilla elegida crea marco + categorías base; y todo queda auditado (`creacion_proyecto` con la fuente y el número de preguntas por tipo —sin valores—, más `importacion_qualtrics`/`importacion_google_forms` con encuesta/planilla y n° de respuestas).

### Paso 0b — Vista previa con tipos de pregunta (RF-22/RF-25, T-010)

Antes de crear el proyecto, `POST /api/projects/preview` (archivo), `/preview/qualtrics` y `/preview/google-forms` leen los datos con el mismo lector que la creación (`_leer_archivo`, tope de 20 MB; las integraciones reutilizan `fetch_responses`) y devuelven el tipo propuesto de cada columna. **Solo lectura y sin IA**: no guardan nada ni registran eventos. La lógica es una función pura, `detectar(df)`, en `app/services/question_types.py`. Para cada columna se aplica, en este orden, la primera regla que calce (las pruebas por texto miran una muestra fija de 1.000 valores; conteos y rangos usan todas las filas):

1. Sin valores → `sin_datos`; un solo valor distinto en todas las filas (o en el 90 % o más) → `constante`. Con un solo valor pero la mayoría de las filas vacías, la columna sigue las reglas de abajo (queda `seleccion_unica`/`segmento`).
2. El título (en sus primeras palabras o terminado en `Id`) es `id`, `rut`, `folio`, `email`, `correo`, `dni`, `uuid`, `matricula`, `ip`… → `identificador`.
3. 90 % o más de los valores con forma de fecha (`2026-07-01`, `01/07/2026`) → `fecha`.
4. Con 10 o más respuestas, 95 % o más de valores distintos, cortos (≤ 40 caracteres) y sin espacios, y que no sean decimales → `identificador`.
5. Enteros entre 0 y 10 y título con `recomend` o `nps` → `nps`. Sin la palabra clave queda `escala`.
6. Exactamente dos respuestas (sí, si, no, s, n, yes, y, true, false, verdadero, falso, 1, 0; sin mayúsculas ni tildes) → `si_no`.
7. Números: enteros 0–10 con hasta 11 valores distintos → `escala` (con el mínimo y máximo observados); si el título es corto (hasta 3 palabras) y habla de año, edad, curso, semestre o ciclo y hay hasta 20 valores → `segmento`; el resto → `numerica`. La coma decimal (`3,5`) cuenta como número.
8. Una de cada cinco respuestas o más con `;` (o `,`) y pocas partes distintas (hasta 40; las 20 más frecuentes suman el 80 % o más de las menciones y cada parte aparece en promedio 2 veces o más) → `seleccion_multiple`, aunque cada parte sea una frase larga. Un título con "seleccion…", "más de una" o "hasta N" baja el mínimo de respuestas con separador a una de cada veinte. Texto libre con comas (partes casi todas distintas) sigue siendo `abierta`.
   - **Reconstrucción de opciones.** Google Forms une las opciones marcadas con `", "`, así que una opción con coma interna llega partida. Antes de contar, se vuelven a unir los trozos: (a) lo que queda dentro de un paréntesis sin cerrar (`Subsidios (DS1, DS19, DS49)`; si el paréntesis nunca cierra, no se une); (b) un trozo que **empieza con minúscula** se une al anterior (las alternativas empiezan con mayúscula; las continuaciones, como `pero todavía no he buscado.` o `fondos mutuos`, con minúscula), salvo que ese mismo trozo aparezca también como respuesta completa por sí solo: entonces es una opción real; (c) dos trozos A y B que siempre aparecen juntos, contiguos y en ese orden (B solo después de A y A siempre seguido de B). Si A aparece a veces sin B, queda ambiguo y se deja separado (el usuario lo corrige al revisar las preguntas). Los conteos de `opciones` salen sobre las opciones reconstruidas.
   - **Selección única con comas.** Si tras reconstruir casi todas las respuestas tienen una sola opción (menos de una de cada cinco, o de cada veinte con pista de título), la coma era parte de la alternativa: no es `seleccion_multiple` y la columna sigue a la regla 9. Lo mismo si los valores completos son 10 % o menos de las respuestas, cada uno se repite y ningún trozo aparece solo como respuesta (alternativas con coma); con pista de grupo en el título sale `segmento`.
9. Texto con pocos valores distintos (no más de la mitad de las respuestas) y hasta 20 valores distintos, o 10 % o menos de las respuestas (con 30 o más respuestas), sin importar el largo de cada valor: si el título nombra un grupo (`sede`, `carrera`, `genero`, `region`, `comuna`, `educacional`…) → `segmento` (en esos títulos se admiten hasta 100 valores si son menos del 30 % de las filas); si no → `seleccion_unica`. En texto la pista de grupo vale con cualquier largo de título, salvo que el título evalúe (`evalu`, `calific`, `satisf`, `opin`). Una columna con menos de 10 respuestas que son menos de la mitad de las filas se trata siempre como esta regla (opción corta de una pregunta casi vacía).
10. Texto restante con promedio de 3 palabras o más, o con la mayoría de valores distintos → `abierta` (el motivo cita promedio de palabras y valores distintos reales); si no, `seleccion_unica`.

Ajustes respecto de la regla sugerida en la orden: el "título corto" (solo para columnas numéricas) evita que una pregunta como "¿Cómo evalúa el curso?" (escala 1–5) se tome por un grupo; "pocos valores" exige además repetición (no más de la mitad de las filas), para que 15 comentarios todos distintos no se tomen por opciones; y el identificador por valores ignora los decimales (una medida continua no es un código). Advertencias: sin abiertas, menos de 10 filas y columnas con más de la mitad vacía. Rendimiento medido: 10.000 filas × 30 columnas en menos de 1 s.

**Los pasos 1 a 6 se hacen por pregunta abierta** (RF-23): todas esas operaciones aceptan `?pregunta=<id>` (ver `docs/API_CONTRATOS.md`) y, sin él, trabajan sobre la primera abierta. Cada pregunta tiene su propio libro de códigos, codificación, léxico, informe y exportaciones.

### Resultados de preguntas cerradas (RF-30, T-020)
`GET /api/projects/{id}/closed-results` (cualquier rol) calcula en `app/services/quantitative.py`, sin IA, conteos y % por opción (sobre quienes respondieron; el N/A va aparte), promedio y desviación muestral de escalas, top-2/bottom-2, NPS y estadísticos de las numéricas. No se guarda nada: se recalcula en cada llamada. La selección múltiple reutiliza `separar_opciones` de `question_types.py` (mismo criterio que la detección); el rango de una escala se toma de los valores recibidos. Con `?por=<pregunta>` (segmento, selección única, sí/no o numérica; en numérica `&cortes=18,25,…`) agrega `grupos` y, en cada pregunta, `por_grupo`: se reutiliza el mismo cálculo (`_pregunta`) sobre las personas de cada grupo, forzando el rango de la escala y las opciones del total (la selección múltiple se separa una sola vez sobre todas las respuestas y los grupos cuentan con esa misma separación, así la suma de una opción entre los grupos es su total); grupos de menos de 10 personas llevan `pocos_datos`. Con `&unir=<json>` (lista de `{nombre, valores}`, solo para `por` no numérica; `_unir` en el mismo servicio) se juntan opciones de `por` en grupos con nombre elegido: se unen las listas de personas antes de calcular, así que `pocos_datos` y `por_grupo` salen del mismo cálculo; el grupo unido lleva `unidos` y no se guarda nada.

### Paso 1 — Análisis léxico (Capa 1, sin IA generativa)

`services/lexical.py` calcula de forma **determinística**: frecuencias (sin stopwords), bigramas, co-ocurrencias, y sentimiento por lexicón con evidencia palabra por palabra. Corre en segundos y no consume API. Al final, una llamada opcional a Claude redacta una interpretación breve; sin API key, el análisis numérico queda igual.

### Paso 2 — Libro de códigos (la IA propone, el humano decide)

- "Proponer categorías con IA": marco teórico + muestra de 60 respuestas → Claude devuelve categorías con nombre, definición, **criterios de inclusión y exclusión** y ejemplo. Entran con estado **`propuesta`**.
- Alternativa: aplicar una **plantilla** (selector agrupado por industria).
- El analista valida, descarta, edita, crea categorías manuales (entran validadas) y deja comentarios 💬.
- **La codificación solo usa categorías `validada`**. Incluso las de plantilla entran como `propuesta`: la validación humana es parte del método.

### Paso 3 — Codificación del corpus

Lotes de 25 respuestas contra el libro validado. Cada asignación: categoría(s), **justificación** y **confianza** (0.0–1.0). Corre en un **hilo en segundo plano** con barra de progreso (polling cada 2 s). El resultado se guarda con un `$set` masivo de `codings` que no pisa lo que el analista haya editado mientras tanto. Re-codificación manual → `source: "analista"`, confianza 1.0, y el antes/después va a la auditoría.

**Sobre la confianza:** es la autoestimación del modelo, no un p-valor. Su uso correcto es **priorizar revisión humana** (verde ≥ 0.85, naranja 0.60–0.84, rojo < 0.60), nunca filtrar datos automáticamente.

### Paso 4 — Trazabilidad

La vista plana de todo lo anterior: respuesta → categoría → justificación → confianza → fuente → estado, con filtros y búsqueda. El argumento de auditoría ante CNA/CNE o cualquier auditor externo.

### Paso 5 — Informe cualitativo (ahora con progreso real)

**Modo rápido (v1):** una llamada grande a Claude con el prompt `qualitative_report`. Corre en un hilo y usa la **API de streaming** de Anthropic. El endpoint `GET /report/progress` expone el avance real —caracteres efectivamente recibidos del modelo y la **sección que está redactando**— y el frontend muestra la misma barra de progreso que la codificación. No es un spinner falso: si el stream se detiene, la barra se detiene.

**Modo profundo (v2, default):** pipeline de tres prompts en `services/thematic.py::generate_qualitative_report_v2`:

1. **Prompt 1 — análisis por respondente** (`analyze_respondent_v2`): una llamada por respondente, en paralelo (`REPORT_V2_MAX_WORKERS`), que conecta la respuesta abierta con sus respuestas cerradas y extrae subtemas con cita textual. Es el paso caro (≈ n llamadas), por eso su resultado se **cachea en el proyecto** (`v2_analyses_cache`, con un hash sha256 del marco teórico + respuestas): un reintento del informe no lo vuelve a pagar mientras los datos no cambien. El botón **"Regenerar desde cero"** de la UI (`POST /report?force_full=true`) es la única forma de saltarse el caché, y lo hace a propósito.
2. **Prompt 2 — síntesis de clusters**, en map-reduce:
   - *map* (`synthesize_clusters_v2_partial`): los análisis se parten en **tandas por presupuesto de tokens de entrada** (`SYNTHESIS_BATCH_INPUT_TOKENS`, no por cantidad fija de respondentes) y cada tanda se sintetiza en paralelo en clusters candidatos con sus `member_ids`. Si la salida de una tanda se trunca igual (`stop_reason=max_tokens`), la tanda **se divide en dos y se reintenta** (recursivo): en el peor caso se llega a tandas de un respondente, cuya salida siempre cabe.
   - *reduce* en tres pasos: el modelo agrupa **solo los nombres** de los candidatos que son el mismo fenómeno (`synthesize_clusters_v2_map_names`, salida de ~20 tokens por candidato); **Python** une los `member_ids`, suma desgloses por metadata y calcula prevalencia y porcentaje sobre el total real del corpus; y el modelo elige citas representativas y variaciones por cluster desde un pool acotado (`synthesize_clusters_v2_select_quotes`), también en tandas que se dividen si se truncan. Si todo el corpus cabe en una tanda, se usa el prompt único `synthesize_clusters_v2`.
3. **Prompt 3 — redacción** (`write_report_v2`): markdown, acotado por el propio prompt (≤ 1500 palabras).

**Por qué está diseñado así (incidente de septiembre 2026):** con 122 respondentes, la síntesis en tandas fijas de 40 se truncaba a 8000 tokens de salida — cada tanda necesitaba ~16.000 — y cada reintento repetía las 122 llamadas del Prompt 1 (> US$10 sin resultado). Ningún techo de `max_tokens` resuelve eso de forma permanente porque un corpus más grande siempre lo vuelve a superar; por eso ahora **ningún paso depende de que su salida "quepa"**: se acota la entrada por tokens y se divide el trabajo cuando hace falta. Además, toda salida JSON se pide con **tool use forzado y schema** (`services/schemas_v2.py`): la API entrega el JSON ya parseado, sin regex ni `json.loads` que se rompan con comillas dentro de citas textuales. Todas las llamadas van por streaming (el SDK exige streaming cuando `max_tokens` es alto) y el techo se acota al **límite real del modelo**, consultado a la API (`model_max_output_tokens`; Sonnet 4.6: 128.000 tokens de salida).

**Registro y costo:** cada llamada a Claude queda en `backend/logs/claude_calls.jsonl` (paso, modelo, `max_tokens`, `stop_reason`, tokens, costo estimado, duración, proyecto); las fallidas o truncadas guardan además el texto crudo en `backend/logs/claude_raw/`. El mismo registro alimenta `claude_usage` en el documento del proyecto (`$inc` por paso), visible en `GET /api/projects/{id}/usage` y en el panel de administración (`GET /api/admin/usage`). `GET /api/admin/health` muestra la versión de `thematic.py` que el proceso tiene cargada, para confirmar que uvicorn recargó el código.

### Paso 6 — Exportación

`services/export.py` genera **en memoria**: **PDF** (portada → resumen ejecutivo → informe cualitativo → análisis léxico con gráfico → libro de códigos con ejemplos → tabla de trazabilidad opcional → nota metodológica), **Word** editable, **CSV** (BOM UTF-8) y **Excel** (2 hojas). La descarga viaja autenticada.

---

## 6. Los prompts son configurables (y por qué importa)

Los 4 prompts (`propose_categories`, `codify`, `interpret_lexical`, `qualitative_report`) viven en `app/prompts_default.json` y se editan desde la UI (los cambios se guardan en `app/prompts.json`, que se superpone a los defaults y no es necesario para arrancar) (Configuración → Configuración metodológica, contraseña `ADMIN_PASSWORD`). Cambios en vivo, sin reiniciar. La "metodología" de SoftInsight es ajustable por el sociólogo del equipo sin tocar código, y afinable por vertical a medida que llegue feedback.

---

## 7. Plantillas de marcos teóricos: 12 en 5 industrias

`app/templates.py` trae 12 plantillas escritas a mano, cada una con marco teórico + 4–5 categorías con definición y criterios de inclusión **y exclusión** (los criterios de exclusión son lo que hace precisa a la codificación IA: le dicen al modelo dónde termina una categoría y empieza la vecina).

| Industria | Plantillas |
| --- | --- |
| **Educación Superior** | Evaluación Docente (CNA) · Satisfacción Estudiantil · Acreditación Institucional (CNA, Ley 21.091) |
| **Estudios de Mercado** | Satisfacción de Clientes (verbatims NPS) · Percepción de Marca · Investigación de Producto/Concepto |
| **Organizaciones y B2B** | Clima y Cultura Organizacional · Feedback de Empleados (pulso/salida) · Voz del Cliente B2B |
| **Sector Público** | Consultas Ciudadanas · Evaluación de Servicios Públicos |
| **Salud** | Experiencia de Pacientes |

En la UI de creación de proyecto aparecen agrupadas por industria; en el Libro de códigos, como selector agrupado. Al aplicarlas, las categorías entran con origen `plantilla` y estado `propuesta`. Las plantillas educativas conservan el anclaje CNA/CNE.

---

## 8. Integraciones: arquitectura

```
app/services/integrations/
├── base.py          ← el contrato: fetch_responses(config) -> pandas.DataFrame
│                       + IntegrationError (mensajes aptos para la UI)
├── qualtrics.py     ← list_surveys() + fetch_responses() vía API v3 (export CSV)
├── google_forms.py  ← fetch_responses() vía planilla de Google Sheets pública
└── credentials.py   ← cifrado Fernet de credenciales (clave derivada de SECRET_KEY)
```

Principios:

1. **Una integración es solo otra fuente del mismo DataFrame.** La creación de proyecto no distingue el origen: `_create_project_from_df()` es el camino común.
2. **Las credenciales nunca llegan al navegador.** El token de Qualtrics se guarda cifrado en `users.integrations`; la UI solo sabe si está configurado y para qué datacenter.
3. **Errores hablables:** token inválido, encuesta sin respuestas, planilla privada (con instrucciones de cómo compartirla), URL mal formada — todos llegan a la UI como mensajes accionables, no como errores 500.
4. **Importación puntual, no sincronización continua** (alcance deliberado de esta versión).

---

## 9. La auditoría: cómo se garantiza el "nada es caja negra"

Cada acción relevante pasa por `store.log_event()`, que registra **timestamp** (UTC), **actor** (`analista` / `claude` / `sistema`), **acción** y **detalle** completo. El evento se escribe en dos lugares: dentro del documento del proyecto (registro canónico, vía `$push`) y en la colección `audit_events` (copia consultable).

Acciones auditadas: creación de proyecto (con fuente), **importaciones** (encuesta/planilla + n° de respuestas), análisis léxico, aplicación de plantilla, cada categoría propuesta por la IA, cada validación/edición/descarte humano, categorías manuales, comentarios, la codificación del corpus, cada re-codificación (antes/después) y la generación del informe.

**Auditoría de organización (T-007).** Las acciones que no pertenecen a un proyecto se insertan con `store.log_org_event()` en `audit_events` con `project_id: null`, `org_id`, `user_id` de quien actúa, `actor: "analista"` y `detail` con el email y rol afectados, **nunca contraseñas**: `miembro_creado`, `miembro_rol_cambiado`, `miembro_desactivado`, `miembro_reactivado` y `cambio_password`. Un PATCH que no cambia nada no genera evento.

No hay endpoint para borrar ni editar eventos: el log solo crece.

---

## 10. El frontend por dentro

### Estructura por features (v1.1)

Cada feature es dueña de sus componentes, hooks, tipos y su slice de API. Lo transversal vive en `shared/`.

```
src/
├── App.tsx / main.tsx        ← router y arranque; nada más
├── shared/
│   ├── api/client.ts         ← ÚNICO punto de contacto HTTP: token, errores, 401 → /login, descargas blob
│   ├── components/           ← Button, Card, Input, Table (el sistema de diseño)
│   ├── layout/               ← Header, Sidebar
│   └── hooks/
│       ├── useAsync.ts       ← patrón busy/error que se repetía en todas las páginas
│       ├── usePolling.ts     ← polling con limpieza automática (codificación e informe)
│       └── useDownload.ts    ← descargas con estado por botón
└── features/
    ├── auth/                 ← useAuth (contexto de sesión), LoginPage, api
    ├── projects/             ← ProjectList, NewProject (3 orígenes), ProjectView,
    │                            Dashboard, useProjectData (fetch + contexto del proyecto activo)
    ├── analysis/             ← api + types del análisis, y por sub-feature:
    │   ├── lexical/          ← LexicalAnalysis
    │   ├── codebook/         ← Codebook, CategoryCard, CommentThread, ManualCategoryForm
    │   ├── coding/           ← Coding, ResponsesTable
    │   ├── traceability/     ← Traceability, CategoryBars, ConfidenceInfo, useTraceabilityFilters
    │   ├── report/           ← ReportView (barra de progreso streaming), ReportBody
    │   └── audit/            ← AuditLog
    ├── export/               ← ExportReport, api de descargas
    ├── integrations/         ← QualtricsSection, api (credenciales + importación)
    ├── settings/             ← cuenta, importar demo, panel de prompts
    └── docs/                 ← Documentation
```

Alias de imports: `@/` apunta a `src/` (configurado en `tsconfig.json` y `vite.config.ts`).

### Rutas

| URL | Pantalla |
| --- | --- |
| `/login`, `/signup` | Acceso (con landing de venta al costado) |
| `/` | Mis proyectos |
| `/proyectos/nuevo` | Crear proyecto (3 orígenes + plantillas por industria) |
| `/proyectos/:id` | Dashboard del proyecto |
| `/proyectos/:id/lexico · codigos · codificacion · trazabilidad · informe · exportar · auditoria` | Las pestañas del proyecto |
| `/configuracion` | Cuenta, importar demo, panel de prompts |
| `/documentacion` | Guía de uso |

### Decisiones de diseño visual (sin cambios en v1.1)

- **Paleta**: fondo crema (`#FFFAF0`), tarjetas blancas, **celeste `#0099CC`** para acción primaria. Verde/naranja/rojo reservados para semántica.
- **Tipografía**: Inter. **Variables CSS** en un solo lugar.
- El refactor por features fue **cero cambios visuales**: el hash del CSS compilado es idéntico al de v1.0.

---

## 11. Seguridad: qué está cubierto y qué no (honestamente)

**Cubierto para la beta:**

- Contraseñas con hash PBKDF2 + sal (irreversibles), email con índice único.
- Tokens firmados con expiración; sin token no hay datos.
- Aislamiento total entre cuentas, verificado con pruebas de acceso cruzado.
- La API key de Anthropic vive solo en el servidor (`.env`).
- Credenciales de integraciones **cifradas** (Fernet) y nunca expuestas al navegador.
- Validación de inputs (Pydantic) y mensajes de error de integraciones sin filtrar secretos.

**Pendiente para producción (consciente y documentado):**

- HTTPS (en beta local no aplica; en despliegue lo da la plataforma).
- Recuperación de contraseña y verificación de email.
- Revocación de tokens en servidor y rate-limiting de login.
- `SECRET_KEY` con default de desarrollo: **en producción debe ser un valor aleatorio largo** (firma los JWT **y** deriva la clave de cifrado de credenciales — si cambia, hay que re-ingresar las credenciales de integraciones).
- MongoDB local sin autenticación (correcto para desarrollo; Atlas la trae por defecto).

---

## 12. Configuración (backend/.env)

| Variable | Qué controla | Default |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | Acceso a Claude | — sin ella, solo funciona el análisis léxico |
| `SECRET_KEY` | Firma de tokens + cifrado de credenciales | valor de desarrollo (cambiar en producción) |
| `MONGODB_URI` | Conexión a MongoDB | `mongodb://localhost:27017/softinsight` |
| `ADMIN_PASSWORD` | Panel interno de prompts | `softinsight2026` |
| `CLAUDE_MODEL` | Qué modelo se usa | `claude-sonnet-4-6` |
| `CLAUDE_MODEL_REPORT_V2` | Modelo del informe profundo | = `CLAUDE_MODEL` |
| `SYNTHESIS_BATCH_INPUT_TOKENS` | Tokens de entrada por tanda de síntesis (informe v2) | `10000` |
| `MERGE_INPUT_TOKENS` | Tokens de entrada por llamada de fusión/selección de citas | `16000` |
| `CLAUDE_LARGE_OUTPUT_TOKENS` | Techo de salida por llamada grande (acotado al límite real del modelo) | `32000` |
| `CLAUDE_MAX_OUTPUT_TOKENS` | Límite de salida del modelo (si no se define, se sondea a la API) | sonda |
| `CLAUDE_LOG_DIR` / `CLAUDE_LOG_RAW` | Carpeta de logs / guardar texto crudo de todas las llamadas | `backend/logs` / `0` |
| `CLAUDE_PRICING_JSON` | Precios por millón de tokens para la estimación de costo | tabla interna |

**Migrar a producción** = apuntar `MONGODB_URI` a un cluster de MongoDB Atlas, definir una `SECRET_KEY` fuerte, y desplegar backend (Render/Railway) + frontend (Vercel). El código no cambia.

---

## 13. Costos de IA por proyecto (orden de magnitud)

Con el dataset demo de 320 respuestas y Claude Sonnet:

| Operación | Llamadas | Nota |
| --- | --- | --- |
| Interpretación léxica | 1 | pequeña |
| Propuesta de categorías | 1 | muestra de 60 respuestas |
| Codificación | ~13 | lotes de 25 respuestas |
| Informe rápido (v1) | 1 | la más grande; en streaming (mismo costo) |
| Informe profundo (v2) | n + ~15 | 1 por respondente (cacheada) + tandas de síntesis, agrupación, citas y redacción |

Total con informe rápido: **menos de US$1 por corrida completa**. El informe profundo, medido con 122 respondentes y Sonnet 4.6: ≈ US$1,9 el Prompt 1 (una sola vez, queda en caché) + ≈ US$1,7 síntesis y redacción, ~7 minutos. El léxico, los filtros, la trazabilidad y las exportaciones no consumen API. El consumo real por proyecto se ve en el panel de administración.

---

## 14. Verificación y limitaciones conocidas

**Cómo se verificó la v1.1:** suite en `backend/tests/` que corre contra mongomock y con la IA simulada (sin gastar API): flujo end-to-end completo (signup → proyecto → léxico → validación → codificación → trazabilidad → informe → 4 exportaciones → auditoría), aislamiento multi-tenant (acceso cruzado a lectura/escritura/borrado/progreso → 404), integraciones con Qualtrics y Google simulados (incluidos los caminos de error), y migración SQLite → Mongo idempotente.

**Limitaciones conocidas:**

1. **Colaboración**: comentarios sí; codificación concurrente de varios analistas todavía no (los roles ya existen: ver 4.1).
2. **Progreso en memoria**: si el servidor se reinicia a mitad de una codificación o informe, la barra se pierde (lo ya guardado persiste; se puede relanzar sin daño).
3. **Sin emails** (confirmación, recuperación): decisión de alcance.
4. **Integraciones puntuales**: importan al crear el proyecto; no hay sincronización continua ni OAuth de Google (documentado).
5. **Tests de UI**: el backend tiene suite propia; Playwright para la UI queda pendiente.

---

## 15. Resumen de las decisiones y su lógica

| Decisión | Alternativa descartada | Razón |
| --- | --- | --- |
| **MongoDB + pymongo** | Seguir en SQLite / saltar a Postgres normalizado | El modelo ya era documental; Mongo da updates parciales e índices anidados sin reescribir el código de análisis. Atlas = cambiar una URI |
| **Updates parciales $set/$push** | Reescribir el documento completo | Operaciones puntuales no tocan las 320 respuestas; el hilo de codificación no pisa el trabajo del analista |
| Documento por proyecto | Normalización relacional completa | Un proyecto se analiza como unidad; los IDs internos estables hacen mecánica una normalización futura |
| **Frontend por features** | Estructura por tipo de archivo / migrar a Next.js | Cada feature es dueña de su código; Next.js no aporta a una SPA detrás de login |
| **Streaming para el informe** | Spinner con mensaje fijo | Progreso genuino (tokens recibidos + sección en curso); honestidad también en la UX |
| **Qualtrics con token cifrado en backend** | Token en localStorage del navegador | El navegador es el lugar menos seguro; la UI no necesita el token, solo saber que existe |
| **Google Forms vía planilla pública** | OAuth completo de Google | Cubre la importación puntual sin flujo de consentimiento ni verificación de app; documentado como iteración futura |
| JWT propio + PBKDF2 (stdlib) | Supabase Auth, passlib/bcrypt | Sin servicios externos ni dependencias frágiles para la beta |
| reportlab | pypdf / HTML-a-PDF | Control total del layout del documento de auditoría |
| CSS propio con variables | Tailwind / Material | Requisito explícito; branding coherente y liviano |
| Categorías de plantilla entran como "propuesta" | Entrar validadas | La validación humana es el método, no un trámite |
| Prompts en JSON editables por UI | Prompts en el código | El sociólogo ajusta la metodología sin deploy |
| Confianza para priorizar, nunca para filtrar | Auto-descarte bajo umbral | Honestidad metodológica: es orientativa, no estadística |

---

*Documento actualizado para el equipo SoftInsight — julio 2026. Corresponde al estado del código en `07_MVP/` (v1.1).*
