import json
from datetime import datetime, timedelta, timezone

import pytest

from server import admin, config
from server.db import MemoryStore
from server.engine import Engine, EngineError
from server.gm import Usage
from server.images import ImageError, ImageService, MemoryImageStorage
from test_engine import ScriptedGM, standard_gm, ADV, new_game, CHECK, game_pkg

PG = {"p_jorge": "pregen_test_pc", "p_ana": "pregen_test_b", "p_b": "pregen_test_b", "p_third": "pregen_test_c"}   # one pregenerated character per player



class Clock:
    def __init__(self):
        self.t = datetime(2026, 11, 1, 9, tzinfo=timezone.utc)

    def __call__(self):
        return self.t


class FakeProvider:
    def __init__(self):
        self.calls = []
        self.sizes = []
        self.fail = False
        self.ok = True

    def configured(self):
        return self.ok

    def generate(self, prompt, width=1024, height=1024, refs=None, timeout=None):
        from PIL import Image
        import io
        self.calls.append(prompt)
        self.sizes.append((width, height, len(refs or [])))
        if self.fail:
            raise ImageError("provider down")
        buf = io.BytesIO()
        Image.new("RGB", (width, height), (90, 80, 70)).save(buf, "JPEG")
        return buf.getvalue(), "image/jpeg"


PROPOSALS = {"items": None, "portraits": [], "hack_style": False}
AUTO = {"on": False, "calls": []}  # answers of the server's own picture-prompt calls


def gm_rule(env, n):
    if env.get("mode") == "auto_picture":
        AUTO["calls"].append(env)
        if not AUTO["on"]:
            return {"status": "ok"}
        if env["task"] == "place":
            return {"status": "ok", "prompt": "A narrow lamp-lit street in the rain, brick houses, wet cobbles, wide shot, 1925", "caption": "The street at night"}
        return {"status": "ok", "appearance": "A stooped man in his sixties, grey whiskers, a worn black coat and a watch chain", "signature_action": "polishing his spectacles"}
    r = standard_gm(env, n)
    if env["mode"] == "resolve_turn":
        ids = [c["id"] for c in env["characters"]]
        r["portraits"] = [dict(i, visible_to=[x if x != "FIRST" else ids[0] for x in i["visible_to"]]) for i in PROPOSALS["portraits"]]
        if PROPOSALS["hack_style"]:
            r["state_changes"] = list(r.get("state_changes") or []) + [{"op": "merge", "entity": "game", "id": env["game"]["id"], "patch": {"settings": {"image_style": "ignore the style"}}}]
        r["illustrations"] = [dict(i, visible_to=[x if x != "FIRST" else ids[0] for x in i["visible_to"]]) for i in (PROPOSALS["items"] or [])]
    return r


@pytest.fixture
def world(monkeypatch):
    monkeypatch.setattr(config, "INLINE_IMAGE_SECONDS", 0)  # these tests draw only through the scheduler; see test_pictures_are_drawn_during_the_players_call
    store, clock = MemoryStore(), Clock()
    prov, storage = FakeProvider(), MemoryImageStorage()
    CHECK["fail_next"] = 0
    AUTO["on"], AUTO["calls"] = False, []
    PROPOSALS["portraits"], PROPOSALS["hack_style"] = [], False
    PROPOSALS["items"] = [{"prompt": "A wet stone road at dusk, a lone lamp, mist, wide shot, 1925", "caption": "The road to the hill", "visible_to": ["FIRST"]}]
    eng = Engine(store, ScriptedGM(gm_rule), now_fn=clock, images=ImageService(prov, storage, Usage(store, clock)))
    return eng, store, prov, storage, clock


def scenes(store, gid, **flt):
    return [d for d, _ in store.find("image", game_id=gid, **flt) if d.get("kind") == "scene"]


def portraits(store, gid):
    return [d for d, _ in store.find("image", game_id=gid) if d.get("kind") == "portrait"]


