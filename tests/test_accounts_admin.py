import json
import os
import pytest
from datetime import datetime, timezone

from server import admin, files, config
from server.db import MemoryStore
from server.engine import Engine, EngineError
from test_engine import ScriptedGM, standard_gm, ADV, new_game, CHECK

PG = {"p_jorge": "pregen_test_pc", "p_ana": "pregen_test_b", "p_b": "pregen_test_b", "p_third": "pregen_test_c"}   # one pregenerated character per player



@pytest.fixture
def world():
    store = MemoryStore()
    gm = ScriptedGM(standard_gm)
    eng = Engine(store, gm, now_fn=lambda: datetime(2026, 11, 1, 9, tzinfo=timezone.utc))
    CHECK["fail_next"] = 0
    CHECK["payloads"].clear()
    return eng, store


def test_register_and_authenticate(world):
    eng, store = world
    r = eng.register_player("Ana", "es")
    key = r["player_key"]
    assert key.startswith("pk_") and len(key) >= 40
    pid = eng.authenticate(key)
    assert pid.startswith("p_") and key not in json.dumps(store.t)       # only the hash is stored
    assert eng.key_hash(key) in store.t["key"]
    assert store.get("player", pid)[0]["display_name"] == "Ana"
    # two players, two different keys and ids
    r2 = eng.register_player("Bob")
    assert eng.authenticate(r2["player_key"]) != pid


@pytest.mark.parametrize("bad", ["", "p_jorge", "pk_short", "pk_" + "x" * 43, None, 5])
def test_impersonation_is_refused(world, bad):
    eng, store = world
    pid = eng.authenticate(eng.register_player("Ana")["player_key"])
    with pytest.raises(EngineError):
        eng.authenticate(bad)
    # knowing someone's internal id is not enough
    with pytest.raises(EngineError):
        eng.authenticate(pid)


def test_setup_guide_has_every_requested_topic(world):
    eng, _ = world
    g = eng.setup_guide()
    keys = {t["key"] for t in g["topics"]}
    assert keys == {"start", "choose", "character", "commands", "ticks", "autonomous", "death", "mechanics"}
    for k in keys:
        one = eng.setup_guide(k)
        assert one["guide"].strip() and one["title"]
    assert "player key" in eng.setup_guide("start")["guide"].lower()
    assert "24 hours" in eng.setup_guide("ticks")["guide"]
    assert "Moderate" in eng.setup_guide("death")["guide"]
    with pytest.raises(EngineError):
        eng.setup_guide("nope")
    # the guide is independent of any ruleset or adventure
    assert not any(w in g["guide"] for w in ("GUMSHOE", "Fear Itself", "Danvers", "Eleanor"))


def test_list_games_private_and_open(world):
    eng, store = world
    a = eng.authenticate(eng.register_player("Ana")["player_key"])
    b = eng.authenticate(eng.register_player("Bob")["player_key"])
    priv = new_game(eng, a, ADV)["game_id"]
    openg = new_game(eng, a, ADV, settings={"visibility": "open"})["game_id"]
    la = eng.list_games(a)
    assert {g["game_id"] for g in la["my_games"]} == {priv, openg} and la["open_games"] == []
    lb = eng.list_games(b)
    assert lb["my_games"] == [] and [g["game_id"] for g in lb["open_games"]] == [openg]
    assert "roster" not in json.dumps(lb) and "gm_state" not in json.dumps(lb)
    eng.join_game(b, openg)
    assert [g["game_id"] for g in eng.list_games(b)["my_games"]] == [openg]


def test_admin_delete_game_cascades(world):
    eng, store = world
    a = eng.authenticate(eng.register_player("Ana")["player_key"])
    gid = new_game(eng, a, ADV)["game_id"]
    eng.generate_character(a, gid, "pregen", pregen_id=PG.get(a, "pregen_test_pc"))
    assert store.find("character", game_id=gid)
    out = admin.run(eng, "delete_game", {"game_id": gid})
    assert out["deleted"] == gid and out["records"]["character"] == 1
    assert store.get("game", gid)[0] is None and not store.find("character", game_id=gid)
    p = store.get("player", a)[0]
    assert gid not in p["games"] and p["characters"] == []
    with pytest.raises(EngineError):
        admin.run(eng, "delete_game", {"game_id": gid})
    with pytest.raises(EngineError):
        admin.run(eng, "nonsense", {})


