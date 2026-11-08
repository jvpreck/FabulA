import json
from datetime import datetime, timedelta, timezone

import pytest

from server import config
from server.db import MemoryStore
from server.engine import Engine, EngineError
from server.gm import GeminiGM, GMBusy, GMUnavailable, Usage
from test_engine import ScriptedGM, standard_gm, start_solo, CHECK


class Clock:
    def __init__(self):
        self.t = datetime(2026, 11, 1, 9, tzinfo=timezone.utc)

    def __call__(self):
        return self.t


@pytest.fixture
def world():
    store, clock = MemoryStore(), Clock()
    gm = ScriptedGM(standard_gm)
    CHECK["fail_next"] = 0
    return Engine(store, gm, now_fn=clock), store, gm, clock


def test_engine_picks_the_tier(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    assert "turn" not in gm.tiers                  # the character cross-check uses the light model: a player is waiting for it
    gm.tiers.clear()
    eng.submit_action("p_jorge", gid, "free_query", "what do I see?", cid)
    assert gm.tiers and set(gm.tiers) == {"light"}  # single-player requests use the light model
    gm.tiers.clear()
    eng.resolve_turn(gid)
    assert gm.tiers == ["turn"]                     # closing the turn uses the strong model


def usage(store, clock):
    return Usage(store, clock, sleep=lambda s: clock.__setattr__("t", clock.t + timedelta(seconds=s)))


def test_usage_limits_per_minute_and_per_day(monkeypatch):
    monkeypatch.setitem(config.GEMINI_LIMITS, "turn", {"rpd": 3, "rpm": 2})
    store, clock = MemoryStore(), Clock()
    u = usage(store, clock)
    assert [u.reserve("turn") for _ in range(3)] == ["ok", "ok", "minute"]
    clock.t += timedelta(seconds=61)
    assert u.reserve("turn") == "ok"
    clock.t += timedelta(seconds=61)
    assert u.reserve("turn") == "day"               # three used today
    # the quota day follows Pacific time: 09:00 UTC on 1 Nov is 02:00 on 1 Nov in Los Angeles; 08:00 UTC next day is still 1 Nov
    clock.t = datetime(2026, 11, 2, 7, 59, tzinfo=timezone.utc)
    assert u.reserve("turn") == "day"
    clock.t = datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc)
    assert u.reserve("turn") == "ok"                # a new Pacific day
    assert u.today()["turn"]["used_today"] == 1


class FakeGemini(GeminiGM):
    def __init__(self, usage, fail=None):
        super().__init__(usage=usage)
        self.sent = []
        self.fail = fail

    def _generate(self, model, level, system, user):
        self.sent.append((model, level))
        if self.fail and model == config.GEMINI_MODEL_TURN:
            raise self.fail
        return "{}"


def test_models_and_thinking_level_are_configured():
    assert config.GEMINI_MODEL_TURN == "gemini-3.8-flash" and config.GEMINI_MODEL_LIGHT == "gemini-3.5-flash-lite"
    assert config.GEMINI_THINKING_LEVEL == "medium" and config.GEMINI_THINKING_LEVEL_TURN == "medium"


def test_strong_model_for_turns_light_for_the_rest():
    store, clock = MemoryStore(), Clock()
    g = FakeGemini(usage(store, clock))
    g.call("s", "u", tier="turn")
    assert g.sent[-1] == (config.GEMINI_MODEL_TURN, "medium") and g.last["degraded"] is None
    g.call("s", "u")
    assert g.sent[-1] == (config.GEMINI_MODEL_LIGHT, "medium")


def test_falls_back_to_light_when_the_strong_daily_quota_is_gone(monkeypatch):
    monkeypatch.setitem(config.GEMINI_LIMITS, "turn", {"rpd": 1, "rpm": 4})
    store, clock = MemoryStore(), Clock()
    g = FakeGemini(usage(store, clock))
    g.call("s", "u", tier="turn")
    clock.t += timedelta(seconds=61)
    g.call("s", "u", tier="turn")
    assert g.sent[-1][0] == config.GEMINI_MODEL_LIGHT and "quota" in g.last["degraded"]


def test_falls_back_to_light_when_the_strong_model_errors():
    store, clock = MemoryStore(), Clock()
    g = FakeGemini(usage(store, clock), fail=RuntimeError("429 RESOURCE_EXHAUSTED"))
    g.call("s", "u", tier="turn")
    assert [m for m, _ in g.sent] == [config.GEMINI_MODEL_TURN, config.GEMINI_MODEL_LIGHT] and g.last["degraded"]
    g2 = FakeGemini(usage(MemoryStore(), clock), fail=ValueError("bad request: invalid schema"))
    with pytest.raises(ValueError):                 # a real bug is not hidden by the fallback
        g2.call("s", "u", tier="turn")


