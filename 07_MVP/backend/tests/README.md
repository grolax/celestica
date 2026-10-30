# Tests de verificación (v1.1)

Corren contra **mongomock** (no necesitan MongoDB corriendo) y con la **IA simulada**
(no gastan API de Claude). Requieren: `pip install mongomock pytest`.

```bash
cd 07_MVP/backend
python tests/test_e2e.py      # flujo completo: signup → proyecto → análisis → export
python tests/test_fase1.py    # store MongoDB + aislamiento multi-tenant
python tests/test_fase3.py    # informe asíncrono con progreso
python tests/test_fase5.py    # integraciones Qualtrics / Google Forms (requests simulado)
```

Cada script imprime PASS/FAIL por check y termina con código 0 si todo pasó.

## Tests con pytest (v1.2)

```bash
cd 07_MVP/backend
pytest tests -q
```

- `test_report_v2_pytest.py` — informe V2 con corpus grande e IA simulada: tandas que se truncan y se dividen, prevalencia calculada en Python, caché del Prompt 1 y `force_full`, registro de costo.
- `test_report_endpoints_pytest.py` — endpoints `POST /report?force_full`, `GET /projects/{id}/usage`, `GET /admin/usage`, `GET /admin/health` (mongomock).

- `test_scripts_pytest.py` — corre `test_e2e.py` y `test_fase1/3/5.py` cada uno en un subproceso y exige código de salida 0 (sus parches globales no contaminan a los demás tests; tarda ~35 s por los scripts).
- `test_aislamiento_pytest.py` — acceso cruzado (RNF-01): el usuario B recibe 404 en las 25 rutas con `{project_id}` del proyecto de A, sin cambios en el proyecto ni llamadas a la IA simulada. Además, `GET /api/projects` y las credenciales de Qualtrics de B no muestran lo de A. Un test recorre `app.routes` y falla si agregas una ruta con `{project_id}` sin añadirla a la lista `ROUTES` de ese archivo.

`pytest tests -q` corre todo, incluidos los scripts. `conftest.py` los excluye de la recolección directa (no se importan en el proceso de pytest) y también siguen funcionando a mano con `python tests/<script>.py`.
