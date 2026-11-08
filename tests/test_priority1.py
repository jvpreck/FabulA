"""TLR-08-006 (call statistics), TLR-06-009 (atomic saves), TLR-06-010 (idempotent requests), TLR-03-015 (structured output)."""
import json
from datetime import datetime, timezone

import pytest

from server import admin, config, schema
from server.db import Conflict, MemoryStore, SupabaseStore, Workspace
from server.engine import Engine, EngineError
from server.gm import GeminiGM, Usage
from test_engine import ScriptedGM, standard_gm, start_solo, CHECK


class Clock:
    def __init__(self):
        self.t = datetime(2026, 11, 1, 9, tzinfo=timezone.utc)

    def __call__(self):
        return self.t


class MeteredGM(ScriptedGM):
    """A scripted AI Master that reports tokens and latency the way GeminiGM does."""

    def __init__(self, rule, usage):
        super().__init__(rule)
        self.usage = usage
        self.last = {}
        self.last_meta = {}
        self.garbage = 0  # answer with invalid JSON this many times first

    def call(self, system, user, tier="light"):
        self.last = {"tier": tier, "model": "m", "degraded": None}
        self.last_meta = {"tokens_in": 1000, "tokens_cached": 600, "tokens_out": 50, "tokens_thought": 20, "latency_ms": 120, "retries": 0}
        if self.garbage > 0:
            self.garbage -= 1
            self.calls.append(("", json.loads(user)))
            return "this is not json"
        return super().call(system, user, tier)


@pytest.fixture
def world():
    store, clock = MemoryStore(), Clock()
    usage = Usage(store, clock)
    gm = MeteredGM(standard_gm, usage)
    CHECK["fail_next"] = 0
    return Engine(store, gm, now_fn=clock), store, gm, clock, usage


# ---------------------------------------------------------------- TLR-08-006
def test_every_ai_master_call_is_logged_with_level_tokens_and_game(world):
    eng, store, gm, clock, usage = world
    gid, cid = start_solo(eng)
    base_calls = usage.stats()["by_game"][gid]["calls"]
    eng.submit_action("p_jorge", gid, "free_query", "what do I know?", cid)
    eng.resolve_turn(gid)
    st = usage.stats()
    labels = st["by_level_tier_mode_kind"]
    assert any(k.startswith("3|light|intake|free_query") for k in labels)
    turn_row = next(v for k, v in labels.items() if k.startswith("4|turn|resolve_turn"))
    assert turn_row["calls"] == 1 and turn_row["tokens_in"] == 1000 and turn_row["cached_share"] == 0.6
    assert turn_row["latency_ms"] == 120 and turn_row["tokens_out"] == 50 and turn_row["tokens_thought"] == 20
    assert st["by_game"][gid]["calls"] == base_calls + 2


def test_invalid_answers_and_retries_are_counted(world):
    eng, store, gm, clock, usage = world
    gid, cid = start_solo(eng)
    before = usage.stats()["by_game"][gid]
    gm.garbage = 1
    eng.submit_action("p_jorge", gid, "free_query", "hello", cid)
    after = usage.stats()["by_game"][gid]
    assert after["invalid_json"] == before["invalid_json"] + 1
    assert after["calls"] == before["calls"] + 2 and after["retries"] > before["retries"]


def test_the_host_command_shows_the_call_statistics(world):
    eng, store, gm, clock, usage = world
    gid, cid = start_solo(eng)
    out = admin.run(eng, "gm_usage")
    assert out["calls"]["by_game"][gid]["calls"] >= 1 and "usage" in out


def test_a_failing_log_never_breaks_a_request(world):
    eng, store, gm, clock, usage = world
    gid, cid = start_solo(eng)
    usage.record = lambda e: (_ for _ in ()).throw(RuntimeError("boom"))
    assert eng.submit_action("p_jorge", gid, "free_query", "hello", cid)


# ---------------------------------------------------------------- TLR-06-009
def test_a_stale_record_stops_the_whole_save():
    store = MemoryStore()
    store.put("player", "a", {"id": "a", "n": 0}, 0)
    store.put("player", "b", {"id": "b", "n": 0}, 0)
    ws = Workspace(store)
    ws.get("player", "a")["n"] = 1
    ws.get("player", "b")["n"] = 1
    ws.touch("player", "a")
    ws.touch("player", "b")
    store.put("player", "b", {"id": "b", "n": 99}, 1)  # someone else changed b meanwhile
    with pytest.raises(Conflict):
        ws.commit()
    assert store.get("player", "a")[0]["n"] == 0, "a must not be saved when b could not be"
    assert store.get("player", "b")[0]["n"] == 99


