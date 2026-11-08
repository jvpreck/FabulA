"""TLR-03-010 and 05-007 (instructions in sections by request kind), TLR-03-011 (provider-side caching), TLR-03-012 (a request sees its own slice)."""
import json
import re
import time
from datetime import datetime, timezone

import pytest

from server import config, files, prompt
from server.db import MemoryStore
from server.engine import Engine
from server.gm import GeminiGM, Usage
from test_engine import ScriptedGM, standard_gm, start_solo, CHECK

TAGGED = """# Doc
Intro.

## A. Always
text a

## B. Setup only
<!-- for: setup -->
text b
### B.1 child of b
text b1

## C. Turn or play
<!-- for: turn, play -->
text c

## D. Pictures
<!-- for: turn; needs: illustrations -->
text d

## E. Generators
<!-- needs: generated -->
text e
```
# this is a code line, not a heading
```
text e2

## F. After
text f
"""


def headings(text):
    return [l for l in text.split("\n") if l.startswith("## ")]


# ------------------------------------------------------------------ TLR-05-007 / 03-010
def test_sections_are_chosen_by_profile_and_flags():
    f = files.select_sections
    assert "<!--" not in f(TAGGED, None), "the tags never reach the AI Master"
    assert headings(f(TAGGED, None)) == headings(TAGGED), "no profile: nothing is left out"
    assert headings(f(TAGGED, "setup")) == ["## A. Always", "## B. Setup only", "## F. After"]
    assert headings(f(TAGGED, "play")) == ["## A. Always", "## C. Turn or play", "## F. After"]
    assert headings(f(TAGGED, "turn")) == ["## A. Always", "## C. Turn or play", "## F. After"]
    assert headings(f(TAGGED, "turn", ("illustrations",))) == ["## A. Always", "## C. Turn or play", "## D. Pictures", "## F. After"]
    assert "## E. Generators" in f(TAGGED, "play", ("generated",))


def test_a_left_out_section_takes_its_sub_sections_and_nothing_else():
    out = files.select_sections(TAGGED, "play")
    assert "text b1" not in out and "child of b" not in out and "text a" in out and "text f" in out


def test_a_hash_line_inside_a_code_block_is_not_a_heading():
    out = files.select_sections(TAGGED, "play", ("generated",))
    assert "this is a code line" in out and "text e2" in out and "text f" in out
    out = files.select_sections(TAGGED, "play")  # section E is out: its code block goes with it and F survives
    assert "this is a code line" not in out and "text e2" not in out and "text f" in out


@pytest.mark.parametrize("name", ["protocol.md", "oracles.md", "state_and_messages.md"])
def test_the_real_documents_lose_their_tags_and_nothing_else_in_the_full_prompt(name):
    raw = files.split_front_matter(files.gm_file(name))[1]
    full = files.select_sections(raw, None)
    assert "<!-- for:" not in full and "<!-- needs:" not in full
    tags = len(re.findall(r"(?m)^<!-- (?:for|needs):", raw))
    assert full.count("\n") == raw.count("\n") - tags, "only the tag lines are removed"


def test_each_profile_gets_the_sections_its_requests_need_and_is_smaller():
    def sys(profile, flags=()):
        return prompt.system_prompt("fear_itself", {"source": "file", "id": "test_adventure"}, None, profile, flags)
    full, turn, play, setup = sys(None), sys("turn"), sys("play"), sys("setup")
    assert "### 5.2 `resolve_turn` mode" in turn and "### 5.2 `resolve_turn` mode" not in play
    assert "### 5.3 Autonomous actions" in play and "### 5.3 Autonomous actions" not in turn
    assert "### 4.1 Setup" in setup and "### 4.1 Setup" not in play and "### 4.1 Setup" not in turn
    assert "### 4.2 Request kinds" in play and "### 4.2 Request kinds" not in turn
    assert "Character intake and validation" in setup and "Character intake and validation" not in play
    assert "### 5.6 Illustrations" not in turn and "### 5.6 Illustrations" in sys("turn", ("illustrations",))
    assert "## 3. Adventure seeds" not in play and "## 3. Adventure seeds" in sys("play", ("generated",))
    for p in (turn, play, setup):
        assert len(p) < len(full) * 0.93, "each profile must save at least 7 percent of the instructions"
        assert "<!--" not in p
    for marker in ("DOCUMENT 1: PROTOCOL", "DOCUMENT 2: ORACLES", "DOCUMENT 3: STATE CONTRACT", "DOCUMENT 4: THE RULESET"):
        assert marker in play


