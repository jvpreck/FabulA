"""TLR-01-009: level 2. A free query with a known topic is answered from the database: the AI Master is not called."""
import pytest

from server import level2

from test_engine import start_solo, world  # noqa: F401  (the fixture)


@pytest.fixture
def silent(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    calls = []

    def call(system, user, tier="light"):
        calls.append(1)
        raise AssertionError("the AI Master must not be called for a level 2 answer")
    gm.call = call
    return eng, store, gid, cid, calls


@pytest.mark.parametrize("topic", sorted(level2.TOPICS))
def test_every_topic_is_answered_without_the_ai_master(silent, topic):
    eng, store, gid, cid, calls = silent
    out = eng.submit_action("p_jorge", gid, "free_query", "what do I know?", cid, {"topic": topic})
    assert out["handling"] == "answered" and out["level"] == 2 and out["topic"] == topic
    assert isinstance(out["answer"], dict) and out["answer"]
    assert "AI Master was not asked" in out["note"] and not calls


def test_time_gives_the_seconds_left_and_the_blocks_left(silent):
    eng, store, gid, cid, calls = silent
    game, _ = store.get("game", gid)
    a = eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": "time"})["answer"]
    assert a["turn"] == 1 and a["turn_closes"] == game["clock"]["turn_closes"] and a["seconds_left"] > 0
    assert a["blocks_left"] == 4 and a["blocks_used"] == []


def test_the_inventory_and_location_come_from_the_character_record(silent):
    eng, store, gid, cid, calls = silent
    ch, _ = store.get("character", cid)
    inv = eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": "inventory"})["answer"]["inventory"]
    assert inv == ch.get("inventory", [])
    loc = eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": "location"})["answer"]
    assert loc["location"] == ch.get("location") and loc["others_here"] == []


def test_the_topic_is_case_insensitive_and_unknown_topics_go_to_the_ai_master(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    out = eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": " Time "})
    assert out["level"] == 2
    seen = []
    orig = gm.call

    def spy(system, user, tier="light"):
        seen.append(1)
        return orig(system, user, tier)
    gm.call = spy
    try:
        eng.submit_action("p_jorge", gid, "free_query", "What is the weather like?", cid, {"topic": "weather"})
    except Exception:
        pass
    assert seen, "an unknown topic is a question for the AI Master"


def test_a_level_2_answer_changes_no_game_state(silent):
    eng, store, gid, cid, calls = silent
    before = (store.get("game", gid)[0], store.get("character", cid)[0])
    eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": "knowledge"})
    after = (store.get("game", gid)[0], store.get("character", cid)[0])
    assert before == after


def test_others_shows_only_public_status(silent):
    eng, store, gid, cid, calls = silent
    out = eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": "others"})["answer"]
    assert out == {"characters": []}  # a solo game
    assert not calls


def test_the_level_2_answer_is_counted_in_the_statistics(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)

    class Usage:
        rows = []

        def record(self, e):
            self.rows.append(e)
    gm.usage = Usage()
    eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": "time"})
    assert Usage.rows and Usage.rows[0]["level"] == 2 and Usage.rows[0]["kind"] == "time" and Usage.rows[0]["tier"] == "database"
