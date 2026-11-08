"""Player-safe views. Everything a client may see is built here, from the database, never from the GM's text."""
import copy


def public_npc(definition: dict | None, state: dict | None, met: bool):
    d = definition or {}
    return {"id": d.get("id") or (state or {}).get("npc_id"), "name": d.get("name"), "role": d.get("role"), "trait": d.get("trait")} if met else None


def others_here(character: dict, characters: list):
    loc = (character.get("location") or {}).get("id")
    out = []
    for c in characters:
        if c["id"] == character["id"] or not c.get("is_alive", True):
            continue
        if loc and (c.get("location") or {}).get("id") == loc:
            out.append({"character_id": c["id"], "name": c.get("name")})
    return out


def sync_block(game: dict, character: dict, characters: list) -> dict:
    clock = game.get("clock") or {}
    kn = character.get("knowledge") or {}
    return {
        "version": (character.get("client_sync") or {}).get("version", 0),
        "time": {"turn": clock.get("turn"), "day": clock.get("day"), "block": clock.get("block"),
                 "turn_closes": clock.get("turn_closes")},
        "character": {
            "id": character["id"], "name": character.get("name"), "is_alive": character.get("is_alive", True),
            "status": character.get("status"), "language": character.get("language"),
            "concept": character.get("concept"), "occupation": character.get("occupation"),
            "sheet": copy.deepcopy(character.get("sheet")), "conditions": character.get("conditions", []),
            "location": character.get("location"), "inventory": character.get("inventory", []),
            "means": character.get("means"), "relationships": character.get("relationships", []),
            "run_notes": character.get("run_notes"), "ruleset_state": character.get("ruleset_state"),
            "death": character.get("death"),
        },
        "knowledge": copy.deepcopy(kn),
        "settings": copy.deepcopy(character.get("settings")),
        "recent_events": (character.get("events") or [])[-15:],
        "decisions": character.get("decisions", []),
        "pending": {
            "unclaimed_spend_offers": kn.get("spend_offers", []),
            "open_threads": [t for t in kn.get("threads", []) if t.get("status") == "open"],
            "open_prompts": character.get("open_prompts", []),
        },
        "others_here": others_here(character, characters),
        "story_summary_turn": (character.get("client_sync") or {}).get("story_summary_turn", 0),
    }


def character_view(game, character, characters):
    v = sync_block(game, character, characters)
    v["story_summary"] = (character.get("client_sync") or {}).get("story_summary", "")
    v["participation"] = character.get("participation")
    return v


def game_summary(game: dict) -> dict:
    s = game.get("settings") or {}
    return {"id": game["id"], "title": game.get("title"), "phase": game.get("phase"), "format": game.get("format"),
            "adventure_id": game.get("adventure_id"), "ruleset_id": game.get("ruleset_id"),
            "settings": {k: s.get(k) for k in ("turn_interval_hours", "turn_close_hour", "turn_timezone", "turn_span", "early_close", "pvp", "lethality", "illustrations")},
            "clock": game.get("clock"), "roster": game.get("roster", [])}
