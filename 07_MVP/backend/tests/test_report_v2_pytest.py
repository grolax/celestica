"""
Tests (pytest) del informe V2 con corpus grande y API de Claude simulada.

Cubren la regresión de septiembre 2026: con 122 respondentes la síntesis de
clusters se truncaba por max_tokens y cada reintento volvía a pagar el
Prompt 1. Aquí la API se simula con un cliente falso que:
- entrega salidas estructuradas (tool use) con la forma que espera el código,
- TRUNCA (stop_reason=max_tokens, input vacío) cualquier tanda de síntesis con
  más de `FakeClient.truncate_above` respondentes, para verificar que el
  código divide la tanda en vez de fallar,
- contabiliza cada llamada por herramienta.

Correr: cd 07_MVP/backend && pytest tests/test_report_v2_pytest.py -q
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# El límite del modelo se fija por env para no sondear la API en tests.
os.environ.setdefault("CLAUDE_MAX_OUTPUT_TOKENS", "16000")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")

from app.services import claude_log, thematic  # noqa: E402


# ---------- Cliente falso ----------

class FakeStream:
    def __init__(self, msg):
        self._msg = msg
        self.text_stream = iter([b.text for b in msg.content if b.type == "text"])

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get_final_message(self):
        return self._msg


def _msg(*, tool_name=None, payload=None, text="", stop_reason="end_turn", in_tok=100, out_tok=50):
    if tool_name is not None:
        content = [SimpleNamespace(type="tool_use", name=tool_name, input=payload if payload is not None else {})]
    else:
        content = [SimpleNamespace(type="text", text=text)]
    return SimpleNamespace(
        content=content, stop_reason=stop_reason,
        usage=SimpleNamespace(input_tokens=in_tok, output_tokens=out_tok),
    )


class FakeClient:
    """Simula `anthropic.Anthropic().messages.stream(...)`."""

    def __init__(self, truncate_above: int = 6, truncate_single_synthesis: bool = True):
        self.truncate_above = truncate_above
        self.truncate_single_synthesis = truncate_single_synthesis
        self.calls: list[dict] = []
        self.messages = self

    # --- helpers ---
    @staticmethod
    def _ids_in(user: str) -> list[str]:
        return re.findall(r'"respondent_id":\s*"(R\d+)"', user)

    def stream(self, **kw):
        user = kw["messages"][0]["content"]
        tool = (kw.get("tools") or [{}])[0].get("name")
        self.calls.append({"tool": tool, "max_tokens": kw["max_tokens"], "user_len": len(user)})
        in_tok = len(user) // 3

        if tool is None:
            # Prompt 3 / v1 / léxico: markdown. Trunca si el techo es ridículo.
            if kw["max_tokens"] < 50:
                return FakeStream(_msg(text="# Informe (cortado", stop_reason="max_tokens", in_tok=in_tok, out_tok=kw["max_tokens"]))
            return FakeStream(_msg(text="# Informe\n\nResumen ejecutivo con **10** clusters.", in_tok=in_tok, out_tok=400))

        if tool == "registrar_analisis_respondente":
            rid = re.search(r"ID DEL RESPONDENTE: (\S+)", user).group(1)
            k = int(rid[1:]) % 5
            payload = {
                "respondent_id": rid, "is_valid": k != 4, "rejection_reason": "vacía" if k == 4 else None,
                "subtopics": [] if k == 4 else [{
                    "subtopic_name": f"tema_{k}",
                    "evidence_quote": f'Dijo "no sé" y "tal vez" — respondente {rid}',
                    "analysis_cluster": f"tema_{k}:contexto",
                }],
                "respondent_profile_line": f"perfil {rid}",
                "metadata_snapshot": {"carrera": f"C{k}"},
            }
            return FakeStream(_msg(tool_name=tool, payload=payload, in_tok=in_tok, out_tok=300))

        if tool == "registrar_clusters_tanda":
            ids = self._ids_in(user)
            if len(ids) > self.truncate_above:
                return FakeStream(_msg(tool_name=tool, payload={}, stop_reason="max_tokens", in_tok=in_tok, out_tok=kw["max_tokens"]))
            by_cluster: dict[str, list[str]] = {}
            for rid in ids:
                k = int(rid[1:]) % 5
                if k != 4:
                    by_cluster.setdefault(f"tema_{k}", []).append(rid)
            clusters = [{
                "cluster_name": name, "member_count": len(members), "member_ids": members,
                "breakdown_by_metadata": {"by_carrera": {f"C{name[-1]}": len(members)}},
                "quote_candidates": [{"quote": f'cita "{m}"', "respondent_profile": m, "rationale": "central"} for m in members[:3]],
                "internal_variations": [{"variation": f"var {name}", "prevalence_note": "n"}],
            } for name, members in by_cluster.items()]
            return FakeStream(_msg(tool_name=tool, payload={"clusters": clusters}, in_tok=in_tok, out_tok=len(ids) * 120))

        if tool == "registrar_sintesis_clusters":
            ids = self._ids_in(user)
            if self.truncate_single_synthesis and len(ids) > self.truncate_above:
                return FakeStream(_msg(tool_name=tool, payload={}, stop_reason="max_tokens", in_tok=in_tok, out_tok=kw["max_tokens"]))
            clusters = [{
                "cluster_name": "tema_unico", "prevalence": {"count": 99, "percentage": 99.0},
                "member_ids": [i for i in ids if int(i[1:]) % 5 != 4],
                "representative_quotes": [{"quote": "q", "respondent_profile": "p", "rationale": "r"}],
            }]
            return FakeStream(_msg(tool_name=tool, payload={"respondents_analyzed": {"total": 1, "valid": 1, "rejected": 0}, "clusters": clusters}, in_tok=in_tok, out_tok=500))

        if tool == "registrar_agrupacion_de_candidatos":
            names = json.loads(user.split("):\n", 1)[1].split("\n\nTAREA")[0])
            groups: dict[str, list[int]] = {}
            for n in names:
                groups.setdefault(n["cluster_name"].lower(), []).append(n["idx"])
            payload = {"groups": [{"canonical_name": k, "candidate_indices": v} for k, v in groups.items()]}
            return FakeStream(_msg(tool_name=tool, payload=payload, in_tok=in_tok, out_tok=len(names) * 12))

        if tool == "registrar_citas_representativas":
            clusters_in = json.loads(user.split("):\n", 1)[1].split("\n\nTAREA")[0])
            payload = {"clusters": [{
                "cluster_name": c["cluster_name"],
                "representative_quotes": c["quote_pool"][:2],
                "internal_variations": c["variation_pool"][:1],
            } for c in clusters_in]}
            return FakeStream(_msg(tool_name=tool, payload=payload, in_tok=in_tok, out_tok=len(clusters_in) * 80))

        if tool in ("registrar_categorias_propuestas", "registrar_codificaciones"):
            payload = {"categorias": [{"nombre": "A", "definicion": "d", "criterios_inclusion": "i", "criterios_exclusion": "e"}]} \
                if tool == "registrar_categorias_propuestas" else \
                {"codificaciones": [{"response_id": rid, "assignments": [{"category_id": "cat_1", "rationale": 'dijo "x"', "confidence": 0.9}]}
                                    for rid in re.findall(r"\[(R\d+)\]", user)]}
            return FakeStream(_msg(tool_name=tool, payload=payload, in_tok=in_tok, out_tok=200))

        raise AssertionError(f"herramienta no simulada: {tool}")

    def count(self, tool: str) -> int:
        return sum(1 for c in self.calls if c["tool"] == tool)


def _responses(n: int) -> list[dict]:
    return [{"id": f"R{i:04d}", "text": f'Respuesta {i} con "comillas" y más texto ' * 8,
             "meta": {"carrera": f"C{i % 5}"}} for i in range(n)]


@pytest.fixture
def fake(monkeypatch, tmp_path):
    client = FakeClient()
    monkeypatch.setattr(thematic, "_client", client)
    monkeypatch.setattr(thematic, "V2_MAX_WORKERS", 3)
    # Presupuesto chico para forzar varias tandas con un corpus de prueba.
    monkeypatch.setattr(thematic, "SYNTHESIS_BATCH_INPUT_TOKENS", 1500)
    monkeypatch.setattr(thematic, "MERGE_INPUT_TOKENS", 4000)
    monkeypatch.setattr(claude_log, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(claude_log, "_logger", None)
    return client


def _run(fake_client, n=150, cached=None, force_full=False, save_cb=None, progress=None):
    return thematic.generate_qualitative_report_v2(
        survey_id="proj_test", marco_teorico="marco", categories=[], codings={},
        responses=_responses(n), columns=["respuesta"], text_column="respuesta",
        progress_cb=progress, cached_analyses=cached, save_analyses_cb=save_cb, force_full=force_full,
    )


# ---------- Tests ----------

def test_corpus_grande_termina_y_divide_tandas_truncadas(fake):
    """150 respondentes, tandas que el modelo 'no alcanza' a sintetizar
    (>6 respondentes truncan): el informe termina igual porque las tandas
    se dividen; ningún paso depende de max_tokens."""
    stages = []
    report = _run(fake, n=150, progress=lambda s, d, t: stages.append(s))
    assert report.startswith("# Informe")
    assert fake.count("registrar_analisis_respondente") == 150
    tandas = [c for c in fake.calls if c["tool"] == "registrar_clusters_tanda"]
    assert len(tandas) > 10, "debería haber varias tandas (presupuesto chico + splits)"
    # Hubo splits: se registraron más llamadas de tanda que tandas iniciales,
    # y quedaron truncamientos en el log persistente.
    log_lines = [json.loads(l) for l in (claude_log.LOG_DIR / "claude_calls.jsonl").read_text().splitlines()]
    assert any(r["stop_reason"] == "max_tokens" for r in log_lines)
    assert all(r["cost_usd"] >= 0 for r in log_lines)
    assert any("Sintetizando clusters" in s for s in stages)
    assert any("Fusionando clusters" in s for s in stages)
    assert stages[-1] == "Informe completado"


def test_prevalencia_la_calcula_python_con_member_ids(fake):
    """Los conteos finales salen de los member_ids únicos (no de sumas del
    modelo) y los porcentajes son sobre el total real del corpus."""
    captured = {}
    orig = thematic._write_report_v2

    def spy(clusters_analysis, marco_teorico):
        captured.update(clusters_analysis)
        return orig(clusters_analysis, marco_teorico)

    fake_write = spy
    thematic._write_report_v2 = fake_write
    try:
        _run(fake, n=60)
    finally:
        thematic._write_report_v2 = orig
    ra = captured["respondents_analyzed"]
    assert ra["total"] == 60 and ra["valid"] == 48 and ra["rejected"] == 12
    names = sorted(c["cluster_name"] for c in captured["clusters"])
    assert names == ["tema_0", "tema_1", "tema_2", "tema_3"]
    for c in captured["clusters"]:
        assert c["prevalence"]["count"] == 12
        assert c["prevalence"]["percentage"] == 20.0
        assert len(c["member_ids"]) == 12
        assert 1 <= len(c["representative_quotes"]) <= 3
    # ordenados por prevalencia descendente (todos iguales → estable)
    assert all(isinstance(c["breakdown_by_metadata"], dict) for c in captured["clusters"])


def test_cache_prompt1_se_reutiliza_y_force_full_lo_ignora(fake):
    saved = {}
    _run(fake, n=30, save_cb=lambda fp, an: saved.update({"fingerprint": fp, "analyses": an}))
    assert fake.count("registrar_analisis_respondente") == 30
    assert len(saved["analyses"]) == 30

    fake.calls.clear()
    _run(fake, n=30, cached=saved)
    assert fake.count("registrar_analisis_respondente") == 0, "con caché vigente no se paga el Prompt 1"

    fake.calls.clear()
    _run(fake, n=30, cached=saved, force_full=True)
    assert fake.count("registrar_analisis_respondente") == 30, "force_full ignora el caché"

    # Si cambian los datos (otro fingerprint) el caché no aplica
    fake.calls.clear()
    stale = {"fingerprint": "otro", "analyses": saved["analyses"]}
    _run(fake, n=30, cached=stale)
    assert fake.count("registrar_analisis_respondente") == 30


def test_corpus_chico_una_tanda_cae_a_map_reduce_si_se_trunca(fake, monkeypatch):
    """Si todo cabe por tokens de entrada pero la salida de la llamada única
    se trunca, se pasa a tandas + fusión en vez de fallar."""
    monkeypatch.setattr(thematic, "SYNTHESIS_BATCH_INPUT_TOKENS", 10**9)
    report = _run(fake, n=20)
    assert report.startswith("# Informe")
    assert fake.count("registrar_sintesis_clusters") == 1
    assert fake.count("registrar_clusters_tanda") >= 2
    assert fake.count("registrar_agrupacion_de_candidatos") >= 1


def test_corpus_chico_una_tanda_sin_truncar(fake, monkeypatch):
    monkeypatch.setattr(thematic, "SYNTHESIS_BATCH_INPUT_TOKENS", 10**9)
    fake.truncate_single_synthesis = False
    report = _run(fake, n=20)
    assert report.startswith("# Informe")
    assert fake.count("registrar_clusters_tanda") == 0


def test_sink_de_uso_acumula_por_proyecto(fake):
    acc = {}

    def sink(project_id, rec):
        acc.setdefault(project_id, {"calls": 0, "cost": 0.0})
        acc[project_id]["calls"] += 1
        acc[project_id]["cost"] += rec["cost_usd"]

    claude_log.set_usage_sink(sink)
    try:
        claude_log.current_project_id.set("proj_x")
        _run(fake, n=12)
    finally:
        claude_log.set_usage_sink(None)
        claude_log.current_project_id.set(None)
    assert acc["proj_x"]["calls"] == len(fake.calls), "las llamadas desde los hilos también llevan el proyecto"
    assert acc["proj_x"]["cost"] > 0


def test_texto_truncado_da_error_claro(fake):
    with pytest.raises(RuntimeError) as ei:
        thematic._call_text("s", "u", label="prueba texto", max_tokens=10)
    assert "prueba texto" in str(ei.value) and "max_tokens" in str(ei.value)


def test_limite_del_modelo_por_env(monkeypatch):
    monkeypatch.setenv("CLAUDE_MAX_OUTPUT_TOKENS", "4321")
    assert thematic.model_max_output_tokens("cualquiera") == 4321
    assert thematic._cap_tokens(999999, "cualquiera") == 4321


def test_chunk_by_tokens_respeta_presupuesto():
    items = [{"t": "x" * 300} for _ in range(10)]  # ~100 tokens c/u
    chunks = thematic._chunk_by_tokens(items, 250)
    assert [len(c) for c in chunks] == [2, 2, 2, 2, 2]
    assert thematic._chunk_by_tokens(items, 1) == [[i] for i in items]
    assert thematic._chunk_by_tokens([], 100) == []


def test_merge_by_groups_aritmetica():
    cands = [
        {"cluster_name": "A", "member_count": 2, "member_ids": ["R1", "R2"],
         "breakdown_by_metadata": {"by_x": {"a": 2}}, "quote_candidates": [{"quote": "q1"}]},
        {"cluster_name": "a_bis", "member_count": 2, "member_ids": ["R2", "R3"],
         "breakdown_by_metadata": {"by_x": {"a": 1, "b": 1}}, "quote_candidates": [{"quote": "q2"}]},
        {"cluster_name": "B", "member_count": 1, "member_ids": ["R9"], "quote_candidates": [{"quote": "q3"}]},
    ]
    # El modelo une 0 y 1, repite el 1 y olvida el 2 → el 2 forma su propio cluster.
    merged = thematic._merge_by_groups(cands, [("A canónico", [0, 1, 1])])
    assert [m["cluster_name"] for m in merged] == ["A canónico", "B"]
    a = merged[0]
    assert a["member_ids"] == ["R1", "R2", "R3"] and a["member_count"] == 3  # R2 una sola vez
    assert a["breakdown_by_metadata"] == {"by_x": {"a": 3, "b": 1}}
    assert len(a["quote_sources"]) == 2


def test_propose_y_codify_usan_salida_estructurada(fake):
    cats = thematic.propose_categories("marco", ["uno", "dos"])
    assert cats[0]["nombre"] == "A"
    out = thematic.codify_batch("marco", [{"id": "cat_1", "nombre": "A", "definicion": "d"}],
                                [{"id": "R0001", "text": "t"}, {"id": "R0002", "text": "t"}])
    assert [o["response_id"] for o in out] == ["R0001", "R0002"]
    assert out[0]["assignments"][0]["rationale"] == 'dijo "x"'
