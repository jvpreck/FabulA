"""Work packages for the player's client: instructions, context, expected shape, and validation of what comes back."""
import json
import re

from . import config, files, prompt
from .dice import make_dice

COMMON_NOTE = ("Follow package.instructions step by step in this chat. Talk to the player where the steps say so. "
               "When finished, call submit_package with the arguments in package.submission.")

SCHEMAS = {
    "generate_character": {
        "route": "generate | provided",
        "concept": "string", "name": "string", "occupation": "string", "era_place": "string",
        "appearance": "string or null (only what the player supplied)",
        "portrait": {"appearance": "string, 20 to 600 characters, English: how the character looks, for the portrait", "signature_action": "string, up to 200 characters, English: a characteristic action"}, "personal_goal": "string",
        "risk_factor": "object or null (as the ruleset defines it)",
        "sheet": {"groups": {"<group>": {"<stat>": {"max": "number", "cur": "number (equal to max at the start)"}}},
                  "derived": "object", "unrated": ["string"]},
        "ruleset_state": "object (as the ruleset defines it)",
        "inventory": [{"item": "string", "qty": "number", "notes": "string"}],
        "means": "object", "relationships": [{"with_type": "pc|npc", "with_id": "string", "attitude": "string", "trust": "-3..3", "notes": "string"}],
        "run_notes": {"known_gaps": ["string"]}, "known_background": ["string (what the character knows at the start)"],
        "language": "string", "settings": {"safety": {"fears": [], "pvp_optout": "bool"},
                                           "standing_orders": "object"},
        "traceability": [{"original": "string", "result": "string", "note": "string"}], "notes": "string"},
    "import_ruleset": {
        "id": "string: lowercase letters, digits, underscores, 3 to 40, not in existing_ids", "title": "string", "system": "string", "version": "int",
        "players": {"min": "int", "max": "int"}, "dice": "string", "language": "string", "summary": "string",
        "modules": ["string"], "tone_presets": ["string"],
        "body": "string: the whole ruleset in markdown, without front matter, following contract_text",
        "source_notes": {"document_title": "string", "rights_confirmed": "true (the player may use the document)", "omitted": "string", "house_rulings": ["string"]},
        "notes": "string"},
    "generate_adventure": {
        "title": "string", "generation": "full | emergent | supplied", "era": "string", "place": "string",
        "players": {"min": "int", "max": "int"},
        "recommended": {"turn_span": "day | block", "turn_interval_hours": "int", "lethality": "low | moderate | high"},
        "language": "string", "summary": "string (one player-safe sentence)",
        "content": "string (markdown with # PART A, # PART B, # PART C)",
        "seed": "object (emergent only: truth, hook, stake, antagonist, clock_turns, anchor_npcs[4], first_place, opening_handout)",
        "npcs": [{"id": "npc_...", "name": "string", "role": "string", "trait": "string", "goal": "string", "secret": "string",
                  "base_stats": "object", "base_inventory": "array", "schedule": "string",
                  "main": "bool (true for the antagonist, the anchor NPCs and anyone the plot cannot lose: a late joiner can never take them over)"}],
        "locations": [{"id": "loc_...", "name": "string", "zone": "string", "past_detail": "string", "features": ["string"], "exits": ["loc_..."]}],
        "pregenerated_ids": ["string"], "dice_used": {"d6": "int", "d10": "int", "d20": "int"}, "notes": "string"},
    "create_game": {
        "title": "string", "language": "string", "display_name": "string",
        "lethality": "low | moderate | high", "turn_interval_hours": "int", "turn_span": "day | block",
        "pvp": "none | soft | full", "visibility": "private | open", "narration_verbosity": "low | medium | high (the host's own, default medium)", "players_expected": "int, 1 to the adventure's maximum (default 1): the game starts when that many players have a confirmed character", "illustrations": "off | on",
        "image_style": "string, 40 to 700 characters, English: the fixed look of every picture in this game (required when illustrations is on)", "notes": "string"},
}


def instructions(kind: str) -> str:
    sec = files.client_task_sections()
    return sec["common"] + "\n\n" + sec[kind]


def lethality_help():
    return {"low": "A character cannot die unless the player chooses it at a decision gate.",
            "moderate": "A character can die only after a clear warning and a chance to withdraw.",
            "high": "A character can die after a clear warning, with no gate (the default: deadly, with fair warning)."}


