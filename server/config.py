"""Environment-driven settings. Nothing here touches the network."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GM_DIR = ROOT / "gm"
# Adventures hold secrets, so they are NOT in this public repository. They are read from a private GitHub repository
# with a read-only token. ADVENTURES_DIR (a local folder) overrides that, for development and tests only.
ADVENTURES_REPO = os.environ.get("ADVENTURES_REPO", "jvpreck/rpg_adventures")
ADVENTURES_REF = os.environ.get("ADVENTURES_REF", "main")
ADVENTURE_SEEDS_FOLDER = "seeds"  # a sub-folder of the adventures repository; the adventure listing never looks inside it
ADVENTURE_SEEDS_FOLDER = "seeds"  # a sub-folder of the adventures repository; the adventure listing never looks inside it
ADVENTURES_CACHE_SECONDS = int(os.environ.get("ADVENTURES_CACHE_SECONDS", "300"))
ADVENTURES_DIR = Path(os.environ["ADVENTURES_DIR"]) if os.environ.get("ADVENTURES_DIR") else None
RULESETS_DIR = ROOT / "rulesets"

# Two tiers. "turn" is the strong, scarce model: closing a turn with every player's actions, and checking a character sheet.
# "light" is the fast, plentiful model: everything a single player does between turns. GEMINI_MODEL is the old name for the light model.
def _models(env, legacy, default):
    """An ordered list of model names: the old single-model setting (if set) first, then the list setting, or the default list."""
    listed = [m.strip() for m in os.environ.get(env, "").split(",") if m.strip()]
    first = [m for m in (os.environ.get(x, "").strip() for x in legacy) if m]
    out = []
    for m in first + (listed or default):
        if m not in out:
            out.append(m)
    return out


# Ordered by what the owner's free-tier key can actually do (probed live 2026-11-09, see README "Gemini models"): the first model that answers
# is used; a model that times out, answers a 5xx or is over its quota is skipped for a while and the next one answers.
# STRONG is for closing a turn (little traffic, quality first, 20 requests a day per model on the free tier); LIGHT is for what a player does
# between turns (many requests, speed and a high daily allowance first).
GEMINI_STRONG_MODELS = _models("GEMINI_STRONG_MODELS", ["GEMINI_MODEL_TURN"], ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.8-flash"])
GEMINI_LIGHT_MODELS = _models("GEMINI_LIGHT_MODELS", ["GEMINI_MODEL_LIGHT", "GEMINI_MODEL"], ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash"])
# OpenRouter (2026-11-11): a second provider, used only after every Gemini model of a tier has failed (a whole-provider outage such as the one of
# 2026-11-10, 15:05 to about 04:45 UTC). Free models (`:free`) only: 20 requests a minute and 50 a day for the whole account (1,000 after a one-time
# purchase of 10 credits), no token limit. Entries are named `openrouter:<model id>` in the chains. On when OPENROUTER_API_KEY is set
# (OPENROUTER=off turns it off). 2026-11-11 evening: the first choice failed in real use (MiniMax M3.1 Flash no longer free, Nemotron 3 Super removed,
# Nemotron 3 Ultra empty answers); the lists follow OpenRouter's free list of 2026-11-09/11 (approved by the owner).
OPENROUTER_PREFIX = "openrouter:"
OPENROUTER_ENABLED = bool(os.environ.get("OPENROUTER_API_KEY")) and os.environ.get("OPENROUTER", "on").lower() not in ("off", "0", "false", "no")
OPENROUTER_URL = os.environ.get("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")
OPENROUTER_STRONG_MODELS = _models("OPENROUTER_STRONG_MODELS", [], ["nvidia/nemotron-3-ultra-550b-a55b:free", "google/gemma-4-31b-it:free",
                                                                   "nvidia/nemotron-3.5-super-vl:free"])
OPENROUTER_LIGHT_MODELS = _models("OPENROUTER_LIGHT_MODELS", [], ["nvidia/nemotron-3.5-lightning:free", "google/gemma-4-26b-a4b-it:free",
                                                                 "nvidia/nemotron-3.5-super-vl:free"])
# Output room for reasoning models: without it a free reasoning model can spend the provider's default on thinking and return no content.
OPENROUTER_MAX_TOKENS = int(os.environ.get("OPENROUTER_MAX_TOKENS", "24000"))
# Games whose AI Master calls try OpenRouter before Gemini (comma-separated game ids), for a live test of the fallback without an outage.
OPENROUTER_TEST_GAMES = {g.strip() for g in os.environ.get("OPENROUTER_TEST_GAMES", "").split(",") if g.strip()}
OPENROUTER_TIMEOUT_SECONDS = int(os.environ.get("OPENROUTER_TIMEOUT_SECONDS", "110"))  # the last model of a chain; free reasoning models are slow
OPENROUTER_QUICK_TIMEOUT_SECONDS = int(os.environ.get("OPENROUTER_QUICK_TIMEOUT_SECONDS", "75"))  # a model with another behind it
if OPENROUTER_ENABLED:
    GEMINI_STRONG_MODELS = GEMINI_STRONG_MODELS + [OPENROUTER_PREFIX + m for m in OPENROUTER_STRONG_MODELS]
    GEMINI_LIGHT_MODELS = GEMINI_LIGHT_MODELS + [OPENROUTER_PREFIX + m for m in OPENROUTER_LIGHT_MODELS]

GEMINI_MODEL_TURN = GEMINI_STRONG_MODELS[0]   # the first choice of each tier (the names older code and the host status use)
GEMINI_MODEL_LIGHT = GEMINI_LIGHT_MODELS[0]
GEMINI_THINKING_LEVEL = os.environ.get("GEMINI_THINKING_LEVEL", "medium")
GEMINI_THINKING_LEVEL_TURN = os.environ.get("GEMINI_THINKING_LEVEL_TURN", GEMINI_THINKING_LEVEL)
# TLR-03-018: thinking effort per kind of request (minimal, low, medium or high). A kind not listed uses GEMINI_THINKING_LEVEL; the turn close uses
# GEMINI_THINKING_LEVEL_TURN. Override all of it with a JSON object in GEMINI_THINKING_BY_KIND, for example {"free_query": "low"}.
THINKING_LEVELS = ("minimal", "low", "medium", "high")
# Measured live on 2026-11-09 (gemini-3.5-flash-lite, about 42k tokens in): minimal used 0 thinking tokens and answered in about 3.5 s, low 0 to 1k and
# 3.5 to 6 s, medium 1.4 to 2k and 7 to 8 s, high 2 to 2.7k and 9 to 10.5 s. The simple kinds (a question, bookkeeping) get `minimal`. `action`,
# `character_submission` and the turn close stay at the general default until their quality has been compared over real play.
GEMINI_THINKING_BY_KIND = {"free_query": "minimal", "setup_answers": "minimal", "join": "minimal", "game_created": "minimal", "character_confirm": "minimal",
                           "thread_note": "minimal", "standing_orders": "minimal", "pause": "minimal", "resume": "minimal", "message": "low", "decision": "low"}
try:
    GEMINI_THINKING_BY_KIND.update({k: v for k, v in json.loads(os.environ.get("GEMINI_THINKING_BY_KIND", "{}")).items() if v in THINKING_LEVELS})
except ValueError:
    pass
# Free-tier quotas with a little headroom (the provider's figures were 20 per day and 5 per minute, 500 per day and 10 per minute).
GEMINI_LIMITS = {
    "turn": {"rpd": int(os.environ.get("GEMINI_TURN_RPD", "18")), "rpm": int(os.environ.get("GEMINI_TURN_RPM", "4"))},
    "light": {"rpd": int(os.environ.get("GEMINI_LIGHT_RPD", "450")), "rpm": int(os.environ.get("GEMINI_LIGHT_RPM", "9"))},
    # images: Cloudflare gives 10,000 Neurons a day. klein 4B costs about 26 per 512 output tile, 5 per input tile: a 1024 picture with
    # references is about 120, a 512 reference about 26. Calls per day are kept low enough for a mix of both.
    "image": {"rpd": int(os.environ.get("IMAGE_RPD", "80")), "rpm": int(os.environ.get("IMAGE_RPM", "10"))},
    "openrouter": {"rpd": int(os.environ.get("OPENROUTER_RPD", "45")), "rpm": int(os.environ.get("OPENROUTER_RPM", "18"))},  # account-wide, all :free models
}
TURN_TIMEZONE = os.environ.get("TURN_TIMEZONE", "Europe/Madrid")  # where "the hour a turn closes" is counted
TURN_CLOSE_HOUR = int(os.environ.get("TURN_CLOSE_HOUR", "3"))  # default hour (0-23) for games whose turn is a whole number of days; -1 = exactly one interval after opening
GEMINI_QUOTA_TZ = "America/Los_Angeles"  # provider quotas reset at midnight Pacific
QUOTA_TZ = {"turn": GEMINI_QUOTA_TZ, "light": GEMINI_QUOTA_TZ, "image": "UTC", "openrouter": "UTC"}  # Cloudflare's free allowance resets at 00:00 UTC

# Illustrations (Cloudflare Workers AI, FLUX.2 klein 4B, which accepts reference images). Needs CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN; without them the option is unavailable.
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "@cf/black-forest-labs/flux-2-klein-4b")
IMAGE_SIZE = int(os.environ.get("IMAGE_SIZE", "1024"))  # every picture shown to players
IMAGE_REF_SIZE = int(os.environ.get("IMAGE_REF_SIZE", "512"))  # reference sheet images, and the largest input the model takes
# Used only for a game that has illustrations on but no style of its own (each game normally gets one, immutable, when it is created).
IMAGE_STYLE = os.environ.get("IMAGE_STYLE", "Atmospheric painterly illustration, muted colours, dramatic light, no text, no letters, no watermark.")
IMAGE_BUCKET = os.environ.get("IMAGE_BUCKET", "gm-images")
IMAGE_INLINE_SIZE = int(os.environ.get("IMAGE_INLINE_SIZE", "768"))  # longest side of a picture returned inline in a tool result
IMAGE_URL_TTL_SECONDS = int(os.environ.get("IMAGE_URL_TTL_SECONDS", "900"))
IMAGES_PER_TURN = int(os.environ.get("IMAGES_PER_TURN", "4"))  # most the AI Master may ask for in one response
IMAGES_PER_RUN = int(os.environ.get("IMAGES_PER_RUN", "6"))  # generation calls, a portrait takes four  # most generated per scheduler run, to stay inside the function time
IMAGE_MAX_ATTEMPTS = 2
PORTRAITS_PER_RESPONSE = 3
STYLE_MIN, STYLE_MAX = 40, 700
IMAGE_TIMEOUT_SECONDS = 25
FUNCTION_BUDGET_SECONDS = int(os.environ.get("FUNCTION_BUDGET_SECONDS", "240"))  # Vercel maxDuration is 300 (see vercel.json)
TURN_RESERVE_SECONDS = int(os.environ.get("TURN_RESERVE_SECONDS", "110"))  # no new turn is started with less than this left
GEMINI_STRUCTURED_OUTPUT = os.environ.get("GEMINI_STRUCTURED_OUTPUT", "off").lower() in ("on", "1", "true", "yes")  # the provider enforces the response schema (server/schema.py)
GEMINI_TIMEOUT_SECONDS = int(os.environ.get("GEMINI_TIMEOUT_SECONDS", "100"))  # one model call must never outlive the function
GEMINI_RETRIES = int(os.environ.get("GEMINI_RETRIES", "3"))  # extra attempts after a transient Gemini error (503 "high demand", 500, 502, 504)
GEMINI_RETRY_BASE_SECONDS = float(os.environ.get("GEMINI_RETRY_BASE_SECONDS", "2"))  # waits are base, 3x base, 9x base, with jitter
GEMINI_RETRY_BUDGET_SECONDS = float(os.environ.get("GEMINI_RETRY_BUDGET_SECONDS", "40"))  # total time spent waiting between attempts for one request
GEMINI_RETRY_MAX_CALL_SECONDS = float(os.environ.get("GEMINI_RETRY_MAX_CALL_SECONDS", "20"))  # a call that already ran longer than this (a slow 504 gateway timeout) is not retried
INLINE_IMAGE_SECONDS = int(os.environ.get("INLINE_IMAGE_SECONDS", "40"))  # pictures drawn during a player call, so they do not wait for the scheduler
AUTO_PICTURES_PER_RESPONSE = int(os.environ.get("AUTO_PICTURES_PER_RESPONSE", "3"))  # automatic place and NPC pictures written by the server per response
AUTO_PICTURES_MAX_PENDING = int(os.environ.get("AUTO_PICTURES_MAX_PENDING", "8"))  # no new automatic pictures while this many wait in a game
IMAGE_PENDING_DAYS = 3  # a picture not drawn after this long is dropped
LIGHT_MAX_WAIT_SECONDS = 8
GM_MAX_ATTEMPTS = int(os.environ.get("GM_MAX_ATTEMPTS", "2"))

TABLES = {
    "player": "gm_players",
    "adventure": "gm_adventures",
    "npc": "gm_npcs",
    "location": "gm_locations",
    "game": "gm_games",
    "character": "gm_characters",
    "npc_state": "gm_npc_states",
    "location_state": "gm_location_states",
    "submit_action": "gm_submit_actions",
    "task": "gm_tasks",
    "key": "gm_keys",
    "usage": "gm_usage",
    "image": "gm_images",
    "ruleset": "gm_rulesets",
}
RULESET_BODY_MIN, RULESET_BODY_MAX = 4000, 150_000
RULESET_DOCUMENT_MAX = 400_000  # characters of source document accepted by import_ruleset
TASK_TTL_HOURS = 48
TASK_MAX_ATTEMPTS = 5

BLOCKS = ["Morning", "Afternoon", "Evening", "Night"]
SPAN_BLOCKS = {"day": 4, "block": 1, "beat": 1}
SAY_MAX_CHARS = 500

# Idempotent requests (TLR-06-010): a request_id sent twice runs once.
REQUEST_RESULT_TTL_SECONDS = int(os.environ.get("REQUEST_RESULT_TTL_SECONDS", "3600"))  # how long a finished request's result can be served again
REQUEST_CLAIM_SECONDS = int(os.environ.get("REQUEST_CLAIM_SECONDS", "300"))  # a claim older than this is a request that died (Vercel's limit is 300 s)
REQUEST_KEEP = 5  # most remembered requests per player

# The AI Master's instructions are sent in sections chosen by the kind of request (TLR-03-010, TLR-05-007). "off" sends everything, as before.
PROMPT_SLIM = os.environ.get("PROMPT_SLIM", "on").lower() not in ("off", "0", "false", "no")

# Provider-side caching of the AI Master's instructions (TLR-03-011). "auto" tries it and falls back when the provider refuses; "off" never tries.
GEMINI_CONTEXT_CACHE = os.environ.get("GEMINI_CONTEXT_CACHE", "auto").lower()
GEMINI_CACHE_TTL_SECONDS = int(os.environ.get("GEMINI_CACHE_TTL_SECONDS", "3600"))  # how long a copy lives at the provider
CACHE_REFRESH_SECONDS = 600  # a copy with less than this left is replaced by a new one
CACHE_OFF_SECONDS = int(os.environ.get("CACHE_OFF_SECONDS", "3600"))  # after the provider refuses, wait this long before trying again
CACHE_MIN_CHARS = int(os.environ.get("CACHE_MIN_CHARS", "20000"))  # shorter instructions are not worth a copy (the provider needs about 4,000 tokens)

# What a request of one character is told about the world (TLR-03-012). "off" sends the whole world, as before.
ENVELOPE_RELEVANT = os.environ.get("ENVELOPE_RELEVANT", "on").lower() not in ("off", "0", "false", "no")
# TLR-03-014: the request is serialized without spaces and without empty values (null, "", [], {}); the state contract says a missing field is not set.
ENVELOPE_COMPACT = os.environ.get("ENVELOPE_COMPACT", "on").lower() not in ("off", "0", "false", "no")
# Server-rolled dice per request: a request that never rolls (a question, a message, setup) gets a few; an action or a decision gets enough for a turn's Blocks.
# A stream that runs out costs one retry with twice as many (`needs_dice`), so the small numbers are safe.
DICE_SMALL = (int(os.environ.get("DICE_SMALL_D6", "6")), int(os.environ.get("DICE_SMALL_D10", "3")), int(os.environ.get("DICE_SMALL_D20", "3")))
DICE_ACTION = (int(os.environ.get("DICE_ACTION_D6", "40")), int(os.environ.get("DICE_ACTION_D10", "20")), int(os.environ.get("DICE_ACTION_D20", "20")))
ENVELOPE_WORLD_NARROW_CHARS = int(os.environ.get("ENVELOPE_WORLD_NARROW_CHARS", "12000"))  # a world smaller than this is sent whole

# The strong model times out or answers 5xx on large prompts. A player waiting for a character check must not wait for that, so the check
# is made by the light model unless CHARACTER_CHECK_TIER=turn, and a strong model that has just failed is skipped for a while.
CHARACTER_CHECK_TIER = "turn" if os.environ.get("CHARACTER_CHECK_TIER", "light").lower() == "turn" else "light"
STRONG_BREAKER_SECONDS = int(os.environ.get("STRONG_BREAKER_SECONDS", "900"))  # 0 never skips the strong model

# A model that has another behind it in its list gives up fast: one quick retry, a short wait, a shorter timeout (the last one gets the full ones).
CHAIN_QUICK_RETRIES = int(os.environ.get("CHAIN_QUICK_RETRIES", "1"))
CHAIN_QUICK_BUDGET_SECONDS = float(os.environ.get("CHAIN_QUICK_BUDGET_SECONDS", "8"))
CHAIN_TIMEOUT_SECONDS = int(os.environ.get("CHAIN_TIMEOUT_SECONDS", "45"))
# The whole list of models of one AI Master call must end well inside the function's 300 s (2026-11-11: a hung OpenRouter call used it all).
CHAIN_TOTAL_SECONDS = int(os.environ.get("CHAIN_TOTAL_SECONDS", "230"))
CHAIN_MIN_SECONDS = int(os.environ.get("CHAIN_MIN_SECONDS", "20"))  # do not start a model with less time than this left
LIGHT_BREAKER_SECONDS = int(os.environ.get("LIGHT_BREAKER_SECONDS", "120"))  # how long a failed light model is left alone (0 = not at all)

# Per-model free-tier limits (requests a minute, input tokens a minute, requests a day), read by the owner from the AI Studio "Rate limit" page of the
# project on 2026-11-09. The server counts its own calls against them and tries a model that is out of headroom last. Override with
# GEMINI_MODEL_LIMITS='{"gemini-3.6-flash": {"rpm": 10, "tpm": 1000000, "rpd": 1000}}' (e.g. on a paid tier). A model that is not listed has no limit here.
MODEL_LIMITS = {
    "gemini-3.5-flash-lite": {"rpm": 15, "tpm": 250000, "rpd": 500},
    "gemini-3.1-flash-lite": {"rpm": 15, "tpm": 250000, "rpd": 500},
    "gemini-3.6-flash": {"rpm": 5, "tpm": 250000, "rpd": 20},
    "gemini-3.5-flash": {"rpm": 5, "tpm": 250000, "rpd": 20},
    "gemini-3.8-flash": {"rpm": 5, "tpm": 250000, "rpd": 20},
    "gemini-3.7-flash": {"rpm": 5, "tpm": 250000, "rpd": 20},
}
try:
    for _m, _l in json.loads(os.environ.get("GEMINI_MODEL_LIMITS", "{}") or "{}").items():
        MODEL_LIMITS[_m] = {**MODEL_LIMITS.get(_m, {}), **_l}
except ValueError:
    pass
MODEL_LIMIT_MARGIN = float(os.environ.get("MODEL_LIMIT_MARGIN", "0.9"))  # use at most this share of a limit; the rest is for the last-resort try
CHARS_PER_TOKEN = float(os.environ.get("CHARS_PER_TOKEN", "3.5"))  # to estimate a request's input tokens before sending it