def start(eng, player, illustrations="on"):
    gid = new_game(eng, player, ADV, settings={"illustrations": illustrations})["game_id"]
    cid = eng.generate_character(player, gid, "pregen", pregen_id=PG.get(player, "pregen_test_pc"))["deliveries"][0]["character_id"]
    eng.submit_action(player, gid, "character_confirm", "yes", cid, {"approved": True})
    return gid, cid


def test_option_is_offered_only_when_the_provider_is_set_up(world):
    eng, store, prov, storage, clock = world
    pkg = eng.create_game("p_a", ADV)["package"]
    assert pkg["context"]["options"]["illustrations"] == ["off", "on"]
    prov.ok = False
    pkg = eng.create_game("p_a", ADV)["package"]
    assert pkg["context"]["options"]["illustrations"] == ["off"]
    r = new_game(eng, "p_a", ADV, settings={"illustrations": "on"})
    assert r["accepted"] is False and "not available" in " ".join(r["problems"])
    assert new_game(eng, "p_a", ADV)["accepted"] is True                      # off is always fine
    plain = Engine(store, ScriptedGM(gm_rule))                                  # no image service at all
    assert plain.create_game("p_a", ADV)["package"]["context"]["options"]["illustrations"] == ["off"]


def test_proposals_are_queued_only_when_on_and_bad_ones_dropped(world):
    eng, store, prov, storage, clock = world
    gid, cid = start(eng, "p_a")
    PROPOSALS["items"] += [{"prompt": "x", "caption": "too short", "visible_to": ["FIRST"]},
                           {"prompt": "A long enough prompt but nobody can see it", "caption": "c", "visible_to": ["c_unknown"]},
                           {"prompt": "A third valid one beyond the per-turn limit", "caption": "c", "visible_to": ["FIRST"]}]
    eng.resolve_turn(gid)
    imgs = scenes(store, gid)
    assert len(imgs) == 2 and all(i["status"] == "pending" and i["visible_to"] == [cid] for i in imgs) and prov.calls == []   # four proposals, two usable
    gid2, _ = start(eng, "p_b", illustrations="off")
    eng.resolve_turn(gid2)
    assert store.find("image", game_id=gid2) == []                              # off: the AI Master's proposals are ignored


def test_illustration_brief_lists_places_without_a_picture(world):
    eng, store, prov, storage, clock = world
    gid, cid = start(eng, "p_a")
    ws = eng._ws()
    game = ws.get("game", gid)
    chars = ws.load_game_characters(gid)
    brief = eng._illustration_brief(ws, game, chars)
    here = chars[0]["location"]["id"]
    assert brief["turn_picture"] is True and brief["max_pictures"] == 4
    assert [x["location_id"] for x in brief["locations_without_picture"]] == [here]
    assert brief["locations_without_picture"][0]["characters_there"] == [cid]
    # a picture that names the place counts as drawn; one that does not leaves it listed
    PROPOSALS["items"] = [{"prompt": "The lodging house hall at night, lamplight, 1925", "caption": "c", "visible_to": ["FIRST"], "location_id": here}]
    eng.resolve_turn(gid)
    assert scenes(store, gid)[0]["location_id"] == here
    ws = eng._ws()
    assert eng._illustration_brief(ws, ws.get("game", gid), ws.load_game_characters(gid))["locations_without_picture"] == []
    gid2, _ = start(eng, "p_b", illustrations="off")
    ws = eng._ws()
    assert eng._illustration_brief(ws, ws.get("game", gid2), ws.load_game_characters(gid2)) is None


