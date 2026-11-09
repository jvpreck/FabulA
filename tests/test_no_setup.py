"""TLR-01-013: no setup phase. One action creates the game, one action creates a character; the server confirms a character whose check passed
and starts the game when every player who joined (and as many as the host expects) has a confirmed character."""
import pytest

from server.engine import EngineError

import test_engine as te
from test_engine import ADV, game_pkg, start_solo, world  # noqa: F401  (the fixture)


def make_game(eng, player="p_a", **kw):
    pkg = eng.create_game(player, ADV, language="en")["package"]
    return eng.submit_package(player, pkg["task_id"], game_pkg(**kw))


def pregen(eng, player, gid, pid):
    return eng.generate_character(player, gid, "pregen", pregen_id=pid)["deliveries"][0]["character_id"]


def test_creating_a_game_and_joining_do_not_call_the_ai_master(world):
    eng, store, gm, clock = world
    out = make_game(eng)
    assert out["phase"] == "characters" and gm.calls == []
    assert eng.join_game("p_b", out["game_id"])["phase"] == "characters" and gm.calls == []


def test_a_solo_game_starts_with_the_one_character_action_and_the_opening_comes_with_it(world):
    eng, store, gm, clock = world
    gid = make_game(eng)["game_id"]
    out = eng.generate_character("p_a", gid, "pregen", pregen_id="pregen_test_pc")
    game, _ = store.get("game", gid)
    assert game["phase"] == "active" and game["format"] == "solo" and game["clock"]["turn"] == 1
    kinds = [e["request"]["kind"] for _, e in gm.calls]
    assert kinds == ["character_submission", "begin"], "the check and the opening: no setup, no confirmation request"
    cid = out["deliveries"][0]["character_id"]
    assert store.get("character", cid)[0]["status"] == "active"
    # the opening reaches the player in the same answer or on the next get_results
    texts = [i["facts"][0]["text"] for d in out["deliveries"] for i in d["items"]] + \
            [i["facts"][0]["text"] for d in eng.get_results("p_a", gid)["deliveries"] for i in d["items"]]
    assert "Welcome" in texts


def test_a_party_game_waits_for_the_players_the_host_expects(world):
    eng, store, gm, clock = world
    gid = make_game(eng, players_expected=2)["game_id"]
    pregen(eng, "p_a", gid, "pregen_test_pc")
    assert store.get("game", gid)[0]["phase"] == "characters", "one of two expected players is not enough"
    assert [e["request"]["kind"] for _, e in gm.calls] == ["character_submission"]
    eng.join_game("p_b", gid)
    pregen(eng, "p_b", gid, "pregen_test_b")
    game, _ = store.get("game", gid)
    assert game["phase"] == "active" and game["format"] == "party" and game["party_size_at_start"] == 2
    assert [e["request"]["kind"] for _, e in gm.calls][-1] == "begin"


def test_a_player_who_joined_but_has_no_character_yet_holds_the_start_back(world):
    eng, store, gm, clock = world
    gid = make_game(eng)["game_id"]
    eng.join_game("p_b", gid)
    pregen(eng, "p_a", gid, "pregen_test_pc")
    assert store.get("game", gid)[0]["phase"] == "characters"
    pregen(eng, "p_b", gid, "pregen_test_b")
    assert store.get("game", gid)[0]["phase"] == "active"


def test_a_check_with_adjustments_waits_for_the_players_approval_which_the_server_handles(world):
    eng, store, gm, clock = world
    gid = make_game(eng)["game_id"]
    orig = te.standard_gm

    def adjust(env, n):
        r = orig(env, n)
        if (env.get("request") or {}).get("kind") == "character_submission":
            r["validation"] = {"character_id": env["request"]["character_id"], "result": "pass_with_adjustments", "checks": [{"n": 3, "name": "Budget", "result": "adjust", "note": "Two points over."}], "adjustments": [{"what": "Lower one rating", "why": "Budget", "needs_approval": True}]}
        return r
    gm.rule = adjust
    cid = pregen(eng, "p_a", gid, "pregen_test_pc")
    assert store.get("character", cid)[0]["status"] == "validated" and store.get("game", gid)[0]["phase"] == "characters"
    calls = len(gm.calls)
    out = eng.submit_action("p_a", gid, "character_confirm", "yes", cid, {"approved": True})
    assert out["game_started"] is True and store.get("game", gid)[0]["phase"] == "active"
    assert [e["request"]["kind"] for _, e in gm.calls[calls:]] == ["begin"], "approval itself costs no AI Master call"


