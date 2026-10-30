"""RF-23 (T-019): una sola codificación a la vez por (proyecto, pregunta). Mongomock e IA simulada."""
from __future__ import annotations

import threading
import uuid
import time

import pytest

from app.deps import _codify_progress
from app.services import thematic
from test_preguntas_pytest import N, _crear, _wait  # noqa: F401  (también deja mongomock listo)
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def ctx(monkeypatch):
    _codify_progress.clear()
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/auth/signup", json={"email": f"lock-{uuid.uuid4().hex[:8]}@x.cl", "password": "clave12345"})
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    env = {"c": c, "h": h}
    base = f"/api/projects/{_crear(env).json()['id']}"
    for q in ("q_1", "q_2"):
        cat = c.post(f"{base}/categories?pregunta={q}", headers=h, json={"nombre": "Tema"}).json()
        c.patch(f"{base}/categories/{cat['id']}?pregunta={q}", headers=h, json={"status": "validada"})

    state = {"calls": 0, "gate": threading.Event(), "fail": False}

    def fake(marco, cats, responses, batch_size=25, progress_cb=None):
        state["calls"] += 1
        state["gate"].wait(5)
        if state["fail"]:
            raise RuntimeError("falla simulada")
        return [{"response_id": r["id"], "assignments": []} for r in responses]

    monkeypatch.setattr(thematic, "codify_all", fake)
    yield c, h, base, state
    state["gate"].set()
    time.sleep(0.2)
    _codify_progress.clear()


def test_segunda_codificacion_de_la_misma_pregunta_no_llama_a_la_ia(ctx):
    c, h, base, st = ctx
    assert c.post(f"{base}/codify?pregunta=q_1", headers=h).json() == {"status": "started", "total": N - 1}
    assert c.post(f"{base}/codify?pregunta=q_1", headers=h).json() == {"status": "already_running", "total": N - 1}
    # otra pregunta del mismo proyecto sí arranca en paralelo
    assert c.post(f"{base}/codify?pregunta=q_2", headers=h).json() == {"status": "started", "total": N - 6}
    time.sleep(0.2)
    assert st["calls"] == 2  # q_1 una sola vez + q_2
    st["gate"].set()
    assert _wait(c, h, f"{base}/codify/progress?pregunta=q_1")["status"] == "done"
    assert _wait(c, h, f"{base}/codify/progress?pregunta=q_2")["status"] == "done"
    assert c.post(f"{base}/codify?pregunta=q_1", headers=h).json()["status"] == "started"


def test_tras_un_error_se_puede_volver_a_lanzar(ctx):
    c, h, base, st = ctx
    st["fail"] = True
    st["gate"].set()
    assert c.post(f"{base}/codify?pregunta=q_1", headers=h).json()["status"] == "started"
    assert _wait(c, h, f"{base}/codify/progress?pregunta=q_1")["status"] == "error"
    assert c.post(f"{base}/codify?pregunta=q_1", headers=h).json()["status"] == "started"