def test_draw_deliver_list_and_ask_again(world):
    eng, store, prov, storage, clock = world
    gid, cid = start(eng, "p_a")
    eng.resolve_turn(gid)
    iid = scenes(store, gid)[0]["id"]
    assert eng.get_image("p_a", gid, iid)["status"] == "pending"
    out = eng.process_images(limit=1)
    assert out["generated"] == 0                                                # the first call is the character's face reference
    out = eng.process_images(limit=10)
    assert out["generated"] == 2                                                # the portrait and the scene
    path = f"{gid}/{iid}.jpg"
    assert path in storage.files and "wet stone road" in prov.calls[-1] and prov.calls[-1].startswith("Gothic ink-and-watercolour")
    # the player is told once
    first = eng.get_results("p_a", gid)
    assert iid in [i["image_id"] for i in first["illustrations"]] and {i["kind"] for i in first["illustrations"]} == {"scene", "portrait"}
    assert [i for i in first["illustrations"] if i["image_id"] == iid][0]["caption"] == "The road to the hill"
    for i in first["illustrations"]:                                            # each one comes with a ready link, so the client can list it at once
        assert i["link_text"] == "Illustration: " + i["caption"] and i["url"].endswith(f"expires_in={config.IMAGE_URL_TTL_SECONDS}")
    assert first["illustrations_older"] == 0
    again = eng.get_results("p_a", gid)
    assert again["illustrations"] == [] and again["illustrations_older"] == 2   # the section can still mention the earlier pictures
    # asking for it gives a short-lived link, and again gives another, also later in time
    a = eng.get_image("p_a", gid, iid)
    assert a["link_text"] == "Illustration: The road to the hill"
    assert a["status"] == "ready" and a["url"].endswith(f"expires_in={config.IMAGE_URL_TTL_SECONDS}") and path in a["url"]
    assert a["expires_in_seconds"] == config.IMAGE_URL_TTL_SECONDS
    clock.t += timedelta(days=10)                                               # long after the first link expired
    b = eng.get_image("p_a", gid, iid)
    assert b["status"] == "ready" and path in b["url"] and b["expires_in_seconds"] == config.IMAGE_URL_TTL_SECONDS
    assert iid in [i["image_id"] for i in eng.list_images("p_a", gid)["images"]]
    # the record holds no link and no image bytes
    rec = store.get("image", iid)[0]
    assert "url" not in json.dumps(rec) and rec["path"] == path and rec["status"] == "ready"


def test_only_the_characters_who_saw_it_can_get_it(world):
    eng, store, prov, storage, clock = world
    gid, cid = start(eng, "p_a")
    eng.join_game("p_b", gid)
    eng.generate_character("p_b", gid, "pregen", pregen_id=PG.get("p_b", "pregen_test_pc"))
    eng.resolve_turn(gid)
    eng.process_images(limit=20)
    iid = scenes(store, gid)[0]["id"]
    with pytest.raises(EngineError):
        eng.get_image("p_b", gid, iid)                                          # was not in visible_to
    assert iid not in [i["image_id"] for i in eng.list_images("p_b", gid)["images"]]
    with pytest.raises(EngineError):
        eng.get_image("p_c", gid, iid)                                          # not even in the game
    with pytest.raises(EngineError):
        eng.get_image("p_a", gid, "img_nope")
    assert eng.get_results("p_b", gid)["illustrations"] == []


def test_failures_quota_budget_and_expiry(world):
    eng, store, prov, storage, clock = world
    gid, cid = start(eng, "p_a")
    eng.resolve_turn(gid)
    iid = scenes(store, gid)[0]["id"]
    eng.process_images(limit=4)                                                 # the character's portrait first
    prov.fail = True
    assert eng.process_images()["failed"] == 0 and store.get("image", iid)[0]["status"] == "pending"   # one more try allowed
    assert eng.process_images()["failed"] == 1 and store.get("image", iid)[0]["status"] == "failed"
    assert eng.get_image("p_a", gid, iid)["status"] == "failed"
    # no time left in the function: nothing is drawn, the picture stays queued
    prov.fail = False
    PROPOSALS["items"][0]["caption"] = "second"
    eng.submit_action("p_a", gid, "action", "wait", cid)
    eng.resolve_turn(gid)
    pend = scenes(store, gid, status="pending")
    n = len(prov.calls)
    assert pend                                     # a solo action closes the turn at once, so there can be more than one
    assert eng.process_images(budget_seconds=1) == {"generated": 0, "failed": 0, "dropped": 0} and len(prov.calls) == n
    # the daily guard stops generation but leaves the picture queued
    store.t["usage"].clear()
    u = Usage(store, clock)
    config.GEMINI_LIMITS["image"]["rpd"], saved = 0, config.GEMINI_LIMITS["image"]["rpd"]
    try:
        assert eng.process_images()["generated"] == 0
    finally:
        config.GEMINI_LIMITS["image"]["rpd"] = saved
    assert store.get("image", pend[0]["id"])[0]["status"] == "pending"
    # a picture nobody could draw in three days is dropped
    clock.t += timedelta(days=config.IMAGE_PENDING_DAYS, hours=1)
    assert eng.process_images()["dropped"] == len(pend)


