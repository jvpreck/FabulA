"""An ordered list of models per tier (GEMINI_STRONG_MODELS, GEMINI_LIGHT_MODELS). The first one that answers is used; one that times out, answers a
5xx or is over its quota is left alone for a while and the next is tried. Found 2026-11-09: three 503s from the light model failed a player's step,
and the strong model had not answered anything for a day."""
import time
from datetime import datetime, timezone

import pytest

from server import config
from server.db import MemoryStore
from server.gm import GeminiGM, GMUnavailable, Usage

S1, S2, S3 = "strong-1", "strong-2", "strong-3"
L1, L2, L3 = "light-1", "light-2", "light-3"


@pytest.fixture(autouse=True)
def chains(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_STRONG_MODELS", [S1, S2, S3])
    monkeypatch.setattr(config, "GEMINI_LIGHT_MODELS", [L1, L2, L3])
    monkeypatch.setattr(config, "GEMINI_MODEL_TURN", S1)
    monkeypatch.setattr(config, "GEMINI_MODEL_LIGHT", L1)


class Fake(GeminiGM):
    """`fail` maps a model to the error it raises (None or absent: it answers)."""

    def __init__(self, fail, store=None):
        super().__init__(usage=Usage(store or MemoryStore()), sleep=lambda s: None)
        self.fail, self.sent, self.timeouts = dict(fail), [], []

    def _generate(self, model, level, system, user):
        self.sent.append(model)
        self.timeouts.append(self._timeout_override)
        if self.fail.get(model):
            raise Exception(self.fail[model])
        return "{}"


E503, E504, E429, E400 = "503 UNAVAILABLE: high demand", "504 DEADLINE_EXCEEDED", "429 RESOURCE_EXHAUSTED: quota", "400 INVALID_ARGUMENT: bad request"


# ---------------------------------------------------------------- the light list
def test_a_503_from_the_first_light_model_is_answered_by_the_next_after_one_quick_retry():
    g = Fake({L1: E503})
    assert g.call("s", "u") == "{}"
    assert g.sent == [L1, L1, L2], "one quick retry, then the next model"
    assert g.last["model"] == L2 and "light model light-1 unavailable, answered by light-2" in g.last["degraded"]
    assert g.last_meta["fallback"] == "used"


def test_the_failed_model_is_then_skipped_so_the_next_request_goes_straight_to_the_next():
    g = Fake({L1: E503})
    g.call("s", "u")
    g.sent.clear()
    g.call("s", "u")
    assert g.sent == [L2] and g.last["model"] == L2


def test_the_skip_is_shared_with_other_instances_and_ends(monkeypatch):
    store = MemoryStore()
    Fake({L1: E503}, store).call("s", "u")
    other = Fake({}, store)
    other.call("s", "u")
    assert other.sent == [L2], "another instance sees the note"
    real = time.time
    monkeypatch.setattr(time, "time", lambda: real() + config.LIGHT_BREAKER_SECONDS + 30)
    other._breakers.clear()
    other.sent.clear()
    other.call("s", "u")
    assert other.sent == [L1] and other.last["model"] == L1, "after the time the first model is tried again, and it answers"
    assert "fallback" not in other.last_meta


def test_a_quota_error_or_a_timeout_on_the_first_model_goes_to_the_next_without_retrying_it():
    for err in (E429, E504):
        g = Fake({L1: err})
        assert g.call("s", "u") == "{}" and g.sent == [L1, L2], err


def test_the_third_model_answers_when_the_first_two_fail():
    g = Fake({L1: E503, L2: E429})
    assert g.call("s", "u") == "{}" and g.last["model"] == L3
    assert g.sent == [L1, L1, L2, L3]


def test_when_every_model_fails_the_player_is_told_gemini_is_not_answering():
    g = Fake({L1: E503, L2: E503, L3: E503})
    with pytest.raises(GMUnavailable):
        g.call("s", "u")
    assert g.sent.count(L1) == 2 and g.sent.count(L2) == 2 and g.sent.count(L3) == config.GEMINI_RETRIES + 1, "only the last one gets the full retries"


def test_a_model_that_was_just_skipped_is_the_last_resort():
    g = Fake({L1: E503})
    g.call("s", "u")  # light-1 is now skipped
    g.fail = {L2: E503, L3: E503}
    g.sent.clear()
    assert g.call("s", "u") == "{}"
    assert g.sent[0] == L2 and g.sent[-1] == L1, "the skipped model comes after the others"


def test_a_bad_request_is_not_answered_by_another_model():
    g = Fake({L1: E400})
    with pytest.raises(Exception):
        g.call("s", "u")
    assert g.sent == [L1]


def test_a_list_of_one_keeps_the_old_behaviour(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_LIGHT_MODELS", [L1])
    g = Fake({L1: E503})
    with pytest.raises(GMUnavailable):
        g.call("s", "u")
    assert set(g.sent) == {L1} and len(g.sent) == config.GEMINI_RETRIES + 1


def test_a_model_with_another_behind_it_gets_a_shorter_timeout_and_the_last_the_full_one():
    g = Fake({L1: E503, L2: E503})
    g.call("s", "u")
    assert g.timeouts == [config.CHAIN_TIMEOUT_SECONDS, config.CHAIN_TIMEOUT_SECONDS, config.CHAIN_TIMEOUT_SECONDS, config.CHAIN_TIMEOUT_SECONDS, None]
    assert g._timeout_override is None


# ---------------------------------------------------------------- the strong list
def test_a_strong_request_goes_to_the_next_strong_model_before_the_light_ones():
    g = Fake({S1: E504})
    assert g.call("s", "u", tier="turn") == "{}"
    assert g.sent == [S1, S2] and g.last["tier"] == "turn" and g.last["model"] == S2
    assert "turn model strong-1 unavailable, answered by strong-2" in g.last["degraded"]


def test_when_every_strong_model_fails_the_light_models_answer_and_the_turn_says_so():
    g = Fake({S1: E504, S2: E429, S3: E503})
    assert g.call("s", "u", tier="turn") == "{}"
    assert g.last["tier"] == "light" and g.last["model"] == L1
    assert "turn models unavailable" in g.last["degraded"]


def test_when_every_strong_model_was_just_skipped_the_light_ones_answer_at_once_without_spending_strong_quota():
    g = Fake({S1: E504, S2: E504, S3: E504})
    g.call("s", "u", tier="turn")
    g.sent.clear()
    assert g.call("s", "u", tier="turn") == "{}"
    assert g.sent == [L1] and g.last_meta["breaker"] == "open" and "skipped" in g.last["degraded"]
    assert Usage(g.usage.store).today()["turn"]["used_today"] == 1


def test_a_strong_success_closes_its_skip():
    g = Fake({S1: E504})
    g.call("s", "u", tier="turn")
    g.fail = {}
    g._breakers.clear()
    real = time.time
    time.time = lambda: real() + config.STRONG_BREAKER_SECONDS + 5
    try:
        g.sent.clear()
        g.call("s", "u", tier="turn")
    finally:
        time.time = real
    assert g.sent == [S1] and g.last["model"] == S1


# ---------------------------------------------------------------- settings, statistics, thinking
def test_the_defaults_follow_the_probe_and_the_old_single_model_settings_still_go_first(monkeypatch):
    import importlib
    monkeypatch.delenv("GEMINI_STRONG_MODELS", raising=False)
    monkeypatch.delenv("GEMINI_LIGHT_MODELS", raising=False)
    monkeypatch.setenv("GEMINI_MODEL_TURN", "my-strong")
    monkeypatch.setenv("GEMINI_MODEL_LIGHT", "gemini-3.1-flash-lite")
    try:
        cfg = importlib.reload(config)
        assert cfg.GEMINI_STRONG_MODELS[0] == "my-strong" and cfg.GEMINI_MODEL_TURN == "my-strong"
        assert cfg.GEMINI_LIGHT_MODELS[0] == "gemini-3.1-flash-lite" and cfg.GEMINI_LIGHT_MODELS.count("gemini-3.1-flash-lite") == 1, "no duplicates"
    finally:
        monkeypatch.undo()
        importlib.reload(config)
    assert config.GEMINI_STRONG_MODELS == ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.8-flash"]
    assert config.GEMINI_LIGHT_MODELS == ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash"]


def test_fallbacks_are_counted_in_the_call_statistics():
    u = Usage(MemoryStore(), lambda: datetime(2026, 11, 1, 9, tzinfo=timezone.utc))
    for f in ("used", "used", None):
        u.record({"level": 3, "tier": "light", "mode": "intake", "kind": "action", "game_id": "g", "fallback": f})
    assert next(iter(u.stats()["by_level_tier_mode_kind"].values()))["fallback_used"] == 2


def test_a_model_that_refuses_thinking_level_is_asked_again_without_it_and_remembered(monkeypatch):
    sent = []

    class Models:
        def generate_content(self, model, contents, config):
            sent.append(config.thinking_config)
            if config.thinking_config is not None:
                raise Exception("400 INVALID_ARGUMENT: Thinking level is not supported for this model.")
            return type("R", (), {"text": "{}", "usage_metadata": None})()

    g = GeminiGM(usage=None)
    monkeypatch.setattr(g, "_get", lambda: type("C", (), {"models": Models()})())
    assert g.call("s", "u") == "{}" and sent[0] is not None and sent[1] is None
    g.call("s", "u")
    assert sent[2] is None, "not asked again with a thinking level"
