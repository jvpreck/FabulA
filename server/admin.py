"""Host-only administration. NOT an MCP tool: players cannot reach it.

It is served at POST /internal/admin and needs `Authorization: Bearer $ADMIN_SECRET` (a secret that is not the players' key and not the
cron secret). The intended way to use it is the GitHub Actions workflow `.github/workflows/admin.yml`: only people with write access to
the repository can run it, and the secret lives in the repository's Actions secrets. Players are readers only, so they cannot.
"""
import secrets

from .db import doc_key
from .engine import EngineError, iso

COMMANDS = {
    "list_games": "no arguments",
    "get_game": "game_id",
    "list_players": "no arguments",
    "list_adventures": "no arguments (generated adventures stored in the database)",
    "delete_game": "game_id: removes the game, its characters, NPC and location states, per-turn actions and tasks",
    "close_game": "game_id: ends the game and keeps its data",
    "delete_adventure": "adventure_id [force]: removes a generated adventure; refused while games use it unless force is true",
    "delete_player": "player_id [force]: removes the player and their characters, and takes them out of games",
    "reset_player_key": "player_id: issues a new secret key (shown once) when a player lost theirs or it leaked",
    "gm_usage": "no arguments: AI Master requests used today per model, and the limits",
    "generate_images": "no arguments: draws the queued pictures now (the scheduler also does it after each run)",
    "list_rulesets": "no arguments: imported rulesets with status pending, approved or rejected",
    "review_ruleset": "ruleset_id: what a pending ruleset contains (fields, headings, checklist rows, suspicious wording flags), not the full text",
    "approve_ruleset": "ruleset_id: makes an imported ruleset available to everyone",
    "reject_ruleset": "ruleset_id [reason]: keeps it but never makes it available",
    "delete_ruleset": "ruleset_id [force]: removes an imported ruleset; refused while adventures or games use it unless force is true",
    "purge_tasks": "no arguments: removes expired, finished and failed work packages",
}


def _need(args, key):
    v = args.get(key)
    if not v or not isinstance(v, str):
        raise EngineError(f"missing argument {key}")
    return v


def run(engine, command, args=None):
    args = args or {}
    fn = globals().get("_cmd_" + str(command))
    if not fn:
        raise EngineError("unknown command. Commands: " + ", ".join(COMMANDS))
    return fn(engine, args)


def _delete_game_records(engine, gid):
    st = engine.store
    n = {}
    for kind in ("character", "npc_state", "location_state", "submit_action"):
        rows = st.find(kind, game_id=gid)
        for d, _ in rows:
            st.delete(kind, doc_key(kind, d))
        n[kind] = len(rows)
    imgs = st.find("image", game_id=gid)
    for d, _ in imgs:
        for path in [d.get("path"), *(d.get("refs") or {}).values()]:
            if path and engine.images:
                try:
                    engine.images.storage.delete(path)
                except Exception:
                    pass
        st.delete("image", d["id"])
    n["image"] = len(imgs)
    for kind in ("npc", "location"):
        rows = st.find(kind, game_id=gid)
        for d, _ in rows:
            st.delete(kind, doc_key(kind, d))
        n[kind] = len(rows)
    t = 0
    for d, _ in st.find("task"):
        if (d.get("params") or {}).get("game_id") == gid:
            st.delete("task", d["id"])
            t += 1
    n["task"] = t
    st.delete("game", gid)
    return n


def _unlink_player_game(engine, gid):
    ws = engine._ws()
    for d, _ in engine.store.find("player"):
        if gid in d.get("games", []):
            p = ws.get("player", d["id"])
            p["games"] = [g for g in p["games"] if g != gid]
            p["characters"] = [c for c in p.get("characters", []) if c.get("game_id") != gid]
            ws.touch("player", d["id"])
    ws.commit()


def _cmd_list_games(engine, args):
    out = []
    for g, _ in engine.store.find("game"):
        out.append({"game_id": g["id"], "title": g.get("title"), "phase": g.get("phase"), "adventure_id": g.get("adventure_id"),
                    "players": len(g.get("roster", [])), "turn": (g.get("clock") or {}).get("turn"),
                    "turn_closes": (g.get("clock") or {}).get("turn_closes"), "visibility": (g.get("settings") or {}).get("visibility")})
    return {"games": out}


def _cmd_get_game(engine, args):
    g, _ = engine.store.get("game", _need(args, "game_id"))
    if g is None:
        raise EngineError("unknown game")
    return {"game": g, "characters": [c for c, _ in engine.store.find("character", game_id=g["id"])]}


def _cmd_list_players(engine, args):
    return {"players": [{"player_id": d["id"], "display_name": d.get("display_name"), "games": d.get("games", []),
                         "registered_at": d.get("registered_at")} for d, _ in engine.store.find("player")]}


def _cmd_list_adventures(engine, args):
    return {"adventures": [{"id": d["id"], "title": d.get("title"), "owner_player_id": d.get("owner_player_id"), "source": d.get("source")}
                           for d, _ in engine.store.find("adventure")]}


def _cmd_delete_game(engine, args):
    gid = _need(args, "game_id")
    if engine.store.get("game", gid)[0] is None:
        raise EngineError("unknown game")
    n = _delete_game_records(engine, gid)
    _unlink_player_game(engine, gid)
    return {"deleted": gid, "records": n}


def _cmd_close_game(engine, args):
    gid = _need(args, "game_id")
    ws = engine._ws()
    g = engine._game(ws, gid)
    g["phase"] = "closed"
    ws.touch("game", gid)
    ws.commit()
    return {"closed": gid}


