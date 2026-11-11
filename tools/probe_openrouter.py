"""Probe the OpenRouter free models FabulA falls back to (config.OPENROUTER_STRONG_MODELS and OPENROUTER_LIGHT_MODELS).

Run on your own machine with the key in the environment (never in a command or a file):
    PYTHONPATH=. python tools/probe_openrouter.py            # every configured model
    PYTHONPATH=. python tools/probe_openrouter.py <model id> # one model, e.g. minimax/minimax-m3.1-flash:free

For each model: a tiny request (reachability, speed), then a full-size request with the real play instructions (about 40,000 tokens) that must
come back as one JSON object. Each model costs 2 requests of the account's free allowance (50 a day without credits). Prints one line per model.
"""
import json
import os
import sys
import time

from server import config, prompt
from server.gm import GeminiGM


def one(model, system, user):
    gm = GeminiGM(usage=None)
    t = time.monotonic()
    try:
        text = gm._generate(config.OPENROUTER_PREFIX + model, "medium", system, user)
        ok = isinstance(json.loads(text.strip().strip("`").removeprefix("json")), dict)
        return f"{time.monotonic() - t:5.1f} s  json={'yes' if ok else 'no'}  in={gm._meta.get('tokens_in')} cached={gm._meta.get('tokens_cached')} out={gm._meta.get('tokens_out')}"
    except Exception as e:
        return f"{time.monotonic() - t:5.1f} s  FAILED {str(e)[:160]}"


def main():
    if not os.environ.get("OPENROUTER_API_KEY"):
        sys.exit("set OPENROUTER_API_KEY first")
    models = sys.argv[1:] or list(dict.fromkeys(config.OPENROUTER_STRONG_MODELS + config.OPENROUTER_LIGHT_MODELS))
    try:
        big = prompt.system_prompt("fear_itself", None, profile="play")
    except Exception:  # older signature: fall back to the instruction files themselves
        big = "\n\n".join(open(p, encoding="utf-8").read() for p in ("gm/protocol.md", "gm/state_and_messages.md", "rulesets/fear_itself.md"))
    ask = json.dumps({"request": {"kind": "free_query", "text": "What time is it in the game?"}, "mode": "intake"})
    for m in models:
        print(m)
        print("  tiny:", one(m, "Answer with one JSON object only.", 'Return {"ok": true}.'))
        print("  full:", one(m, big, ask))


if __name__ == "__main__":
    main()
