"""
Tests (pytest) de los endpoints nuevos alrededor del informe V2, con
mongomock y la IA simulada a nivel de módulo (misma técnica que test_e2e.py):

- POST /report?force_full=true llega a thematic con force_full=True.
- El consumo de Claude se acumula por proyecto ($inc) y se lee en
  GET /projects/{id}/usage y GET /admin/usage.
- GET /admin/health expone la versión de thematic.py cargada.

Correr: cd 07_MVP/backend && pytest tests/test_report_endpoints_pytest.py -q
"""
from __future__ import annotations

import io
import os
import sys
import time
from pathlib import Path

import mongomock
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("CLAUDE_MAX_OUTPUT_TOKENS", "16000")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")

from app import database  # noqa: E402

database._client = mongomock.MongoClient()

from fastapi.testclient import TestClient  # noqa: E402

from app.main import ADMIN_PASSWORD, app  # noqa: E402
from app.services import claude_log, thematic  # noqa: E402

ADMIN = {"X-Admin-Password": ADMIN_PASSWORD}


@pytest.fixture(scope="module")
def client_and_project():
    """Usuario + proyecto con categorías validadas y codificado (IA simulada)."""
    received: dict = {}

    def fake_codify_all(marco, categories, responses, batch_size=25, progress_cb=None):
        return [{"response_id": r["id"], "assignments": [
            {"category_id": categories[0]["id"], "rationale": "x", "confidence": 0.9}]} for r in responses]

    def fake_report_v2(survey_id, marco_teorico, categories, codings, responses, columns, text_column,
                       lexical_data=None, progress_cb=None, cached_analyses=None, save_analyses_cb=None,
                       force_full=False):
        received.update({"force_full": force_full, "cached": cached_analyses})
        # Simula una llamada a Claude registrada por el log → alimenta el sink de uso.
        claude_log.record_call(label="síntesis de clusters — tanda 1/2 (9 resp.)", model="claude-sonnet-4-6",
                               max_tokens=100, stop_reason="tool_use", input_tokens=1000, output_tokens=500,
                               duration_s=1.0, ok=True)
        if save_analyses_cb:
            save_analyses_cb("fp-test", [{"respondent_id": r["id"]} for r in responses])
        if progress_cb:
            progress_cb("Informe completado", len(responses) + 2, len(responses) + 2)
        return "# Informe simulado"

    # Parche con restauración al final del módulo: los tests de
    # test_report_v2_pytest.py usan el thematic real y corren en la misma sesión.
    mp = pytest.MonkeyPatch()
    mp.setattr(thematic, "codify_all", fake_codify_all)
    mp.setattr(thematic, "generate_qualitative_report_v2", fake_report_v2)

    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/auth/signup", json={"email": "usage@x.cl", "password": "clave12345"})
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    csv = "id_respuesta,respuesta\n" + "\n".join(f"E{i:03d},El curso fue bueno ({i})" for i in range(1, 11))
    r = c.post("/api/projects", headers=h,
               files={"file": ("demo.csv", io.BytesIO(csv.encode()), "text/csv")},
               data={"name": "Uso", "template": "evaluacion_docente_cna"})
    pid = r.json()["id"]
    for cat in c.get(f"/api/projects/{pid}", headers=h).json()["categories"]:
        c.patch(f"/api/projects/{pid}/categories/{cat['id']}", headers=h, json={"status": "validada"})
    c.post(f"/api/projects/{pid}/codify", headers=h)
    for _ in range(50):
        time.sleep(0.1)
        if c.get(f"/api/projects/{pid}/codify/progress", headers=h).json()["status"] in ("done", "error"):
            break
    yield c, h, pid, received
    mp.undo()


def _wait_report(c, h, pid):
    for _ in range(50):
        time.sleep(0.1)
        p = c.get(f"/api/projects/{pid}/report/progress", headers=h).json()
        if p["status"] in ("done", "error"):
            return p
    return p


def test_report_normal_usa_cache_y_force_full_lo_ignora(client_and_project):
    c, h, pid, received = client_and_project
    r = c.post(f"/api/projects/{pid}/report", headers=h)
    assert r.json()["status"] == "started" and r.json()["force_full"] is False
    assert _wait_report(c, h, pid)["status"] == "done"
    assert received["force_full"] is False

    # Segunda corrida: ya hay caché guardado en Mongo y se entrega al servicio
    r = c.post(f"/api/projects/{pid}/report", headers=h)
    assert _wait_report(c, h, pid)["status"] == "done"
    assert received["cached"] and received["cached"]["fingerprint"] == "fp-test"

    r = c.post(f"/api/projects/{pid}/report?force_full=true", headers=h)
    assert r.json()["force_full"] is True
    assert _wait_report(c, h, pid)["status"] == "done"
    assert received["force_full"] is True

    audit = c.get(f"/api/projects/{pid}/audit", headers=h).json()
    inicios = [e for e in audit if e["action"] == "informe_v2_inicio"]
    assert inicios[-1]["detail"]["regeneracion_completa"] is True
    assert inicios[-1]["detail"]["usa_cache_prompt1"] is False


def test_consumo_acumulado_por_proyecto_y_panel_admin(client_and_project):
    c, h, pid, _ = client_and_project
    u = c.get(f"/api/projects/{pid}/usage", headers=h).json()["usage"]
    assert u["calls"] == 3 and u["input_tokens"] == 3000 and u["output_tokens"] == 1500
    assert u["cost_usd"] == pytest.approx(3 * (1000 * 3e-6 + 500 * 15e-6))
    assert "sintesis_de_clusters" in u["by_step"]  # la etiqueta se normaliza a familia de paso

    assert c.get("/api/admin/usage").status_code == 401
    r = c.get("/api/admin/usage", headers=ADMIN)
    assert r.status_code == 200
    projects = {p["id"]: p for p in r.json()["projects"]}
    assert projects[pid]["claude_usage"]["calls"] == 3 and projects[pid]["n_responses"] == 10
    assert r.json()["total"]["calls"] >= 3


def test_health_expone_version_cargada(client_and_project):
    c, *_ = client_and_project
    r = c.get("/api/admin/health", headers=ADMIN)
    assert r.status_code == 200
    body = r.json()
    assert body["thematic_version"] == thematic.THEMATIC_VERSION
    assert body["synthesis_batch_input_tokens"] == thematic.SYNTHESIS_BATCH_INPUT_TOKENS
