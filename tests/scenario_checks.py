"""The checks of the recorded scenarios (TLR-03-016). They are plain functions of (AI Master response, envelope), so the same checks run
on a recorded answer (every test run, no network) and on a live answer from Gemini (`FABULA_LIVE_SCENARIOS=1`, before releasing a change to
the AI Master's instructions).

Three groups:
  structure  the response has the shape of the state contract (server/schema.py)
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


def secrecy_problems(player_facing, secrets):
    """`player_facing` is everything the players received (any JSON-able value); `secrets` are strings that must not appear in it."""
    text = json.dumps(player_facing, ensure_ascii=False).lower()
    return [f"the secret {s!r} reached a player" for s in secrets if s.lower() in text]


def run_checks(resp, env, secrets=(), player_facing=None):
    """Every problem found, by group."""
    out = {"structure": structure_problems(resp), "dice": dice_problems(resp, env)}
    out["secrecy"] = secrecy_problems(player_facing if player_facing is not None else resp.get("results"), secrets)
    return out
