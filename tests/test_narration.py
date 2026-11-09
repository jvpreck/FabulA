"""TLR-07-010 and 07-011: the verbosity of the client's narration is a setting of each player in each game; the world is narrated, mechanics are plain."""
import pytest

from server import engine as engine_module, level2, redact
from server.engine import EngineError

from test_engine import ADV, game_pkg, start_solo, world  # noqa: F401  (the fixture)


def make_game(eng, player="p_a", **kw):
    pkg = eng.create_game(player, ADV, language="en")["package"]
    return eng.submit_package(player, pkg["task_id"], game_pkg(**kw))["game_id"]


def seat(store, gid, player):
    return next(r for r in store.get("game", gid)[0]["roster"] if r["player_id"] == player)


def test_the_default_is_medium_and_the_host_can_choose_when_the_game_is_made(world):
    eng, store, gm, clock = world
    assert seat(store, make_game(eng), "p_a")["narration_verbosity"] == "medium"
    assert seat(store, make_game(eng, narration_verbosity="low"), "p_a")["narration_verbosity"] == "low"


def test_a_bad_level_is_refused_in_the_package(world):
    eng, store, gm, clock = world
    pkg = eng.create_game("p_a", ADV, language="en")["package"]
    bad = eng.submit_package("p_a", pkg["task_id"], game_pkg(narration_verbosity="loud"))
    assert bad["accepted"] is False and any("narration_verbosity" in p for p in bad["problems"])


def test_players_of_the_same_game_have_their_own_level(world):
    eng, store, gm, clock = world
    gid = make_game(eng, players_expected=2, narration_verbosity="high")
    eng.join_game("p_b", gid, narration_verbosity="low")
    eng.join_game("p_c", gid)
    assert [seat(store, gid, p)["narration_verbosity"] for p in ("p_a", "p_b", "p_c")] == ["high", "low", "medium"]
    with pytest.raises(EngineError):
        eng.join_game("p_d", gid, narration_verbosity="loud")


def test_the_player_default_applies_to_games_made_or_joined_later_not_to_earlier_ones(world):
    eng, store, gm, clock = world
    g1 = make_game(eng)
    eng.set_narration("p_a", "high")
    assert seat(store, g1, "p_a")["narration_verbosity"] == "medium"
    assert seat(store, make_game(eng), "p_a")["narration_verbosity"] == "high"
    g3 = make_game(eng, "p_b")
    eng.join_game("p_a", g3)
    assert seat(store, g3, "p_a")["narration_verbosity"] == "high"


def test_changing_it_for_one_game_changes_only_that_seat(world):
    eng, store, gm, clock = world
    gid = make_game(eng, players_expected=2)
    eng.join_game("p_b", gid)
    out = eng.set_narration("p_b", "low", gid)
    assert out["applies_to"] == "this game" and seat(store, gid, "p_b")["narration_verbosity"] == "low" and seat(store, gid, "p_a")["narration_verbosity"] == "medium"
    with pytest.raises(EngineError):
        eng.set_narration("p_b", "loud", gid)
    with pytest.raises(EngineError):
        eng.set_narration("p_zzz", "low", gid)


def test_it_belongs_to_the_player_so_a_replacement_character_keeps_it(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    eng.set_narration("p_jorge", "high", gid)
    ch, _ = store.get("character", cid)
    game, _ = store.get("game", gid)
    assert redact.verbosity(game, ch) == "high"
    assert redact.verbosity(game, {"player_id": "p_jorge", "id": "c_new"}) == "high", "a new character of the same player"


def test_every_delivery_and_the_sync_block_carry_the_level(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    eng.set_narration("p_jorge", "low", gid)
    out = eng.submit_action("p_jorge", gid, "action", "search the desk", cid)
    assert out["deliveries"] and all(d["narration_verbosity"] == "low" and d["sync"]["narration"]["verbosity"] == "low" for d in out["deliveries"])
    assert eng.get_character("p_jorge", gid, cid)["character"]["narration"]["verbosity"] == "low"


def test_the_settings_topic_and_level_2_answers_say_what_to_narrate_and_what_to_state(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    eng.set_narration("p_jorge", "high", gid)
    s = eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": "settings"})
    assert s["answer"]["narration_verbosity"] == "high" and s["presentation"] == "plain"
    inv = eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": "inventory"})
    assert inv["presentation"] == "narrate" and "narrate it in the voice of the story" in inv["note"]
    assert set(level2.PRESENTATION) == set(level2.TOPICS), "every topic says how to present its answer"


def test_the_brief_tells_the_client_the_levels_and_the_world_and_mechanics_rule():
    b = engine_module.NARRATION_BRIEF
    for needle in ("narration_verbosity", "low:", "medium (the default)", "high:", "WORLD AND MECHANICS", "outside the blockquote", "never handed over as a list"):
        assert needle in b