def test_admin_delete_adventure_player_and_reset_key(world):
    eng, store = world
    r = eng.register_player("Ana")
    a = eng.authenticate(r["player_key"])
    store.put("adventure", "adv_gen_1", {"id": "adv_gen_1", "title": "x", "owner_player_id": a}, 0, {"owner_player_id": a})
    gid = new_game(eng, a, "adv_gen_1")["game_id"] if False else None
    out = admin.run(eng, "delete_adventure", {"adventure_id": "adv_gen_1"})
    assert out["deleted"] == "adv_gen_1" and store.get("adventure", "adv_gen_1")[0] is None
    with pytest.raises(EngineError):
        admin.run(eng, "delete_adventure", {"adventure_id": ADV})      # a file adventure lives in the private repo
    gid = new_game(eng, a, ADV)["game_id"]
    new = admin.run(eng, "reset_player_key", {"player_id": a})
    assert new["player_key"] != r["player_key"] and new["old_keys_removed"] == 1
    with pytest.raises(EngineError):
        eng.authenticate(r["player_key"])                                # the old key is dead
    assert eng.authenticate(new["player_key"]) == a                      # same player, same games
    assert gid in store.get("player", a)[0]["games"]
    with pytest.raises(EngineError):
        admin.run(eng, "delete_player", {"player_id": a})                # hosts a game
    admin.run(eng, "delete_player", {"player_id": a, "force": True})
    assert store.get("player", a)[0] is None and not store.find("key", player_id=a)


def test_adventure_files_come_from_the_private_repo(monkeypatch):
    monkeypatch.setattr(config, "ADVENTURES_DIR", None)
    files.clear_adventure_cache()
    seen = []
    listing = [{"name": "one.md", "type": "file"}, {"name": "README.md", "type": "file"}, {"name": "notes.txt", "type": "file"}, {"name": "sub", "type": "dir"}]
    text = "---\nid: one\ntitle: One\nruleset: fear_itself\n---\n# PART A\nx\n# PART B\nsecret"

    def fake(url, raw=False):
        seen.append(url)
        return (text if raw else json.dumps(listing)).encode()
    monkeypatch.setattr(files, "_github_get", fake)
    got = files.adventure_files()
    assert list(got) == ["one"] and got["one"]["meta"]["file"] == "rpg_adventures/one.md"
    assert "jvpreck/rpg_adventures" in seen[0]
    n = len(seen)
    files.adventure_files()
    assert len(seen) == n                                                # cached
    # repository unreachable: the cached copy is served
    monkeypatch.setattr(files, "_github_get", lambda *a, **k: (_ for _ in ()).throw(files.AdventureSourceError("down")))
    files._cache["at"] = 0
    assert list(files.adventure_files()) == ["one"]
    files.clear_adventure_cache()
    with pytest.raises(files.AdventureSourceError):
        files.adventure_files()
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.undo()
    with pytest.raises(files.AdventureSourceError):
        files._github_get("https://api.github.com/x")                   # no token: refuses without calling out


def test_catalog_never_leaks_adventure_secrets(world):
    eng, store = world
    a = eng.authenticate(eng.register_player("Ana")["player_key"])
    out = json.dumps(eng.list_adventures(a))
    assert "The mill is only a mill" not in out and "PART B" not in out


def test_player_safe_text_is_part_a_only():
    body = "# Title\n\n> intro with a spoiler: the villain is the miller\n\n# PART A: SHEET\nsafe\n\n# PART B: GM\nsecret"
    assert files.player_safe_part(body) == "# PART A: SHEET\nsafe"
    assert files.player_safe_part("no markers at all") == ""
    assert files.player_safe_part("# PART B\nx\n# PART A\ny") == ""


def test_start_here_and_every_guide_exist_and_name_real_tools(world):
    import asyncio
    from server import files
    from server.app import build_mcp
    eng = world[0]
    sh = eng.start_here()
    assert "register_player" in sh["start_here"] and {g["name"] for g in sh["guides"]} == set(files.GUIDES)
    tool_names = {t.name for t in asyncio.run(build_mcp(eng).list_tools())}
    import re
    for name in files.GUIDES:
        g = eng.guide(name)
        text = g.get("guide") or ""
        assert text and g.get("name", "players-guide") in (name, "players-guide") or name == "players-guide"
        for tool in set(re.findall(r"`([a-z_]+)\(", sh["start_here"] + text)):
            assert tool in tool_names, (name, tool)
    assert eng.guide("")["guides"] and "free-text" not in eng.guide("player-client-guide")["guide"]
    assert "player key" in eng.guide("players-guide", "start")["guide"].lower()
    with pytest.raises(EngineError):
        eng.guide("nope")


def test_errors_say_what_to_do_next():
    import asyncio
    from server.app import build_mcp
    eng = Engine(MemoryStore(), None)
    out = asyncio.run(build_mcp(eng).call_tool("get_results", {"player_key": "pk_bad"}))
    text = json.dumps(out, default=str)
    assert "next_step" in text and "start_here" in text
