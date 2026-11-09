"""The light model's second chance: a 503 or a timeout from the light model is answered by GEMINI_MODEL_LIGHT_FALLBACK, and the failed model is
left alone for a while (found 2026-11-09: three 503s in a row failed a player's step)."""
import time
from datetime import datetime, timezone

import pytest

from server import config
from server.db import MemoryStore
from server.gm import GeminiGM, GMUnavailable, Usage

LIGHT, SECOND = "light-model", "second-model"


@pytest.fixture(autouse=True)
def models(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_MODEL_LIGHT", LIGHT)
    monkeypatch.setattr(config, "GEMINI_MODEL_LIGHT_FALLBACK", SECOND)


class Fake(GeminiGM):
    """`fail` maps a model to the error it raises (or None to answer)."""

    def __init__(self, fail, store=None):
        super().__init__(usage=Usage(store or MemoryStore()), sleep=lambda s: None)
        self.fail, self.sent = dict(fail), []

    def _generate(self, model, level, system, user):
        self.sent.append(model)
        err = self.fail.get(model)
        if err:
            raise Exception(err)
        return "{}"


def test_a_503_from_the_light_model_is_answered_by_the_second_after_one_quick_retry():
    g = Fake({LIGHT: "503 UNAVAILABLE: high demand"})
    assert g.call("s", "u") == "{}"
    assert g.sent == [LIGHT, LIGHT, SECOND], "one quick retry, then the second model"
    assert g.last["model"] == SECOND and "answered by second-model" in g.last["degraded"] and g.last_meta["fallback"] == "used"


def test_the_failed_model_is_then_skipped_so_the_next_request_goes_straight_to_the_second():
    g = Fake({LIGHT: "503 UNAVAILABLE"})
    g.call("s", "u")
    g.sent.clear()
    g.call("s", "u")
    assert g.sent == [SECOND] and g.last["model"] == SECOND


def test_the_skip_is_shared_with_other_instances_and_ends(monkeypatch):
    store = MemoryStore()
    Fake({LIGHT: "503 UNAVAILABLE"}, store).call("s", "u")
    other = Fake({}, store)
    other.call("s", "u")
    assert other.sent == [SECOND], "another instance sees the note"
    real = time.time
    monkeypatch.setattr(time, "time", lambda: real() + config.LIGHT_BREAKER_SECONDS + 30)
    other._breakers.clear()
    other.sent.clear()
    other.call("s", "u")
    assert other.sent == [LIGHT] and other.last["model"] == LIGHT, "after the time the first model is tried again, and it answers"
    assert "fallback" not in other.last_meta


def test_a_quota_error_on_the_first_model_is_answered_by_the_second():
    g = Fake({LIGHT: "429 RESOURCE_EXHAUSTED: input tokens per minute limit exceeded"})
    assert g.call("s", "u") == "{}" and g.sent == [LIGHT, SECOND], "a 429 is not retried: the second model's quota is separate"


def test_a_timeout_on_the_first_model_is_answered_by_the_second():
    g = Fake({LIGHT: "504 DEADLINE_EXCEEDED"})
    assert g.call("s", "u") == "{}" and g.sent == [LIGHT, SECOND]


def test_when_both_fail_the_player_is_told_gemini_is_not_answering():
    g = Fake({LIGHT: "503 UNAVAILABLE", SECOND: "503 UNAVAILABLE"})
    with pytest.raises(GMUnavailable):
        g.call("s", "u")
    assert g.sent.count(LIGHT) == 2 and g.sent.count(SECOND) >= 2


def test_when_the_first_is_skipped_and_the_second_fails_the_first_is_tried_again():
    g = Fake({LIGHT: "503 UNAVAILABLE"})
    g.call("s", "u")  # light is now skipped
    g.fail = {SECOND: "503 UNAVAILABLE"}
    g.sent.clear()
    assert g.call("s", "u") == "{}"
    assert g.sent[0] == SECOND and g.sent[-1] == LIGHT, "the skipped model is the last resort"


def test_a_bad_request_is_not_answered_by_another_model():
    g = Fake({LIGHT: "400 INVALID_ARGUMENT: bad request"})
    with pytest.raises(Exception):
        g.call("s", "u")
    assert g.sent == [LIGHT]


def test_with_no_second_model_the_old_behaviour_stays(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_MODEL_LIGHT_FALLBACK", "")
    g = Fake({LIGHT: "503 UNAVAILABLE"})
    with pytest.raises(GMUnavailable):
        g.call("s", "u")
    assert set(g.sent) == {LIGHT} and len(g.sent) == config.GEMINI_RETRIES + 1


def test_the_strong_tier_still_ends_in_the_light_chain():
    g = Fake({config.GEMINI_MODEL_TURN: "504 DEADLINE_EXCEEDED", LIGHT: "503 UNAVAILABLE"})
    assert g.call("s", "u", tier="turn") == "{}"
    assert g.last["model"] == SECOND and "strong model unavailable" in g.last["degraded"] and "answered by second-model" in g.last["degraded"]


def test_fallbacks_are_counted_in_the_call_statistics():
    u = Usage(MemoryStore(), lambda: datetime(2026, 11, 1, 9, tzinfo=timezone.utc))
    for f in ("used", "used", None):
        u.record({"level": 3, "tier": "light", "mode": "intake", "kind": "action", "game_id": "g", "fallback": f})
    assert next(iter(u.stats()["by_level_tier_mode_kind"].values()))["fallback_used"] == 2
