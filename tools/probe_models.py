"""Probes every text-capable Gemini model on the key in GEMINI_API_KEY (the documentation of what a free tier allows does not match reality: probe it).
Run from any folder: python tools/probe_models.py. Environment: PROBE_PASSES (default ABCD), PROBE_ONLY (comma list), PROBE_API (v1beta), PROBE_OUT.
Four passes, results written to model_probe.json (in the current folder) after each step.
  A  metadata, reachability and speed: a tiny question, with and without thinking_level
  B  the full-size prompt (about 55,000 tokens) asked twice: speed, implicit caching (cached tokens on the second call), per-minute limits
  C  explicit caching: a small cache on v1beta (storage quota)
  D  the real tasks: a character check (must end in a verdict) and an autonomous action (must carry its parse), with the contract checks
Reads GEMINI_API_KEY from the environment. Prints no key."""
import json
import os
import re
import sys
import time

HERE = os.getcwd()  # the results are written here
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "tests")]
import conftest  # noqa: E402,F401  (the tests' fixture adventure)

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

from server import config, files, prompt  # noqa: E402

OUT = os.path.join(HERE, os.environ.get("PROBE_OUT", "model_probe.json"))
MODELS = [
    "gemini-4-argon", "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite", "gemini-3.1-pro-preview", "gemini-3-flash-preview", "gemini-2.5-flash", "gemini-2.5-flash-lite",
    "gemini-2.5-pro", "gemma-4-26b-a4b-it", "gemma-4-31b-it",
]
only = os.environ.get("PROBE_ONLY")
if only:
    MODELS = [m for m in MODELS if m in only.split(",")]
PASSES = os.environ.get("PROBE_PASSES", "ABCD")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options=types.HttpOptions(timeout=100000, **({"api_version": os.environ["PROBE_API"]} if os.environ.get("PROBE_API") else {})))
beta = genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options=types.HttpOptions(api_version="v1beta", timeout=60000))
results = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}