def test_the_engine_sends_the_profile_of_the_request(monkeypatch):
    CHECK["fail_next"] = 0
    gm = ScriptedGM(standard_gm)
    eng = Engine(MemoryStore(), gm, now_fn=lambda: datetime(2026, 11, 1, 9, tzinfo=timezone.utc))
    gid, cid = start_solo(eng)
    gm.calls.clear()
    eng.submit_action("p_jorge", gid, "free_query", "what do I know?", cid)
    eng.resolve_turn(gid)
    play_system, turn_system = gm.calls[0][0], gm.calls[1][0]
    assert "### 5.3 Autonomous actions" in play_system and "### 5.2 `resolve_turn` mode" not in play_system
    assert "### 5.2 `resolve_turn` mode" in turn_system and "### 5.3 Autonomous actions" not in turn_system
    assert Engine._profile("intake", {"kind": "join"}) == "setup" and Engine._profile("intake", {"kind": "character_submission"}) == "setup"
    assert Engine._profile("intake", {"kind": "action"}) == "play" and Engine._profile("resolve_turn", None) == "turn"
    monkeypatch.setattr(config, "PROMPT_SLIM", False)
    assert Engine._profile("intake", {"kind": "action"}) is None


# ------------------------------------------------------------------ TLR-03-011
class FakeCaches:
    def __init__(self, outcome=None):
        self.created, self.outcome = [], outcome

    def create(self, model, config):
        self.created.append((model, config))
        if self.outcome:
            raise self.outcome
        return type("C", (), {"name": f"cachedContents/{len(self.created)}"})()


class FakeModels:
    def __init__(self, sent, fail_cached_once=False):
        self.sent, self.fail_cached_once = sent, fail_cached_once

    def generate_content(self, model, contents, config):
        self.sent.append(config)
        if config.cached_content and self.fail_cached_once:
            self.fail_cached_once = False
            raise Exception("404 NOT_FOUND: CachedContent not found (or permission denied)")
        um = type("U", (), {"prompt_token_count": 100, "cached_content_token_count": 90 if config.cached_content else 0,
                            "candidates_token_count": 2, "thoughts_token_count": 1})()
        return type("R", (), {"text": "{}", "usage_metadata": um})()


def fake_client(caches, models):
    return type("Client", (), {"caches": caches, "models": models})()


BIG = "x" * (config.CACHE_MIN_CHARS + 10)


def make_gm(monkeypatch, caches, models, store=None):
    gm = GeminiGM(usage=Usage(store or MemoryStore()))
    monkeypatch.setattr(gm, "_get", lambda: fake_client(caches, models))
    return gm


def test_the_instructions_are_stored_once_and_each_request_refers_to_them(monkeypatch):
    sent, caches = [], FakeCaches()
    gm = make_gm(monkeypatch, caches, FakeModels(sent))
    gm.call(BIG, "{}", tier="light")
    assert gm.last_meta["cache"] == "created" and len(caches.created) == 1
    assert sent[0].cached_content == "cachedContents/1" and not sent[0].system_instruction, "the text is not sent again"
    gm.call(BIG, '{"a":1}', tier="light")
    assert gm.last_meta["cache"] == "hit" and len(caches.created) == 1
    assert gm.last_meta["tokens_cached"] == 90
    gm.call(BIG + "y", "{}", tier="light")  # other instructions: another copy
    assert len(caches.created) == 2


