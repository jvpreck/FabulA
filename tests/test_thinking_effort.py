"""TLR-03-018: the thinking effort follows the request."""
import json

import pytest

from server import config
from server.engine import Engine
from server.gm import GeminiGM

from test_engine import ScriptedGM, standard_gm, start_solo, world  # noqa: F401  (the fixture)


def levels_sent(monkeypatch, tier, effort):
    sent = []

    class Models:
        def generate_content(self, model, contents, config):
            sent.append(config.thinking_config.thinking_level)
            return type("R", (), {"text": "{}", "usage_metadata": None})()

    g = GeminiGM(usage=None)
    monkeypatch.setattr(g, "_get", lambda: type("C", (), {"models": Models()})())
    g.call("s", "u", tier=tier, effort=effort)
    return sent


@pytest.mark.parametrize("tier", ["light", "turn"])
def test_the_requested_level_reaches_the_provider(monkeypatch, tier):
    got = levels_sent(monkeypatch, tier, "low")
    assert str(got[0]).lower().endswith("low")


def test_without_a_request_the_configured_default_is_used(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_THINKING_LEVEL", "medium")
    assert str(levels_sent(monkeypatch, "light", None)[0]).lower().endswith("medium")


def test_an_unknown_level_is_ignored(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_THINKING_LEVEL", "medium")
    assert str(levels_sent(monkeypatch, "light", "extreme")[0]).lower().endswith("medium")


def test_the_engine_picks_the_level_by_kind(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_THINKING_LEVEL", "medium")
    monkeypatch.setattr(config, "GEMINI_THINKING_LEVEL_TURN", "high")
    monkeypatch.setattr(config, "GEMINI_THINKING_BY_KIND", {"free_query": "low", "action": "medium"})
    assert Engine._effort("intake", {"kind": "free_query"}) == "low"
    assert Engine._effort("intake", {"kind": "action"}) == "medium"
    assert Engine._effort("intake", {"kind": "message"}) == "medium"  # not listed: the general default
    assert Engine._effort("resolve_turn", None) == "high"


def test_the_engine_sends_the_level_only_to_a_model_that_takes_it(world, monkeypatch):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    monkeypatch.setattr(config, "GEMINI_THINKING_BY_KIND", {"free_query": "low"})
    seen = {}
    orig = gm.call

    def call(system, user, tier="light", effort=None):
        seen["effort"] = effort
        return orig(system, user, tier)
    gm.call = call
    eng.submit_action("p_jorge", gid, "free_query", "What is the weather?", cid)
    assert seen["effort"] is None, "a model that does not declare supports_effort is called as before"
    gm.supports_effort = True
    eng.submit_action("p_jorge", gid, "free_query", "What is the weather?", cid)
    assert seen["effort"] == "low"


def test_the_level_table_can_be_set_from_the_environment(monkeypatch):
    import importlib
    monkeypatch.setenv("GEMINI_THINKING_BY_KIND", json.dumps({"free_query": "minimal", "action": "bogus"}))
    importlib.reload(config)
    try:
        assert config.GEMINI_THINKING_BY_KIND["free_query"] == "minimal" and "bogus" not in config.GEMINI_THINKING_BY_KIND.values()
    finally:
        monkeypatch.delenv("GEMINI_THINKING_BY_KIND")
        importlib.reload(config)


def test_by_default_the_simple_kinds_think_least_and_actions_and_character_checks_keep_the_general_level():
    t = config.GEMINI_THINKING_BY_KIND
    assert t["free_query"] == "minimal" and t["thread_note"] == "minimal"
    assert "action" not in t and "character_submission" not in t