def test_a_new_record_that_already_exists_stops_the_whole_save():
    store = MemoryStore()
    store.put("player", "x", {"id": "x"}, 0)
    ws = Workspace(store)
    ws.put("player", "y", {"id": "y"})
    ws.put("player", "x", {"id": "x", "dup": True})
    ws.versions[("player", "x")] = 0  # as if created by two requests at once
    with pytest.raises(Conflict):
        ws.commit()
    assert store.get("player", "y")[0] is None


class FakeRpc:
    def __init__(self, client):
        self.client = client

    def execute(self):
        if isinstance(self.client.result, Exception):
            raise self.client.result
        return type("R", (), {"data": self.client.result})()


class FakeClient:
    def __init__(self, result):
        self.result, self.calls = result, []

    def rpc(self, name, args):
        self.calls.append((name, args))
        return FakeRpc(self)


def test_supabase_store_commits_through_one_database_function():
    SupabaseStore._no_rpc = False
    c = FakeClient([1, 5])
    out = SupabaseStore(c).put_many([("player", "a", {"id": "a"}, 0, {}), ("game", "g", {"id": "g"}, 4, {"phase": "active"})])
    assert out == [1, 5] and len(c.calls) == 1 and c.calls[0][0] == "gm_commit"
    first, second = c.calls[0][1]["batch"]
    assert first["table"] == "gm_players" and second["table"] == "gm_games" and second["index"] == {"phase": "active"}


def test_supabase_store_turns_a_database_conflict_into_conflict():
    SupabaseStore._no_rpc = False
    with pytest.raises(Conflict):
        SupabaseStore(FakeClient(Exception("conflict: gm_games g changed"))).put_many([("game", "g", {"id": "g"}, 4, {})])


def test_supabase_store_falls_back_when_the_function_is_not_installed_yet():
    SupabaseStore._no_rpc = False
    store = SupabaseStore(FakeClient(Exception("PGRST202 Could not find the function public.gm_commit(batch)")))
    puts = []
    store.put = lambda k, i, d, v, ix: puts.append((k, i)) or v + 1
    assert store.put_many([("player", "a", {}, 0, {}), ("player", "b", {}, 2, {})]) == [1, 3]
    assert puts == [("player", "a"), ("player", "b")] and SupabaseStore._no_rpc is True
    SupabaseStore._no_rpc = False


def test_the_schema_file_defines_the_commit_function():
    sql = (config.ROOT / "supabase" / "schema.sql").read_text(encoding="utf-8")
    assert "create or replace function gm_commit" in sql and "grant execute on function gm_commit(jsonb) to service_role" in sql


# ---------------------------------------------------------------- TLR-06-010
def test_the_same_request_id_runs_once(world):
    eng, store, gm, clock, usage = world
    gid, cid = start_solo(eng)
    n = len(gm.calls)
    first = eng.submit_action("p_jorge", gid, "free_query", "what do I know?", cid, request_id="r1")
    assert len(gm.calls) == n + 1
    again = eng.submit_action("p_jorge", gid, "free_query", "what do I know?", cid, request_id="r1")
    assert len(gm.calls) == n + 1, "the AI Master must not be called again"
    assert again["duplicate_request"] == "r1" and again["deliveries"] == first["deliveries"]
    eng.submit_action("p_jorge", gid, "free_query", "another", cid, request_id="r2")
    assert len(gm.calls) == n + 2


def test_a_retry_gets_the_results_even_though_they_were_already_delivered(world):
    eng, store, gm, clock, usage = world
    gid, cid = start_solo(eng)
    first = eng.submit_action("p_jorge", gid, "free_query", "q", cid, request_id="r1")
    assert first["deliveries"]
    assert not eng.get_results("p_jorge", gid)["deliveries"], "delivered once already"
    assert eng.submit_action("p_jorge", gid, "free_query", "q", cid, request_id="r1")["deliveries"] == first["deliveries"]