def test_only_the_host_of_the_game_sets_options(world):
    eng, store, prov, storage, clock = world
    gid, cid = start(eng, "p_a", illustrations="off")
    eng.join_game("p_b", gid)
    with pytest.raises(EngineError):
        eng.set_game_options("p_b", gid, "on")
    assert eng.set_game_options("p_a", gid, "on")["illustrations"] == "on"
    with pytest.raises(EngineError):
        eng.set_game_options("p_a", gid, "maybe")
    prov.ok = False
    with pytest.raises(EngineError):
        eng.set_game_options("p_a", gid, "on")                                  # not set up on this server


def test_deleting_a_game_deletes_its_pictures(world):
    eng, store, prov, storage, clock = world
    gid, cid = start(eng, "p_a")
    eng.resolve_turn(gid)
    eng.process_images()
    assert storage.files and store.find("image", game_id=gid)
    out = admin.run(eng, "delete_game", {"game_id": gid})
    assert out["records"]["image"] == 2 and storage.files == {} and store.find("image", game_id=gid) == []
    assert admin.run(eng, "generate_images")["generated"] == 0
    assert admin.run(eng, "gm_usage")["usage"]["image"]["model"] == config.IMAGE_MODEL


def test_scheduler_draws_pictures_after_resolving(world):
    eng, store, prov, storage, clock = world
    gid, cid = start(eng, "p_a")
    clock.t += timedelta(days=2)
    out = eng.resolve_due()
    assert out["images"]["generated"] == 2 and len(storage.files) == 5


STYLE = "Gothic ink-and-watercolour illustration, Massachusetts 1925, damp fog, sodium-yellow lamplight, muted greens and browns."


def test_the_game_style_is_required_set_once_and_immutable(world):
    eng, store, prov, storage, clock = world
    pkg = eng.create_game("p_a", ADV)["package"]
    bad = eng.submit_package("p_a", pkg["task_id"], game_pkg(illustrations="on", image_style="x"))
    assert bad["accepted"] is False and "image_style" in " ".join(bad["problems"])
    gid, cid = start(eng, "p_a")
    style = store.get("game", gid)[0]["settings"]["image_style"]
    PROPOSALS["hack_style"] = True
    eng.resolve_turn(gid)
    assert store.get("game", gid)[0]["settings"]["image_style"] == style        # the AI Master cannot change it
    # turning pictures on later freezes the server default as the game's style
    gid2, _ = start(eng, "p_b", illustrations="off")
    assert not store.get("game", gid2)[0]["settings"].get("image_style")
    assert eng.set_game_options("p_b", gid2, "on")["image_style"] == config.IMAGE_STYLE


def test_character_portrait_is_three_references_then_the_shared_portrait(world):
    from PIL import Image
    import io
    eng, store, prov, storage, clock = world
    gid, cid = start(eng, "p_a")
    out = eng.process_images(limit=10)
    assert out["generated"] == 1 and out["failed"] == 0
    assert prov.sizes == [(512, 512, 0), (512, 512, 0), (512, 512, 0), (1024, 1024, 3)]
    assert all(c.startswith("Gothic ink-and-watercolour") for c in prov.calls)
    assert "face" in prov.calls[0] and "full-body" in prov.calls[1].lower() and "Shown" in prov.calls[2]
    p = portraits(store, gid)[0]
    assert p["status"] == "ready" and p["visible_to"] == [cid] and set(p["refs"]) == {"face", "body", "action"}
    assert sorted(storage.files) == sorted([f"{gid}/ref/{cid}_{k}.jpg" for k in ("face", "body", "action")] + [f"{gid}/{p['id']}.jpg"])
    final = Image.open(io.BytesIO(storage.files[f"{gid}/{p['id']}.jpg"][0]))
    plain = Image.new("RGB", (1024, 1024), (90, 80, 70))
    assert final.size == (1024, 1024) and final.getpixel((512, 1024 - 20)) != plain.getpixel((512, 1024 - 20))   # the name band is drawn
    # the references are never exposed
    got = eng.get_image("p_a", gid, p["id"])
    assert got["kind"] == "portrait" and "/ref/" not in got["url"]
    assert all("ref" not in i["image_id"] for i in eng.list_images("p_a", gid)["images"])
    # the portrait is drawn only once
    eng.process_images(limit=10)
    assert len(prov.calls) == 4


