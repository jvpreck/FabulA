"""Model probe (2026-11-21, owner): how long each Gemini and OpenRouter model takes to answer a real-size request, and whether it answers
at all when it is given much more time than in play. Off unless PROBE_RUN is set (a run name). The scheduler (/internal/resolve_turn,
every 5 minutes) tests ONE model per run, after its normal work, with the time the function has left (about 4.5 minutes at most:
Vercel stops a function at 300 s). Results are kept in gm_usage, record `probe:<run>`; read them with SQL or the host command gm_usage.

The request is the real `play` instructions for Fear Itself (about 40k tokens) and a small free_query envelope, the size of a normal
level 3 call. OpenRouter is called with streaming, to see when the first token arrives (time to first token) apart from the total.
Each Gemini strong model uses one of its 20 daily requests; each OpenRouter model one of the 50 free requests.
"""
import json
import os
import time

from . import config

ENVELOPE = json.dumps({"mode": "intake", "request": {"kind": "free_query", "text": "What time of day is it, and where am I?"},
                       "note": "Answer with one JSON object as the state contract says."})


def _models():
    names = os.environ.get("PROBE_MODELS", "")
    if names.strip():
        return [m.strip() for m in names.split(",") if m.strip()]
    return list(dict.fromkeys(config.GEMINI_STRONG_MODELS + config.GEMINI_LIGHT_MODELS))


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


def _openrouter(model, system, user, wait):
    """Streams one answer; returns timing and outcome. Never raises."""
    import urllib.error
    import urllib.request
    name = model[len(config.OPENROUTER_PREFIX):]
    body = {"model": name, "stream": True, "max_tokens": config.OPENROUTER_MAX_TOKENS,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "reasoning": {"effort": "medium"}, "response_format": {"type": "json_object"}}
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


def _gemini(model, system, user, wait):
    from .gm import GeminiGM
    gm = GeminiGM(usage=None)
    gm._timeout_override = int(wait)
    t0 = time.monotonic()
    out = {}
    try:
        text = gm._generate(model, "medium", system, user)
        out.update(answer_chars=len(text), json_ok=_is_json(text), answered=bool(text.strip()))
    except Exception as e:
        out.update(error=f"{type(e).__name__}: {str(e)[:200]}", answered=False)
    out["total_s"] = round(time.monotonic() - t0, 1)
    m = getattr(gm, "_meta", {}) or {}
    out.update({k: m.get(k) for k in ("tokens_in", "tokens_out", "tokens_thought") if m.get(k) is not None})
    return out


def run_one(store, seconds_left, now_iso):
    """Tests the next model of the run named by PROBE_RUN, if any, within `seconds_left`. Returns a short summary or None."""
    run = os.environ.get("PROBE_RUN", "").strip()
    if not run or seconds_left < config.PROBE_MIN_SECONDS:
        return None
    key = f"probe:{run}"
    doc, ver = store.get("usage", key)
    if doc is None:
        doc = {"id": key, "run": run, "started": now_iso, "queue": _models(), "results": []}
    if not doc["queue"]:
        return {"probe": run, "done": True}
    model = doc["queue"].pop(0)
    doc["current"] = model
    try:  # claim the model first, so two scheduler runs never probe the same one
        store.put("usage", key, doc, ver)
    except Exception:
        return None
    doc, ver = store.get("usage", key)
    wait = max(10, int(seconds_left) - 10)
    system = _system()
    res = (_openrouter if model.startswith(config.OPENROUTER_PREFIX) else _gemini)(model, system, ENVELOPE, wait)
    res.update(model=model, at=now_iso, wait_s=wait, system_chars=len(system))
    for _ in range(3):
        doc["results"].append(res)
        doc.pop("current", None)
        try:
            store.put("usage", key, doc, ver)
            break
        except Exception:
            doc, ver = store.get("usage", key)
    return {"probe": run, "model": model, "answered": res.get("answered"), "total_s": res.get("total_s")}
