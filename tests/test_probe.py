"""server/probe.py: one model per scheduler run, results kept in gm_usage probe:<run>, off without PROBE_RUN."""
from server import config, probe
from server.db import MemoryStore


def test_off_without_a_run_name(monkeypatch):
    monkeypatch.delenv("PROBE_RUN", raising=False)
    assert probe.run_one(MemoryStore(), 280, "2026-11-23T15:00:00Z") is None


def test_one_model_per_run_until_the_queue_is_empty(monkeypatch):
    monkeypatch.setenv("PROBE_RUN", "r1")
    monkeypatch.setenv("PROBE_MODELS", "g-a,openrouter:x/y:free")
    calls = []
    monkeypatch.setattr(probe, "_system", lambda: "SYS")
    monkeypatch.setattr(probe, "_gemini", lambda m, s, u, w: calls.append(m) or {"answered": True, "total_s": 3.0})
    monkeypatch.setattr(probe, "_openrouter", lambda m, s, u, w: calls.append(m) or {"answered": False, "total_s": 270.0, "error": "slow"})
    store = MemoryStore()
    assert probe.run_one(store, 280, "2026-11-23T15:00:00Z")["model"] == "g-a"
    assert probe.run_one(store, 280, "2026-11-23T15:05:00Z")["model"] == "openrouter:x/y:free"
    assert probe.run_one(store, 280, "2026-11-23T15:10:00Z") == {"probe": "r1", "done": True}
    doc, _ = store.get("usage", "probe:r1")
    assert calls == ["g-a", "openrouter:x/y:free"] and [r["model"] for r in doc["results"]] == calls
    assert doc["results"][1]["error"] == "slow" and doc["results"][0]["wait_s"] == 270


def test_not_enough_time_left_skips(monkeypatch):
    monkeypatch.setenv("PROBE_RUN", "r2")
    assert probe.run_one(MemoryStore(), config.PROBE_MIN_SECONDS - 1, "2026-11-23T15:00:00Z") is None


def test_json_detection():
    assert probe._is_json('{"a": 1}') and probe._is_json('```json\n{"a": 1}\n```') and not probe._is_json("hello")


def test_a_scheduled_run_starts_at_its_time_and_stops_after_the_window(monkeypatch):
    monkeypatch.delenv("PROBE_RUN", raising=False)
    monkeypatch.setenv("PROBE_SCHEDULE", "2026-11-23T15:00Z")
    store = MemoryStore()
    assert probe.active_run(store, "2026-11-23T14:59:00Z") is None
    assert probe.active_run(store, "2026-11-23T15:04:00Z") == "sched-20261123T1500Z"
    assert probe.active_run(store, "2026-11-23T18:01:00Z") is None


def test_the_host_command_adds_times_to_the_schedule(monkeypatch):
    from server import admin

    class E:
        store = MemoryStore()
    monkeypatch.delenv("PROBE_SCHEDULE", raising=False)
    out = admin.run(E, "probe_schedule", {"times": ["2026-11-24T02:00Z"]})
    assert out["schedule"] == ["2026-11-24T02:00Z"]
    assert probe.active_run(E.store, "2026-11-24T02:10:00Z") == "sched-20261124T0200Z"
    assert admin.run(E, "probe_status", {}) == {"runs": []}