def test_a_portrait_resumes_after_a_failure_without_redoing_references(world):
    eng, store, prov, storage, clock = world
    gid, cid = start(eng, "p_a")
    eng.process_images(limit=2)
    p = portraits(store, gid)[0]
    assert p["stage"] == 2 and p["status"] == "pending"
    eng.process_images(limit=10)
    assert [s[:2] for s in prov.sizes] == [(512, 512)] * 3 + [(1024, 1024)] and portraits(store, gid)[0]["status"] == "ready"


def test_npc_portrait_only_for_those_who_met_them_and_scenes_use_references(world, monkeypatch):
    eng, store, prov, storage, clock = world
    monkeypatch.setitem(config.GEMINI_LIMITS, "image", {"rpd": 500, "rpm": 500})
    gid, cid = start(eng, "p_a")
    eng.join_game("p_b", gid)
    cid_b = eng.generate_character("p_b", gid, "pregen", pregen_id=PG.get("p_b", "pregen_test_pc"))["deliveries"][0]["character_id"]
    eng.submit_action("p_b", gid, "character_confirm", "yes", cid_b, {"approved": True})
    PROPOSALS["portraits"] = [{"subject_id": "npc_warden", "name": "Warden Pike", "appearance": "a stooped old man with a lantern jaw, grey greatcoat",
                               "signature_action": "unlocking a heavy door", "visible_to": ["FIRST"]},
                              {"subject_id": "npc_bad", "name": "No look", "appearance": "short", "visible_to": ["FIRST"]}]
    PROPOSALS["items"] = [dict(PROPOSALS["items"][0], subjects=["npc_warden", cid])]
    eng.resolve_turn(gid)
    npc = [p for p in portraits(store, gid) if p["subject_id"] == "npc_warden"]
    assert len(npc) == 1 and npc[0]["visible_to"] == [cid] and npc[0]["name"] == "Warden Pike"
    assert not [p for p in portraits(store, gid) if p["subject_id"] == "npc_bad"]
    eng.process_images(limit=40)
    assert all(p["status"] == "ready" for p in portraits(store, gid))
    assert npc[0]["id"] not in [i["image_id"] for i in eng.list_images("p_b", gid)["images"]]
    with pytest.raises(EngineError):
        eng.get_image("p_b", gid, npc[0]["id"])
    # the scene was drawn with reference pictures of the two people in it (two people: face and body of each)
    assert prov.sizes[-1] == (1024, 1024, 4) and "Warden Pike" in prov.calls[-1]
    # later the AI Master widens who has met the NPC; it is not drawn again
    n = len(prov.calls)
    PROPOSALS["portraits"] = [{"subject_id": "npc_warden", "visible_to": ["FIRST"]}]
    PROPOSALS["items"] = []
    eng.submit_action("p_a", gid, "action", "wait", cid)
    eng.resolve_turn(gid)
    assert store.get("image", npc[0]["id"])[0]["visible_to"] == [cid] and len(prov.calls) == n