def build_package(kind, task_id, expires_at, context):
    return {"package_version": 1, "task_id": task_id, "task": kind, "expires_at": expires_at,
            "instructions": instructions(kind), "context": context,
            "submission": {"tool": "submit_package", "arguments": {"task_id": task_id, "package": "<an object matching schema>"},
                           "schema": SCHEMAS[kind]},
            "limits": {"max_attempts": config.TASK_MAX_ATTEMPTS}, "note": COMMON_NOTE}


# ------------------------------------------------------------------ contexts
def character_context(game, adventure, route, provided_sheet, replaces, other_names, pregenerated, rulesets=None):
    safe = files.player_safe_part(prompt.adventure_text(adventure))
    return {
        "route": route, "ruleset_id": game["ruleset_id"], "ruleset_text": prompt.ruleset_text(game["ruleset_id"], rulesets),
        "adventure": {"id": adventure["id"], "title": adventure.get("title"), "era": adventure.get("era"),
                      "summary": adventure.get("summary"), "player_safe_text": safe,
                      "pregenerated_ids": pregenerated},
        "game": {"id": game["id"], "phase": game["phase"], "language": game.get("language"),
                 "party_size_at_start": game.get("party_size_at_start"),
                 "expected_party_size": game.get("party_size_at_start") or max(1, len(game.get("roster", []))),
                 "lethality": (game.get("settings") or {}).get("lethality"), "tone_preset": (game.get("settings") or {}).get("tone_preset")},
        "provided_sheet": provided_sheet or None, "replaces": replaces, "other_characters": other_names,
    }


def adventure_context(ruleset_id, seed_text, document_text, generation, language, rulesets=None, seed_info=None):
    rs = files.rulesets() if rulesets is None else rulesets
    extra = {}
    if seed_info:
        extra = {"seed_info": seed_info,
                 "seed_notice": "seed_text is a published seed: it is FULL OF SPOILERS and is for you only. Do not quote, summarize or hint at it in the chat. "
                                "Tell the player only the title, the premise, the era and the player count. Build a complete adventure from it in the module "
                                "format, in your own words, and make it playable by the number of players the seed suggests. If seed_info.modules lists the "
                                "supernatural module, switch it on in the adventure's setup parameters (ruleset section 10) and state in Part B what is real."}
    return {**extra, "ruleset_id": ruleset_id, "ruleset_text": prompt.ruleset_text(ruleset_id, rs),
            "oracles_text": files.split_front_matter(files.gm_file("oracles.md"))[1],
            "dice": make_dice(60, 30, 30), "seed_text": seed_text or None, "document_text": document_text or None,
            "generation": "import" if document_text else generation, "language": language,
            "available_rulesets": [{"id": k, "title": v["meta"].get("title")} for k, v in rs.items()]}


def ruleset_context(document_text, suggested_id, existing_ids, language):
    return {"contract_text": files.ruleset_contract_text(), "outline": files.ruleset_outline(), "document_text": document_text,
            "suggested_id": suggested_id or None, "existing_ids": sorted(existing_ids), "language": language,
            "limits": {"body_chars": [config.RULESET_BODY_MIN, config.RULESET_BODY_MAX]}}


def game_context(adventure, defaults, images_available=False):
    return {"adventure": {"id": adventure["id"], "title": adventure.get("title"), "era": adventure.get("era"),
                          "summary": adventure.get("summary"), "players": adventure.get("players"),
                          "recommended": adventure.get("recommended"),
                          "language": adventure.get("language")},
            "ruleset_id": adventure.get("ruleset_id"), "defaults": defaults,
            "options": {"lethality": ["low", "moderate", "high"], "turn_span": ["day", "block"],
                        "turn_close_hour": "0 to 23 = the hour of the day (in turn_timezone) at which a turn of a whole number of days closes; -1 = exactly one interval after it opens", "pvp": ["none", "soft", "full"], "visibility": ["private", "open"],
                        "illustrations": ["off", "on"] if images_available else ["off"]},
            "explanations": {"lethality": lethality_help()}}


# ---------------------------------------------------------------- validators
def _s(d, k, lo=1, hi=500, problems=None, required=True):
    v = d.get(k)
    if v is None or v == "":
        if required:
            problems.append(f"{k} is required")
        return
    if not isinstance(v, str) or not (lo <= len(v) <= hi):
        problems.append(f"{k} must be text of {lo} to {hi} characters")


