"""TLR-01-009, level 2: answers the engine gives from the database, without calling the AI Master and without using its quota.
Every answer is built from player-safe views (see redact.py): what the character holds, knows, or can see. Nothing here creates a fact."""
import copy
from datetime import datetime

from . import redact

# topic -> what the player asked for
TOPICS = {
    "time": "time left in the turn, the in-game day and Block, Blocks already used",
    "inventory": "what the character carries, stores, has lent or lost",
    "sheet": "pools, ratings and derived values",
    "conditions": "injuries and conditions",
    "location": "where the character is and which other characters are there",
    "relationships": "attitude and trust toward people the character has dealt with",
    "threads": "open tasks, ideas and questions the player wrote down",
    "knowledge": "what the character knows: facts, clues, documents, journal, people met",
    "messages": "messages sent to or by the character and speech heard",
    "others": "public status of the other characters in the game",
    "settings": "standing orders and safety settings",
}


def _seconds_left(game, now):
    closes = (game.get("clock") or {}).get("turn_closes")
    if not closes:
        return None
    return max(0, int((datetime.fromisoformat(closes.replace("Z", "+00:00")) - now).total_seconds()))


# TLR-07-011: what the client does with the answer. The world is narrated; the mechanics are stated plainly, outside the narration.
PRESENTATION = {"inventory": "narrate", "location": "narrate", "relationships": "narrate", "knowledge": "narrate", "messages": "narrate", "others": "narrate",
                "conditions": "narrate", "time": "plain", "sheet": "plain", "threads": "plain", "settings": "plain"}


def _ready(game, c):
    """TLR-01-012: the character has told the engine it is ready to pass this turn."""
    return (c.get("participation") or {}).get("ready_turn") == (game.get("clock") or {}).get("turn") and game.get("phase") == "active"


def answer(topic, game, character, characters, now, span_blocks):
    """The answer for `topic` (a key of TOPICS), or None if the topic is unknown."""
    c = character
    kn = c.get("knowledge") or {}
    if topic == "time":
        clock = game.get("clock") or {}
        used = list((c.get("turn_state") or {}).get("blocks_used") or [])
        return {"turn": clock.get("turn"), "day": clock.get("day"), "block": clock.get("block"), "turn_closes": clock.get("turn_closes"),
                "seconds_left": _seconds_left(game, now), "blocks_used": used, "blocks_left": max(0, span_blocks - len(used)),
                "turn_span": (game.get("settings") or {}).get("turn_span"),
                "ready_to_pass": _ready(game, c)}
    if topic == "inventory":
        return {"inventory": copy.deepcopy(c.get("inventory", [])), "means": c.get("means")}
    if topic == "sheet":
        return {"sheet": copy.deepcopy(c.get("sheet")), "ruleset_state": copy.deepcopy(c.get("ruleset_state"))}
    if topic == "conditions":
        return {"conditions": copy.deepcopy(c.get("conditions", [])), "status": c.get("status"), "is_alive": c.get("is_alive", True),
                "run_notes": copy.deepcopy(c.get("run_notes"))}
    if topic == "location":
        return {"location": c.get("location"), "others_here": redact.others_here(c, characters)}
    if topic == "relationships":
        return {"relationships": copy.deepcopy(c.get("relationships", []))}
    if topic == "threads":
        return {"threads": [t for t in kn.get("threads", []) if t.get("status") == "open"], "spend_offers": copy.deepcopy(kn.get("spend_offers", []))}
    if topic == "knowledge":
        return {"facts": copy.deepcopy(kn.get("facts", [])), "clues": copy.deepcopy(kn.get("clues", [])), "documents": copy.deepcopy(kn.get("documents", [])),
                "journal": kn.get("journal", ""), "met": copy.deepcopy(kn.get("met", [])),
                "story_summary": (c.get("client_sync") or {}).get("story_summary", "")}
    if topic == "messages":
        mine = [m for m in game.get("messages", []) if c["id"] in (m.get("visible_to") or []) or m.get("to") == c["id"] or m.get("from") == c["id"]]
        return {"messages": [{k: m.get(k) for k in ("id", "from", "to", "channel", "text", "sent_turn", "deliver_turn", "status")} for m in mine[-20:]]}
    if topic == "others":
        here = {o["character_id"] for o in redact.others_here(c, characters)}
        return {"characters": [{"character_id": o["id"], "name": o.get("name"), "is_alive": o.get("is_alive", True), "status": o.get("status"),
                                "in_the_same_place": o["id"] in here, "ready_to_pass": _ready(game, o)}
                               for o in characters if o["id"] != c["id"]]}
    if topic == "settings":
        return {"settings": copy.deepcopy(c.get("settings")), "language": c.get("language"), "narration_verbosity": redact.verbosity(game, c)}
    return None
