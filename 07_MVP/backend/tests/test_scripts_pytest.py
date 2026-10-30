"""Corre los 4 scripts de verificación (test_e2e / test_fase1/3/5) dentro de pytest.

Cada uno va en un subproceso: sus parches globales de módulo
(thematic.codify_all = ..., requests.get = ..., database._client = ...) no
contaminan a los demás tests, y conftest.py sigue sin importarlos.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("script", ["test_e2e.py", "test_fase1.py", "test_fase3.py", "test_fase5.py"])
def test_script(script):
    # Clave falsa: si un script llegara a la IA real fallaría en vez de gastar API.
    env = {**os.environ, "ANTHROPIC_API_KEY": "sk-test"}
    r = subprocess.run([sys.executable, f"tests/{script}"], cwd=BACKEND, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    assert r.returncode == 0, f"{script} terminó con código {r.returncode}\n{r.stdout}\n{r.stderr}"
