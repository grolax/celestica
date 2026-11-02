# Contratos de API

Archivo mantenido por el agente `supervisor`. Es la única fuente de verdad entre backend y frontend.
Los endpoints ya existentes en la v1.1 están documentados en `07_MVP/COMO_FUNCIONA.md` y en `/docs` del backend (FastAPI).
Aquí solo se registran endpoints **nuevos o modificados**.

## Formato de cada entrada

### `MÉTODO /api/ruta`
- **Tarea:** T-xxx · **Requerimiento:** RF-xx
- **Roles permitidos:** admin | analista | lector
- **Entrada:** (JSON de ejemplo o parámetros)
- **Respuesta 200:** (JSON de ejemplo)
- **Errores:** código — mensaje para la UI — cuándo ocurre

---

## RF-02 · Organizaciones (T-004)

Sin endpoints nuevos. Cambia la **forma del usuario** que devuelven los tres endpoints de autenticación, y el alcance de todos los endpoints de proyectos pasa de "proyectos del usuario" a "proyectos de su organización". Rutas, entradas y el resto de las respuestas no cambian.

### Objeto `user` (compartido por `POST /auth/signup`, `POST /auth/login` y `GET /auth/me`)
Campos nuevos: `rol` y `organizacion`. Los existentes se mantienen (incluido `empresa`, por compatibilidad).
```json
{
  "id": "usr_1a2b3c4d5e",
  "email": "ana@udp.cl",
  "nombre": "Ana",
  "empresa": "UDP",
  "rol": "admin",
  "organizacion": { "id": "org_9f8e7d6c5b", "nombre": "UDP" }
}
```
- `rol`: `"admin" | "analista" | "lector"`. En T-004 todo usuario es `"admin"` de su organización; los permisos por rol llegan con RF-03.

### `POST /auth/signup`
- **Tarea:** T-004 · **Requerimiento:** RF-02
- **Roles permitidos:** público
- **Entrada:** sin cambios: `{"email": "ana@udp.cl", "password": "clave12345", "nombre": "Ana", "empresa": "UDP"}`
- **Efecto nuevo:** crea una organización y deja al usuario como su `admin`. Nombre de la organización: `empresa` (sin espacios sobrantes); si está vacío, `"Organización de <nombre>"`; si también falta el nombre, `"Organización de <email>"`.
- **Respuesta 200:** `{"token": "<jwt>", "user": <objeto user>}`
- **Errores:** sin cambios. 409 — "Ya existe una cuenta con ese email." · 422 — validación (contraseña < 8 caracteres, email inválido).

### `POST /auth/login` y `GET /auth/me`
- **Tarea:** T-004 · **Requerimiento:** RF-02
- **Roles permitidos:** público (login) · cualquier usuario autenticado (me)
- **Entrada:** sin cambios.
- **Respuesta 200:** login `{"token": "<jwt>", "user": <objeto user>}`; me `<objeto user>`.
- **Errores:** sin cambios (401 en ambos casos).

### Endpoints de proyectos (`/api/projects`, `/api/projects/{project_id}/...`, `from-qualtrics`, `from-google-forms`, `import-legacy`)
- **Tarea:** T-004 · **Requerimiento:** RF-02
- **Cambio de alcance:** un usuario ve y opera los proyectos **de su organización**. Un proyecto de otra organización responde **404 — "Proyecto no encontrado"**, igual que hoy con proyectos de otro usuario.
- **Entradas y respuestas:** sin cambios.

---

## RF-03 · Permisos por rol (T-006)

Sin endpoints nuevos. Se agrega un error **403** en las operaciones que el rol no permite y un campo `author_id` en los comentarios. Decisiones del usuario del 2026-10-30.

### Matriz de permisos
| Operación | Lector | Analista | Admin |
| --- | --- | --- | --- |
| Ver: `GET /api/projects`, `GET /api/projects/{id}`, `responses`, `GET lexical`, `codify/progress`, `summary`, `audit`, `GET report`, `report/progress`, `usage`, `GET /api/framework-templates` | ✅ | ✅ | ✅ |
| Descargar: `export/traceability`, `export/pdf`, `docx`, `csv`, `xlsx` | ✅ | ✅ | ✅ |
| Comentar: `POST .../categories/{cid}/comments` | ✅ | ✅ | ✅ |
| Borrar comentario: `DELETE .../comments/{comid}` | solo los suyos | todos | todos |
| Crear proyecto: `POST /api/projects`, `from-qualtrics`, `from-google-forms`, `import-legacy` | ❌ | ✅ | ✅ |
| Analizar: `apply-template`, `POST lexical`, `categories/propose`, `POST categories`, `PATCH categories/{cid}`, `POST codify`, `PUT responses/{rid}/codings`, `POST report` | ❌ | ✅ | ✅ |
| Borrar proyecto: `DELETE /api/projects/{id}` | ❌ | ✅ | ✅ |
| Credenciales y encuestas de Qualtrics: `/api/integrations/qualtrics/*` | ❌ | ✅ | ✅ |
| Gestión de miembros (`/api/org/members`, T-007) | ❌ | ❌ | ✅ |

Los endpoints `/api/admin/*` siguen protegidos por la contraseña interna (`X-Admin-Password`) hasta RF-07; no dependen del rol.

### Error nuevo (todas las operaciones marcadas ❌)
- **403** — `"Tu rol (Lector) no permite esta acción."` (el texto usa la etiqueta en español del rol del usuario).
- Orden de verificación: sesión (401) → rol (403) → proyecto de la organización (404). El 403 no depende de que el proyecto exista, así que no revela proyectos de otras organizaciones.
- Borrar un comentario ajeno siendo lector: **403** — `"Solo puedes borrar tus propios comentarios."`

### Comentarios (`POST .../comments`, y dentro de `categories[].comments[]` en `GET /api/projects/{id}`)
Campo nuevo `author_id` (id del usuario). Los comentarios antiguos no lo tienen: un lector no puede borrarlos.
```json
{ "id": "com_ab12cd34", "text": "Revisar esta definición", "author": "Ana", "author_id": "usr_1a2b3c4d5e", "timestamp": "2026-10-30T15:00:00+00:00" }
```

---

## RF-03 · Gestión de miembros (T-007)

Solo el **admin** de la organización. Todas responden **403** `"Tu rol (<rol>) no permite esta acción."` a analistas y lectores. Un `user_id` que no pertenece a la organización del admin responde **404** `"Miembro no encontrado"`.

### Objeto `member`
```json
{ "id": "usr_5f6g7h8i9j", "email": "luis@udp.cl", "nombre": "Luis", "rol": "lector", "activo": true, "debe_cambiar_password": true, "created_at": "2026-10-30T15:00:00+00:00" }
```

