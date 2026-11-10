# T-046: Perfil de organización (servidor)
Lado: backend
Requerimientos: RF-10, RF-02, RNF-01
Rama: tarea/T-046-perfil-organizacion (ya creada desde `main`, con esta orden; trabaja en ella)
Depende de: —

## Objetivo
El administrador puede editar el nombre, el rubro y el color de su organización, y subir, ver o quitar su logo. Todos los miembros reciben esos datos en `organizacion` y pueden pedir el logo. Ninguna organización ve ni toca los datos de otra.

## Alcance
- SÍ: el objeto `organizacion` ampliado, `PUT /api/org/profile`, `PUT`/`GET`/`DELETE /api/org/logo`, auditoría, pruebas y documentación.
- NO: el efecto del rubro en las plantillas (irá en T-048), la marca en PDF y Word (RF-11), elegir el rubro al registrarse, redimensionar o recortar imágenes, SVG, pantallas.

## Contrato de API
`docs/API_CONTRATOS.md`, sección "RF-10 · Perfil de organización (T-046)". Respeta los mensajes de error al pie de la letra.

## Archivos probables
- Se tocan: `07_MVP/backend/app/routers/org.py`, `app/auth.py` (`_user_out`), `app/store.py` (funciones de perfil y logo), `app/models.py` (docstring del esquema), pruebas nuevas en `tests/test_perfil_org_pytest.py`, `tests/test_permisos_pytest.py` (tabla `OPS`), `07_MVP/COMO_FUNCIONA.md`.
- No se tocan: `07_MVP/frontend/**`, `templates.py`, `recommendations.py`, exportaciones.

## Notas de implementación
- **Logo en su propia colección** `org_logos`: `{_id: org_id, tipo, datos (bytes), updated_at}`. Así `organizations` queda liviano y `_user_out` no carga la imagen. `tiene_logo` sale de si existe ese documento.
- Las funciones nuevas del `store` reciben `org_id` y filtran por él. Las rutas toman siempre `user.org_id`.
- Mensajes 422 como **texto** en `detail` (`HTTPException(422, "...")`), no el formato de lista de Pydantic: la pantalla los muestra tal cual. Si validas con Pydantic, convierte el error al mensaje del contrato.
- Para el logo, lee como mucho 512.001 bytes antes de decidir que se pasa del límite, para no cargar archivos enormes en memoria.
- Auditoría con `store.log_org_event`, como en miembros.
- **Sin migración:** las organizaciones existentes se leen con valores por defecto (`rubro: null`, `color: null`). No hay que rellenar nada. Si cambias de idea y escribes en documentos existentes, el script de migración idempotente pasa a ser obligatorio.
- Los rubros quedan en una constante del backend con el texto exacto del contrato.

## Criterios de aceptación
- [ ] `/auth/me`, `/auth/login` y `/auth/signup` devuelven `organizacion` con `rubro`, `color` y `tiene_logo`. Una organización vieja sale con `null`, `null` y `false`.
- [ ] `PUT /api/org/profile`: el admin edita y recibe el objeto actualizado. El color queda en minúsculas y el nombre sin espacios en los extremos. Cada error 422 del contrato tiene su prueba con el mensaje exacto.
- [ ] Analista y lector reciben 403 en `PUT /api/org/profile`, `PUT /api/org/logo` y `DELETE /api/org/logo`. El lector sí puede hacer `GET /api/org/logo`.
- [ ] Logo: un PNG y un JPG válidos se aceptan. Un archivo vacío, un SVG, un GIF y un texto con nombre `.png` se rechazan. Un archivo de 512.001 bytes se rechaza y uno de 512.000 se acepta.
- [ ] `GET /api/org/logo` devuelve el data URL con el tipo correcto; tras `DELETE`, 404 con el mensaje del contrato. `DELETE` sin logo responde 200 y no registra evento.
- [ ] Auditoría: `organizacion_editada` solo con los campos cambiados, y nada sin cambios; `logo_actualizado` y `logo_eliminado`.
- [ ] **Aislamiento:** el admin de A edita su perfil y sube su logo; B no ve el nombre, rubro, color ni logo de A (ni `GET /api/org/logo` ni `/auth/me`). Los cambios de B no tocan A.
- [ ] Las 4 rutas declaradas en `OPS` de `test_permisos_pytest.py`.
- [ ] `python -m pytest tests -q` en verde, sin llamadas a la IA real.
- [ ] `COMO_FUNCIONA.md` y el docstring de `models.py` describen los campos nuevos y `org_logos`.
