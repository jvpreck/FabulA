"""2026-11-25 (owner, after three probe runs): failed early turn closes are retried by the scheduler, turn closes are spread over the
night, and the probe has realistic request kinds and counts its own requests."""
from datetime import timedelta

from server import config, probe
from server.gm import GMUnavailable
from test_engine import world, start_solo  # noqa: F401  (pytest fixture)


def _down(gm, state):
    real = gm.call

    def call(system, user, tier="light"):
        if state["down"]:
            raise GMUnavailable("503 UNAVAILABLE")
        return real(system, user, tier)
    gm.call = call


def test_a_failed_turn_close_is_retried_by_the_scheduler_before_its_deadline(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    state = {"down": True}
    _down(gm, state)
    assert eng.resolve_turn(gid)["resolved"] is False             # an early close (e.g. every player acted) that failed
    doc, _ = store.get("usage", eng.RETRY_KEY)
    first = doc["games"][gid]
    assert first["tries"] == 1
    g, _ = store.get("game", gid)
    trouble = next(t for t in g["turns"] if t["n"] == g["clock"]["turn"])["gm_trouble"]
    assert trouble["next_retry"] == first["next"]
    assert eng.resolve_due()["checked"] == 0                       # not due yet: neither the deadline nor the retry time
    clock["t"] += timedelta(minutes=config.TURN_RETRY_FIRST_MINUTES + 1)
    out = eng.resolve_due()                                        # still down: tried again, the pause doubles
    assert out["checked"] == 1 and out["results"][0]["resolved"] is False
    doc, _ = store.get("usage", eng.RETRY_KEY)
    assert doc["games"][gid]["tries"] == 2
    clock["t"] += timedelta(minutes=2 * config.TURN_RETRY_FIRST_MINUTES + 1)
    state["down"] = False
    out = eng.resolve_due()
    assert out["results"][0]["resolved"] is True
    doc, _ = store.get("usage", eng.RETRY_KEY)
    assert gid not in doc["games"]                                 # cleared once the turn is resolved


def test_the_retry_pause_is_capped(world):
    eng, store, gm, clock = world
    for _ in range(10):
        eng._retry_mark("g_x", 4)
    doc, _ = store.get("usage", eng.RETRY_KEY)
    nxt = doc["games"]["g_x"]["next"]
    assert nxt <= (clock["t"] + timedelta(minutes=config.TURN_RETRY_MAX_MINUTES)).isoformat().replace("+00:00", "Z")
    eng._retry_mark("g_x", 5)                                      # a new turn starts the pauses again
    assert store.get("usage", eng.RETRY_KEY)[0]["games"]["g_x"]["tries"] == 1


def test_close_slots_full_hours_then_half_then_quarters(world):
    eng, store, gm, clock = world
    seen = []
    for _ in range(11):
        gid, _ = start_solo(eng)
        g, _ = store.get("game", gid)
        seen.append((g["settings"]["turn_close_hour"], g["settings"]["turn_close_minute"]))
    assert seen[:5] == [(6, 0), (5, 0), (4, 0), (3, 0), (2, 0)]        # latest first: the end of the night is the least busy
    assert seen[5:9] == [(5, 30), (4, 30), (3, 30), (2, 30)]
    assert seen[9:11] == [(5, 45), (5, 15)]
    slots = eng._suggest_close_slot.__doc__
    assert "full hours" in slots


def test_probe_queue_kinds(monkeypatch):
    monkeypatch.delenv("PROBE_MODELS", raising=False)
    monkeypatch.setenv("PROBE_KINDS", "action,turn_close,bogus")
    q = probe._queue()
    assert [x["model"] for x in q if x["kind"] == "action"] == config.GEMINI_LIGHT_MODELS
    assert [x["model"] for x in q if x["kind"] == "turn_close"] == config.GEMINI_STRONG_MODELS
    assert probe._tier(config.GEMINI_STRONG_MODELS[0], "turn_close") == "turn"
    assert probe._tier(config.GEMINI_LIGHT_MODELS[0], "action") == "light"
    assert probe._tier("openrouter:x/y:free", "simple") == "openrouter"


def test_probe_counts_its_requests_and_skips_when_the_guard_is_used_up(monkeypatch):
    from server.db import MemoryStore
    monkeypatch.setenv("PROBE_RUN", "u1")
    monkeypatch.setenv("PROBE_MODELS", "g-a,g-b")
    monkeypatch.delenv("PROBE_KINDS", raising=False)
    monkeypatch.setattr(probe, "_system", lambda: "SYS")
    sent = []
    monkeypatch.setattr(probe, "_gemini", lambda m, s, u, w, e="medium": sent.append(m) or {"answered": True, "total_s": 1.0})
    store = MemoryStore()
    probe.run_one(store, 280, "2026-11-23T15:00:00Z")
    counters = [r["data"] for r in store.t["usage"].values() if r["data"].get("tier") == "light"]
    assert len(counters) == 1 and counters[0]["count"] == 1               # counted like a request in play
    monkeypatch.setitem(config.GEMINI_LIMITS, "light", {**config.GEMINI_LIMITS["light"], "rpd": 1})
    probe.run_one(store, 280, "2026-11-23T15:05:00Z")
    doc, _ = store.get("usage", "probe:u1")
    assert sent == ["g-a"]
    assert doc["results"][0]["tier"] == "light" and "used up" in doc["results"][1]["skipped"]


def test_realistic_requests_are_built_from_a_real_game_and_change_nothing(world, monkeypatch):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    before = store.get("game", gid)
    monkeypatch.setenv("PROBE_GAME", gid)
    system, env, effort, info = probe.real_request(store, "action")
    assert probe.REAL_TEXTS["action"] in env and info["game"] == gid and len(system) > 1000
    system2, env2, effort2, _ = probe.real_request(store, "turn_close")
    assert '"mode":"resolve_turn"' in env2.replace(" ", "") and probe.REAL_TEXTS["turn_close"] in env2
    assert effort2 == config.GEMINI_THINKING_LEVEL_TURN
    assert store.get("game", gid) == before                           # read only
    sa, _ = store.get("submit_action", f"{gid}:{before[0]['clock']['turn']}")
    assert not any(a.get("id") == "a_probe" for acts in (sa or {}).get("actions", {}).values() for a in acts)


def test_realistic_kind_without_a_game_is_recorded_as_skipped(monkeypatch):
    from server.db import MemoryStore
    monkeypatch.setenv("PROBE_RUN", "u2")
    monkeypatch.setenv("PROBE_MODELS", "g-a")
    monkeypatch.setenv("PROBE_KINDS", "action")
    monkeypatch.delenv("PROBE_GAME", raising=False)
    monkeypatch.setattr(probe, "_gemini", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not be sent")))
    store = MemoryStore()
    probe.run_one(store, 280, "2026-11-23T15:00:00Z")
    doc, _ = store.get("usage", "probe:u2")
    assert doc["results"][0]["kind"] == "action" and "PROBE_GAME" in doc["results"][0]["skipped"]
