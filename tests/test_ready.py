"""TLR-01-012: a player who has played enough tells the engine "ready to pass turn". No more actions from that character this turn;
when every active player is ready the turn closes before its formal time."""
import pytest

from server.engine import EngineError
from server.gm import GMUnavailable

from test_engine import ADV, game_pkg, start_solo, world  # noqa: F401  (the fixture)


def party(eng, n=2):
    pkg = eng.create_game("p_a", ADV, language="en")["package"]
    gid = eng.submit_package("p_a", pkg["task_id"], game_pkg(players_expected=n))["game_id"]
    cids = {}
    for i, p in enumerate(["p_a", "p_b", "p_c"][:n]):
        if p != "p_a":
            eng.join_game(p, gid)
        cids[p] = eng.generate_character(p, gid, "pregen", pregen_id=["pregen_test_pc", "pregen_test_b", "pregen_test_c"][i])["deliveries"][0]["character_id"]
    return gid, cids


def ready(eng, p, gid, cid, value=True):
    return eng.submit_action(p, gid, "ready", "", cid, {"ready": value})


def test_ready_is_recorded_without_the_ai_master_and_the_turn_waits_for_the_others(world):
    eng, store, gm, clock = world
    gid, c = party(eng)
    calls = len(gm.calls)
    out = ready(eng, "p_a", gid, c["p_a"])
    assert out["handling"] == "answered" and out["ready_to_pass"] is True and out["players_ready"] == 1 and out["players_active"] == 2
    assert len(gm.calls) == calls, "no AI Master call"
    assert store.get("game", gid)[0]["clock"]["turn"] == 1
    assert store.get("character", c["p_a"])[0]["participation"]["ready_turn"] == 1


def test_when_every_active_player_is_ready_the_turn_closes_at_once(world):
    eng, store, gm, clock = world
    gid, c = party(eng)
    ready(eng, "p_a", gid, c["p_a"])
    out = ready(eng, "p_b", gid, c["p_b"])
    assert out["handling"] == "resolved_turn" and out["turn_resolved"] is True
    game, _ = store.get("game", gid)
    assert game["clock"]["turn"] == 2 and [t["status"] for t in game["turns"]] == ["resolved", "open"]


def test_a_ready_character_sends_no_more_actions_say_or_message_but_may_ask(world):
    eng, store, gm, clock = world
    gid, c = party(eng)
    ready(eng, "p_a", gid, c["p_a"])
    for kind, payload in (("action", {}), ("say", {"to": c["p_b"]}), ("message", {"to": "npc_x", "channel": "letter"})):
        with pytest.raises(EngineError) as e:
            eng.submit_action("p_a", gid, kind, "hello", c["p_a"], payload)
        assert "ready to pass the turn" in str(e.value) and "withdraw" in str(e.value)
    assert eng.submit_action("p_a", gid, "free_query", "", c["p_a"], {"topic": "inventory"})["level"] == 2
    assert eng.submit_action("p_a", gid, "thread_note", "remember", c["p_a"], {"type": "idea", "text": "x"})["handling"]
    eng.submit_action("p_b", gid, "action", "search the desk", c["p_b"])      # the other player can still act


def test_withdrawing_lets_the_character_act_again_and_the_turn_does_not_close(world):
    eng, store, gm, clock = world
    gid, c = party(eng)
    ready(eng, "p_a", gid, c["p_a"])
    out = ready(eng, "p_a", gid, c["p_a"], False)
    assert out["ready_to_pass"] is False and out["players_ready"] == 0
    assert eng.submit_action("p_a", gid, "action", "search the desk", c["p_a"])["handling"] == "autonomous"
    ready(eng, "p_b", gid, c["p_b"])
    assert store.get("game", gid)[0]["clock"]["turn"] == 1, "p_a is not ready"


def test_a_solo_player_who_is_ready_closes_the_turn(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    out = ready(eng, "p_jorge", gid, cid)
    assert out["handling"] == "resolved_turn" and store.get("game", gid)[0]["clock"]["turn"] == 2


def test_a_player_who_is_away_or_paused_does_not_hold_the_turn_back(world):
    eng, store, gm, clock = world
    gid, c = party(eng)
    ch, v = store.get("character", c["p_b"])
    ch["participation"]["status"] = "away"
    store.put("character", c["p_b"], ch, v, {"game_id": gid, "player_id": "p_b", "is_alive": True})
    out = ready(eng, "p_a", gid, c["p_a"])
    assert out["handling"] == "resolved_turn" and out["players_active"] == 1


def test_the_new_turn_starts_with_nobody_ready(world):
    eng, store, gm, clock = world
    gid, c = party(eng)
    ready(eng, "p_a", gid, c["p_a"])
    ready(eng, "p_b", gid, c["p_b"])
    t = eng.submit_action("p_a", gid, "free_query", "", c["p_a"], {"topic": "time"})["answer"]
    assert t["turn"] == 2 and t["ready_to_pass"] is False
    assert eng.submit_action("p_a", gid, "action", "search the desk", c["p_a"])["handling"] == "autonomous"


def test_ready_is_not_a_missed_turn_and_is_shown_in_time_others_and_sync(world):
    eng, store, gm, clock = world
    gid, c = party(eng)
    ready(eng, "p_a", gid, c["p_a"])
    t = eng.submit_action("p_a", gid, "free_query", "", c["p_a"], {"topic": "time"})["answer"]
    assert t["ready_to_pass"] is True
    others = eng.submit_action("p_b", gid, "free_query", "", c["p_b"], {"topic": "others"})["answer"]["characters"]
    assert others[0]["ready_to_pass"] is True
    assert eng.get_character("p_a", gid, c["p_a"])["character"]["time"]["ready_to_pass"] is True
    ready(eng, "p_b", gid, c["p_b"])
    ch = store.get("character", c["p_a"])[0]
    assert ch["participation"]["missed_turns"] == 0 and ch["participation"]["status"] == "active"


def test_if_the_ai_master_is_down_when_the_last_player_is_ready_nothing_is_lost(world):
    eng, store, gm, clock = world
    gid, c = party(eng)
    ready(eng, "p_a", gid, c["p_a"])

    def down(system, user, tier="light"):
        raise GMUnavailable("503")
    gm.call = down
    out = ready(eng, "p_b", gid, c["p_b"])
    assert out["ready_to_pass"] is True and out["turn_resolved"] is False and "could not be reached" in out["message"]
    assert store.get("game", gid)[0]["clock"]["turn"] == 1


def test_ready_needs_an_active_game_and_a_character(world):
    eng, store, gm, clock = world
    pkg = eng.create_game("p_a", ADV, language="en")["package"]
    gid = eng.submit_package("p_a", pkg["task_id"], game_pkg(players_expected=2))["game_id"]
    with pytest.raises(EngineError):
        ready(eng, "p_a", gid, None)