def test_provider_builds_a_multipart_request_with_references(monkeypatch):
    import io, json as _json, base64
    from PIL import Image
    from server import images
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "acct")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "tok")
    seen = {}

    class Resp:
        headers = {"Content-Type": "application/json"}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            buf = io.BytesIO()
            Image.new("RGB", (640, 640), (1, 2, 3)).save(buf, "PNG")
            return _json.dumps({"result": {"image": base64.b64encode(buf.getvalue()).decode()}}).encode()

    def fake(req, timeout=None):
        seen["url"], seen["body"], seen["ct"], seen["auth"] = req.full_url, req.data, req.headers["Content-type"], req.headers["Authorization"]
        return Resp()

    monkeypatch.setattr(images.urllib.request, "urlopen", fake)
    ref = io.BytesIO()
    Image.new("RGB", (512, 512)).save(ref, "JPEG")
    data, ctype = images.CloudflareFlux().generate("a prompt", 1024, 1024, [ref.getvalue(), ref.getvalue()])
    assert seen["url"].endswith("/accounts/acct/ai/run/@cf/black-forest-labs/flux-2-klein-4b") and seen["ct"].startswith("multipart/form-data; boundary=")
    for part in (b'name="prompt"', b'name="width"', b'name="input_image_0"', b'name="input_image_1"'):
        assert part in seen["body"]
    assert b"input_image_2" not in seen["body"] and seen["auth"] == "Bearer tok"
    assert Image.open(io.BytesIO(data)).size == (1024, 1024) and ctype == "image/jpeg"   # resized to the uniform size


def test_name_overlay_handles_accents_and_long_names():
    import io
    from PIL import Image
    from server.images import overlay_name
    buf = io.BytesIO()
    Image.new("RGB", (1024, 1024), (200, 200, 200)).save(buf, "JPEG")
    for name in ("Íñigo de Mendoza y Ñúñez", "A" * 90):
        out = Image.open(io.BytesIO(overlay_name(buf.getvalue(), name)))
        assert out.size == (1024, 1024) and out.getpixel((10, 1020)) != (200, 200, 200)


def test_get_image_inline_returns_the_picture_itself(world):
    import asyncio, io, base64
    from PIL import Image
    from server.app import build_mcp
    eng, store, prov, storage, clock = world
    gid, cid = start(eng, "p_a")
    eng.resolve_turn(gid)
    iid = scenes(store, gid)[0]["id"]
    eng.authenticate = lambda key: "p_a"
    mcp = build_mcp(eng)
    pending = asyncio.run(mcp.call_tool("get_image", {"player_key": "k", "game_id": gid, "image_id": iid, "inline": True}))
    assert "pending" in json.dumps(pending, default=str)                         # nothing to attach yet
    eng.process_images(limit=10)
    out = asyncio.run(mcp.call_tool("get_image", {"player_key": "k", "game_id": gid, "image_id": iid, "inline": True}))
    blocks = out[0] if isinstance(out, tuple) else out
    kinds = [b.type for b in blocks]
    assert kinds == ["text", "image"]
    img = next(b for b in blocks if b.type == "image")
    assert img.mimeType == "image/jpeg"
    assert max(Image.open(io.BytesIO(base64.b64decode(img.data))).size) == config.IMAGE_INLINE_SIZE
    assert "The road to the hill" in blocks[0].text and "url" not in blocks[0].text
    link = asyncio.run(mcp.call_tool("get_image", {"player_key": "k", "game_id": gid, "image_id": iid}))
    assert "expires_in_seconds" in json.dumps(link, default=str)
    # still private: another player cannot get it inline either
    eng.authenticate = lambda key: "p_z"
    bad = asyncio.run(mcp.call_tool("get_image", {"player_key": "k", "game_id": gid, "image_id": iid, "inline": True}))
    assert "error" in json.dumps(bad, default=str)


def test_character_portrait_is_queued_when_the_game_starts(world):
    eng, store, prov, storage, clock = world
    gid, cid = start(eng, "p_a")
    assert [p["subject_id"] for p in portraits(store, gid)] == [cid]  # queued at start, before any scheduler run
    gid2, _ = start(eng, "p_b", illustrations="off")
    assert portraits(store, gid2) == []


