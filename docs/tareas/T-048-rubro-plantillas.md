# T-048: El rubro ordena la lista de plantillas y desempata la sugerencia
Lado: backend
Requerimientos: RF-10, RF-41, RF-40
Rama: tarea/T-048-rubro-plantillas (ya creada desde `main`, con esta orden; trabaja en ella)
Depende de: T-046 (fusionada, PR #53)

## Objetivo
Con el rubro ya guardado en la organización (T-046), la lista de plantillas muestra primero las del rubro, y la sugerencia automática usa el rubro solo para desempatar. Sin rubro o con "Otro", nada cambia.

## Alcance
- SÍ: orden de `GET /api/framework-templates`; desempate en `plantilla_sugerida` para `suggest-template` y `recommendations`; frase extra en `motivo`; pruebas; `COMO_FUNCIONA.md`.
- NO: frontend (la pantalla ya agrupa respetando el orden del servidor); cambiar el mínimo de 2 coincidencias; que el rubro sugiera sin coincidencias; plantillas propias por organización (RF-12); tocar los textos ni las `palabras_clave` de `templates.py`.

## Contrato de API
`docs/API_CONTRATOS.md`, sección "RF-10 · El rubro ordena y desempata las plantillas (T-048)". La frase del `motivo` va al pie de la letra.

## Archivos probables
- Se tocan: `07_MVP/backend/app/services/recommendations.py` (`plantilla_sugerida(project, rubro=None)`), `app/routers/projects.py` (las tres rutas pasan el rubro), `app/store.py` (una lectura liviana del rubro, p. ej. `get_org_rubro(org_id)` con proyección, sin cargar el logo), `app/templates.py` (solo si `list_templates` recibe el rubro), pruebas en `tests/test_sugerir_plantilla_pytest.py`, `tests/test_recomendaciones_pytest.py` o `tests/test_plantillas_pytest.py`, y `07_MVP/COMO_FUNCIONA.md`.
- No se tocan: `07_MVP/frontend/**`, `auth.py`, `org.py`.

## Notas de implementación
- `plantilla_sugerida` sigue sin IA y sin escribir nada. El desempate se decide solo entre las plantillas que alcanzan el máximo de coincidencias: si la mejor tiene 3 y la del rubro 2, gana la de 3, sin frase extra.
- La frase extra se agrega **solo** cuando hubo empate y el rubro lo resolvió. Si la del rubro ganó sola por más coincidencias, el `motivo` queda como hoy.
- Orden estable en la lista: dentro de "las del rubro" y "las demás", el orden de `FRAMEWORK_TEMPLATES`.
- Para las pruebas del empate puedes usar `monkeypatch` sobre `FRAMEWORK_TEMPLATES` con dos plantillas de industrias distintas y las mismas palabras clave, o buscar títulos reales que empaten; lo importante es que la prueba sea determinista y legible.

## Criterios de aceptación
- [ ] `GET /api/framework-templates`: con rubro "Retail", las 4 plantillas de Retail salen primero y luego las demás en su orden; sin rubro y con "Otro", el orden es el de hoy. Prueba para los tres casos.
- [ ] Empate entre dos plantillas de industrias distintas: sin rubro gana la primera y el `motivo` no lleva la frase; con el rubro de la segunda gana la segunda y el `motivo` termina con la frase exacta del contrato. Probado en `suggest-template` y en `recommendations`.
- [ ] Sin empate, el rubro no cambia el resultado ni el `motivo`, aunque la del rubro tenga menos coincidencias.
- [ ] Con una sola coincidencia y rubro que calza, `plantilla` sigue siendo `null`.
- [ ] El rubro se lee de la organización de quien llama: un usuario de la organización B, sin rubro, no recibe el orden ni el desempate de A. Prueba de aislamiento.
- [ ] `python -m pytest tests -q` en verde, sin IA real. Las pruebas existentes de T-044 y de recomendaciones siguen pasando sin cambiar sus expectativas.
- [ ] `COMO_FUNCIONA.md` menciona el orden por rubro y el desempate.
