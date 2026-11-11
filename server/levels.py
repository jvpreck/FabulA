"""The four request levels (TLR-01-007 to 01-011), decided by fixed rules (TLR-03-007), and reported on every answer (TLR-01-016).

1. LOCAL    the client answers alone. The engine never sees these requests; the number exists so a client can declare it.
2. DATABASE the engine answers from its data, with no AI Master call and no quota.
3. IMMEDIATE the AI Master resolves it at once; it affects only the requesting character and nothing shared.
4. TURN_CLOSE it involves other players or shared state, or the AI Master could not be reached, so it waits for the turn close,
   and a request that closes the turn is answered at this level.

The engine works out the level it expects from the request alone (`expected_level`), runs it, and reports the level at which it was
really answered (`final_level`). A client may declare the level it expects (`declared`); when the three differ the answer says why
(TLR-03-007, 03-008): the final level may be higher or lower than the client expected, and the player is told the reason.
"""
from . import level2

LOCAL, DATABASE, IMMEDIATE, TURN_CLOSE = 1, 2, 3, 4
NAMES = {LOCAL: "client", DATABASE: "database", IMMEDIATE: "immediate", TURN_CLOSE: "turn close"}

# Fixed rules: the level a request of this kind is expected to have before it runs (TLR-03-007).
DATABASE_KINDS = frozenset({"ready", "say", "setup_answers", "character_confirm"})
SHARED_KINDS = frozenset({"message"})  # involves another player: the turn close (TLR-01-011)


def expected_level(kind, payload=None):
    """The level the server expects for a request, from its kind and payload alone."""
    topic = str((payload or {}).get("topic") or "").strip().lower()
    if kind == "free_query" and topic in level2.TOPICS:
        return DATABASE
    if kind in DATABASE_KINDS:
        return DATABASE
    if kind in SHARED_KINDS:
        return TURN_CLOSE
    return IMMEDIATE


def final_level(out):
    """The level at which an answer was really produced, read from the answer itself."""
    if out.get("turn_resolved") or out.get("handling") in ("resolved_turn", "queued"):
        return TURN_CLOSE
    if out.get("server_only") or out.get("level") == DATABASE:
        return DATABASE
    return IMMEDIATE


def reason(out, expected, final, declared=None):
    """Why the level is what it is, when the client or the rules expected another one. None when there is nothing to explain."""
    if out.get("deferred"):
        return ("The AI Master could not be reached, so the request was queued for the turn close instead of being resolved at once "
                "(level 4 instead of level 3). Nothing was lost.")
    if out.get("turn_resolved") or out.get("handling") == "resolved_turn":
        return "This request closed the turn, so its answer is the turn close (level 4)."
    if final != expected and final == TURN_CLOSE:
        return "The AI Master judged that this involves shared state or other players, so it waits for the turn close (level 4)."
    if final != expected and final == IMMEDIATE:
        return "The AI Master resolved this at once because it affects only the requesting character (level 3)."
    if final != expected and final == DATABASE:
        return "The engine answered this from its data, without the AI Master (level 2)."
    if declared and declared != final:
        return f"The server decides the level by fixed rules over the request and the game data: this was answered at level {final}, not level {declared}."
    return None


def stamp(out, kind, payload=None, declared=0):
    """Puts `level` (always), `level_name`, and `expected_level` / `level_reason` (when something needs explaining) on an answer.
    Returns the final level."""
    declared = declared if declared in (LOCAL, DATABASE, IMMEDIATE, TURN_CLOSE) else 0
    expected = expected_level(kind, payload)
    final = final_level(out)
    out["level"] = final
    out["level_name"] = NAMES[final]
    why = reason(out, expected, final, declared)
    if declared:
        out["expected_level"] = declared
    if why:
        out["level_reason"] = why
    return final
