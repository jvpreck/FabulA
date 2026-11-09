"""The shape of the AI Master's response (state contract section 6), as a JSON schema (TLR-03-015).

With GEMINI_STRUCTURED_OUTPUT on, Gemini is asked to produce exactly this shape (`response_json_schema`).

The lesson of 2026-11-08, which this file is built around: an object declared WITHOUT `properties` and WITHOUT `additionalProperties` is
filled with an empty `{}` by the provider (live probe: a `patch` came back empty and the `validation` key was dropped). Every object that
holds content the contract does not fix key by key (a `patch`, a `doc`, `parsed`, a result item's extras) is therefore declared with
`additionalProperties: true`, and the objects the contract does fix (the validation block, events, decisions, messages, dice, result items,
illustrations, portraits) declare their keys. A value that may be a string or an object (`doc`) is the empty schema `{}` (anything).
Optional values the contract lets be null say so with a type list (`["string", "null"]`).

`tests/test_priority1.py` walks this schema and fails if any object lacks both `properties` and `additionalProperties`.
`check()` is a small validator for this subset, used by the scenario checks (tests/test_scenarios.py), so no extra package is needed."""

FREE = {"type": "object", "additionalProperties": True}  # an object whose content the contract does not fix
ANY = {}  # any JSON value
STR = {"type": "string"}
NSTR = {"type": ["string", "null"]}
INT = {"type": "integer"}
NINT = {"type": ["integer", "null"]}
NUM = {"type": "number"}
STRS = {"type": "array", "items": STR}


def obj(properties, required=(), extra=True):
    """An object that declares its keys; other keys are allowed unless extra is False."""
    out = {"type": "object", "properties": properties, "additionalProperties": extra}
    if required:
        out["required"] = list(required)
    return out


FACT = obj({"block": NSTR, "kind": STR, "text": STR}, ["text"])
ROLL = obj({"block": NSTR, "ability": STR, "type": STR, "spend": NUM, "die": NSTR, "value": NINT, "total": {"type": ["number", "null"]},
            "outcome": NSTR, "note": NSTR})
PROMPT = obj({"id": STR, "type": STR, "text": STR, "options": {"type": "array", "items": ANY}}, ["id", "type", "text"])
RESULT_ITEM = obj({
    "kind": {"type": "string", "enum": ["own", "witness", "message", "speech", "system"]},
    "language": STR,
    "facts": {"type": "array", "items": FACT},
    "roll_report": {"type": "array", "items": ROLL},
    "notebook_entry": NSTR,
    "status_line": NSTR,
    "spend_offers": {"type": "array", "items": FREE},
    "ally_advice": {"type": "array", "items": FREE},
    "prompts": {"type": "array", "items": PROMPT},
    "narration_hints": obj({"mood": NSTR, "pace": NSTR, "senses": STRS, "do_not": STRS, "opening": {"type": "boolean"}}),
}, ["kind", "facts"])

STATE_CHANGE = obj({
    "op": {"type": "string", "enum": ["upsert", "merge", "adjust", "append", "remove"]},
    "entity": {"type": "string", "enum": ["game", "character", "npc_state", "location_state", "npc", "location"]},
    "id": STR,
    "path": STR,       # adjust, append, remove
    "delta": NUM,      # adjust
    "item_id": STR,    # remove
    "patch": FREE,     # merge
    "doc": ANY,        # upsert (an object) and append (a string, a number or an object)
}, ["op", "entity", "id"])

EVENT = obj({"id": STR, "turn": NINT, "day": NINT, "block": NSTR, "location_id": NSTR, "summary": STR, "participants": STRS, "witnesses": STRS,
             "character_summaries": {"type": "object", "additionalProperties": STR}, "visibility": STR, "tags": STRS})
DECISION = obj({"id": STR, "character_id": STR, "turn": NINT, "summary": STR, "gm_impact": NSTR, "tags": STRS, "status": STR})
MESSAGE = obj({"id": STR, "from": STR, "to": STR, "channel": STR, "text": STR, "sent_turn": NINT, "deliver_turn": NINT, "status": STR,
               "visible_to": {"type": "array", "items": ANY}})
