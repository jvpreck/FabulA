"""The shape of the AI Master's response (state contract §6), as a JSON schema (TLR-03-015).

NOT SWITCHED ON (GEMINI_STRUCTURED_OUTPUT is off by default). The provider fills an object that has no declared `properties` with an empty
`{}`: with this schema `validation`, `action`, `events`, `decisions`, `messages` and `dice_log` come back empty and `state_changes` entries can
carry only op, entity and id (no `patch`, `path` or `doc`). A character check then ends without a verdict. Before this is switched on again every
object the contract defines must be declared in full (state contract sections 6.2 to 6.7), and the live scenarios must check that those fields arrive.

Gemini is asked to produce exactly this shape (`response_json_schema`), so a malformed answer is rare. The schema fixes the containers
(object, list), the `status` values and the fields every result item needs; it does not fix the contents of state changes, events or
facts, which `apply.py` still validates. It is deliberately permissive: a schema stricter than the contract would reject good answers.
`check()` is a small validator for this subset, used by the scenario checks (tests/test_scenarios.py), so no extra package is needed."""

_OBJ = {"type": "object"}
_LIST_OF_OBJECTS = {"type": "array", "items": _OBJ}

RESULT_ITEM = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": ["own", "witness", "message", "speech", "system"]},
        "language": {"type": "string"},
        "facts": {"type": "array", "items": {"type": "object", "properties": {"kind": {"type": "string"}, "text": {"type": "string"}},
                                              "required": ["text"]}},
        "prompts": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "type": {"type": "string"},
                                                                                 "text": {"type": "string"}, "options": {"type": "array"}},
                                                "required": ["id", "type", "text"]}},
        "roll_report": _LIST_OF_OBJECTS,
        "spend_offers": _LIST_OF_OBJECTS,
        "ally_advice": _LIST_OF_OBJECTS,
        "narration_hints": _OBJ,
    },
    "required": ["kind", "facts"],
}

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["ok", "needs_dice", "error"]},
        "mode": {"type": "string"},
        "game_id": {"type": "string"},
        "handling": {"type": "string", "enum": ["answered", "queued", "autonomous", "clarify", "rejected", "resolved_turn"]},
        "results": {"type": "object", "additionalProperties": {"type": "array", "items": RESULT_ITEM}},
        "shared_digest": _LIST_OF_OBJECTS,
        "state_changes": {"type": "array", "items": {"type": "object", "properties": {
            "op": {"type": "string", "enum": ["upsert", "merge", "adjust", "append", "remove"]},
            "entity": {"type": "string", "enum": ["game", "character", "npc_state", "location_state", "npc", "location"]},
            "id": {"type": "string"}}, "required": ["op", "entity", "id"]}},
        "events": _LIST_OF_OBJECTS,
        "decisions": _LIST_OF_OBJECTS,
        "messages": _LIST_OF_OBJECTS,
        "dice_log": _LIST_OF_OBJECTS,
        "illustrations": _LIST_OF_OBJECTS,
        "portraits": _LIST_OF_OBJECTS,
        "gm_notes": {"type": "string"},
        "validation": _OBJ,
        "action": _OBJ,
        "errors": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["status"],
}


def check(data, schema=RESPONSE_SCHEMA, path="$"):
    """Returns a list of problems (empty when `data` fits `schema`). Handles type, enum, required, properties, items, additionalProperties."""
    problems = []
    t = schema.get("type")
    py = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool}
    if t and not isinstance(data, py[t]) or (t == "integer" and isinstance(data, bool)):
        return [f"{path}: expected {t}, got {type(data).__name__}"]
    if "enum" in schema and data not in schema["enum"]:
        problems.append(f"{path}: {data!r} is not one of {schema['enum']}")
    if t == "object":
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
    elif t == "array" and "items" in schema:
        for i, v in enumerate(data):
            problems += check(v, schema["items"], f"{path}[{i}]")
    return problems
