"""The checks of the recorded scenarios (TLR-03-016). They are plain functions of (AI Master response, envelope), so the same checks run
on a recorded answer (every test run, no network) and on a live answer from Gemini (`FABULA_LIVE_SCENARIOS=1`, before releasing a change to
the AI Master's instructions).

Four groups:
  structure  the response has the shape of the state contract (server/schema.py)
  contract   the fields that matter arrive filled: a verdict for a character check, the parsed action, state changes with their patch/path/doc
  dice       rules fidelity: every die used comes from the server's stream, in order from the first unused value, and is logged
  secrecy    nothing the players must not learn appears in anything a player receives"""
import json

from server import schema

SIDES = {"d6": 6, "d10": 10, "d20": 20}


def structure_problems(resp):
    return schema.check(resp)


def dice_problems(resp, env):
    """Protocol §1.12: use only the server dice, in order, from the first unused value, and log every die used."""
    problems, used = [], {}
    for i, d in enumerate(resp.get("dice_log") or []):
        die, value = d.get("die"), d.get("value")
        if die not in SIDES:
            problems.append(f"dice_log[{i}]: unknown die {die!r}")
            continue
        if not isinstance(value, int) or not 1 <= value <= SIDES[die]:
            problems.append(f"dice_log[{i}]: {value!r} is not a {die}")
            continue
        n = used.get(die, 0)
        stream = (env.get("dice") or {}).get(die) or []
        if n >= len(stream) or stream[n] != value:
            problems.append(f"dice_log[{i}]: {die} {value} is not the next server die (expected {stream[n] if n < len(stream) else 'none left'})")
        used[die] = n + 1
    for ch_id, items in (resp.get("results") or {}).items():
        for item in items if isinstance(items, list) else []:
            for r in item.get("roll_report") or []:
                if r.get("die") and r.get("value") is not None and not any(
                        d.get("die") == r["die"] and d.get("value") == r["value"] for d in resp.get("dice_log") or []):
                    problems.append(f"results.{ch_id}: a roll of {r['die']} {r['value']} is not in dice_log")
    return problems


def contract_problems(resp, request=None):
    """The fields that matter arrive FILLED, not only well-formed (the schema incident of 2026-11-08 passed every structure check while
    `validation`, `action` and the state-change patches came back empty). `request` is the request that was sent (kind), or None."""
    problems = []
    kind = (request or {}).get("kind")
    if kind == "character_submission":
        v = resp.get("validation")
        if not isinstance(v, dict) or v.get("result") not in ("pass", "pass_with_adjustments", "fail"):
            problems.append("a character check ended without a verdict: validation.result is missing")
        elif v["result"] != "pass" and not v.get("checks"):
            problems.append("the verdict is not a pass but validation.checks is empty")
    if kind == "action" and resp.get("handling") in ("queued", "autonomous"):
        parsed = (resp.get("action") or {}).get("parsed")
        if not isinstance(parsed, dict) or not parsed.get("blocks"):
            problems.append("a queued or autonomous action came back without action.parsed.blocks")
    for i, op in enumerate(resp.get("state_changes") or []):
        o = op.get("op")
        need = {"merge": ("patch",), "adjust": ("path", "delta"), "append": ("path", "doc"), "upsert": ("doc",), "remove": ("path", "item_id")}.get(o, ())
        for k in need:
            if k not in op or op[k] in (None, {}, ""):
                problems.append(f"state_changes[{i}] ({o} {op.get('entity')} {op.get('id')}) has no {k}")
    for i, d in enumerate(resp.get("dice_log") or []):
        if not d.get("die") or d.get("value") is None:
            problems.append(f"dice_log[{i}] is empty")
    for i, e in enumerate(resp.get("events") or []):
        if not e.get("summary"):
            problems.append(f"events[{i}] has no summary")
    return problems


def secrecy_problems(player_facing, secrets):
    """`player_facing` is everything the players received (any JSON-able value); `secrets` are strings that must not appear in it."""
    text = json.dumps(player_facing, ensure_ascii=False).lower()
    return [f"the secret {s!r} reached a player" for s in secrets if s.lower() in text]


def run_checks(resp, env, secrets=(), player_facing=None):
    """Every problem found, by group."""
    out = {"structure": structure_problems(resp), "dice": dice_problems(resp, env), "contract": contract_problems(resp, env.get("request"))}
    out["secrecy"] = secrecy_problems(player_facing if player_facing is not None else resp.get("results"), secrets)
    return out