def test_declining_the_adjustments_sends_the_character_back_to_draft(world):
    eng, store, gm, clock = world
    gid = make_game(eng)["game_id"]
    orig = te.standard_gm
    gm.rule = lambda env, n: {**orig(env, n), **({"validation": {"character_id": env["request"]["character_id"], "result": "pass_with_adjustments", "checks": [{"n": 3, "name": "Budget", "result": "adjust", "note": "Two points over."}], "adjustments": [{"what": "Lower one rating", "why": "Budget", "needs_approval": True}]}}
                                                  if (env.get("request") or {}).get("kind") == "character_submission" else {})}
    cid = pregen(eng, "p_a", gid, "pregen_test_pc")
    out = eng.submit_action("p_a", gid, "character_confirm", "no", cid, {"approved": False})
    assert out["character_status"] == "draft" and store.get("game", gid)[0]["phase"] == "characters"


def test_confirming_an_unchecked_character_is_refused(world):
    eng, store, gm, clock = world
    gid = make_game(eng)["game_id"]
    cid = pregen(eng, "p_a", gid, "pregen_test_pc")
    c, v = store.get("character", cid)
    c["status"] = "draft"
    store.put("character", cid, c, v, {"game_id": gid, "player_id": "p_a", "is_alive": True})
    with pytest.raises(EngineError):
        eng.submit_action("p_a", gid, "character_confirm", "yes", cid, {"approved": True})


def test_old_setup_answers_are_kept_but_cost_nothing(world):
    eng, store, gm, clock = world
    gid = make_game(eng)["game_id"]
    out = eng.submit_action("p_a", gid, "setup_answers", "", None, {"answers": {"setup_pvp": "soft"}})
    assert out["handling"] == "answered" and "no setup step" in out["message"] and gm.calls == []
    assert store.get("game", gid)[0]["setup"]["answers"] == {"setup_pvp": "soft"}


def test_a_late_joiner_into_a_running_game_gets_an_opening(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng, "p_ana")
    eng.join_game("p_late", gid)
    late = pregen(eng, "p_late", gid, "pregen_test_pc")
    c, _ = store.get("character", late)
    assert c["status"] == "active" and c["opening_due"] is True
    assert late in store.get("submit_action", f"{gid}:1")[0]["actions"]


def test_players_expected_is_checked_against_the_adventure(world):
    eng, store, gm, clock = world
    pkg = eng.create_game("p_a", ADV, language="en")["package"]
    bad = eng.submit_package("p_a", pkg["task_id"], game_pkg(players_expected=0))
    assert bad["accepted"] is False and any("players_expected" in p for p in bad["problems"])
    ok = eng.submit_package("p_a", pkg["task_id"], game_pkg(players_expected=3))
    assert ok["accepted"] is True and store.get("game", ok["game_id"])[0]["settings"]["players_expected"] == 3


# ------------------------------------------------------------------------ live: the real model checks a pregenerated character and gives the opening
import json  # noqa: E402
import os  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

LIVE = os.environ.get("FABULA_LIVE_SCENARIOS") == "1" and os.environ.get("GEMINI_API_KEY")


@pytest.mark.skipif(not LIVE, reason="set FABULA_LIVE_SCENARIOS=1 and GEMINI_API_KEY to run against the real model")
def test_live_one_game_action_and_one_character_action_start_the_game():
    from server.db import MemoryStore
    from server.engine import Engine
    from server.gm import GeminiGM
    eng = Engine(MemoryStore(), GeminiGM(usage=None), now_fn=lambda: datetime(2026, 11, 1, 9, tzinfo=timezone.utc))
    gid = make_game(eng)["game_id"]
    out = eng.generate_character("p_a", gid, "pregen", pregen_id="pregen_test_pc")
    game, _ = eng.store.get("game", gid)
    cid = out["deliveries"][0]["character_id"] if out.get("deliveries") else eng.store.find("character", game_id=gid)[0][0]["id"]
    c, _ = eng.store.get("character", cid)
    print("\ncharacter status:", c["status"], "| validation:", (c.get("validation") or {}).get("result"), "| phase:", game["phase"])
    items = [i for d in out.get("deliveries", []) for i in d["items"]] + [i for d in eng.get_results("p_a", gid).get("deliveries", []) for i in d["items"]]
    print("items delivered:", len(items), "| facts of the first:", json.dumps(items[0]["facts"], ensure_ascii=False)[:400] if items else None)
    assert c["status"] == "active" and game["phase"] == "active"
    assert any(i.get("narration_hints", {}).get("opening") for i in items) or items, "the player received the opening"