def validate_character(p):
    problems = []
    if not isinstance(p, dict):
        return ["the package must be an object"]
    if len(json.dumps(p, ensure_ascii=False)) > 60_000:
        problems.append("the package is too large")
    if p.get("route", "generate") not in ("generate", "provided"):
        problems.append("route must be generate or provided")
    _s(p, "name", 1, 80, problems)
    _s(p, "concept", 1, 400, problems)
    _s(p, "personal_goal", 1, 600, problems)
    pt = p.get("portrait")
    if pt is not None:
        if not isinstance(pt, dict) or not isinstance(pt.get("appearance"), str) or not (20 <= len(pt["appearance"]) <= 600) or \
                not isinstance(pt.get("signature_action", ""), str) or len(pt.get("signature_action", "")) > 200:
            problems.append("portrait must be {appearance: 20 to 600 characters, signature_action: up to 200 characters}")
    sheet = p.get("sheet")
    if not isinstance(sheet, dict) or not isinstance(sheet.get("groups"), dict) or not sheet["groups"]:
        problems.append("sheet.groups must list the character's stats")
    else:
        for g, stats in sheet["groups"].items():
            if not isinstance(stats, dict) or not stats:
                problems.append(f"sheet.groups.{g} must be an object of stats")
                continue
            for name, v in stats.items():
                ok = isinstance(v, dict) and all(isinstance(v.get(x), (int, float)) and not isinstance(v.get(x), bool) for x in ("max", "cur"))
                if not ok:
                    problems.append(f"{g}.{name} needs numeric max and cur")
                elif v["cur"] != v["max"]:
                    problems.append(f"{g}.{name}: cur must equal max at the start")
    for k, lim in (("inventory", 40), ("relationships", 12), ("known_background", 20)):
        if k in p and (not isinstance(p[k], list) or len(p[k]) > lim):
            problems.append(f"{k} must be a list of at most {lim}")
    for t in p.get("known_background") or []:
        if not isinstance(t, str) or len(t) > 400:
            problems.append("each known_background entry must be text of at most 400 characters")
            break
    return problems


_REQ_B = [("the truth", r"\bthe truth\b|\btruth\b"), ("cast", r"\bcast\b"), ("places", r"\bplaces?\b"), ("timeline", r"\btimeline\b|\bclock\b"),
          ("clues", r"\bclues?\b"), ("finale", r"\bfinale\b"), ("endings", r"\bendings?\b")]
_SEED_KEYS = ("truth", "hook", "stake", "antagonist", "clock_turns", "anchor_npcs", "first_place", "opening_handout")


def validate_adventure(p, ruleset_ids):
    problems = []
    if not isinstance(p, dict):
        return ["the package must be an object"]
    _s(p, "title", 1, 120, problems)
    _s(p, "summary", 1, 600, problems)
    _s(p, "era", 1, 80, problems)
    if p.get("generation") not in ("full", "emergent", "supplied"):
        problems.append("generation must be full, emergent or supplied")
    pl = p.get("players")
    if not (isinstance(pl, dict) and isinstance(pl.get("min"), int) and isinstance(pl.get("max"), int) and 1 <= pl["min"] <= pl["max"] <= 8):
        problems.append("players must be {min, max} integers, 1 to 8, min not above max")
    rec = p.get("recommended") or {}
    if rec.get("turn_span", "day") not in ("day", "block"):
        problems.append("recommended.turn_span must be day or block")
    h = rec.get("turn_interval_hours", 24)
    if not isinstance(h, int) or not (1 <= h <= 168):
        problems.append("recommended.turn_interval_hours must be 1 to 168")
    if rec.get("lethality", "high") not in ("low", "moderate", "high"):
        problems.append("recommended.lethality must be low, moderate or high")
    c = p.get("content")
    if not isinstance(c, str) or not (1500 <= len(c) <= 400_000):
        problems.append("content must be markdown of 1500 to 400000 characters")
    else:
        a = re.search(r"^# PART A", c, re.M)
        b = re.search(r"^# PART B", c, re.M)
        if not a or not b or a.start() > b.start():
            problems.append("content needs a '# PART A' heading followed by a '# PART B' heading")
        elif p.get("generation") in ("full", "supplied"):
            partb = c[b.start():].lower()
            for name, rx in _REQ_B:
                if not re.search(rx, partb):
                    problems.append(f"Part B has no section on {name}")
    if p.get("generation") == "emergent":
        seed = p.get("seed")
        if not isinstance(seed, dict) or any(k not in seed for k in _SEED_KEYS):
            problems.append(f"an emergent adventure needs a seed with: {', '.join(_SEED_KEYS)}")
        elif not isinstance(seed.get("anchor_npcs"), list) or len(seed["anchor_npcs"]) < 4:
            problems.append("seed.anchor_npcs needs at least four NPCs")
    for kind, prefix in (("npcs", "npc_"), ("locations", "loc_")):
        items = p.get(kind) or []
        if not isinstance(items, list) or len(items) > 80:
            problems.append(f"{kind} must be a list of at most 80")
            continue
        ids = [i.get("id") if isinstance(i, dict) else None for i in items]
        if any(not (isinstance(i, str) and i.startswith(prefix) and re.fullmatch(r"[a-z0-9_]{3,60}", i)) for i in ids):
            problems.append(f"every {kind[:-1]} id must be lowercase and start with {prefix}")
        if len(set(ids)) != len(ids):
            problems.append(f"{kind} ids must be unique")
        if any(not isinstance(i, dict) or not i.get("name") for i in items):
            problems.append(f"every {kind[:-1]} needs a name")
    return problems