### `GET /api/org/members`
- **Roles permitidos:** admin
- **Respuesta 200:** `[<member>, ...]` (incluye desactivados, ordenados por `created_at`).

### `POST /api/org/members`
- **Roles permitidos:** admin
- **Entrada:** `{"email": "luis@udp.cl", "nombre": "Luis", "rol": "lector"}`
- **Efecto:** crea el usuario en la organización del admin con una **contraseña temporal generada por el servidor** (12 caracteres aleatorios) y `debe_cambiar_password: true`.
- **Respuesta 201:** `{"member": <member>, "password_temporal": "k7Q2-mX9p-Lr4z"}`. La contraseña temporal **solo se entrega en esta respuesta**; no se guarda en claro ni se puede volver a consultar.
- **Errores:** 409 — "Ya existe una cuenta con ese email." · 422 — email inválido o rol fuera de `admin | analista | lector`.

### `PATCH /api/org/members/{user_id}`
- **Roles permitidos:** admin
- **Entrada:** uno o ambos campos: `{"rol": "analista"}`, `{"activo": false}` (desactivar = "quitar"), `{"activo": true}` (reactivar).
- **Respuesta 200:** `<member>` actualizado.
- **Errores:** 404 — "Miembro no encontrado" · 409 — "La organización debe tener al menos un administrador activo." (al quitar el rol admin o desactivar al último admin activo) · 400 — "No puedes desactivar tu propia cuenta." · 422 — rol inválido o cuerpo vacío.
- **Precedencia:** el 409 se evalúa antes que el 400. Si el admin es el único admin activo y se desactiva a sí mismo, recibe 409; con otro admin activo, recibe 400. Un admin puede cambiarse su propio rol si queda otro admin activo.
- **Sesiones:** cambiar la contraseña no cierra las sesiones abiertas (el token anterior vale hasta que expira). La revocación llega con RNF-04.

### `POST /auth/change-password`
- **Roles permitidos:** cualquier usuario autenticado (también con `debe_cambiar_password: true`)
- **Entrada:** `{"password_actual": "k7Q2-mX9p-Lr4z", "password_nueva": "miClaveNueva1"}`
- **Respuesta 200:** `{"user": <objeto user>}` con `debe_cambiar_password: false`.
- **Errores:** 400 — "La contraseña actual no es correcta." · 422 — "La contraseña debe tener al menos 8 caracteres" · 400 — "La contraseña nueva debe ser distinta de la actual."

### Cambios en endpoints existentes
- **Objeto `user`** (signup, login, me, change-password): campo nuevo `debe_cambiar_password: boolean`.
- **Contraseña temporal pendiente:** mientras `debe_cambiar_password` sea `true`, toda ruta salvo `GET /auth/me` y `POST /auth/change-password` responde **403** — `"Debes cambiar tu contraseña temporal antes de continuar."`
- **Miembro desactivado:** `POST /auth/login` y cualquier ruta con su token responden **401** — `"Tu cuenta fue desactivada. Contacta al administrador de tu organización."`
- **Auditoría:** crear miembro, cambiar rol, desactivar/reactivar y cambiar contraseña quedan en `audit_events` con `org_id`, `project_id: null`, actor y detalle (sin contraseñas).


---

## Panel interno (`/api/admin/*`) · T-009

- **Cambio de código de error:** con `X-Admin-Password` ausente o incorrecta, los 5 endpoints (`GET /api/admin/usage`, `GET /api/admin/health`, `GET /api/admin/prompts`, `PUT /api/admin/prompts/{key}`, `POST /api/admin/prompts/{key}/reset`) responden **403** — "Contraseña de administrador incorrecta" (antes 401). Motivo: el 401 se reserva para la sesión del usuario; el frontend lo interpreta como sesión vencida.

---

## RF-22 / RF-25 · Vista previa con tipos de pregunta detectados (T-010)

Tres endpoints de **solo lectura**: leen los datos, detectan el tipo de cada columna con **reglas determinísticas (sin IA)** y devuelven un resumen. **No crean ni guardan nada.** Uno por cada fuente, con la misma entrada que su endpoint de creación (sin `name`, `marco_teorico`, `text_column` ni `template`).

| Endpoint | Entrada |
| --- | --- |
| `POST /api/projects/preview` | multipart: `file` (CSV o XLSX) |
| `POST /api/projects/preview/qualtrics` | `{"survey_id": "SV_abc123"}` (usa las credenciales Qualtrics del usuario) |
| `POST /api/projects/preview/google-forms` | `{"sheet_url": "https://docs.google.com/spreadsheets/d/..."}` |

- **Roles permitidos:** analista, admin (lector → 403 como el resto de las operaciones de creación).
- **Respuesta 200:**
```json
{
  "n_filas": 240,
  "preguntas": [
    {
      "columna": "respuesta",
      "tipo": "abierta",
      "motivo": "Textos largos y casi todos distintos (promedio 18 palabras).",
      "n_respuestas": 236,
      "n_vacias": 4,
      "valores_distintos": 231,
      "ejemplos": ["La ponderación de las evaluaciones no está clara…", "…", "…"]
    },
    {
      "columna": "P5_recomendaria",
      "tipo": "nps",
      "motivo": "Números enteros entre 0 y 10 y el título menciona \"recomendar\".",
      "n_respuestas": 240,
      "n_vacias": 0,
      "valores_distintos": 11,
      "ejemplos": ["9", "10", "6"],
      "escala": {"min": 0, "max": 10}
    },
    {
      "columna": "carrera",
      "tipo": "segmento",
      "motivo": "Pocos valores repetidos y el título sugiere un grupo (carrera).",
      "n_respuestas": 240,
      "n_vacias": 0,
      "valores_distintos": 6,
      "ejemplos": ["Psicología", "Medicina", "Enfermería"],
      "opciones": [{"valor": "Psicología", "n": 61}, {"valor": "Medicina", "n": 55}]
    }
  ],
  "advertencias": []
}
```
- **`tipo`**: `abierta` · `escala` · `nps` · `si_no` · `seleccion_unica` · `seleccion_multiple` · `numerica` · `fecha` · `identificador` · `segmento` · `constante` (un solo valor en todas las filas, por ejemplo el enunciado de la pregunta) · `sin_datos` (columna vacía).
- **`motivo`**: frase corta en español, sin jerga, que explica por qué se detectó ese tipo (para mostrar al usuario).
- **`ejemplos`**: hasta 3 valores no vacíos, en el orden en que aparecen; textos largos recortados a 120 caracteres con "…".
- **`escala`**: solo en `escala` y `nps`.
- **`opciones`**: solo en `si_no`, `seleccion_unica`, `seleccion_multiple` y `segmento`; hasta 20 valores con su conteo, de mayor a menor (en `seleccion_multiple`, cada opción separada).
- **`advertencias`** (frases para la UI):
  - Sin columnas `abierta`: `"Esta encuesta no tiene preguntas abiertas: se analizarán solo las preguntas cerradas, sin libro de códigos ni IA."` (texto actualizado en T-025; antes decía "…llegará pronto.")
  - `n_filas < 10`: `"La encuesta tiene muy pocas respuestas (N); los resultados serán poco representativos."`
  - Por cada columna con más de la mitad vacía: `"La columna «X» tiene más de la mitad de sus respuestas vacías."`
