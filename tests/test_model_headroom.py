"""The server counts its own calls against each model's free-tier limits (config.MODEL_LIMITS, read from the AI Studio rate-limit page) and
tries a model that is out of headroom after the ones that have room; a 429 that names its quota says how long to leave the model alone."""
from datetime import datetime, timezone

import pytest

from server import config
from server.db import MemoryStore
from server.gm import GeminiGM, Usage

A, B, C = "model-a", "model-b", "model-c"


@pytest.fixture(autouse=True)
def limits(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_LIGHT_MODELS", [A, B, C])
    monkeypatch.setattr(config, "GEMINI_STRONG_MODELS", [A, B, C])
    monkeypatch.setattr(config, "MODEL_LIMITS", {A: {"rpm": 5, "tpm": 250000, "rpd": 20}, B: {"rpm": 15, "tpm": 250000, "rpd": 500}})
    monkeypatch.setattr(config, "MODEL_LIMIT_MARGIN", 0.9)


class Clock:
    def __init__(self):
        self.t = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.t

    def advance(self, seconds):
        from datetime import timedelta
        self.t += timedelta(seconds=seconds)


class Fake(GeminiGM):
    def __init__(self, usage, fail=None, tokens=0):
        super().__init__(usage=usage, sleep=lambda s: None)
        self.fail, self.sent, self.tokens = dict(fail or {}), [], tokens

    def _generate(self, model, level, system, user):
        self.sent.append(model)
        if self.fail.get(model):
            raise Exception(self.fail[model])
        self._meta["tokens_in"] = self.tokens
        return "{}"


def test_calls_are_counted_per_model_with_their_input_tokens():
    u = Usage(MemoryStore(), Clock())
    g = Fake(u, tokens=50000)
    g.call("s", "u")
    g.call("s", "u")
    assert u.model_state(A) == {"requests_today": 2, "requests_minute": 2, "tokens_minute": 100000}
    assert u.model_state(B)["requests_today"] == 0


def test_a_model_out_of_requests_a_minute_is_tried_after_the_ones_with_room():
    u = Usage(MemoryStore(), Clock())
    for _ in range(4):  # 90% of 5 requests a minute is 4
        u.model_record(A, 1000)
    g = Fake(u)
    g.call("s", "u")
    assert g.sent == [B] and g.last["model"] == B
    assert g.last_meta["fallback"] == "used" and "out of minute headroom" in g.last_meta["limit"]


def test_the_tokens_a_minute_limit_counts_the_size_of_the_next_request():
    u = Usage(MemoryStore(), Clock())
    u.model_record(A, 200000)
    g = Fake(u)
    g.call("s" * 100000, "u")  # about 28,500 tokens more: 228,500 of 225,000 (90% of 250,000)
    assert g.sent == [B]
    g.sent.clear()
    g.call("s", "u")  # a small one fits
    assert g.sent == [A]


def test_the_minute_window_slides_and_the_model_comes_back():
    clock = Clock()
    u = Usage(MemoryStore(), clock)
    for _ in range(4):
        u.model_record(A, 1000)
    assert u.model_headroom(A) == "minute"
    clock.advance(61)
    assert u.model_headroom(A) == "ok"


def test_a_model_out_of_requests_today_is_skipped_until_the_provider_day_changes():
    clock = Clock()
    u = Usage(MemoryStore(), clock)
    for _ in range(18):  # 90% of 20
        u.model_record(A, 0)
        clock.advance(61)  # (spread out so the minute limit is not the one that stops it)
    assert u.model_headroom(A) == "day"
    clock.advance(24 * 3600)
    assert u.model_headroom(A) == "ok"


def test_when_every_model_is_out_of_headroom_the_first_is_still_tried_as_a_last_resort(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_LIGHT_MODELS", [A, B])
    u = Usage(MemoryStore(), Clock())
    for m in (A, B):
        for _ in range(500):
            u.model_record(m, 0)
    g = Fake(u)
    assert g.call("s", "u") == "{}"
    assert g.sent == [A], "the 10% margin is for this try; the provider decides"


def test_a_model_without_listed_limits_is_never_held_back():
    u = Usage(MemoryStore(), Clock())
    assert u.model_headroom(C, 10 ** 9) == "ok"


def test_a_daily_429_leaves_the_model_alone_until_the_day_changes_for_every_instance(monkeypatch):
    store, clock = MemoryStore(), Clock()
    monkeypatch.setattr("time.time", lambda: clock().timestamp())
    u = Usage(store, clock)
    day = "429 RESOURCE_EXHAUSTED. Quota exceeded for metric: generativelanguage.googleapis.com/generate_requests_per_model_per_day, quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier"
    g = Fake(u, {A: day})
    g.call("s", "u")
    assert g.sent == [A, B], "no quick retry of a quota answer"
    assert u.model_state(A)["requests_today"] == 20, "counted as used up"
    b = u.breakers()
    assert b and b[0]["model"] == A and b[0]["seconds_left"] > 3600, "left alone for the rest of the day, not for 15 minutes"
    other = Fake(Usage(store, clock))
    other.call("s", "u")
    assert other.sent == [B]


def test_a_per_minute_429_is_left_alone_for_about_a_minute_only(monkeypatch):
    clock = Clock()
    monkeypatch.setattr("time.time", lambda: clock().timestamp())
    u = Usage(MemoryStore(), clock)
    minute = "429 RESOURCE_EXHAUSTED. Quota exceeded for metric: generate_content_free_tier_input_token_count, quotaId': 'GenerateContentInputTokensPerModelPerMinute-FreeTier', 'retryDelay': '41s'"
    g = Fake(u, {A: minute})
    g.call("s", "u")
    b = u.breakers()
    assert b[0]["model"] == A and 40 <= b[0]["seconds_left"] <= 45
    assert u.model_state(A)["requests_today"] == 0, "a minute limit does not use up the day"


def test_the_admin_view_lists_what_was_sent_against_each_limit():
    u = Usage(MemoryStore(), Clock())
    Fake(u, tokens=1234).call("s", "u")
    m = u.models_today()[A]
    assert m["requests_today"] == 1 and m["tokens_minute"] == 1234 and m["limits"]["rpd"] == 20


def test_the_limits_can_be_overridden_from_the_environment(monkeypatch):
    import importlib
    monkeypatch.setenv("GEMINI_MODEL_LIMITS", '{"gemini-3.6-flash": {"rpd": 1000}, "my-model": {"rpm": 1}}')
    try:
        cfg = importlib.reload(config)
        assert cfg.MODEL_LIMITS["gemini-3.6-flash"] == {"rpm": 5, "tpm": 250000, "rpd": 1000} and cfg.MODEL_LIMITS["my-model"] == {"rpm": 1}
    finally:
        monkeypatch.undo()
        importlib.reload(config)