def test_strong_per_minute_limit_defers_instead_of_degrading(monkeypatch):
    monkeypatch.setitem(config.GEMINI_LIMITS, "turn", {"rpd": 18, "rpm": 1})
    store, clock = MemoryStore(), Clock()
    g = FakeGemini(usage(store, clock))
    g.call("s", "u", tier="turn")
    with pytest.raises(GMBusy):
        g.call("s", "u", tier="turn")
    assert len(g.sent) == 1


def test_light_waits_a_little_then_gives_up(monkeypatch):
    monkeypatch.setitem(config.GEMINI_LIMITS, "light", {"rpd": 450, "rpm": 1})
    store, clock = MemoryStore(), Clock()
    g = FakeGemini(usage(store, clock))
    g.call("s", "u")
    with pytest.raises(GMBusy):                     # the minute does not clear within the short wait
        g.call("s", "u")
    monkeypatch.setitem(config.GEMINI_LIMITS, "light", {"rpd": 1, "rpm": 9})
    clock.t += timedelta(days=1)
    g.call("s", "u")
    with pytest.raises(GMBusy) as e:
        g.call("s", "u")
    assert "daily" in str(e.value)


def test_a_deferred_turn_stays_open_and_is_retried(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    real = gm.call
    state = {"busy": True}

    def call(system, user, tier="light"):
        if state["busy"] and tier == "turn":
            raise GMBusy("the strong AI Master model is at its per-minute limit")
        return real(system, user, tier)
    gm.call = call
    out = eng.resolve_turn(gid)
    assert out["resolved"] is False and "per-minute" in out["reason"]
    g, _ = store.get("game", gid)
    assert next(t for t in g["turns"] if t["n"] == g["clock"]["turn"])["status"] == "open"
    state["busy"] = False
    assert eng.resolve_turn(gid)["resolved"] is True


def test_light_quota_error_reaches_the_player_as_a_plain_message(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    gm.call = lambda *a, **k: (_ for _ in ()).throw(GMBusy("the AI Master is busy right now (request quota). Please try again in a few minutes"))
    with pytest.raises(EngineError) as e:
        eng.submit_action("p_jorge", gid, "free_query", "hello", cid)
    assert "busy" in str(e.value)


class FlakyGemini(GeminiGM):
    """Fails with the given errors in order, then answers. Records the pauses instead of sleeping."""

    def __init__(self, usage, errors):
        super().__init__(usage=usage, sleep=lambda s: self.pauses.append(s))
        self.errors, self.calls, self.pauses = list(errors), [], []

    def _generate(self, model, level, system, user):
        self.calls.append(model)
        if self.errors:
            raise self.errors.pop(0)
        return "{}"


def test_a_503_high_demand_is_retried_quietly_with_backoff():
    store, clock = MemoryStore(), Clock()
    busy = RuntimeError("503 UNAVAILABLE. {'error': {'message': 'This model is currently experiencing high demand.'}}")
    g = FlakyGemini(usage(store, clock), [busy, busy])
    assert g.call("s", "u") == "{}"
    assert len(g.calls) == 3 and len(g.pauses) == 2
    assert 2 <= g.pauses[0] < 3 and 6 <= g.pauses[1] < 7.6      # base, then 3x base, with a little jitter
    assert g.last["degraded"] is None


def test_retries_stop_after_the_limit_then_the_strong_model_falls_back_to_light():
    store, clock = MemoryStore(), Clock()
    busy = RuntimeError("503 UNAVAILABLE")
    g = FlakyGemini(usage(store, clock), [busy] * (config.GEMINI_RETRIES + 1))
    g.call("s", "u", tier="turn")
    assert g.calls == [config.GEMINI_MODEL_TURN] * (config.GEMINI_RETRIES + 1) + [config.GEMINI_MODEL_LIGHT]
    assert g.last["degraded"]
    g2 = FlakyGemini(usage(store, clock), [busy] * (config.GEMINI_RETRIES + 1))
    with pytest.raises(GMUnavailable):               # the light model has nowhere to fall back to: the player is told
        g2.call("s", "u")


def test_quota_errors_timeouts_and_bugs_are_not_retried():
    store, clock = MemoryStore(), Clock()
    for err, outcome in ((RuntimeError("429 RESOURCE_EXHAUSTED"), GMUnavailable), (RuntimeError("504 DEADLINE_EXCEEDED"), GMUnavailable),
                         (TimeoutError("timed out"), GMUnavailable), (ValueError("400 invalid argument"), ValueError)):
        g = FlakyGemini(usage(store, clock), [err])
        with pytest.raises(outcome):
            g.call("s", "u")
        assert len(g.calls) == 1 and not g.pauses


def test_the_retry_wait_has_a_total_budget(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_RETRY_BUDGET_SECONDS", 3)
    store, clock = MemoryStore(), Clock()
    g = FlakyGemini(usage(store, clock), [RuntimeError("503 UNAVAILABLE")] * 5)
    with pytest.raises(GMUnavailable):
        g.call("s", "u")
    assert len(g.calls) == 2 and len(g.pauses) == 1           # the 6 s second wait would exceed the budget


def test_an_error_with_a_status_code_attribute_counts():
    class ServerError(Exception):
        code = 503
    g = FlakyGemini(usage(MemoryStore(), Clock()), [ServerError("The service is overloaded")])
    assert g.call("s", "u") == "{}" and len(g.calls) == 2


def test_gemini_that_keeps_failing_becomes_gm_unavailable():
    store, clock = MemoryStore(), Clock()
    busy = RuntimeError("503 UNAVAILABLE. high demand")
    g = FlakyGemini(usage(store, clock), [busy] * 10)
    with pytest.raises(GMUnavailable) as e:
        g.call("s", "u")
    assert "503" in e.value.reason
    g2 = FlakyGemini(usage(store, clock), [ValueError("400 invalid argument")])
    with pytest.raises(ValueError):                 # a real bug is still a bug, not "Gemini is down"
        g2.call("s", "u")


def test_a_player_action_tells_the_client_that_gemini_has_problems(world):
    from server.tools import _safe
    from server.engine import GeminiTrouble
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)

    def down(system, user, tier="light"):
        raise GMUnavailable("503 UNAVAILABLE")
    gm.call = down
    with pytest.raises(GeminiTrouble):
        eng.submit_action("p_jorge", gid, "free_query", "Look around.", cid)
    out = _safe(lambda: eng.submit_action("p_jorge", gid, "free_query", "Look around.", cid))()
    assert out["gemini_unavailable"] is True and "Gemini" in out["error"] and "nothing was lost" in out["error"].lower()
    assert "problems with Gemini" in out["next_step"]


def test_a_turn_that_cannot_be_resolved_because_of_gemini_is_announced_and_then_clears(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    real = gm.call
    state = {"down": True}

    def call(system, user, tier="light"):
        if state["down"]:
            raise GMUnavailable("503 UNAVAILABLE")
        return real(system, user, tier)
    gm.call = call
    out = eng.resolve_turn(gid)
    assert out["resolved"] is False
    g, _ = store.get("game", gid)
    assert next(t for t in g["turns"] if t["n"] == g["clock"]["turn"])["gm_trouble"]["since"]
    res = eng.get_results("p_jorge")
    notice = res["gm_notice"][0]
    assert notice["kind"] == "gemini_unavailable" and notice["game_id"] == gid and "Gemini" in notice["message"]
    state["down"] = False
    assert eng.resolve_turn(gid)["resolved"] is True
    assert "gm_notice" not in eng.get_results("p_jorge")


def test_writes_to_server_owned_fields_are_dropped_not_rejected():
    from server.apply import Applier

    class WS:
        def __init__(self):
            self.d = {("character", "c1"): {"id": "c1", "game_id": "g1", "events": [], "hp": 5}}
        def get(self, kind, id_, create=None):
            return self.d.get((kind, id_))
        def touch(self, *a):
            pass
    ws = WS()
    ap = Applier(ws, "g1", "resolve_turn", "2026-01-01T00:00:00Z")
    ap.apply_ops([
        {"op": "append", "entity": "character", "id": "c1", "path": "events", "doc": {"summary": "x"}},   # the GM's usual mistake
        {"op": "merge", "entity": "character", "id": "c1", "patch": {"events": [1], "hp": 4}},
        {"op": "adjust", "entity": "character", "id": "c1", "path": "hp", "delta": -1},
    ])
    c = ws.d[("character", "c1")]
    assert c["events"] == [] and c["hp"] == 3          # server-owned writes dropped, the rest applied
    assert len(ap.ignored) == 2


class Err504(Exception):
    code = 504


def _fake_time(monkeypatch):
    now = {"t": 1000.0}
    monkeypatch.setattr("time.monotonic", lambda: now["t"])
    return now


def test_a_slow_504_is_not_retried(monkeypatch):
    now = _fake_time(monkeypatch)
    store, clock = MemoryStore(), Clock()

    class Slow(FlakyGemini):
        def _generate(self, model, level, system, user):
            now["t"] += 98                                  # Google's gateway gave up after ~100 s
            return super()._generate(model, level, system, user)
    g = Slow(usage(store, clock), [Err504("504 Gateway Timeout")])
    assert g.call("s", "u", tier="turn") == "{}"
    assert g.pauses == []                                   # no backoff and no second 100 s attempt on the strong model
    assert g.calls == [config.GEMINI_MODEL_TURN, config.GEMINI_MODEL_LIGHT] and g.last["degraded"]


def test_a_quick_504_is_still_retried(monkeypatch):
    _fake_time(monkeypatch)
    store, clock = MemoryStore(), Clock()
    g = FlakyGemini(usage(store, clock), [Err504("504 Gateway Timeout")])
    assert g.call("s", "u") == "{}"
    assert len(g.pauses) == 1 and len(g.calls) == 2


def test_the_character_check_can_be_sent_back_to_the_strong_model(monkeypatch):
    monkeypatch.setattr(config, "CHARACTER_CHECK_TIER", "turn")
    store, gm, clock = MemoryStore(), ScriptedGM(standard_gm), Clock()
    CHECK["fail_next"] = 0
    eng = Engine(store, gm, now_fn=clock)
    start_solo(eng)
    assert "turn" in gm.tiers


# ------------------------------------------------------------------ the strong model that keeps failing is left alone for a while
class Timeouts(GeminiGM):
    """A strong model that times out (as the live one does on large prompts) and a light model that answers."""

    def __init__(self, usage, strong_fails=True):
        super().__init__(usage=usage)
        self.sent, self.strong_fails = [], strong_fails

    def _generate(self, model, level, system, user):
        self.sent.append(model)
        if model == config.GEMINI_MODEL_TURN and self.strong_fails:
            raise Exception("504 Gateway Timeout")
        return "{}"


def test_after_one_failure_the_strong_model_is_skipped_and_the_light_one_answers_at_once():
    store, clock = MemoryStore(), Clock()
    g = Timeouts(usage(store, clock))
    g.call("s", "u", tier="turn")
    assert g.sent == [config.GEMINI_MODEL_TURN, config.GEMINI_MODEL_LIGHT] and g.last_meta["breaker"] == "tripped"
    g.sent.clear()
    g.call("s", "u", tier="turn")
    assert g.sent == [config.GEMINI_MODEL_LIGHT], "the strong model is not asked again"
    assert g.last["tier"] == "light" and "skipped" in g.last["degraded"] and g.last_meta["breaker"] == "open"
    assert Usage(store, clock).today()["turn"]["used_today"] == 1, "a skipped call does not use the strong model's daily quota"


def test_the_skip_is_shared_with_other_server_instances_and_ends_after_its_time(monkeypatch):
    store, clock = MemoryStore(), Clock()
    Timeouts(usage(store, clock)).call("s", "u", tier="turn")
    other = Timeouts(usage(store, clock), strong_fails=False)
    other.call("s", "u", tier="turn")
    assert other.sent == [config.GEMINI_MODEL_LIGHT], "another instance sees the note in the database"
    import time as _t
    real = _t.time
    monkeypatch.setattr(_t, "time", lambda: real() + config.STRONG_BREAKER_SECONDS + 30)
    other._breakers.clear()
    other.sent.clear()
    other.call("s", "u", tier="turn")
    assert other.sent == [config.GEMINI_MODEL_TURN] and other.last["tier"] == "turn", "tried again after the time, and it answered"
    other.sent.clear()
    other.call("s", "u", tier="turn")
    assert other.sent == [config.GEMINI_MODEL_TURN], "a success closes the breaker"


def test_a_bad_request_does_not_trip_the_breaker():
    g = FakeGemini(usage(MemoryStore(), Clock()), fail=ValueError("bad request: invalid schema"))
    with pytest.raises(ValueError):
        g.call("s", "u", tier="turn")
    assert g._breaker(config.GEMINI_MODEL_TURN) is None


def test_the_breaker_can_be_switched_off(monkeypatch):
    monkeypatch.setattr(config, "STRONG_BREAKER_SECONDS", 0)
    g = Timeouts(usage(MemoryStore(), Clock()))
    g.call("s", "u", tier="turn")
    g.sent.clear()
    g.call("s", "u", tier="turn")
    assert g.sent == [config.GEMINI_MODEL_TURN, config.GEMINI_MODEL_LIGHT]


def test_breaker_events_are_counted_in_the_call_statistics():
    store = MemoryStore()
    u = Usage(store, Clock())
    for b in ("tripped", "open", "open"):
        u.record({"level": 4, "tier": "light", "mode": "resolve_turn", "kind": "-", "game_id": "g", "breaker": b})
    row = next(iter(u.stats()["by_level_tier_mode_kind"].values()))
    assert (row["breaker_tripped"], row["breaker_open"]) == (1, 2)
