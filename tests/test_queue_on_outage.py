"""TLR-03-009, 07-009, 07-004: when the AI Master cannot answer (Gemini down, or its quota used up), an `action` is saved for the turn close instead of
failing, and the player is told so plainly. Other requests fail with a clear message and nothing lost."""
import json

import pytest

from server.engine import AIMasterBusy, GeminiTrouble
from server.gm import GMBusy, GMUnavailable
from server.tools import _safe

from test_engine import start_solo, world  # noqa: F401  (the fixture)


def down(error):
    def call(system, user, tier="light"):
        raise error
    return call


@pytest.mark.parametrize("error, why", [(GMUnavailable("503 UNAVAILABLE"), "Gemini is not answering"), (GMBusy("request quota"), "quota")])
def test_an_action_is_saved_for_the_turn_close_when_the_ai_master_cannot_answer(world, error, why):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    gm.call = down(error)
    out = eng.submit_action("p_jorge", gid, "action", "I will visit Tom in the afternoon.", cid)
    assert out["handling"] == "queued" and out["deferred"] is True
    assert why in out["message"] and "Nothing was lost" in out["message"]
    game, _ = store.get("game", gid)
    assert out["turn_closes_at"] == game["clock"]["turn_closes"]
    sa, _ = store.get("submit_action", f"{gid}:1")
    rec = sa["actions"][cid][-1]
    assert rec["raw_text"] == "I will visit Tom in the afternoon." and rec["parsed"] is None and rec["needs_parse"] is True and rec["status"] == "queued"
    ch, _ = store.get("character", cid)
    assert rec["id"] in ch["turn_state"]["queued_action_ids"] and ch["participation"]["last_submitted_turn"] == 1


def test_the_turn_close_receives_the_saved_action_to_parse(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    gm.call = down(GMUnavailable("503"))
    eng.submit_action("p_jorge", gid, "action", "I will visit Tom.", cid)
    seen = []

    def back(system, user, tier="light"):
        env = json.loads(user)
        seen.append(env)
        from test_engine import standard_gm
        return json.dumps(standard_gm(env, 1))
    gm.call = back
    assert eng.resolve_turn(gid)["resolved"] is True
    acts = seen[0]["submit_action"]["actions"][cid]
    assert acts[0]["needs_parse"] is True and acts[0]["raw_text"] == "I will visit Tom." and acts[0]["parsed"] is None
    sa, _ = store.get("submit_action", f"{gid}:1")
    assert sa["actions"][cid][0]["status"] == "resolved"


def test_a_deferred_action_does_not_try_an_early_close_with_the_ai_master_down(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    gm.call = down(GMUnavailable("503"))
    calls = []
    real = eng.resolve_turn
    eng.resolve_turn = lambda g: calls.append(g) or real(g)
    eng.submit_action("p_jorge", gid, "action", "I wait.", cid)
    assert calls == []


def test_the_same_request_id_is_not_saved_twice(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    gm.call = down(GMUnavailable("503"))
    a = eng.submit_action("p_jorge", gid, "action", "I wait.", cid, request_id="r1")
    b = eng.submit_action("p_jorge", gid, "action", "I wait.", cid, request_id="r1")
    assert b["duplicate_request"] == "r1" and a["deferred"] is True
    sa, _ = store.get("submit_action", f"{gid}:1")
    assert len(sa["actions"][cid]) == 1


def test_a_query_cannot_wait_for_the_turn_and_says_so_plainly(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    gm.call = down(GMUnavailable("503"))
    with pytest.raises(GeminiTrouble):
        eng.submit_action("p_jorge", gid, "free_query", "Look around.", cid)
    gm.call = down(GMBusy("request quota used up"))
    with pytest.raises(AIMasterBusy):
        eng.submit_action("p_jorge", gid, "free_query", "Look around.", cid)
    out = _safe(lambda: eng.submit_action("p_jorge", gid, "free_query", "Look around.", cid))()
    assert out["ai_master_busy"] is True and out["retry_in_minutes"] == 2 and "nothing was lost" in out["next_step"]
    sa, _ = store.get("submit_action", f"{gid}:1")
    assert sa["actions"][cid] == [], "nothing was stored for a query"


def test_a_normal_action_is_unchanged(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    out = eng.submit_action("p_jorge", gid, "action", "I will visit Tom in the afternoon.", cid)
    assert out["handling"] == "resolved_turn" and "deferred" not in out  # a solo game closes its turn at once
    sa, _ = store.get("submit_action", f"{gid}:1")
    assert sa["actions"][cid][0]["parsed"] and "needs_parse" not in sa["actions"][cid][0]
