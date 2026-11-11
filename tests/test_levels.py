"""TLR-01-007 to 01-011, 01-016, 03-007, 03-008, 08-005: every answer says the level at which it was really answered, the server
decides the level by fixed rules, and the level of each request is counted."""
import pytest

from server import levels
from server.gm import GMUnavailable, Usage

from test_engine import start_solo, world  # noqa: F401  (the fixture)
from test_ready import party, ready  # noqa: F401
from test_queue_on_outage import down  # noqa: F401


def test_the_fixed_rules_give_the_expected_level_from_the_request_alone():
    assert levels.expected_level("free_query", {"topic": "inventory"}) == 2
    assert levels.expected_level("free_query", {"topic": " TIME "}) == 2
    assert levels.expected_level("free_query", {"topic": "nonsense"}) == 3
    assert levels.expected_level("free_query") == 3
    assert levels.expected_level("ready") == 2 and levels.expected_level("say") == 2 and levels.expected_level("character_confirm") == 2
    assert levels.expected_level("action") == 3
    assert levels.expected_level("message") == 4


def test_a_database_answer_is_level_2_and_needs_no_explanation(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    out = eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": "time"})
    assert out["level"] == 2 and out["level_name"] == "database" and "level_reason" not in out and "expected_level" not in out


def test_an_action_resolved_at_once_is_level_3(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    out = eng.submit_action("p_jorge", gid, "action", "search the desk", cid)
    assert out["handling"] == "autonomous" and out["level"] == 3 and "level_reason" not in out


def test_a_free_query_without_a_topic_goes_to_the_ai_master_at_level_3(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    out = eng.submit_action("p_jorge", gid, "free_query", "what do I remember about Tom?", cid)
    assert out["level"] == 3


def test_ready_is_level_2_until_it_closes_the_turn_and_then_level_4(world):
    eng, store, gm, clock = world
    gid, c = party(eng)
    first = ready(eng, "p_a", gid, c["p_a"])
    assert first["handling"] == "answered" and first["level"] == 2
    last = ready(eng, "p_b", gid, c["p_b"])
    assert last["handling"] == "resolved_turn" and last["level"] == 4 and last["level_name"] == "turn close"
    assert "closed the turn" in last["level_reason"]


def test_say_is_level_2(world):
    eng, store, gm, clock = world
    gid, c = party(eng)
    out = eng.submit_action("p_a", gid, "say", "hello", c["p_a"], {"to": c["p_b"]})
    assert out["level"] == 2


def test_an_action_queued_because_the_ai_master_is_down_is_level_4_with_the_reason(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    gm.call = down(GMUnavailable("503"))
    out = eng.submit_action("p_jorge", gid, "action", "I will visit Tom.", cid)
    assert out["deferred"] is True and out["level"] == 4
    assert "could not be reached" in out["level_reason"] and "level 4 instead of level 3" in out["level_reason"]


def test_the_client_can_declare_a_level_and_is_told_when_the_server_decided_otherwise(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    out = eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": "inventory"}, expected_level=3)
    assert out["level"] == 2 and out["expected_level"] == 3
    assert "decides the level by fixed rules" in out["level_reason"] and "level 2, not level 3" in out["level_reason"]
    same = eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": "inventory"}, expected_level=2)
    assert same["level"] == 2 and same["expected_level"] == 2 and "level_reason" not in same


def test_a_nonsense_declared_level_is_ignored(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    out = eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": "time"}, expected_level=9)
    assert out["level"] == 2 and "expected_level" not in out


def test_a_retried_request_id_returns_the_same_level(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    a = eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": "time"}, "r-1")
    b = eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": "time"}, "r-1")
    assert a["level"] == b["level"] == 2 and b["duplicate_request"] == "r-1"


def test_every_request_is_counted_by_the_level_it_was_answered_at(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    usage = gm.usage = Usage(store, lambda: clock["t"])
    eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": "time"})
    eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": "time"}, expected_level=3)
    eng.submit_action("p_jorge", gid, "action", "search the desk", cid)
    s = usage.stats()
    req = s["requests_by_level_kind"]
    assert req["2|free_query"]["count"] == 2 and req["2|free_query"]["declared_wrong"] == 1 and req["2|free_query"]["moved"] == 0
    assert req["3|action"]["count"] == 1
    assert s["requests_by_game_level"][gid]["2"] == 2 and s["requests_by_game_level"][gid]["3"] == 1


def test_a_request_that_moved_level_is_counted_as_moved(world):
    eng, store, gm, clock = world
    usage = gm.usage = Usage(store, lambda: clock["t"])
    gid, c = party(eng)
    ready(eng, "p_a", gid, c["p_a"])
    ready(eng, "p_b", gid, c["p_b"])          # expected level 2, answered at level 4
    req = usage.stats()["requests_by_level_kind"]
    assert req["4|ready"]["count"] == 1 and req["4|ready"]["moved"] == 1 and req["2|ready"]["count"] == 1
