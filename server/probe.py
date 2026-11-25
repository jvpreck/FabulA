"""Model probe (2026-11-21, owner): how long each Gemini and OpenRouter model takes to answer a real-size request, and whether it answers
at all when it is given much more time than in play. Off unless PROBE_RUN is set (a run name). The scheduler (/internal/resolve_turn,
every 5 minutes) tests ONE model per run, after its normal work, with the time the function has left (about 4.5 minutes at most:
Vercel stops a function at 300 s). Results are kept in gm_usage, record `probe:<run>`; read them with SQL or the host command gm_usage.

The request is the real `play` instructions for Fear Itself (about 40k tokens) and a small free_query envelope, the size of a normal
level 3 call. OpenRouter is called with streaming, to see when the first token arrives (time to first token) apart from the total.
Each probe request is counted in the same daily guards as play (Usage.reserve: tier turn for a strong Gemini model, light for a light one,
openrouter for OpenRouter), and is skipped, not sent, when that guard is used up (2026-11-25, owner).

Kinds (2026-11-25, owner: realistic requests, to retest when the free models change). Env PROBE_KINDS, comma-separated, default `simple`:
- simple: the small free_query above, for every model of both lists.
- action: a real level 3 request (an ordinary action, the text from the recorded scenario minor_action_uses_server_dice_in_order),
  built by the engine from the game PROBE_GAME exactly as in play (system prompt with the adventure, envelope, effort), for the
  models of the light list.
- turn_close: a real level 4 turn close of PROBE_GAME with one queued action (the text from major_action_is_queued_for_the_turn),
  for the models of the strong list.
The game is only read: nothing is applied or saved to it. Without PROBE_GAME (or when it is not an active game) these kinds are
recorded as skipped.
"""
import json
import os
import time

from . import config

ENVELOPE = json.dumps({"mode": "intake", "request": {"kind": "free_query", "text": "What time of day is it, and where am I?"},
                       "note": "Answer with one JSON object as the state contract says."})


# texts adapted from tests/scenarios/scenarios.json (the recorded ones name places of the test adventure)
REAL_TEXTS = {"action": "I search the desk in the office for letters or notes, and I read anything I find.",
              "turn_close": "I ask the person in charge here about what happened and follow them if they leave."}
KINDS = ("simple", "action", "turn_close")


def _models():
    names = os.environ.get("PROBE_MODELS", "")
    if names.strip():
        return [m.strip() for m in names.split(",") if m.strip()]
    return list(dict.fromkeys(config.GEMINI_STRONG_MODELS + config.GEMINI_LIGHT_MODELS))


def _kinds():
    ks = [k.strip() for k in os.environ.get("PROBE_KINDS", "simple").split(",") if k.strip() in KINDS]
    return ks or ["simple"]


def _queue():
    """(kind, model) pairs: simple for every model, action for the light list, turn_close for the strong list (PROBE_MODELS overrides)."""
    custom = bool(os.environ.get("PROBE_MODELS", "").strip())
    out = []
    for k in _kinds():
        models = _models() if (custom or k == "simple") else (config.GEMINI_LIGHT_MODELS if k == "action" else config.GEMINI_STRONG_MODELS)
        out += [{"kind": k, "model": m} for m in models]
    return out


def _tier(model, kind):
    if model.startswith(config.OPENROUTER_PREFIX):
        return "openrouter"
    if kind == "turn_close" or (kind == "simple" and model in config.GEMINI_STRONG_MODELS and model not in config.GEMINI_LIGHT_MODELS):
        return "turn"
    return "light"