def validate_game(p, adventure, images_available=False):
    problems = []
    if not isinstance(p, dict):
        return ["the package must be an object"]
    if p.get("lethality", "high") not in ("low", "moderate", "high"):
        problems.append("lethality must be low, moderate or high")
    if p.get("turn_span", "day") not in ("day", "block"):
        problems.append("turn_span must be day or block")
    h = p.get("turn_interval_hours", 24)
    if not isinstance(h, int) or not (1 <= h <= 168):
        problems.append("turn_interval_hours must be 1 to 168")
    ch = p.get("turn_close_hour")
    if ch is not None and (isinstance(ch, bool) or not isinstance(ch, int) or not (-1 <= ch <= 23)):
        problems.append("turn_close_hour must be -1 (no fixed hour) or an hour from 0 to 23")
    tzn = p.get("turn_timezone")
    if tzn:
        try:
            from zoneinfo import ZoneInfo
            ZoneInfo(str(tzn).strip())
        except Exception:
            problems.append("turn_timezone must be an IANA timezone name such as Europe/Madrid")
    if p.get("pvp", "soft") not in ("none", "soft", "full"):
        problems.append("pvp must be none, soft or full")
    if p.get("narration_verbosity") not in (None, "low", "medium", "high"):
        problems.append("narration_verbosity must be low, medium or high")
    pe = p.get("players_expected")
    top = ((adventure or {}).get("players") or {}).get("max", 5)
    if pe is not None and (isinstance(pe, bool) or not isinstance(pe, int) or not (1 <= pe <= top)):
        problems.append(f"players_expected must be a whole number from 1 to {top}")
    ill = p.get("illustrations") or ("on" if images_available else "off")  # on by default when the server can draw
    if ill not in ("off", "on"):
        problems.append("illustrations must be off or on")
    elif ill == "on" and not images_available:
        problems.append("illustrations are not available on this server; use off")
    st = p.get("image_style")
    if st is not None and (not isinstance(st, str) or not (config.STYLE_MIN <= len(st.strip()) <= config.STYLE_MAX)):
        problems.append(f"image_style must be text of {config.STYLE_MIN} to {config.STYLE_MAX} characters")
    elif ill == "on" and not st:
        problems.append("image_style is required when illustrations are on")
    if p.get("visibility", "private") not in ("private", "open"):
        problems.append("visibility must be private or open")
    for k in ("title", "language", "display_name"):
        if p.get(k) is not None and (not isinstance(p[k], str) or len(p[k]) > 120):
            problems.append(f"{k} must be text of at most 120 characters")
    return problems


# ---------------------------------------------------------------- rulesets
RULESET_ID = re.compile(r"^[a-z][a-z0-9_]{2,39}$")
_REQUIRED_HEADINGS = [("core concept", r"core concept"), ("characters", r"character"), ("abilities", r"abilit|\bstats?\b|attribute|skill"),
                      ("core mechanics", r"mechanics"), ("solo and party play", r"solo|party"), ("npc statistics", r"\bnpc"), ("sheet layout", r"sheet")]
_SUSPICIOUS = [r"ignore (all |any |the )?(previous|prior|above|earlier)", r"disregard .{0,40}(instruction|rule|protocol)", r"system prompt",
               r"you are now\b", r"reveal .{0,40}(secret|truth|adventure)", r"override .{0,30}(protocol|secrecy|secrets)", r"<\|",
               r"forget (all |your |the )?(instruction|rule)", r"do not (follow|obey) the (protocol|instruction)"]