- **Errores:**
  - 400 — "No se pudo leer el archivo: …" (archivo ilegible) · "Los datos no contienen filas" (sin filas).
  - 400 — mensajes de integración (Qualtrics/Google) igual que en `from-qualtrics` / `from-google-forms`.
  - 403 — "Tu rol (Lector) no permite esta acción."
  - 413 — "El archivo supera el máximo de 20 MB." (solo `preview` con archivo).

---

## RF-23 · Preguntas del proyecto y varias preguntas abiertas (T-011a)

Decisiones del usuario (2026-10-30): un análisis por pregunta abierta, la IA solo se ejecuta a pedido y pregunta por pregunta; respuestas vacías = **N/A** (se guardan como `null`, nunca como una opción); columnas ramificadas se unen en una pregunta; a la IA solo se le envían como contexto las preguntas marcadas `contexto_ia` (por defecto solo **género** y **edad**) y **nunca** las de tipo `identificador`.

### Objeto `pregunta`
```json
{ "id": "q_3", "titulo": "¿En qué comuna vives actualmente?", "columnas": ["¿En qué comuna vives actualmente?  ", "¿En qué comuna vives actualmente?   2"],
  "tipo": "segmento", "contexto_ia": false, "n_respuestas": 498, "n_na": 2 }
```
- `tipo`: los mismos de T-010. `columnas`: una o varias (varias = columnas ramificadas unidas; el valor de cada persona es el primero no vacío). `n_na`: respuestas vacías.

### `POST /api/projects`, `/api/projects/from-qualtrics`, `/api/projects/from-google-forms` (modificados)
- **Roles:** analista, admin.
- **Entrada nueva (opcional):** `preguntas`: lista con lo que el usuario confirmó en la vista previa. En `POST /api/projects` va como campo de formulario con JSON en texto; en los otros dos, como campo del cuerpo JSON.
```json
[ {"titulo": "28. ¿Qué tendría que cambiar…?", "columnas": ["28. ¿Qué tendría que cambiar…?"], "tipo": "abierta", "contexto_ia": false},
  {"titulo": "Comuna", "columnas": ["¿En qué comuna vives actualmente?  ", "¿En qué comuna vives actualmente?   2"], "tipo": "segmento", "contexto_ia": false},
  {"titulo": "1. ¿Cuál es tu edad?", "columnas": ["1. ¿Cuál es tu edad?"], "tipo": "segmento", "contexto_ia": true} ]
```
  - Columnas que no aparecen en ninguna pregunta no se guardan.
  - **Sin `preguntas` (compatibilidad):** se arman con `detectar()` sobre todas las columnas, se fuerza `text_column` (o la detectada, como hoy) a `abierta`, y `contexto_ia` queda `true` solo en preguntas `segmento`, `numerica` o `seleccion_unica` cuyo título menciona género/sexo o edad (nunca `identificador`).
- **Respuesta 200:** la de hoy más `preguntas_abiertas`:
```json
{ "id": "proj_ab12cd34ef", "n_responses": 484, "text_column": "28. ¿Qué tendría que cambiar…?",
  "preguntas_abiertas": [ {"id": "q_28", "titulo": "28. ¿Qué tendría que cambiar…?", "n_respuestas": 484}, {"id": "q_30", "titulo": "30. ¿Qué palabras asocias…?", "n_respuestas": 211} ] }
```
  `n_responses` y `text_column` corresponden a la **primera** pregunta abierta (la "pregunta por defecto").
- **Errores nuevos:**
  - ~~400 — "Esta encuesta no tiene preguntas abiertas…"~~ Reemplazado en T-025 (RF-24): ver "RF-24 · Proyectos sin preguntas abiertas".
  - 422 — "La columna «X» no existe en los datos." · "La columna «X» está en más de una pregunta." · "Tipo de pregunta no válido: X." · "Una columna de identificación no se puede enviar a la IA." (`tipo: identificador` con `contexto_ia: true`).

### Parámetro `pregunta` en las operaciones de análisis (nuevo, opcional)
Query `?pregunta=<id>` en: `GET /api/projects/{id}`, `POST .../apply-template`, `GET .../responses`, `POST/GET .../lexical`, `POST .../categories/propose`, `POST .../categories`, `PATCH .../categories/{cid}`, `POST/DELETE .../comments`, `POST .../codify`, `GET .../codify/progress`, `PUT .../responses/{rid}/codings`, `GET .../summary`, `POST/GET .../report`, `GET .../report/progress`, `GET .../export/*`.
- Sin `pregunta`: se usa la **pregunta por defecto** (primera abierta). Con un id que no existe o que no es `abierta`: **404** — "Pregunta no encontrada".
- Las respuestas y los campos de análisis (`responses`, `lexical`, `lexical_interpretation`, `categories`, `codings`, `qualitative_report`) que devuelven estas operaciones **son los de esa pregunta**, con la misma forma que hoy. `responses[].meta` contiene **solo** las preguntas con `contexto_ia: true` (por título), nunca identificadores.
- Codificación e informe se lanzan por pregunta y su progreso es por pregunta: dos preguntas del mismo proyecto pueden tener estados distintos.

### `GET /api/projects/{id}` (modificado)
Además de lo de hoy (para la pregunta elegida o por defecto): `preguntas: [<pregunta>, ...]` (todas, sin las respuestas) y `pregunta: "<id de la pregunta que se está mostrando>"`.

## RF-23 · Una sola codificación a la vez por pregunta (T-019)

### `POST /api/projects/{id}/codify?pregunta=<id>` (modificado)
Rol: analista o admin (sin cambios).

Si ya hay una codificación en curso para el mismo `(proyecto, pregunta)`, **no se lanza otra** ni se llama a la IA. Responde `200` con el mismo formato que el informe:

```json
{ "status": "already_running", "total": 484 }
```

`total` es el del proceso que ya corre. Si no hay ninguna en curso, responde como hoy (`{"status": "started", "total": 484}`). La comprobación y el inicio son atómicos: dos llamadas simultáneas producen un solo `started`. Otra pregunta del mismo proyecto sí puede codificarse en paralelo.