def test_a_failed_request_can_be_sent_again_with_the_same_id(world):
    eng, store, gm, clock, usage = world
    gid, cid = start_solo(eng)
    real = gm.call
    gm.call = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down"))
    with pytest.raises(RuntimeError):
        eng.submit_action("p_jorge", gid, "free_query", "q", cid, request_id="r1")
    gm.call = real
    out = eng.submit_action("p_jorge", gid, "free_query", "q", cid, request_id="r1")
    assert out["deliveries"] and "duplicate_request" not in out


def test_a_request_still_running_is_not_started_twice(world):
    eng, store, gm, clock, usage = world
    gid, cid = start_solo(eng)
    assert eng._claim_request("p_jorge", f"{gid}:r1") is None
    with pytest.raises(EngineError) as e:
        eng.submit_action("p_jorge", gid, "free_query", "q", cid, request_id="r1")
    assert "still being processed" in str(e.value)
    clock.t = clock.t.replace(hour=11)  # the first call died long ago: its claim is stale
    assert eng.submit_action("p_jorge", gid, "free_query", "q", cid, request_id="r1")["deliveries"]


def test_request_ids_are_checked_and_old_results_are_forgotten(world):
    eng, store, gm, clock, usage = world
    gid, cid = start_solo(eng)
    with pytest.raises(EngineError):
        eng.submit_action("p_jorge", gid, "free_query", "q", cid, request_id="has space")
    for i in range(8):
        eng.submit_action("p_jorge", gid, "free_query", "q", cid, request_id=f"r{i}")
    assert len(store.get("player", "p_jorge")[0]["requests"]) <= config.REQUEST_KEEP


# ---------------------------------------------------------------- TLR-03-015
def test_the_response_schema_accepts_a_good_answer_and_rejects_a_malformed_one():
    good = {"status": "ok", "handling": "answered", "state_changes": [], "events": [], "errors": [],
            "results": {"c": [{"kind": "own", "language": "en", "facts": [{"kind": "scene", "text": "x"}],
                               "prompts": [{"id": "q", "type": "next", "text": "?", "options": []}]}]}}
    assert schema.check(good) == []
    assert schema.check({"status": "maybe"}) and schema.check({"results": {}})
    bad = dict(good, results={"c": {"kind": "own"}}, state_changes=[{"op": "explode", "entity": "game", "id": "g"}])
    problems = schema.check(bad)
    assert any("results.c" in p for p in problems) and any("explode" in p for p in problems)


def _fake_models(sent, refuse_schema):
    class Models:
        def generate_content(self, model, contents, config):
            sent.append(config.response_json_schema)
            if refuse_schema and config.response_json_schema is not None:
                raise Exception("400 INVALID_ARGUMENT: response_json_schema is not supported")
            um = type("U", (), {"prompt_token_count": 10, "cached_content_token_count": 4, "candidates_token_count": 2, "thoughts_token_count": 1})()
            return type("R", (), {"text": "{}", "usage_metadata": um})()
    return type("C", (), {"models": Models()})()


def test_gemini_is_asked_for_the_schema_and_stops_asking_if_it_is_refused(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_STRUCTURED_OUTPUT", True)
    sent = []
    gm = GeminiGM(usage=None)
    monkeypatch.setattr(gm, "_get", lambda: _fake_models(sent, True))
    assert gm.call("sys", "{}", tier="light") == "{}"
    assert sent[0] is not None and sent[1] is None, "the first try carries the schema, the second does not"
    assert gm.last_meta["tokens_in"] == 10 and gm.last_meta["tokens_cached"] == 4 and gm.last_meta["schema_disabled"]
    gm.call("sys", "{}", tier="light")
    assert sent[2] is None, "after a refusal the schema is not sent again"


def test_structured_output_can_be_switched_off(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_STRUCTURED_OUTPUT", False)
    sent = []
    gm = GeminiGM(usage=None)
    monkeypatch.setattr(gm, "_get", lambda: _fake_models(sent, False))
    gm.call("s", "{}", tier="light")
    assert sent == [None]


def test_structured_output_is_off_by_default():
    """The schema in server/schema.py leaves the objects of the contract empty (see its docstring): it must not be sent unless asked for."""
    assert config.GEMINI_STRUCTURED_OUTPUT is False and GeminiGM(usage=None)._structured is False