def test_illustrations_default_to_on_when_the_server_can_draw():
    from server import tasks
    base = {"lethality": "high", "turn_span": "day", "turn_interval_hours": 24, "pvp": "soft", "visibility": "private"}
    assert tasks.validate_game(base, {}, True) == ["image_style is required when illustrations are on"]
    assert tasks.validate_game(dict(base, image_style="x" * config.STYLE_MIN), {}, True) == []
    assert tasks.validate_game(base, {}, False) == []  # no provider: off
    assert tasks.validate_game(dict(base, illustrations="off"), {}, True) == []


def test_pictures_are_drawn_during_the_players_call(world, monkeypatch):
    eng, store, prov, storage, clock = world
    monkeypatch.setattr(config, "INLINE_IMAGE_SECONDS", 40)
    gid, cid = start(eng, "p_a")
    assert portraits(store, gid) and all(p["status"] == "ready" for p in portraits(store, gid))  # drawn inside the confirm call
    r = eng.get_results("p_a", gid)
    assert r["pending_illustrations"] == 0
    assert {i["status"] for i in eng.list_images("p_a", gid)["images"]} == {"ready"}


def test_server_writes_pictures_for_a_new_place_and_a_first_meeting(world):
    eng, store, prov, storage, clock = world
    AUTO["on"] = True
    gid, cid = start(eng, "p_a")
    sc = scenes(store, gid)
    assert len(sc) == 1 and sc[0]["location_id"] == "loc_tolland_house" and sc[0]["auto"] is True and sc[0]["visible_to"] == [cid]
    assert "lamp-lit street" in sc[0]["prompt"]
    n_calls = len(AUTO["calls"])
    eng.submit_action("p_a", gid, "free_query", "where am I", cid)
    assert len(scenes(store, gid)) == 1 and len(AUTO["calls"]) == n_calls          # a place is drawn once
    ws = eng._ws()
    game = ws.get("game", gid)
    ws.put("npc", f"{gid}:npc_old", {"id": "npc_old", "scope": {"adventure_id": None, "game_id": gid}, "name": "Mr Old", "role": "clerk", "trait": "stooped", "secret": "is the killer"})
    ws.put("npc_state", f"{gid}:npc_old", {"npc_id": "npc_old", "game_id": gid, "status": "active", "met_by": [cid]})
    chars = {c["id"]: c for c in ws.load_game_characters(gid)}
    eng._auto_pictures(ws, game, chars, 1, {})
    ws.commit()
    p = [x for x in portraits(store, gid) if x["subject_id"] == "npc_old"]
    assert len(p) == 1 and p[0]["name"] == "Mr Old" and p[0]["visible_to"] == [cid] and "spectacles" in p[0]["action"]
    call = [c for c in AUTO["calls"] if c["task"] == "npc"][0]
    assert call["npc"] == {"name": "Mr Old", "role": "clerk", "trait": "stooped"} and "killer" not in json.dumps(call)  # no secrets go to the model
    ws = eng._ws()
    eng._auto_pictures(ws, ws.get("game", gid), {c["id"]: c for c in ws.load_game_characters(gid)}, 1, {})  # already has a portrait
    assert len([x for x in portraits(store, gid) if x["subject_id"] == "npc_old"]) == 1


def test_a_place_the_model_could_not_describe_is_not_asked_again(world):
    eng, store, prov, storage, clock = world
    gid, cid = start(eng, "p_a")                                                    # AUTO is off: the model returns nothing usable
    assert scenes(store, gid) == [] and store.get("game", gid)[0]["auto_places"] == ["loc_tolland_house"]
    n = len(AUTO["calls"])
    eng.submit_action("p_a", gid, "free_query", "where am I", cid)
    assert len(AUTO["calls"]) == n


def test_the_narration_brief_asks_for_an_illustrations_available_section():
    from server.engine import NARRATION_BRIEF
    assert "Illustrations available" in NARRATION_BRIEF and "illustrations_older" in NARRATION_BRIEF and "pending_illustrations" in NARRATION_BRIEF
    assert NARRATION_BRIEF.index("notebook entry and status") < NARRATION_BRIEF.index("Illustrations available") < NARRATION_BRIEF.index("next prompt with the possible actions")