def real_request(store, kind, game_id=None):
    """(system, envelope text, effort, info) for a realistic request of `kind`, built from the game as the engine builds it in play.
    Read-only: the workspace is never committed."""
    from . import prompt
    from .engine import Engine
    gid = (game_id or os.environ.get("PROBE_GAME", "")).strip()
    if not gid:
        raise ValueError("no PROBE_GAME set")
    eng = Engine(store, None)
    ws = eng._ws()
    game = eng._game(ws, gid)
    if game.get("phase") != "active":
        raise ValueError(f"game {gid} is not active (phase {game.get('phase')})")
    adv = eng._adventure(ws, game["adventure_id"])
    chars = [c for c in ws.load_game_characters(gid) if c.get("is_alive", True) and c.get("status") in ("active", "npc_controlled", "sidelined")]
    if not chars:
        raise ValueError(f"game {gid} has no playing character")
    c = chars[0]
    text = REAL_TEXTS[kind]
    if kind == "action":
        mode, cid = "intake", c["id"]
        request = {"player_id": c.get("player_id"), "character_id": c["id"], "kind": "action", "text": text, "payload": {}}
    else:
        mode, cid, request = "resolve_turn", None, None
        sa = ws.get("submit_action", f"{gid}:{game['clock'].get('turn')}")
        if sa is not None:  # in memory only
            sa["actions"].setdefault(c["id"], []).append({"id": "a_probe", "player_id": c.get("player_id"), "submitted_at": game["clock"].get("turn_opens"),
                                                          "kind": "action", "raw_text": text, "parsed": None, "needs_parse": True,
                                                          "handling": "queued", "status": "queued", "supersedes": [], "clarifications": []})
    profile = eng._profile(mode, request)
    system = prompt.system_prompt(game["ruleset_id"], adv, eng.rulesets(), profile,
                                  prompt.flags_for(game, adv, eng._images_available()) if profile else ())
    env = eng._dumps(eng._envelope(ws, game, adv, mode, request, cid))
    return system, env, eng._effort(mode, request), {"game": gid, "turn": game["clock"].get("turn"), "envelope_chars": len(env)}


def _system():
    from . import prompt
    try:
        return prompt.system_prompt("fear_itself", None, profile="play")
    except Exception:
        return prompt.system_prompt("fear_itself", None)


def _is_json(text):
    try:
        s = text.strip()
        if s.startswith("```"):
            s = s.strip("`")
            s = s[s.find("{"):]
        return isinstance(json.loads(s), dict)
    except Exception:
        return False


def _openrouter(model, system, user, wait, effort="medium"):
    """Streams one answer; returns timing and outcome. Never raises."""
    import urllib.error
    import urllib.request
    name = model[len(config.OPENROUTER_PREFIX):]
    body = {"model": name, "stream": True, "max_tokens": config.OPENROUTER_MAX_TOKENS,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "reasoning": {"effort": effort or "medium"}, "response_format": {"type": "json_object"}}
    req = urllib.request.Request(config.OPENROUTER_URL, data=json.dumps(body).encode(), method="POST", headers={
        "Authorization": "Bearer " + os.environ.get("OPENROUTER_API_KEY", ""), "Content-Type": "application/json",
        "HTTP-Referer": "https://fabula-rpg.vercel.app", "X-Title": "FabulA probe"})
    t0 = time.monotonic()
    deadline = t0 + wait
    out = {"first_byte_s": None, "first_reasoning_s": None, "first_content_s": None, "keepalives": 0}
    text, usage, finish = [], None, None
    try:
        with urllib.request.urlopen(req, timeout=min(60, wait)) as resp:
            out["first_byte_s"] = round(time.monotonic() - t0, 1)
            buf = b""
            while time.monotonic() < deadline:
                chunk = resp.read1(65536) if hasattr(resp, "read1") else resp.read(65536)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith(b":"):
                        out["keepalives"] += 1
                        continue
                    if not line.startswith(b"data:"):
                        continue
                    data = line[5:].strip()
                    if data == b"[DONE]":
                        buf = b""
                        break
                    try:
                        ev = json.loads(data)
                    except Exception:
                        continue
                    if ev.get("error"):
                        out["error"] = str(ev["error"])[:200]
                    for ch in ev.get("choices") or []:
                        d = ch.get("delta") or {}
                        if d.get("reasoning") and out["first_reasoning_s"] is None:
                            out["first_reasoning_s"] = round(time.monotonic() - t0, 1)
                        if d.get("content"):
                            if out["first_content_s"] is None:
                                out["first_content_s"] = round(time.monotonic() - t0, 1)
                            text.append(d["content"])
                        finish = ch.get("finish_reason") or finish
                    usage = ev.get("usage") or usage
            else:
                out["error"] = out.get("error") or f"no complete answer within {wait} s"
    except urllib.error.HTTPError as e:
        out["error"] = f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}"
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {str(e)[:200]}"
    full = "".join(text)
    out.update(total_s=round(time.monotonic() - t0, 1), finish_reason=finish, answer_chars=len(full), json_ok=_is_json(full) if full else False)
    if usage:
        out.update(tokens_in=usage.get("prompt_tokens"), tokens_out=usage.get("completion_tokens"),
                   tokens_reasoning=(usage.get("completion_tokens_details") or {}).get("reasoning_tokens"))
    out["answered"] = bool(full.strip()) and not out.get("error")
    return out