La UI no necesita cambios: tras cualquiera de las dos respuestas empieza a consultar `codify/progress`, que mostrará el proceso en curso.

Errores: sin cambios (400 sin categorías validadas, 403, 404).

## RF-30 · Resultados de preguntas cerradas (T-020)

Decisiones del usuario (2026-10-30): porcentajes sobre quienes respondieron (sin N/A, que se informan aparte); en selección múltiple el % es de personas (puede sumar más de 100 %); escalas con palabras quedan como selección única por ahora; opciones de más a menos respuestas, salvo escalas y tramos, que van en su orden natural. **Sin IA:** todo se calcula en el servidor.

### `GET /api/projects/{id}/closed-results`
- **Roles:** lector, analista, admin (es "Ver").
- **Sin parámetros.** Devuelve todas las preguntas del proyecto de tipo `escala`, `nps`, `si_no`, `seleccion_unica`, `seleccion_multiple`, `segmento` y `numerica`, en el orden del proyecto. No incluye `abierta`, `identificador`, `fecha`, `constante` ni `sin_datos`.
- **Respuesta 200:**
```json
{
  "n_personas": 500,
  "preguntas": [
    { "id": "q_10", "titulo": "10. ¿Qué tan importante es para ti ser propietario/a…?", "tipo": "escala",
      "n_respuestas": 498, "n_na": 2, "tasa_respuesta": 99.6,
      "opciones": [ {"valor": "1", "n": 10, "pct": 2.0}, {"valor": "2", "n": 18, "pct": 3.6}, {"valor": "3", "n": 70, "pct": 14.1},
                    {"valor": "4", "n": 150, "pct": 30.1}, {"valor": "5", "n": 250, "pct": 50.2} ],
      "escala": { "min": 1, "max": 5, "promedio": 4.23, "desviacion": 0.98,
                  "top2": {"valores": [4, 5], "n": 400, "pct": 80.3}, "bottom2": {"valores": [1, 2], "n": 28, "pct": 5.6} } },
    { "id": "q_31", "titulo": "¿Qué tan probable es que nos recomiendes?", "tipo": "nps",
      "n_respuestas": 240, "n_na": 0, "tasa_respuesta": 100.0,
      "opciones": [ {"valor": "0", "n": 3, "pct": 1.3}, "… 0 a 10 …" ],
      "escala": { "min": 0, "max": 10, "promedio": 7.9, "desviacion": 2.1 },
      "nps": { "valor": 32.5, "promotores": {"n": 120, "pct": 50.0}, "pasivos": {"n": 82, "pct": 34.2}, "detractores": {"n": 38, "pct": 15.8} } },
    { "id": "q_5", "titulo": "5. ¿Con quién vives actualmente?", "tipo": "seleccion_multiple",
      "n_respuestas": 497, "n_na": 3, "tasa_respuesta": 99.4,
      "opciones": [ {"valor": "Con mi pareja", "n": 210, "pct": 42.3}, {"valor": "Con mis padres", "n": 190, "pct": 38.2} ],
      "nota": "Cada persona puede elegir varias opciones; los porcentajes pueden sumar más de 100 %." },
    { "id": "q_40", "titulo": "Edad", "tipo": "numerica", "n_respuestas": 230, "n_na": 10, "tasa_respuesta": 95.8,
      "numerica": { "promedio": 34.2, "desviacion": 9.8, "mediana": 33, "min": 18, "max": 71 } }
  ]
}
```
- **Reglas de cálculo:**
  - `n_personas`: total de respondentes del proyecto. `n_respuestas` y `n_na` de esa pregunta (`n_respuestas + n_na = n_personas`). `tasa_respuesta` = `n_respuestas / n_personas × 100`.
  - `pct` = `n / n_respuestas × 100`. Porcentajes con 1 decimal; promedio, desviación y NPS con 2 decimales como máximo (los ejemplos son ilustrativos).
  - **`escala` y `nps`:** `opciones` con **todos** los valores enteros de `min` a `max`, en ese orden (con `n: 0` si nadie lo eligió). Rango: en `nps`, 0–10; en `escala` el proyecto no guarda el rango, así que `min` = 0 si alguien respondió 0 y 1 si no, y `max` = el mayor valor respondido. Valores no enteros o fuera de rango no entran en los cálculos y se cuentan en `n_invalidas` (campo presente solo si es > 0); en estas preguntas `pct`, top2/bottom2 y NPS se calculan sobre las respuestas válidas (`n_respuestas − n_invalidas`). Desviación **muestral** (n − 1; 0 si hay una sola respuesta). `top2`/`bottom2` solo en `escala`: los dos valores más altos y los dos más bajos del rango.
  - **`nps`:** promotores 9–10, pasivos 7–8, detractores 0–6; `valor` = % promotores − % detractores.
  - **`seleccion_multiple`:** cada respuesta se separa en opciones con el mismo criterio de la detección de T-010 (separador `;` o `,` y reconstrucción de opciones con el separador adentro); `n` = personas que eligieron la opción; incluye `nota`.
  - **`si_no`, `seleccion_unica`, `segmento`:** todas las opciones (sin límite de 20), de más a menos `n`; empate por orden alfabético. **Orden natural (tramos):** si todas las opciones salvo como máximo 2 contienen un número, se ordenan por el primer número que aparece en el texto (sin puntos de miles: "Menos de $360.000" → 360000, "20-24" → 20) y las que no tienen número van al final por `n`.
  - **`numerica`:** sin `opciones`; `numerica` con promedio, desviación muestral, mediana, mínimo y máximo de los valores numéricos (los no numéricos van a `n_invalidas`).
- **Proyectos sin preguntas cerradas** (por ejemplo, los antiguos migrados): `200` con `"preguntas": []`.
- **Errores:** 404 "Proyecto no encontrado" (incluye proyectos de otra organización); 401 sin sesión.

## RF-31 · Cruces por grupo de las preguntas cerradas (T-022)

Decisiones del usuario (2026-10-30): aviso de pocos datos con **menos de 10 personas** en el grupo (umbral fijo hasta la iteración 4); tramos de edad por defecto 18–24, 25–34, 35–44, 45–54, 55–64, 65+, **modificables por el cliente**. En T-022 los tramos llegan como parámetro y no se guardan; guardarlos por organización es de la iteración 4. **Sin IA.**