def test_another_server_instance_reuses_the_copy_through_the_database(monkeypatch):
    store, sent, caches = MemoryStore(), [], FakeCaches()
    make_gm(monkeypatch, caches, FakeModels(sent), store).call(BIG, "{}", tier="light")
    second = make_gm(monkeypatch, caches, FakeModels(sent), store)
    second.call(BIG, "{}", tier="light")
    assert len(caches.created) == 1 and second.last_meta["cache"] == "hit"


def test_a_copy_about_to_expire_is_replaced(monkeypatch):
    sent, caches = [], FakeCaches()
    gm = make_gm(monkeypatch, caches, FakeModels(sent))
    gm.call(BIG, "{}", tier="light")
    for e in gm._caches.values():
        e["expires"] = time.time() + 30
    gm.call(BIG, "{}", tier="light")
    assert len(caches.created) == 2 and gm.last_meta["cache"] == "created"


def test_a_provider_that_refuses_caching_is_left_alone_for_a_while(monkeypatch):
    sent, caches = [], FakeCaches(outcome=Exception("403 PERMISSION_DENIED: caching is not available on the free tier"))
    gm = make_gm(monkeypatch, caches, FakeModels(sent))
    assert gm.call(BIG, "{}", tier="light") == "{}"
    assert gm.last_meta["cache"].startswith("off") and sent[0].system_instruction == BIG and not sent[0].cached_content
    gm.call(BIG, "{}", tier="light")
    assert len(caches.created) == 1, "no second attempt within the waiting time"
    gm._cache_off_until = 0
    gm.call(BIG, "{}", tier="light")
    assert len(caches.created) == 2, "tried again after the waiting time"


def test_a_copy_that_has_disappeared_is_replaced_without_failing_the_request(monkeypatch):
    sent, caches = [], FakeCaches()
    models = FakeModels(sent, fail_cached_once=True)
    gm = make_gm(monkeypatch, caches, models)
    assert gm.call(BIG, "{}", tier="light") == "{}"
    assert gm.last_meta["cache"].startswith("stale") and sent[-1].system_instruction == BIG
    gm.call(BIG, "{}", tier="light")
    assert len(caches.created) == 2 and gm.last_meta["cache"] == "created"


def test_short_instructions_and_the_off_switch_do_not_use_the_cache(monkeypatch):
    sent, caches = [], FakeCaches()
    gm = make_gm(monkeypatch, caches, FakeModels(sent))
    gm.call("short", "{}", tier="light")
    monkeypatch.setattr(config, "GEMINI_CONTEXT_CACHE", "off")
    gm.call(BIG, "{}", tier="light")
    assert caches.created == [] and all(c.system_instruction for c in sent)


def test_cache_outcomes_are_counted_in_the_call_statistics():
    store = MemoryStore()
    u = Usage(store, lambda: datetime(2026, 11, 1, 9, tzinfo=timezone.utc))
    for c in ("created", "hit", "hit", "off: 403 free tier"):
        u.record({"level": 3, "tier": "light", "mode": "intake", "kind": "action", "game_id": "g", "cache": c})
    row = next(iter(u.stats()["by_level_tier_mode_kind"].values()))
    assert (row["cache_created"], row["cache_hit"], row["cache_off"]) == (1, 2, 1)
    assert "403" in u.stats()["cache_note"]


# ------------------------------------------------------------------ TLR-03-012
def make_game_with_noise(eng, store, gid, cid):
    """A running game whose record holds events and messages of other characters, and other places."""
    g, v = store.get("game", gid)
    c, _ = store.get("character", cid)
    here = (c.get("location") or {}).get("id")
    g["events"] = [
        {"id": "e_mine", "turn": 1, "location_id": "loc_far", "participants": [cid], "witnesses": [], "summary": "mine"},
        {"id": "e_here", "turn": 1, "location_id": here, "participants": ["c_other"], "witnesses": [], "summary": "same place"},
        {"id": "e_far", "turn": 1, "location_id": "loc_far", "participants": ["c_other"], "witnesses": [], "summary": "elsewhere"},
        {"id": "e_pub", "turn": 1, "location_id": "loc_far", "participants": ["c_other"], "witnesses": [], "summary": "public", "visibility": "all"},
    ]
    g["messages"] = [{"id": "m1", "from": cid, "to": "c_other", "text": "hi"}, {"id": "m2", "from": "c_a", "to": "c_b", "text": "secret"}]
    g["turns"][-1]["results"] = {cid: ["own result"], "c_other": ["somebody else's result"]}
    store.put("game", gid, g, v)


