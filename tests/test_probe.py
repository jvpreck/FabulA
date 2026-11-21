"""server/probe.py: one model per scheduler run, results kept in gm_usage probe:<run>, off without PROBE_RUN."""
from server import config, probe
from server.db import MemoryStore


def test_off_without_a_run_name(monkeypatch):
    monkeypatch.delenv("PROBE_RUN", raising=False)
    assert probe.run_one(MemoryStore(), 280, "t") is None


def test_one_model_per_run_until_the_queue_is_empty(monkeypatch):
    monkeypatch.setenv("PROBE_RUN", "r1")
    monkeypatch.setenv("PROBE_MODELS", "g-a,openrouter:x/y:free")
    calls = []
    monkeypatch.setattr(probe, "_system", lambda: "SYS")
    monkeypatch.setattr(probe, "_gemini", lambda m, s, u, w: calls.append(m) or {"answered": True, "total_s": 3.0})
    monkeypatch.setattr(probe, "_openrouter", lambda m, s, u, w: calls.append(m) or {"answered": False, "total_s": 270.0, "error": "slow"})
    store = MemoryStore()
    assert probe.run_one(store, 280, "t1")["model"] == "g-a"
    assert probe.run_one(store, 280, "t2")["model"] == "openrouter:x/y:free"
    assert probe.run_one(store, 280, "t3") == {"probe": "r1", "done": True}
    doc, _ = store.get("usage", "probe:r1")
    assert calls == ["g-a", "openrouter:x/y:free"] and [r["model"] for r in doc["results"]] == calls
    assert doc["results"][1]["error"] == "slow" and doc["results"][0]["wait_s"] == 270


def test_not_enough_time_left_skips(monkeypatch):
    monkeypatch.setenv("PROBE_RUN", "r2")
    assert probe.run_one(MemoryStore(), config.PROBE_MIN_SECONDS - 1, "t") is None


def test_json_detection():
    assert probe._is_json('{"a": 1}') and probe._is_json('```json\n{"a": 1}\n```') and not probe._is_json("hello")
