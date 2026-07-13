# Tests de verificación (v1.1)

Corren contra **mongomock** (no necesitan MongoDB corriendo) y con la **IA simulada**
(no gastan API de Claude). Requieren: `pip install mongomock`.

```bash
cd 07_MVP/backend
python tests/test_e2e.py      # flujo completo: signup → proyecto → análisis → export
python tests/test_fase1.py    # store MongoDB + aislamiento multi-tenant
python tests/test_fase3.py    # informe asíncrono con progreso
python tests/test_fase5.py    # integraciones Qualtrics / Google Forms (requests simulado)
```

Cada script imprime PASS/FAIL por check y termina con código 0 si todo pasó.
