"""A character check must end in a verdict. The light model answered one with `validation: {}` and no results: the draft stayed stuck and the player
was told only "see the results". The server now sends such an answer back to the AI Master with the reason."""
from datetime import datetime, timezone

import pytest

from server.db import MemoryStore
from server.engine import Engine, EngineError
from test_engine import ADV, ScriptedGM, standard_gm, new_game, char_pkg, CHECK


def world(validations):
    """A scripted AI Master whose answers to character checks are the given `validation` blocks, in order (None = the standard pass)."""
    queue = list(validations)
    seen = []

    def rule(env, n):
        r = standard_gm(env, n)
        if (env.get("request") or {}).get("kind") == "character_submission":
            seen.append(env.get("previous_errors"))
            v = queue.pop(0) if queue else None
            if v is not None:
                r["validation"] = v
                if v == {} or not v.get("result"):
                    r["state_changes"] = []
                    r["results"] = {}
        return r

    CHECK["fail_next"] = 0
    gm = ScriptedGM(rule)
    eng = Engine(MemoryStore(), gm, now_fn=lambda: datetime(2026, 11, 1, 9, tzinfo=timezone.utc))
    return eng, gm, seen


def submit(eng):
    gid = new_game(eng, "p_jorge", ADV, language="en")["game_id"]
    pkg = eng.generate_character("p_jorge", gid, "generate", concept="a reporter")["package"]
    return gid, eng.submit_package("p_jorge", pkg["task_id"], char_pkg(concept="a reporter"))


def test_an_empty_validation_is_sent_back_and_the_second_answer_is_used():
    eng, gm, seen = world([{}, None])
    gid, out = submit(eng)
    assert out.get("accepted") is True
    assert len(seen) == 2 and seen[0] is None and "validation" in " ".join(seen[1])
    assert len([c for c in gm.calls if (c[1].get("request") or {}).get("kind") == "character_submission"]) == 2


def test_two_empty_answers_stop_with_a_clear_error_and_leave_the_draft_alone():
    eng, gm, seen = world([{}, {}])
    gid = new_game(eng, "p_jorge", ADV, language="en")["game_id"]
    pkg = eng.generate_character("p_jorge", gid, "generate", concept="a reporter")["package"]
    with pytest.raises(EngineError) as e:
        eng.submit_package("p_jorge", pkg["task_id"], char_pkg(concept="a reporter"))
    assert "validation" in str(e.value)
    chars = eng.store.find("character", game_id=gid)
    assert chars and all(c[0]["status"] == "draft" for c in chars)


def test_a_failed_check_must_say_what_failed():
    eng, gm, seen = world([{"result": "fail", "checks": []}, {"result": "fail", "checks": [
        {"n": 3, "name": "Budget", "result": "fail", "note": "Total is 24, budget is 22."}]}])
    gid, out = submit(eng)
    assert len(seen) == 2 and "checks" in " ".join(seen[1])
    assert out.get("accepted") is False and any("Total is 24" in p for p in out["problems"]), "the player gets the reason"


def test_a_verdict_without_a_character_id_is_still_applied_to_the_draft():
    eng, gm, seen = world([{"result": "pass", "checks": []}])
    gid, out = submit(eng)
    assert out.get("accepted") is True and len(seen) == 1