### `GET /api/projects/{id}/closed-results?por=<pregunta_id>[&cortes=18,25,35,45,55,65]` (modificado)
- **Roles:** lector, analista, admin (es "Ver").
- **Sin `por`:** responde exactamente como en T-020 (compatibilidad).
- **`por`:** id de una pregunta del proyecto de tipo `segmento`, `seleccion_unica`, `si_no` o `numerica`. Separa a las personas en grupos según su respuesta a esa pregunta.
  - Categóricas: un grupo por opción, en el mismo orden de las opciones en T-020 (de más a menos personas, u orden natural en tramos).
  - `numerica`: grupos por tramos según `cortes`, una lista de enteros crecientes separados por coma (por defecto `18,25,35,45,55,65`). Las etiquetas son `"18–24"`, …, `"55–64"` y `"65+"` (con guion largo `–`), más `"Menos de 18"` si hay valores bajo el primer corte, en orden de menor a mayor. Los valores no numéricos de la pregunta `por` quedan sin grupo.
  - Las personas sin respuesta en `por` (N/A o no numérica) **no entran en ningún grupo** y se informan en `n_sin_grupo`.
- **Respuesta 200:** el cuerpo de T-020, completo para el total, más:
```json
{
  "n_personas": 500,
  "por": { "id": "q_2", "titulo": "Género", "tipo": "segmento" },
  "umbral_pocos_datos": 10,
  "n_sin_grupo": 4,
  "grupos": [
    { "valor": "Mujer", "n_personas": 262, "pocos_datos": false },
    { "valor": "Hombre", "n_personas": 228, "pocos_datos": false },
    { "valor": "Otro", "n_personas": 6, "pocos_datos": true }
  ],
  "preguntas": [
    { "id": "q_10", "titulo": "10. ¿Qué tan importante…?", "tipo": "escala", "n_respuestas": 500, "n_na": 0, "tasa_respuesta": 100.0,
      "opciones": ["… igual que T-020 …"], "escala": { "…": "…" },
      "por_grupo": [
        { "valor": "Mujer", "n_respuestas": 262, "n_na": 0, "tasa_respuesta": 100.0,
          "opciones": [ {"valor": "1", "n": 4, "pct": 1.5}, "…" ],
          "escala": { "min": 1, "max": 5, "promedio": 4.4, "desviacion": 0.9, "top2": {"valores": [4, 5], "n": 215, "pct": 82.1}, "bottom2": {"valores": [1, 2], "n": 12, "pct": 4.6} } },
        { "valor": "Hombre", "…": "…" },
        { "valor": "Otro", "…": "…" }
      ] }
  ]
}
```
- **Reglas:**
  - `por_grupo` trae un elemento por cada grupo de `grupos`, en el mismo orden. Cada elemento se calcula con **las mismas reglas de T-020**, pero solo sobre las personas de ese grupo: `n_respuestas + n_na = n_personas del grupo`, y `pct` es sobre quienes respondieron en el grupo. Incluye `opciones`, `escala`, `nps`, `numerica`, `nota` y `n_invalidas` según el tipo, igual que en el total.
  - En `escala`, el rango (`min`/`max`) de cada grupo es **el del total**, para que los grupos se comparen sobre las mismas opciones. En categóricas, `opciones` de cada grupo lista **las mismas opciones del total y en su orden**, con `n: 0` si nadie del grupo la eligió.
  - `pocos_datos` = `n_personas` del grupo < `umbral_pocos_datos`. Los grupos con pocos datos **se calculan y se devuelven igual**; la pantalla muestra la advertencia.
  - La pregunta usada en `por` **no aparece** en `preguntas`.
  - Sin `por`, no vienen `por`, `umbral_pocos_datos`, `n_sin_grupo`, `grupos` ni `por_grupo`.
- **Errores:**
  - 404 "Proyecto no encontrado" (incluye proyectos de otra organización); 401 sin sesión.
  - 400 "Esa pregunta no se puede usar para separar en grupos." si `por` no existe en el proyecto o es de otro tipo.
  - 400 "Los tramos deben ser números enteros, separados por coma y de menor a mayor." si `cortes` no cumple; también si `cortes` viene sin `por` o con un `por` que no es `numerica`.

## RF-31 · Unir grupos en los cruces (T-023)

Decisión del usuario (2026-10-31): el cliente puede juntar grupos que ya vienen hechos (por ejemplo, los tramos de edad "20-24" y "25-29" en "20-29", o comunas en zonas) **según su preferencia y solo para ese análisis**: no se guarda. **Sin IA.**

### `GET /api/projects/{id}/closed-results?por=<pregunta_id>&unir=<json>` (modificado)
- **Roles:** lector, analista, admin (es "Ver").
- **`unir`:** solo junto con un `por` de tipo `segmento`, `seleccion_unica` o `si_no` (no `numerica`, que usa `cortes`). Es una lista JSON, codificada en la URL, de grupos unidos:
```json
[ { "nombre": "20-29", "valores": ["20-24", "25-29"] },
  { "nombre": "50 o más", "valores": ["50-54", "55-59", "60-64", "Mayor a 65"] } ]
```
- **Reglas:**
  - Cada grupo unido junta a las personas de todas sus `valores`, que son opciones de la pregunta `por` tal como aparecen en `grupos` sin unir. Las opciones que no se mencionan siguen como grupos propios.
  - Orden: el grupo unido ocupa el lugar de la primera de sus opciones en el orden de T-022; las demás opciones unidas desaparecen de la lista.
  - Los elementos de `grupos` que vienen de una unión llevan además `"unidos": ["20-24", "25-29"]`, en el orden de T-022. Los demás no traen ese campo.
  - Todo lo demás (`pocos_datos`, `por_grupo`, `n_sin_grupo`, rangos y opciones del total) funciona igual que en T-022, ahora sobre los grupos unidos.
  - Sin `unir`, la respuesta es igual a la de T-022.
- **Ejemplo de `grupos` con la unión de arriba** (edad):
```json
[ { "valor": "20-29", "n_personas": 216, "pocos_datos": false, "unidos": ["20-24", "25-29"] },
  { "valor": "30-34", "n_personas": 22, "pocos_datos": false },
  "…",
  { "valor": "50 o más", "n_personas": 151, "pocos_datos": false, "unidos": ["50-54", "55-59", "60-64", "Mayor a 65"] } ]
```
- **Errores 400** (mensaje exacto; `<x>` es el valor recibido):
  - "La forma de unir grupos no es válida." si `unir` no es JSON, no es una lista, o un elemento no tiene `nombre` (texto) y `valores` (lista de textos).
  - "Solo se pueden unir opciones de una pregunta de grupos." si `unir` viene sin `por` o con un `por` de tipo `numerica`.
  - "Un grupo unido necesita al menos dos opciones." si `valores` tiene menos de 2 elementos distintos.
  - "La opción «<x>» no existe en esa pregunta." si un valor no es una opción de `por`.
  - "La opción «<x>» está en más de un grupo." si un valor se repite entre grupos.
  - "Cada grupo unido necesita un nombre distinto." si un `nombre` está vacío (tras quitar espacios), se repite, o coincide con una opción que queda sin unir.
  - Los errores de T-022 se mantienen (404 de otra organización, 401 sin sesión, `por` y `cortes` inválidos).