def save():
    json.dump(results, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def err(e):
    m = re.sub(r"\s+", " ", f"{type(e).__name__} {e}")
    limits = re.findall(r"limit: (\d+)", m) + re.findall(r"limit=(\d+)", m)
    metric = re.findall(r"metric: ([\w./]+)", m) + re.findall(r"quotaId': '([\w-]+)", m)
    return {"error": m[:230], "limits": limits[:2], "metric": metric[:2]}


def ask(model, system, user, level="low", json_mode=True, timeout=100):
    cfg = dict(response_mime_type="application/json" if json_mode else None)
    if system:
        cfg["system_instruction"] = system
    if level:
        cfg["thinking_config"] = types.ThinkingConfig(thinking_level=level)
    cfg["http_options"] = types.HttpOptions(timeout=timeout * 1000)
    t = time.time()
    r = client.models.generate_content(model=model, contents=user, config=types.GenerateContentConfig(**{k: v for k, v in cfg.items() if v is not None}))
    um = r.usage_metadata
    return {"seconds": round(time.time() - t, 1), "text": (r.text or "")[:80],
            "tokens_in": getattr(um, "prompt_token_count", None), "tokens_cached": getattr(um, "cached_content_token_count", 0) or 0,
            "tokens_out": getattr(um, "candidates_token_count", None), "tokens_thought": getattr(um, "thoughts_token_count", 0) or 0}


adv = files.adventure_record_from_file(files.adventure_files()["test_adventure"])
BIG = prompt.system_prompt("fear_itself", adv, None, "play", ())
print(f"full instructions: {len(BIG)} characters", flush=True)

# ------------------------------------------------------------------ A
if "A" in PASSES:
    for m in MODELS:
        r = results.setdefault(m, {})
        try:
            info = client.models.get(model=m)
            r["meta"] = {"display": info.display_name, "input_limit": info.input_token_limit, "output_limit": info.output_token_limit,
                         "actions": list(info.supported_actions or []), "thinking": getattr(info, "thinking", None), "version": info.version}
        except Exception as e:
            r["meta"] = err(e)
        for label, kw in (("tiny_default", dict(level=None)), ("tiny_thinking_low", dict(level="low"))):
            try:
                r[label] = {"ok": True, **ask(m, None, 'Reply with {"ok": true}', timeout=40, **kw)}
            except Exception as e:
                r[label] = {"ok": False, **err(e)}
        t = r["tiny_default"]
        print(f"A {m:26s} default: {'OK  %.1fs' % t['seconds'] if t['ok'] else 'ERR ' + t['error'][:70]:40s} | thinking_level: {'ok' if r['tiny_thinking_low']['ok'] else 'refused'}", flush=True)
        save()

# ------------------------------------------------------------------ B
if "B" in PASSES:
    for m in MODELS:
        r = results.setdefault(m, {})
        if not r.get("tiny_default", {}).get("ok"):
            continue
        level = "medium" if r.get("tiny_thinking_low", {}).get("ok") else None
        r["full"] = {}
        for label in ("cold", "warm"):
            try:
                r["full"][label] = {"ok": True, **ask(m, BIG, 'Reply with {"ok": true}', level=level, timeout=100)}
            except Exception as e:
                r["full"][label] = {"ok": False, **err(e)}
                break
        f = r["full"]
        print(f"B {m:26s} cold: {('%.1fs in=%s' % (f['cold']['seconds'], f['cold']['tokens_in'])) if f['cold']['ok'] else 'ERR ' + f['cold']['error'][:60]:34s} | warm: " +
              (('%.1fs cached=%s' % (f['warm']['seconds'], f['warm']['tokens_cached'])) if f.get('warm', {}).get('ok') else 'n/a'), flush=True)
        save()

# ------------------------------------------------------------------ C
if "C" in PASSES:
    text = "The mill stands by the river and has stood there for two hundred years. " * 400
    for m in MODELS:
        r = results.setdefault(m, {})
        if not r.get("tiny_default", {}).get("ok"):
            continue
        try:
            c = beta.caches.create(model=m, config=types.CreateCachedContentConfig(system_instruction=text, ttl="120s", display_name="fabula-probe"))
            r["explicit_cache"] = {"ok": True}
            beta.caches.delete(name=c.name)
        except Exception as e:
            r["explicit_cache"] = {"ok": False, **err(e)}
        print(f"C {m:26s} explicit cache: {'OK' if r['explicit_cache']['ok'] else r['explicit_cache']['error'][:100]}", flush=True)
        save()

# ------------------------------------------------------------------ D
from datetime import datetime, timezone  # noqa: E402
from server.db import MemoryStore  # noqa: E402
from server.engine import Engine  # noqa: E402
from server.gm import GeminiGM, parse  # noqa: E402
from scenario_checks import run_checks  # noqa: E402
from test_engine import ADV, char_pkg, new_game  # noqa: E402
from test_scenarios import D, HybridGM, PLAYER, start  # noqa: E402


def _scenario(name):
    import test_scenarios
    return next(s for s in test_scenarios.DATA["scenarios"] if s["name"] == name)


def _summary(problems, extra=""):
    bad = {k: v for k, v in problems.items() if v}
    return ("PASS" if not bad else "FAIL " + "; ".join(f"{k}: {v[0][:50]}" for k, v in bad.items())) + extra


def run_tasks(model, level):
    config.GEMINI_MODEL_LIGHT = model
    config.GEMINI_MODEL_LIGHT_FALLBACK = ""
    config.GEMINI_STRUCTURED_OUTPUT = False
    config.GEMINI_THINKING_LEVEL = level or "medium"
    out = {}
    for key, name in (("character_check", "character_check_gives_a_verdict"), ("action", "minor_action_uses_server_dice_in_order")):
        sc = _scenario(name)
        gm = HybridGM(GeminiGM(usage=None), sc)
        eng = Engine(MemoryStore(), gm, now_fn=lambda: datetime(2026, 11, 1, 9, tzinfo=timezone.utc))
        import server.engine as engine_mod
        engine_mod.make_dice = lambda *a, **k: json.loads(json.dumps(D))
        t = time.time()
        try:
            if key == "character_check":
                gid = new_game(eng, PLAYER, ADV, language="en")["game_id"]
                pkg = eng.generate_character(PLAYER, gid, "generate", concept=sc["request"]["text"])["package"]
                eng.submit_package(PLAYER, pkg["task_id"], char_pkg(concept=sc["request"]["text"]))
            else:
                gid, cid = start(eng)
                eng.submit_action(PLAYER, gid, sc["request"]["kind"], sc["request"]["text"], cid)
            user, raw, system, tier = gm.recorded
            resp = parse(raw)
            problems = run_checks(resp, json.loads(user), [], resp.get("results"))
            meta = gm.last_meta
            out[key] = {"summary": _summary(problems), "seconds": round(time.time() - t, 1), "problems": problems,
                        "tokens_out": meta.get("tokens_out"), "tokens_cached": meta.get("tokens_cached"), "answered_by": gm.last.get("model")}
        except Exception as e:
            out[key] = {"summary": "ERROR " + f"{type(e).__name__}: {str(e)[:60]}".replace("\n", " "), "seconds": round(time.time() - t, 1)}
        time.sleep(25)
    return out


if "D" in PASSES:
    for m in MODELS:
        r = results.setdefault(m, {})
        if not r.get("full", {}).get("cold", {}).get("ok"):
            continue
        level = "medium" if r.get("tiny_thinking_low", {}).get("ok") else None
        r["tasks"] = run_tasks(m, level)
        t = r["tasks"]
        print(f"D {m:26s} character check: {t['character_check']['summary']:48s} | action: {t['action']['summary']}", flush=True)
        save()
        time.sleep(40)
print("done", flush=True)