def _gemini(model, system, user, wait, effort="medium"):
    from .gm import GeminiGM
    gm = GeminiGM(usage=None)
    gm._timeout_override = int(wait)
    t0 = time.monotonic()
    out = {}
    try:
        text = gm._generate(model, effort or "medium", system, user)
        out.update(answer_chars=len(text), json_ok=_is_json(text), answered=bool(text.strip()))
    except Exception as e:
        out.update(error=f"{type(e).__name__}: {str(e)[:200]}", answered=False)
    out["total_s"] = round(time.monotonic() - t0, 1)
    m = getattr(gm, "_meta", {}) or {}
    out.update({k: m.get(k) for k in ("tokens_in", "tokens_out", "tokens_thought") if m.get(k) is not None})
    return out


SCHEDULE_KEY = "probe:schedule"
WINDOW_HOURS = 3  # a scheduled run that has not finished within this many hours of its start is left unfinished


def _parse(ts):
    from datetime import datetime, timezone
    return datetime.fromisoformat(ts.strip().replace("Z", "+00:00")).astimezone(timezone.utc)


def scheduled_times(store):
    """Start times (UTC ISO) from the env PROBE_SCHEDULE (comma-separated) and the gm_usage record probe:schedule (host command
    probe_schedule), without duplicates."""
    times = [x for x in os.environ.get("PROBE_SCHEDULE", "").split(",") if x.strip()]
    doc, _ = store.get("usage", SCHEDULE_KEY)
    times += list((doc or {}).get("times") or [])
    out = []
    for x in times:
        try:
            out.append(_parse(x).strftime("%Y-%m-%dT%H:%MZ"))
        except ValueError:
            continue
    return sorted(set(out))


def active_run(store, now_iso):
    """The run to work on now: PROBE_RUN if set, else the scheduled start that has passed and is less than WINDOW_HOURS old."""
    run = os.environ.get("PROBE_RUN", "").strip()
    if run:
        return run
    now = _parse(now_iso)
    for t in reversed(scheduled_times(store)):
        start = _parse(t)
        if start <= now and (now - start).total_seconds() < WINDOW_HOURS * 3600:
            return "sched-" + t.replace(":", "").replace("-", "")
    return None


def run_one(store, seconds_left, now_iso):
    """Tests the next model of the active run (see active_run), if any, within `seconds_left`. Returns a short summary or None."""
    run = active_run(store, now_iso)
    if not run or seconds_left < config.PROBE_MIN_SECONDS:
        return None
    key = f"probe:{run}"
    doc, ver = store.get("usage", key)
    if doc is None:
        doc = {"id": key, "run": run, "started": now_iso, "kinds": _kinds(), "queue": _queue(), "results": []}
    if not doc["queue"]:
        return {"probe": run, "done": True}
    item = doc["queue"].pop(0)
    item = item if isinstance(item, dict) else {"kind": "simple", "model": item}  # runs started before 2026-11-25
    model, kind = item["model"], item.get("kind", "simple")
    doc["current"] = item
    try:  # claim the model first, so two scheduler runs never probe the same one
        store.put("usage", key, doc, ver)
    except Exception:
        return None
    doc, ver = store.get("usage", key)
    wait = max(10, int(seconds_left) - 10)
    res = {"kind": kind}
    try:
        if kind == "simple":
            system, user, effort = _system(), ENVELOPE, "medium"
        else:
            system, user, effort, info = real_request(store, kind)
            res.update(info)
    except Exception as e:
        system = None
        res.update(answered=False, skipped=f"no realistic request: {type(e).__name__}: {str(e)[:160]}")
    if system is not None:
        from .gm import Usage
        tier = _tier(model, kind)
        r = Usage(store).reserve(tier)  # the probe's requests count against the same daily guards as play
        res["tier"] = tier
        if r != "ok":
            res.update(answered=False, skipped=f"the {tier} guard is used up ({r}); not sent")
        else:
            res.update((_openrouter if model.startswith(config.OPENROUTER_PREFIX) else _gemini)(model, system, user, wait, effort))
            res.update(effort=effort, system_chars=len(system), envelope_chars=len(user))
    res.update(model=model, at=now_iso, wait_s=wait)
    for _ in range(3):
        doc["results"].append(res)
        doc.pop("current", None)
        try:
            store.put("usage", key, doc, ver)
            break
        except Exception:
            doc, ver = store.get("usage", key)
    return {"probe": run, "kind": kind, "model": model, "answered": res.get("answered"), "total_s": res.get("total_s")}