## RF-24 · Proyectos sin preguntas abiertas (T-025)

Decisiones del usuario (2026-10-30): RF-24 va en la iteración 3 junto con RF-30. Un proyecto que solo tiene preguntas cerradas omite léxico, libro de códigos, codificación, informe cualitativo y sus exportaciones, y entrega los resultados de las cerradas y sus cruces. **Sin IA.**

### `POST /api/projects`, `/api/projects/from-qualtrics`, `/api/projects/from-google-forms` (modificados)
- Se acepta un proyecto **sin ninguna pregunta `abierta`** si tiene al menos una pregunta cerrada (`escala`, `nps`, `si_no`, `seleccion_unica`, `seleccion_multiple`, `segmento` o `numerica`).
- **Respuesta 200 sin abiertas:**
```json
{ "id": "proj_ab12cd34ef", "n_responses": 500, "text_column": "", "preguntas_abiertas": [] }
```
  `n_responses` = número de personas del proyecto. Con abiertas, la respuesta no cambia.
- Si viene `template` y no hay abiertas: el marco teórico de la plantilla se guarda como hoy, pero **no se agregan categorías** ni se registra `aplicacion_plantilla` (no hay libro de códigos).
- Evento de auditoría `creacion_proyecto` sin abiertas: `n_respuestas` = número de personas y `columna_texto` = `null`.
- **Error que reemplaza al anterior** ("Esta encuesta no tiene preguntas abiertas…" deja de existir):
  - 400 — "Esta encuesta no tiene preguntas que se puedan analizar: marca al menos una pregunta abierta o cerrada." (ni abiertas ni cerradas).
- El camino de compatibilidad (sin `preguntas`) **no cambia**: sigue forzando `text_column` (o la detectada) a `abierta`.

### `GET /api/projects/{id}` (modificado)
- En un proyecto sin abiertas y **sin** `?pregunta`: `200` con
```json
{ "id": "proj_ab12cd34ef", "name": "Encuesta solo cerradas", "marco_teorico": "", "created_at": "…", "columns": ["…"],
  "text_column": "", "categories": [], "n_responses": 500, "has_lexical": false, "n_coded": 0, "has_report": false,
  "n_audit_events": 1, "preguntas": ["<pregunta>", "…"], "pregunta": null }
```
  `n_responses` = número de personas. Con `?pregunta=<id>`: 404 "Pregunta no encontrada" (como hoy).
- Proyectos con abiertas: sin cambios.

### `GET /api/projects` (modificado)
- Cada proyecto agrega `n_abiertas` (número de preguntas `abierta`; los proyectos antiguos migrados tienen 1).
- En un proyecto sin abiertas, `n_responses` = número de personas (hoy saldría 0); `has_lexical`, `n_categories`, `n_coded` y `has_report` quedan en `false`/`0`.

### Operaciones de análisis en un proyecto sin abiertas
- Todas las que reciben `?pregunta` (léxico, categorías, codificación, informe, resumen, respuestas, exportaciones, `apply-template`): **404 "Pregunta no encontrada"**, con o sin `pregunta`. No se llama a la IA.
- `closed-results` (con y sin `por`), auditoría y borrar el proyecto funcionan igual que en cualquier proyecto.

## RF-30 / RF-31 · Excel de resultados de preguntas cerradas (T-027)

Decisiones del usuario (2026-10-31): los proyectos (con o sin abiertas) descargan un **Excel con los resultados de las cerradas**, con los **grupos** elegidos en "Ver por…" (tramos y grupos juntados incluidos) y **gráficos que tengan sentido**. **Sin IA.** El informe integrado llega con RF-51.