def _cmd_delete_adventure(engine, args):
    aid = _need(args, "adventure_id")
    a, _ = engine.store.get("adventure", aid)
    if a is None:
        raise EngineError("that adventure is not in the database. Adventure files live in the private adventures repository: delete or edit them there")
    using = [g["id"] for g, _ in engine.store.find("game") if g.get("adventure_id") == aid]
    if using and not args.get("force"):
        raise EngineError(f"games still use this adventure: {using}. Delete them first or pass force")
    n = 0
    for kind in ("npc", "location"):
        for d, _ in engine.store.find(kind, adventure_id=aid):
            engine.store.delete(kind, doc_key(kind, d))
            n += 1
    engine.store.delete("adventure", aid)
    return {"deleted": aid, "definitions_removed": n, "games_still_referencing": using}


def _cmd_delete_player(engine, args):
    pid = _need(args, "player_id")
    p, _ = engine.store.get("player", pid)
    if p is None:
        raise EngineError("unknown player")
    hosted = [g["id"] for g, _ in engine.store.find("game") if g.get("host_player_id") == pid]
    if hosted and not args.get("force"):
        raise EngineError(f"this player hosts games {hosted}. Delete or close them first, or pass force")
    for c, _ in engine.store.find("character", player_id=pid):
        engine.store.delete("character", c["id"])
    ws = engine._ws()
    for g, _ in engine.store.find("game"):
        if any(r["player_id"] == pid for r in g.get("roster", [])):
            gg = ws.get("game", g["id"])
            gg["roster"] = [r for r in gg["roster"] if r["player_id"] != pid]
            ws.touch("game", g["id"])
    ws.commit()
    for k in _keys_of(engine, pid):
        engine.store.delete("key", k)
    engine.store.delete("player", pid)
    return {"deleted": pid}


def _cmd_reset_player_key(engine, args):
    """The player keeps the same internal id. Their old keys are deleted and one new key is issued."""
    pid = _need(args, "player_id")
    if engine.store.get("player", pid)[0] is None:
        raise EngineError("unknown player")
    ws = engine._ws()
    old = _keys_of(engine, pid)
    key = engine._new_key(ws, pid)
    ws.commit()
    for k in old:
        engine.store.delete("key", k)
    return {"player_id": pid, "player_key": key, "old_keys_removed": len(old),
            "note": "Give this key to the player privately. It is shown only now. The old key no longer works."}


def _keys_of(engine, pid):
    return [d["id"] for d, _ in engine.store.find("key", player_id=pid)]


def _cmd_purge_tasks(engine, args):
    now = iso(engine.now())
    n = 0
    for d, _ in engine.store.find("task"):
        if d.get("status") != "open" or d.get("expires_at", "") < now:
            engine.store.delete("task", d["id"])
            n += 1
    return {"purged": n}


def _cmd_gm_usage(engine, args):
    from .gm import Usage
    return {"usage": Usage(engine.store, engine.now_fn).today(), "note": "Counts are per provider day (Pacific time)."}


def _cmd_generate_images(engine, args):
    return engine.process_images()


def _ruleset(engine, args):
    rid = _need(args, "ruleset_id")
    r, _ = engine.store.get("ruleset", rid)
    if r is None:
        raise EngineError("that ruleset is not an imported one. Rulesets in the rulesets/ folder are files: edit or delete them in the repository")
    return rid, r


def _cmd_list_rulesets(engine, args):
    return {"rulesets": [{"id": d["id"], "title": d["meta"].get("title"), "status": d["status"], "owner_player_id": d.get("owner_player_id"),
                          "chars": len(d["body"]), "created_at": d.get("created_at")} for d, _ in engine.store.find("ruleset")]}


def _cmd_review_ruleset(engine, args):
    from . import tasks
    rid, r = _ruleset(engine, args)
    problems, info = tasks.ruleset_checks(r["meta"], r["body"])
    return {"id": rid, "status": r["status"], "meta": r["meta"], "source_notes": r.get("source_notes"), "notes": r.get("notes"),
            "checks": info, "problems": problems, "note": "Read the full text in the gm_rulesets table (Supabase) before approving."}


def _cmd_approve_ruleset(engine, args):
    rid, r = _ruleset(engine, args)
    if rid in __import__("server.files", fromlist=["rulesets"]).rulesets():
        raise EngineError("a ruleset file with that id exists; it would take precedence. Reject or delete this one")
    ws = engine._ws()
    d = ws.get("ruleset", rid)
    d["status"] = "approved"
    d["approved_at"] = iso(engine.now())
    ws.touch("ruleset", rid)
    ws.commit()
    return {"approved": rid}


def _cmd_reject_ruleset(engine, args):
    rid, r = _ruleset(engine, args)
    ws = engine._ws()
    d = ws.get("ruleset", rid)
    d["status"] = "rejected"
    d["reject_reason"] = str(args.get("reason") or "")[:300]
    ws.touch("ruleset", rid)
    ws.commit()
    return {"rejected": rid}


def _cmd_delete_ruleset(engine, args):
    rid, r = _ruleset(engine, args)
    using = [g["id"] for g, _ in engine.store.find("game") if g.get("ruleset_id") == rid]
    using += [a["id"] for a, _ in engine.store.find("adventure") if a.get("ruleset_id") == rid]
    if using and not args.get("force"):
        raise EngineError(f"games or adventures still use this ruleset: {using}. Delete them first or pass force")
    engine.store.delete("ruleset", rid)
    return {"deleted": rid, "still_referencing": using}