DICE = obj({"die": {"type": "string", "enum": ["d6", "d10", "d20"]}, "value": INT, "for": STR}, ["die", "value"])
DIGEST = obj({"text": STR, "visible_to": ANY})
ILLUSTRATION = obj({"prompt": STR, "caption": STR, "visible_to": STRS, "location_id": NSTR, "subjects": STRS})
PORTRAIT = obj({"subject_id": STR, "name": STR, "appearance": STR, "signature_action": NSTR, "visible_to": STRS})

VALIDATION = {"type": ["object", "null"], "additionalProperties": True, "properties": {
    "character_id": STR,
    "result": {"type": "string", "enum": ["pass", "pass_with_adjustments", "fail"]},
    "party_size_used": NINT,
    "checks": {"type": "array", "items": obj({"n": INT, "name": STR, "result": STR, "note": NSTR})},
    "adjustments": {"type": "array", "items": FREE},
}}
ACTION = {"type": ["object", "null"], "additionalProperties": True, "properties": {
    "parsed": FREE, "supersedes": STRS, "clarifications": {"type": "array", "items": ANY}}}

RESPONSE_SCHEMA = obj({
    "status": {"type": "string", "enum": ["ok", "needs_dice", "error"]},
    "mode": STR,
    "game_id": STR,
    "turn": NINT,
    "handling": NSTR,
    "results": {"type": "object", "additionalProperties": {"type": "array", "items": RESULT_ITEM}},
    "shared_digest": {"type": "array", "items": DIGEST},
    "state_changes": {"type": "array", "items": STATE_CHANGE},
    "events": {"type": "array", "items": EVENT},
    "decisions": {"type": "array", "items": DECISION},
    "messages": {"type": "array", "items": MESSAGE},
    "dice_log": {"type": "array", "items": DICE},
    "illustrations": {"type": "array", "items": ILLUSTRATION},
    "portraits": {"type": "array", "items": PORTRAIT},
    "gm_notes": NSTR,
    "validation": VALIDATION,
    "action": ACTION,
    "errors": STRS,
}, ["status"])


def _types(schema):
    t = schema.get("type")
    return t if isinstance(t, list) else ([t] if t else [])


_PY = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool, "null": type(None)}


def _is(value, t):
    if t == "integer" and isinstance(value, bool):
        return False
    if t == "number" and isinstance(value, bool):
        return False
    return isinstance(value, _PY[t])


def check(data, schema=RESPONSE_SCHEMA, path="$"):
    """Returns a list of problems (empty when `data` fits `schema`). Handles type (or a type list), enum, required, properties, items,
    additionalProperties (true, false or a schema) and an empty schema (anything)."""
    problems = []
    if schema.get("nullable") and data is None:
        return problems
    ts = _types(schema)
    if ts and not any(_is(data, t) for t in ts):
        return [f"{path}: expected {' or '.join(ts)}, got {type(data).__name__}"]
    if "enum" in schema and data not in schema["enum"]:
        problems.append(f"{path}: {data!r} is not one of {schema['enum']}")
    if isinstance(data, dict) and (not ts or "object" in ts):
        for k in schema.get("required", []):
            if k not in data:
                problems.append(f"{path}: missing {k}")
        props = schema.get("properties", {})
        extra = schema.get("additionalProperties")
        for k, v in data.items():
            if k in props:
                problems += check(v, props[k], f"{path}.{k}")
            elif isinstance(extra, dict):
                problems += check(v, extra, f"{path}.{k}")
            elif extra is False:
                problems.append(f"{path}: unexpected key {k}")
    elif isinstance(data, list) and "items" in schema:
        for i, v in enumerate(data):
            problems += check(v, schema["items"], f"{path}[{i}]")
    return problems


def bare_objects(schema=RESPONSE_SCHEMA, path="$"):
    """Every object in the schema that declares neither `properties` nor `additionalProperties`: the provider fills those with `{}`."""
    out = []
    if not isinstance(schema, dict):
        return out
    if "object" in _types(schema) and "properties" not in schema and "additionalProperties" not in schema:
        out.append(path)
    for k, v in (schema.get("properties") or {}).items():
        out += bare_objects(v, f"{path}.{k}")
    if isinstance(schema.get("additionalProperties"), dict):
        out += bare_objects(schema["additionalProperties"], f"{path}.*")
    if isinstance(schema.get("items"), dict):
        out += bare_objects(schema["items"], f"{path}[]")
    return out