### `GET /api/projects/{id}/export/closed-xlsx[?por=<pregunta_id>&cortes=…&unir=<json>]`
- **Roles:** lector, analista, admin (como las demás exportaciones).
- **Parámetros:** los mismos de `closed-results` (T-020, T-022, T-023), con las mismas validaciones y **los mismos mensajes 400**. Las cifras del Excel son **exactamente** las que devuelve `closed-results` con esos parámetros (se calculan con la misma función).
- **Respuesta 200:** archivo `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, nombre `resultados_cerradas_<slug del proyecto>.xlsx`; si viene `por`, se agrega `_por_<slug del título de por>` antes de `.xlsx`.
- **Contenido:**
  - Hoja **"Resumen"**: nombre del proyecto, fecha de descarga, número de personas y la nota **"Cifras calculadas por la plataforma directamente desde las respuestas, sin IA. Los porcentajes son sobre quienes respondieron cada pregunta; quienes no respondieron aparecen como N/A."** Con `por`, además:
    - "Separado por: <título>" y la lista de grupos con su número de personas;
    - los grupos unidos ("<nombre>: <opciones>") y los tramos usados si la pregunta es numérica;
    - las personas sin grupo;
    - si hay grupos con pocos datos: **"Los grupos marcados con «Pocos datos» tienen menos de <umbral> personas: tómalos con cautela."**
  - Hoja **"Totales"**: un bloque por pregunta cerrada, en el orden del proyecto.
    - Encabezado del bloque: título, tipo, respondieron, N/A y % de respuesta.
    - Tabla de opciones (opción, personas, %).
    - Según el tipo: promedio, desviación, notas altas y bajas (escala); NPS, promotores, pasivos y detractores (nps); promedio, mediana, mínimo y máximo (numérica); la nota de la selección múltiple.
    - Gráfico: cada bloque con opciones lleva **barras horizontales** del % por opción, con el valor escrito en cada barra. En `escala` y `nps`, **todos** los valores en su orden (por ejemplo, 0 a 10), sin límite. En las demás, máximo 10 opciones; si hay más, el gráfico muestra las 10 con más personas (en el orden de la tabla) y el título lo dice: "10 opciones más frecuentes de <n>". (Precisado en la revisión 1 de T-027.)
  - Hoja **"Por grupo"** (solo con `por`): un bloque por pregunta.
    - Filas: "Todas las personas" y una por grupo, en el orden de `grupos`.
    - Columnas: "Respondieron", **"Pocos datos"** ("Sí" o vacía) y las que muestra la pantalla según el tipo: escala (promedio, notas altas, notas bajas); nps (NPS, promotores, detractores); numérica (promedio, mediana, mínimo, máximo); categóricas (% de cada opción, **todas** las opciones).
    - Gráfico por bloque:
      - Escala, NPS y numérica con grupos de **orden natural** (pregunta `por` numérica con tramos, o categórica ordenada por número según la regla de T-020): **líneas** del promedio (o del NPS) a lo largo de los grupos, para mostrar la **tendencia**.
      - Escala, NPS y numérica con grupos sin orden (género, comuna…): **barras** del promedio (o NPS) por grupo.
      - Categóricas: **barras agrupadas** del % de cada opción por grupo (máximo 6 opciones, las primeras del total).
      - Con más de 15 grupos, sin gráfico; en su lugar, el texto "Hay demasiados grupos para un gráfico legible; revisa la tabla."
      - Todos los gráficos muestran los valores escritos (no dependen solo del color). La fila "Todas las personas" no aparece como una barra más.
- **Errores:** los de `closed-results`: 400 con sus mensajes; 404 "Proyecto no encontrado" (incluida otra organización); 401 sin sesión.
- **Proyecto sin preguntas cerradas:** descarga un Excel con la hoja "Resumen" y la nota "Este proyecto no tiene preguntas cerradas."

## RF-23 / RNF-08 · Léxico y propuesta de categorías: una sola vez a la vez y estado consultable (T-029)

Problema: si el usuario sale de la pestaña mientras corre el léxico o la propuesta de categorías, la pantalla olvida que hay algo en curso y permite lanzarlo de nuevo. Eso duplica el gasto de IA y, en la propuesta, también las categorías. El servidor sigue trabajando y guarda el resultado.

### `POST /api/projects/{id}/lexical?pregunta=<id>` y `POST /api/projects/{id}/categories/propose?pregunta=<id>` (modificados)
- Rol, cuerpo y respuesta 200: **sin cambios** (siguen siendo síncronos y devuelven lo mismo que hoy).
- Si ya hay una ejecución **de la misma operación** en curso para el mismo `(proyecto, pregunta)`: **409**, sin llamar a la IA ni escribir nada:
  - léxico: `"El análisis léxico ya está en curso para esta pregunta. Espera a que termine."`
  - propuesta: `"Claude ya está proponiendo categorías para esta pregunta. Espera a que termine."`
- La comprobación y la marca son atómicas: de dos llamadas simultáneas, una responde 200 y la otra 409. La marca se quita al terminar, **también si hay error**; la ejecución que falla responde su error de siempre (por ejemplo, 503).
- Otra pregunta del mismo proyecto, u otra operación (léxico mientras se proponen categorías), sí puede correr en paralelo.
- Errores existentes sin cambios (403, 404, 503).

### `GET /api/projects/{id}/analysis-status?pregunta=<id>` (nuevo)
- **Roles:** lector, analista, admin.
- **Respuesta 200:**

```json
{ "lexical": "running", "propose": "idle" }
```

  Valores: `"running"` o `"idle"`. Solo informa si hay algo en curso; el resultado se obtiene con `GET .../lexical` y `GET /api/projects/{id}`.
- **Errores:** 404 "Proyecto no encontrado" (incluida otra organización); 401 sin sesión.
- Limitación conocida (igual que `codify/progress`): el estado vive en memoria de un solo proceso.

**Uso en la pantalla (T-030):**
- Al entrar a "Análisis léxico" o "Libro de códigos", consultar `analysis-status`.
- Si la operación está `running`, mostrar el estado ocupado y consultar cada 2 s hasta `idle`; entonces recargar el resultado.
- Un 409 al pulsar el botón también activa esa espera.

## RF-41 · Recomendaciones automáticas (T-032)

Reglas fijas, **sin IA**: alertas de calidad de datos, segmentos sugeridos para cruzar y plantilla sugerida. Las cifras se calculan en Python desde las respuestas guardadas.

### `GET /api/projects/{id}/recommendations`
- **Roles:** lector, analista, admin.
- **Respuesta 200:**

```json
{
  "alertas": [
    { "id": "pocas_respuestas_30", "nivel": "aviso", "pregunta_id": null,
      "mensaje": "La encuesta tiene 24 respuestas: los resultados pueden variar mucho. Tómalos como una primera mirada." },
    { "id": "muchas_vacias", "nivel": "aviso", "pregunta_id": "q_7",
      "mensaje": "Más de la mitad de las personas no respondió «¿Cuál es tu ingreso?» (15 de 24)." }
  ],
  "segmentos": [
    { "pregunta_id": "q_3", "titulo": "Género", "n_grupos": 3,
      "motivo": "Separa a las personas en 3 grupos con datos suficientes." }
  ],
  "plantilla": { "key": "evaluacion_docente_cna", "nombre": "Evaluación Docente (marco CNA)", "industria": "Educación Superior",
                 "motivo": "La encuesta menciona «profesor», «clase» y «evaluación»." }
}
```

- `alertas`: se generan en el orden de la tabla. `nivel` es `"importante"` o `"aviso"`, y `n` = personas del proyecto.

| `id` | Regla | Nivel | Mensaje |
| --- | --- | --- | --- |
| `pocas_respuestas` | n < 10 | importante | "La encuesta tiene muy pocas respuestas ({n}); los resultados serán poco representativos." |
| `pocas_respuestas_30` | 10 ≤ n < 30 | aviso | "La encuesta tiene {n} respuestas: los resultados pueden variar mucho. Tómalos como una primera mirada." |
| `muchas_vacias` | por pregunta (no `identificador`): `n_na > n / 2` | aviso | "Más de la mitad de las personas no respondió «{título}» ({n_na} de {n})." |
| `abierta_repetida` | abierta con ≥ 20 respuestas y ≤ 10 textos distintos (sin distinguir mayúsculas ni espacios) | aviso | "Las respuestas de «{título}» se repiten mucho (solo {k} distintas): quizás es una pregunta cerrada." |
| `abierta_corta` | abierta con ≥ 20 respuestas y mediana de palabras ≤ 2 (si no aplica `abierta_repetida`) | aviso | "La mitad de las respuestas de «{título}» tiene 2 palabras o menos: el análisis de temas tendrá poco material." |
| `cerrada_dispersa` | `seleccion_unica` o `segmento` con ≥ 30 respuestas y valores distintos > 50 % de sus respuestas | aviso | "«{título}» tiene casi tantas opciones distintas como respuestas ({k} de {r}): quizás es una pregunta abierta." |

  Los títulos de más de 80 caracteres se recortan con "…". La lista queda vacía si no hay alertas.
- `segmentos`: preguntas de tipo `segmento`, `seleccion_unica`, `si_no` o `numerica` (con los tramos por defecto). Se sugieren solo si cumplen todo:
  - forman entre 2 y 15 grupos;
  - al menos 2 grupos tienen ≥ 10 personas (`UMBRAL_POCOS_DATOS`);
  - responden al menos la mitad de las personas.

  Los grupos se arman con la **misma función** que `closed-results`.
  - **Orden:** primero las preguntas cuyo título dice género, sexo, edad, comuna, región, sede, carrera, tienda, área o cargo; después, las que tienen más grupos con datos suficientes.
  - **Máximo:** 3.
  - **`n_grupos`:** grupos con ≥ 10 personas; el motivo usa ese número.

  La lista queda vacía si no hay ninguna.
- `plantilla`: una plantilla sugerida por palabras clave, o `null`.
  - Cada plantilla de `templates.py` define `palabras_clave`: entre 6 y 15 palabras o raíces, sin tildes.
  - Se buscan, sin tildes ni mayúsculas, en el nombre del proyecto, su marco teórico y los títulos de todas sus preguntas. Cuenta cada palabra distinta encontrada.
  - Gana la de más coincidencias, con un mínimo de 2. En un empate, gana la primera en el orden de `FRAMEWORK_TEMPLATES`.
  - El motivo cita hasta 3 de las palabras encontradas, tal como aparecen en `palabras_clave`.
  - Es `null` si el proyecto no tiene preguntas abiertas, si ninguna plantilla llega al mínimo, o si el marco teórico del proyecto es exactamente el de una plantilla (ya eligió una).
- **Errores:** 404 "Proyecto no encontrado" (incluida otra organización); 401 sin sesión.
- Solo lectura: no escribe nada en la base ni en la auditoría.

## RF-31 / RF-41 · Cruce de 2 preguntas y pares sugeridos (T-035)

Pedido del usuario: ver el cruce de **una** pregunta elegida contra el "Ver por…", en vez de la lista completa, y recibir sugerencias de pares.

### `GET /api/projects/{id}/closed-results` y `GET /api/projects/{id}/export/closed-xlsx` (modificados)
- Parámetro nuevo opcional **`ver=<pregunta_id>`**: el resultado incluye **solo** esa pregunta cerrada en `preguntas` (lista de un elemento). Todo lo demás es igual (`n_personas`, `por`, `grupos`, `n_sin_grupo`, `umbral_pocos_datos`), y las cifras son idénticas a las que tiene esa pregunta sin `ver`.
- Sin `ver`, todo funciona como hoy (todas las preguntas).
- Se combina con `por`, `cortes` y `unir`, y también funciona sin `por` (solo el total de esa pregunta).
- Errores nuevos, 400 con estos mensajes:
  - `ver` no es una pregunta cerrada del proyecto: "La pregunta elegida no existe o no es una pregunta cerrada."
  - `ver` es igual a `por`: "Elige una pregunta distinta a la de «Ver por…»."
- Excel con `ver`: las hojas "Totales" y "Por grupo" traen solo esa pregunta; "Resumen" agrega la línea "Pregunta: <título>". Al nombre del archivo se agrega `_<slug del título de ver>`, al final, antes de `.xlsx`.
- Solo se calcula la pregunta pedida, para que sea más rápido.

### `GET /api/projects/{id}/recommendations` (modificado)
Campo nuevo **`cruces`**. `segmentos` se mantiene sin cambios, por compatibilidad.

```json
"cruces": [
  { "por": "q_2", "por_titulo": "1. ¿Cuál es tu edad?", "ver": "q_9", "ver_titulo": "¿Qué tan importante es para ti ser propietario?",
    "motivo": "Compara «¿Qué tan importante es para ti ser propietario?» entre los grupos de «1. ¿Cuál es tu edad?»." }
]
```

- **Pares:** cada segmento que hoy se sugiere en `segmentos` (mismas reglas y orden; se consideran todos los que cumplen las reglas, no solo los 3 primeros) se combina con cada pregunta de tipo **`escala` o `nps`** del proyecto, en el orden de la encuesta.
- **Orden de los pares** (precisado en la revisión 1 de T-035, para que se mezclen preguntas y grupos):
  - Con `i` = posición del segmento en su orden y `j` = posición de la escala o NPS en la encuesta (desde 0), los pares se ordenan por `(i + j, i)`.
  - Es decir: (seg0, m0), (seg0, m1), (seg1, m0), (seg0, m2), (seg1, m1), (seg2, m0)…
  - **Máximo 5.**
- Lista vacía si no hay segmentos o no hay escalas ni NPS.
- En `motivo`, los títulos de más de 60 caracteres se recortan con "…". `por_titulo` y `ver_titulo` van completos.

## RF-25 · Cambiar el tipo de una pregunta cerrada después de crear el proyecto (T-037)

Decisión del usuario (2026-11-01): solo se cambia **entre tipos cerrados** (`escala`, `nps`, `si_no`, `seleccion_unica`, `seleccion_multiple`, `segmento`, `numerica`). Pasar de abierta a cerrada, o al revés, no se permite.

### `PATCH /api/projects/{id}/preguntas/{pregunta_id}`
- **Roles:** analista, admin. El lector recibe 403.
- **Cuerpo:** `{ "tipo": "escala" }`
- **Respuesta 200:** la pregunta con la misma forma de `preguntas[]` en `GET /api/projects/{id}`.

```json
{ "id": "q_9", "titulo": "¿Qué tan satisfecho estás?", "columnas": ["¿Qué tan satisfecho estás?"],
  "tipo": "escala", "contexto_ia": false, "n_respuestas": 480, "n_na": 20 }
