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
  - Sin columnas `abierta`: `"Esta encuesta no tiene preguntas abiertas. El análisis de preguntas cerradas llegará pronto."`
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
  - 400 — "Esta encuesta no tiene preguntas abiertas. El análisis de preguntas cerradas llegará pronto." (ninguna pregunta `abierta`).
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
  - **`escala` y `nps`:** `opciones` con **todos** los valores enteros de `min` a `max`, en ese orden (con `n: 0` si nadie lo eligió). Valores no numéricos o fuera de rango no entran en los cálculos y se cuentan en `n_invalidas` (campo presente solo si es > 0). Desviación **muestral** (n − 1; 0 si hay una sola respuesta). `top2`/`bottom2` solo en `escala`: los dos valores más altos y los dos más bajos del rango.
  - **`nps`:** promotores 9–10, pasivos 7–8, detractores 0–6; `valor` = % promotores − % detractores.
  - **`seleccion_multiple`:** cada respuesta se separa en opciones con el mismo criterio de la detección de T-010 (separador `;` o `,` y reconstrucción de opciones con el separador adentro); `n` = personas que eligieron la opción; incluye `nota`.
  - **`si_no`, `seleccion_unica`, `segmento`:** todas las opciones (sin límite de 20), de más a menos `n`; empate por orden alfabético. **Orden natural (tramos):** si todas las opciones salvo como máximo 2 contienen un número, se ordenan por el primer número que aparece en el texto (sin puntos de miles: "Menos de $360.000" → 360000, "20-24" → 20) y las que no tienen número van al final por `n`.
  - **`numerica`:** sin `opciones`; `numerica` con promedio, desviación muestral, mediana, mínimo y máximo de los valores numéricos (los no numéricos van a `n_invalidas`).
- **Proyectos sin preguntas cerradas** (por ejemplo, los antiguos migrados): `200` con `"preguntas": []`.
- **Errores:** 404 "Proyecto no encontrado" (incluye proyectos de otra organización); 401 sin sesión.
