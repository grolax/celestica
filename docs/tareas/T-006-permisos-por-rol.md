# T-006: Permisos por rol verificados en el backend
Lado: backend
Requerimientos: RF-03, RNF-02, RNF-01
Rama: tarea/T-006-permisos-por-rol
Depende de: T-004 (fusionada)

## Objetivo
Cada operación verifica en el servidor que el rol del usuario la permite, según la matriz de `docs/API_CONTRATOS.md` (**RF-03 · Permisos por rol (T-006)**). La UI solo reflejará estos permisos; el backend es la barrera.

## Decisiones del usuario (2026-10-30)
- Lector: ver resultados, descargar informes y comentar. Analista: todo el análisis, incluido borrar proyectos. Admin: lo del analista más la gestión de la organización y sus miembros.
- El lector solo borra sus propios comentarios; analista y admin borran cualquiera.

## Alcance
- SÍ: una dependencia común en `app/deps.py`, análoga a `get_current_user` (RNF-02): por ejemplo `require_role("analista")`, que devuelve el `User` si su rol alcanza el nivel (`lector < analista < admin`) y si no lanza **403** `"Tu rol (<Etiqueta>) no permite esta acción."` con la etiqueta en español (Administrador, Analista, Lector). Una sola tabla de niveles y etiquetas.
- SÍ: aplicar la dependencia a cada operación ❌ para lector de la matriz, en lugar de `get_current_user`. Debe correr **antes** de `_get_or_404` (orden 401 → 403 → 404).
- SÍ: comentarios: `add_comment` guarda `author_id = user.id`; `delete_comment` permite al lector borrar solo si `author_id == user.id` y si no responde 403 `"Solo puedes borrar tus propios comentarios."` (comentarios antiguos sin `author_id`: el lector no puede borrarlos).
- SÍ: prueba nueva `tests/test_permisos_pytest.py` (mongomock, IA simulada):
  - Una tabla `PERMISOS` con **cada** operación de `app.routes` bajo `/api/` (salvo `/api/admin/*`) y el rol mínimo que exige.
  - Test que falla si aparece una ruta `/api/` sin entrada en `PERMISOS` (como el de cobertura de T-002).
  - Test parametrizado: para cada operación que exige analista, un **lector** de la misma organización (insertado directo en `users` con el `org_id` del admin y `rol: "lector"`) recibe 403 con el mensaje exacto; el proyecto queda intacto y la IA simulada no se invoca.
  - Para cada operación permitida al lector, el lector **no** recibe 403 (usa cuerpos válidos).
  - Un **analista** de la misma organización puede crear, analizar y borrar proyectos.
  - Comentarios: el lector borra el suyo (200), no el de otro (403); el analista borra el de otro (200).
  - Un lector de **otra** organización recibe 403 en una operación de analista y 404 en una de lectura (no se revela el proyecto).
- NO: endpoints de miembros, cambio de contraseña, desactivación (T-007); cambios en `/api/admin/*`; frontend.

## Contrato de API
`docs/API_CONTRATOS.md`, sección **RF-03 · Permisos por rol (T-006)**.

## Archivos probables
- Tocar: `app/deps.py`, `app/routers/{projects,analysis,reports,integrations}.py` (solo la dependencia de cada endpoint y `author_id` en comentarios), `07_MVP/COMO_FUNCIONA.md` (sección de seguridad).
- Crear: `tests/test_permisos_pytest.py`.
- No tocar: `07_MVP/frontend/**`, `docs/**`, `store.py` (salvo que haga falta para comentarios; explícalo), las pruebas existentes.

## Criterios de aceptación
- [ ] `pytest tests -q` en verde; las 59 existentes **sin modificar** (todos sus usuarios son admin).
- [ ] La matriz implementada coincide exactamente con el contrato; el test de cobertura de `PERMISOS` falla ante una ruta nueva sin declarar.
- [ ] Orden 401 → 403 → 404 comprobado en las pruebas.
- [ ] El OpenAPI solo cambia en lo esperado (sin rutas nuevas ni cambios de nombres de operación).
- [ ] `COMO_FUNCIONA.md` describe la dependencia de roles y la matriz.
- [ ] Commits con el formato `T-006 RF-03: ...`.

## Notas
- Usuarios de prueba con otros roles: insertarlos con `users.insert_one` reutilizando `hash_password` (los endpoints de miembros llegan en T-007).
- No inventar roles nuevos; un `rol` desconocido en la base debe tratarse como el nivel más bajo (lector), nunca como admin.

## Revisión 1
2026-10-30 — **Con cambios** (supervisor).

Lo de T-006 está bien: `require_role` en `deps.py` con tabla única de niveles y etiquetas, rol desconocido = lector; la dependencia corre antes de `_get_or_404` y de la validación del cuerpo; la matriz coincide con el contrato; `author_id` y la regla del lector en `delete_comment` son correctas; 99 pruebas pasan sin modificar las 59 existentes; `test_toda_ruta_api_tiene_permiso_declarado` usa OpenAPI y exige `len(declared) > 30`.

Cambio pedido (hallazgo del programador, confirmado por el supervisor):

1. **`tests/test_aislamiento_pytest.py::test_toda_ruta_con_project_id_esta_cubierta` pasa en vacío.** Desde T-003a, `app.routes` contiene objetos `_IncludedRouter` sin `.path` (FastAPI 0.143); el conjunto `declared` queda vacío (el supervisor obtuvo 0 rutas con `{project_id}`) y el test no puede fallar. **Se autoriza modificar solo esa función:** obtener las operaciones desde `app.openapi()["paths"]` (como en `test_permisos_pytest.py`), mantener la comparación con `ROUTES` y agregar `assert len(declared) >= 25` para que no vuelva a pasar en vacío. Comprueba que falla si quitas temporalmente una entrada de `ROUTES` (sin commitearlo) y cuéntalo en el resumen. No cambies nada más de esa prueba.

## Revisión 2
2026-10-30 — **Aprobada** (supervisor).
- `pytest tests -q`: 99 pasan.
- `test_toda_ruta_con_project_id_esta_cubierta` lee `app.openapi()["paths"]`, detecta las 25 operaciones con `{project_id}` y exige `>= 25`; el commit solo toca esa función (+3/-2).
- Prueba de control del programador: quitar `GET .../usage` de `ROUTES` hace fallar el test con esa ruta en el mensaje.
- Nota: el umbral 25 es igual al número actual; si se elimina una ruta con `{project_id}` hay que bajarlo a mano (deliberado).