```

- **Efecto:**
  - Se guarda el `tipo` nuevo. Desde ese momento, `closed-results`, el Excel y `recommendations` lo usan; no hay caché.
  - Queda un evento en la auditoría: `cambio_tipo_pregunta`, actor `analista`, con `{ "pregunta": "<id>", "titulo": "...", "antes": "seleccion_unica", "despues": "escala", "usuario": "<email>" }`.
  - Si el tipo es el mismo que ya tenía: 200, sin escribir nada ni registrar en la auditoría.
- **Validación de números:** para pasar a `escala`, `nps` o `numerica`, al menos el **90 %** de las respuestas no vacías deben leerse como número. Se usa la misma lectura que `closed-results`. Para `nps`, además, esos números deben estar entre 0 y 10.
- **Errores** (mensajes para la UI):
  - 400 `"«{tipo}» no es un tipo de pregunta válido."`
  - 400 `"Solo se puede cambiar el tipo entre preguntas cerradas."` (la pregunta actual o el tipo nuevo no es cerrado)
  - 400 `"Las respuestas de esta pregunta no son números, así que no puede ser «{etiqueta}»."` (etiquetas: Escala, NPS, Numérica)
  - 400 `"Para ser NPS, las respuestas deben ser números del 0 al 10."`
  - 403 (lector); 404 `"Proyecto no encontrado"` (incluida otra organización); 404 `"Pregunta no encontrada"`.
