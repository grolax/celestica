"""prompt_store funciona sin prompts.json y nunca toca el archivo real."""
import json

import pytest

from app import prompt_store


@pytest.fixture
def store(tmp_path, monkeypatch):
    defaults = {
        "a": {"system": "sa", "instructions": "ia"},
        "b": {"system": "sb", "instructions": "ib"},
    }
    (tmp_path / "prompts_default.json").write_text(json.dumps(defaults), encoding="utf-8")
    monkeypatch.setattr(prompt_store, "_DEFAULTS_PATH", tmp_path / "prompts_default.json")
    monkeypatch.setattr(prompt_store, "_PROMPTS_PATH", tmp_path / "prompts.json")
    return defaults


def test_sin_archivo_devuelve_defaults(store):
    assert prompt_store.get_prompts() == store


def test_archivo_parcial_se_superpone_a_defaults(store, tmp_path):
    (tmp_path / "prompts.json").write_text(
        json.dumps({"a": {"system": "X", "instructions": "Y"}}), encoding="utf-8"
    )
    got = prompt_store.get_prompts()
    assert got["a"] == {"system": "X", "instructions": "Y"}
    assert got["b"] == store["b"]


def test_save_sin_archivo_lo_crea_y_reset_restaura(store, tmp_path):
    assert not (tmp_path / "prompts.json").exists()
    prompt_store.save_prompt("a", "nuevo", "nuevas")
    assert (tmp_path / "prompts.json").exists()
    assert prompt_store.get_prompts()["a"] == {"system": "nuevo", "instructions": "nuevas"}
    assert prompt_store.get_prompts()["b"] == store["b"]
    assert prompt_store.reset_prompt("a") == store["a"]
    assert prompt_store.get_prompts()["a"] == store["a"]


def test_clave_inexistente_lanza_keyerror(store):
    with pytest.raises(KeyError):
        prompt_store.save_prompt("zzz", "s", "i")
    with pytest.raises(KeyError):
        prompt_store.reset_prompt("zzz")