def test_a_request_sees_the_events_messages_and_results_that_concern_the_character():
    CHECK["fail_next"] = 0
    store, gm = MemoryStore(), ScriptedGM(standard_gm)
    eng = Engine(store, gm, now_fn=lambda: datetime(2026, 11, 1, 9, tzinfo=timezone.utc))
    gid, cid = start_solo(eng)
    make_game_with_noise(eng, store, gid, cid)
    gm.calls.clear()
    eng.submit_action("p_jorge", gid, "free_query", "hello", cid)
    env = gm.calls[0][1]
    assert {e["id"] for e in env["game"]["events"]} == {"e_mine", "e_here", "e_pub"}
    assert [m["id"] for m in env["game"]["messages"]] == ["m1"]
    assert all(set(t.get("results", {})) <= {cid} for t in env["game"]["turns"])
    gm.calls.clear()
    eng.resolve_turn(gid)
    env = gm.calls[0][1]
    assert {e["id"] for e in env["game"]["events"]} >= {"e_far"} and len(env["game"]["messages"]) == 2, "the turn close sees everything"


def test_narrowing_can_be_switched_off(monkeypatch):
    monkeypatch.setattr(config, "ENVELOPE_RELEVANT", False)
    CHECK["fail_next"] = 0
    store, gm = MemoryStore(), ScriptedGM(standard_gm)
    eng = Engine(store, gm, now_fn=lambda: datetime(2026, 11, 1, 9, tzinfo=timezone.utc))
    gid, cid = start_solo(eng)
    make_game_with_noise(eng, store, gid, cid)
    gm.calls.clear()
    eng.submit_action("p_jorge", gid, "free_query", "hello", cid)
    assert len(gm.calls[0][1]["game"]["events"]) == 4


def world(n):
    npcs = [{"id": f"npc_{i}", "name": f"Person Number{i}", "bio": "b" * 400} for i in range(n)]
    states = [{"npc_id": f"npc_{i}", "location_id": "loc_a" if i == 0 else "loc_z", "met_by": ["c_me"] if i == 1 else []} for i in range(n)]
    locs = [{"id": f"loc_{k}", "name": f"Place {k}", "desc": "d" * 400} for k in "az"]
    lstates = [{"location_id": f"loc_{k}", "visited_by": []} for k in "az"]
    return npcs, states, locs, lstates


def test_a_large_world_is_narrowed_to_where_the_character_is_whom_they_met_and_what_is_named():
    me = {"id": "c_me", "location": {"id": "loc_a"}, "knowledge": {}, "relationships": [], "events": []}
    npcs, states, locs, lstates = world(40)
    req = {"kind": "action", "text": "I look for Person Number7 and call npc_9"}
    n, ns, lo, ls = Engine._narrow_world(me, req, {"events": []}, npcs, states, locs, lstates)
    assert {x["id"] for x in n} == {"npc_0", "npc_1", "npc_7", "npc_9"} and len(ns) == 4
    assert [x["id"] for x in lo] == ["loc_a"] and len(ls) == 1


def test_a_small_world_is_sent_whole():
    me = {"id": "c_me", "location": {"id": "loc_a"}}
    npcs, states, locs, lstates = world(3)
    out = Engine._narrow_world(me, {"kind": "action", "text": "x"}, {"events": []}, npcs, states, locs, lstates)
    assert out == (npcs, states, locs, lstates)