def ruleset_checks(meta, body):
    """Structural checks shared by import validation and the host's review. Returns (problems, info)."""
    problems = []
    heads = [h.strip().lower() for h in re.findall(r"^#{2,3}\s+(.+)$", body, flags=re.M)]
    joined = "\n".join(heads)
    for name, rx in _REQUIRED_HEADINGS:
        if not re.search(rx, joined):
            problems.append(f"the body needs a section for '{name}' (a ## heading containing that word)")
    rows = 0
    m = re.search(r"^\|\s*#\s*\|\s*Check\s*\|\s*Passes when[^\n]*\n\|[-| :]+\n((?:\|\s*\d+\s*\|[^\n]*\n?)+)", body, flags=re.M | re.I)
    if m:
        rows = len(m.group(1).strip().splitlines())
    if rows < 5:
        problems.append("the character validation checklist must be a table headed '| # | Check | Passes when |' with at least 5 numbered rows")
    low = body.lower()
    for k in ("pass_with_adjustments", "fail"):
        if k not in low:
            problems.append(f"the validation outcomes must name {k}")
    if not re.search(r"\bdead\b|\bdeath\b|\bdies\b", low) or "lethality" not in low:
        problems.append("the rules must state when a character is dead and how lethality (low, moderate, high) applies, or that it does not")
    if "groups" not in low or "ruleset_state" not in low:
        problems.append("the sheet layout must describe sheet.groups and ruleset_state")
    flags = [rx for rx in _SUSPICIOUS if re.search(rx, low)]
    if flags:
        problems.append("the text contains wording that addresses the AI or tries to change its instructions; remove it")
    return problems, {"headings": [h for h in heads], "checklist_rows": rows, "suspicious_patterns": len(flags), "chars": len(body)}


def validate_ruleset(p, existing_ids):
    problems = []
    if not isinstance(p, dict):
        return ["the package must be an object"]
    if len(json.dumps(p, ensure_ascii=False)) > config.RULESET_BODY_MAX + 20_000:
        return ["the package is too large"]
    rid = p.get("id")
    if not isinstance(rid, str) or not RULESET_ID.match(rid):
        problems.append("id must be lowercase letters, digits and underscores, 3 to 40 characters, starting with a letter")
    elif rid in existing_ids:
        problems.append(f"the id {rid} is already taken; choose another")
    for k, hi in (("title", 120), ("system", 120), ("dice", 40), ("language", 20), ("summary", 600)):
        if not isinstance(p.get(k), str) or not (1 <= len(p[k].strip()) <= hi):
            problems.append(f"{k} must be text of 1 to {hi} characters")
    if not isinstance(p.get("version"), int) or isinstance(p.get("version"), bool) or p["version"] < 1:
        problems.append("version must be an integer of at least 1")
    pl = p.get("players")
    if not (isinstance(pl, dict) and all(isinstance(pl.get(k), int) and not isinstance(pl.get(k), bool) for k in ("min", "max")) and 1 <= pl["min"] <= pl["max"] <= 12):
        problems.append("players must be {min, max}, integers with 1 <= min <= max <= 12")
    for k in ("modules", "tone_presets"):
        v = p.get(k, [])
        if not isinstance(v, list) or len(v) > 20 or any(not isinstance(x, str) or not re.match(r"^[a-z0-9_]{1,40}$", x) for x in v):
            problems.append(f"{k} must be a list of at most 20 slugs (lowercase letters, digits, underscores)")
    sn = p.get("source_notes")
    if not isinstance(sn, dict) or sn.get("rights_confirmed") is not True:
        problems.append("source_notes.rights_confirmed must be true: the player must confirm they may use the document")
    body = p.get("body")
    if not isinstance(body, str):
        problems.append("body must be the whole ruleset as markdown text")
    elif not (config.RULESET_BODY_MIN <= len(body) <= config.RULESET_BODY_MAX):
        problems.append(f"body must be {config.RULESET_BODY_MIN} to {config.RULESET_BODY_MAX} characters (it has {len(body)})")
    elif body.lstrip().startswith("---"):
        problems.append("body must not contain the front matter; give the fields separately")
    else:
        more, _ = ruleset_checks(p, body)
        problems += more
    return problems
