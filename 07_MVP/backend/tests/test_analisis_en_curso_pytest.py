"""RF-23 / RNF-08 (T-029): léxico y propuesta de categorías, una sola vez a la vez por (proyecto, pregunta).

mongomock e IA simulada bloqueada con un Event: ninguna llamada a Anthropic.
"""
from __future__ import annotations

import threading
import time
import uuid

import pytest

from app.deps import _analisis_en_curso
from app.services import lexical, thematic
from test_preguntas_pytest import _crear  # noqa: F401  (también deja mongomock listo)
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

MSG = {
    "lexical": "El análisis léxico ya está en curso para esta pregunta. Espera a que termine.",
    "propose": "Claude ya está proponiendo categorías para esta pregunta. Espera a que termine.",
}


@pytest.fixture
def ctx(monkeypatch):
    _analisis_en_curso.clear()
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/auth/signup", json={"email": f"en-curso-{uuid.uuid4().hex[:8]}@x.cl", "password": "clave12345"})
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    base = f"/api/projects/{_crear({'c': c, 'h': h}).json()['id']}"
    st = {"lex": 0, "prop": 0, "gate": threading.Event(), "fail": False}

    def interpret(marco, lex):
        st["lex"] += 1
        st["gate"].wait(5)
        return "interpretación simulada"

    def propose(marco, sample):
        st["prop"] += 1
        st["gate"].wait(5)
        if st["fail"]:
            raise RuntimeError("falla simulada")
        return [{"nombre": "Tema"}]

    monkeypatch.setattr(thematic, "interpret_lexical", interpret)
    monkeypatch.setattr(thematic, "propose_categories", propose)
    yield c, h, base, st
    st["gate"].set()
    time.sleep(0.2)
    _analisis_en_curso.clear()


def _en_hilo(c, h, url):
    out = {}
    t = threading.Thread(target=lambda: out.setdefault("r", c.post(url, headers=h)))
    t.start()
    return t, out


def _estado(c, h, base, q="q_1"):
    return c.get(f"{base}/analysis-status?pregunta={q}", headers=h).json()


def _esperar(cond):
    for _ in range(100):
        if cond():
            return
        time.sleep(0.05)
    raise AssertionError("no se cumplió a tiempo")


@pytest.mark.parametrize("op,ruta,campo", [("lexical", "lexical", "lex"), ("propose", "categories/propose", "prop")])
def test_segunda_llamada_da_409_sin_ia_ni_auditoria_y_otras_corren_en_paralelo(ctx, op, ruta, campo):
    c, h, base, st = ctx
    assert _estado(c, h, base) == {"lexical": "idle", "propose": "idle"}
    t, out = _en_hilo(c, h, f"{base}/{ruta}?pregunta=q_1")
    _esperar(lambda: st[campo] == 1)
    assert _estado(c, h, base)[op] == "running"
    assert _estado(c, h, base, "q_2")[op] == "idle"  # otra pregunta: libre

    audit_antes = len(c.get(f"{base}/audit", headers=h).json())
    r = c.post(f"{base}/{ruta}?pregunta=q_1", headers=h)
    assert (r.status_code, r.json()["detail"]) == (409, MSG[op])
    assert st[campo] == 1 and len(c.get(f"{base}/audit", headers=h).json()) == audit_antes

    # la otra operación y la misma operación en otra pregunta sí arrancan
    otra = "categories/propose" if op == "lexical" else "lexical"
    t2, out2 = _en_hilo(c, h, f"{base}/{otra}?pregunta=q_1")
    t3, out3 = _en_hilo(c, h, f"{base}/{ruta}?pregunta=q_2")
    _esperar(lambda: st["lex"] + st["prop"] == 3)

    st["gate"].set()
    for t_ in (t, t2, t3):
        t_.join(5)
    assert out["r"].status_code == out2["r"].status_code == out3["r"].status_code == 200
    assert _estado(c, h, base) == {"lexical": "idle", "propose": "idle"}


def test_dos_simultaneas_una_200_y_una_409(ctx):
    c, h, base, st = ctx
    res = []
    ts = [threading.Thread(target=lambda: res.append(c.post(f"{base}/categories/propose?pregunta=q_1", headers=h)))
          for _ in range(2)]
    for t in ts:
        t.start()
    _esperar(lambda: st["prop"] >= 1 and len(res) == 1)  # la perdedora responde 409 de inmediato
    st["gate"].set()
    for t in ts:
        t.join(5)
    assert sorted(r.status_code for r in res) == [200, 409]
    assert st["prop"] == 1


def test_la_marca_se_libera_si_falla(ctx):
    c, h, base, st = ctx
    st["fail"] = True
    st["gate"].set()
    assert c.post(f"{base}/categories/propose?pregunta=q_1", headers=h).status_code == 503
    assert _estado(c, h, base)["propose"] == "idle"
    st["fail"] = False
    assert c.post(f"{base}/categories/propose?pregunta=q_1", headers=h).status_code == 200


def test_la_marca_se_libera_si_el_lexico_revienta(ctx, monkeypatch):
    c, h, base, st = ctx
    st["gate"].set()
    real = lexical.analyze
    monkeypatch.setattr(lexical, "analyze", lambda r: (_ for _ in ()).throw(RuntimeError("boom")))
    assert c.post(f"{base}/lexical?pregunta=q_1", headers=h).status_code == 500
    assert _estado(c, h, base)["lexical"] == "idle"
    monkeypatch.setattr(lexical, "analyze", real)
    assert c.post(f"{base}/lexical?pregunta=q_1", headers=h).status_code == 200
