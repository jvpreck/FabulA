"""The AI Master call. Gemini runs at thinking level `medium`. The client is injectable for tests."""
import json
import re

from . import config, schema


class GMError(Exception):
    pass


class GMBusy(Exception):
    """The AI Master cannot be called right now because of a quota. Nothing was sent. Try again later."""


class ModelSkip(Exception):
    """A model that cannot be used right now (not free any more, removed, an empty answer): try the next model at once, never retry it."""


class GMUnavailable(Exception):
    """Gemini did not answer after the automatic retries (overloaded, down, over its own quota or too slow). Nothing was applied.
    The player must be told that Gemini has problems and that nothing was lost."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


class Usage:
    """Counts requests per tier, per day (provider day, Pacific time) and per minute, in the database, so that all server instances share it."""

    def __init__(self, store, now_fn=None, sleep=None):
        from datetime import datetime, timezone
        self.store = store
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))
        self.sleep = sleep or __import__("time").sleep

    def _day(self, now, tier="light"):
        from zoneinfo import ZoneInfo
        return now.astimezone(ZoneInfo(config.QUOTA_TZ.get(tier, config.GEMINI_QUOTA_TZ))).strftime("%Y-%m-%d")

    def reserve(self, tier):
        """'ok' and counts the request, or 'day' (daily quota used up) or 'minute' (too many in the last 60 seconds)."""
        from .db import Conflict
        lim = config.GEMINI_LIMITS[tier]
        for _ in range(4):
            now = self.now_fn()
            t = now.timestamp()
            key = f"{tier}:{self._day(now, tier)}"
            doc, ver = self.store.get("usage", key)
            doc = doc or {"id": key, "tier": tier, "day": self._day(now, tier), "count": 0, "recent": []}
            doc["recent"] = [x for x in doc.get("recent", []) if t - x < 60]
            if doc["count"] >= lim["rpd"]:
                return "day"
            if len(doc["recent"]) >= lim["rpm"]:
                return "minute"
            doc["count"] += 1
            doc["recent"].append(t)
            try:
                self.store.put("usage", key, doc, ver)
                return "ok"
            except Conflict:
                continue
        return "ok"  # heavy contention on the counter: do not block play over bookkeeping

    def reserve_waiting(self, tier):
        """For the light tier: a short wait is fine, a long one is not."""
        waited = 0
        while True:
            r = self.reserve(tier)
            if r != "minute" or waited >= config.LIGHT_MAX_WAIT_SECONDS:
                return r
            self.sleep(2)
            waited += 2

    # ---- per-model use against the provider's per-model limits (config.MODEL_LIMITS): requests and input tokens in the last minute, requests today.
    # Only this server's own calls are counted, so the numbers can only be lower than the provider's; a 429 that names a quota corrects them.
    def _model_doc(self, model):
        now = self.now_fn()
        key = f"model:{model}:{self._day(now)}"
        doc, ver = self.store.get("usage", key)
        return key, doc or {"id": key, "model": model, "day": self._day(now), "count": 0, "recent": []}, ver, now.timestamp()

    def model_state(self, model):
        key, doc, ver, t = self._model_doc(model)
        recent = [x for x in doc.get("recent", []) if t - x[0] < 60]
        return {"requests_today": doc.get("count", 0), "requests_minute": len(recent), "tokens_minute": sum(x[1] for x in recent)}

    def model_headroom(self, model, tokens=0):
        """'ok', or 'day' / 'minute' when sending a request of about `tokens` input tokens to `model` would pass (the margin of) its limits."""
        lim = config.MODEL_LIMITS.get(model)
        if not lim:
            return "ok"
        s = self.model_state(model)

        def cap(k):
            return max(1, int(lim[k] * config.MODEL_LIMIT_MARGIN)) if lim.get(k) else None

        if cap("rpd") and s["requests_today"] >= cap("rpd"):
            return "day"
        if (cap("rpm") and s["requests_minute"] >= cap("rpm")) or (cap("tpm") and s["tokens_minute"] + tokens > cap("tpm")):
            return "minute"
        return "ok"

    def model_record(self, model, tokens=0, exhausted=False):
        """Counts one answered request of `model` (`tokens` input tokens). `exhausted`: the provider says its daily quota is gone, so count it as used up."""
        from .db import Conflict
        for _ in range(4):
            key, doc, ver, t = self._model_doc(model)
            doc["recent"] = [x for x in doc.get("recent", []) if t - x[0] < 60]
            if exhausted:
                doc["count"] = max(doc["count"], int(config.MODEL_LIMITS.get(model, {}).get("rpd", doc["count"])))
            else:
                doc["count"] += 1
                doc["recent"].append([t, int(tokens or 0)])
            try:
                self.store.put("usage", key, doc, ver)
                return True
            except Conflict:
                continue
        return False

    def seconds_to_reset(self):
        """Seconds until the provider's day changes (midnight Pacific)."""
        from datetime import timedelta
        from zoneinfo import ZoneInfo
        now = self.now_fn().astimezone(ZoneInfo(config.GEMINI_QUOTA_TZ))
        nxt = (now + timedelta(days=1)).replace(hour=0, minute=0, second=5, microsecond=0)
        return int((nxt - now).total_seconds())

    def models_today(self):
        """Each listed model: what this server has sent against the limits (the provider's own page may show more)."""
        return {m: {**self.model_state(m), "limits": lim} for m, lim in config.MODEL_LIMITS.items()}

    # ---- call statistics (TLR-08-006): what every AI Master call cost, by level, tier, request type and game
    STAT_FIELDS = ("calls", "ok", "invalid_json", "rejected", "needs_dice", "failed", "retries", "cache_hit", "cache_created", "cache_off", "cache_stale", "breaker_open", "breaker_tripped", "fallback_used",
                   "tokens_in", "tokens_cached", "tokens_out", "tokens_thought", "latency_ms")

    def record(self, entry):
        """Adds one AI Master call to the day's statistics. `entry` has level, tier, mode, kind, game_id, outcome, retries, latency_ms and
        token counts (missing counts are 0). Bookkeeping never blocks play: after a few conflicts the entry is dropped."""
        from .db import Conflict
        for _ in range(4):
            now = self.now_fn()
            day = self._day(now)
            key = f"stats:{day}"
            doc, ver = self.store.get("usage", key)
            doc = doc or {"id": key, "day": day, "by": {}, "games": {}}
            label = "|".join(str(entry.get(k) or "-") for k in ("level", "tier", "mode", "kind"))
            for bucket in (doc["by"].setdefault(label, {}), doc["games"].setdefault(entry.get("game_id") or "-", {})):
                for f in self.STAT_FIELDS:
                    bucket.setdefault(f, 0)
                bucket["calls"] += 1
                outcome = entry.get("outcome", "ok")
                if outcome in bucket:
                    bucket[outcome] += 1
                bucket["retries"] += int(entry.get("retries") or 0)
                if entry.get("fallback") == "used":
                    bucket["fallback_used"] += 1
                if entry.get("breaker") in ("open", "tripped"):
                    bucket["breaker_" + entry["breaker"]] += 1
                cache = (entry.get("cache") or "").split(":")[0]
                if "cache_" + cache in bucket:
                    bucket["cache_" + cache] += 1
                bucket["latency_ms"] += int(entry.get("latency_ms") or 0)
                for f in ("tokens_in", "tokens_cached", "tokens_out", "tokens_thought"):
                    bucket[f] += int(entry.get(f) or 0)
            if (entry.get("cache") or "").startswith(("off", "stale")):
                doc["cache_note"] = entry["cache"]  # the last reason the provider's cache was not used
            try:
                self.store.put("usage", key, doc, ver)
                return True
            except Conflict:
                continue
        return False

    def record_request(self, level, expected, kind, game_id, declared=0):
        """TLR-08-005: counts one player request by the level at which it was answered (not one AI Master call: see `record`).
        `by_level_kind` has `<level>|<kind>`; `moved` counts requests answered at another level than the rules expected, and
        `declared_wrong` those answered at another level than the client declared."""
        from .db import Conflict
        for _ in range(4):
            now = self.now_fn()
            day = self._day(now)
            key = f"stats:{day}"
            doc, ver = self.store.get("usage", key)
            doc = doc or {"id": key, "day": day, "by": {}, "games": {}}
            req = doc.setdefault("requests", {})
            row = req.setdefault(f"{level}|{kind}", {"count": 0, "moved": 0, "declared_wrong": 0})
            row["count"] += 1
            if expected != level:
                row["moved"] += 1
            if declared and declared != level:
                row["declared_wrong"] += 1
            g = doc.setdefault("request_games", {}).setdefault(game_id or "-", {})
            g[str(level)] = g.get(str(level), 0) + 1
            try:
                self.store.put("usage", key, doc, ver)
                return True
            except Conflict:
                continue
        return False

    def stats(self, day=None):
        """The day's call statistics (default today), with the share of input served from the provider's cache per level."""
        day = day or self._day(self.now_fn())
        doc = self.store.get("usage", f"stats:{day}")[0] or {"day": day, "by": {}, "games": {}}
        by = {}
        for label, b in doc["by"].items():
            row = dict(b)
            row["cached_share"] = round(b["tokens_cached"] / b["tokens_in"], 3) if b.get("tokens_in") else 0
            by[label] = row
        return {"day": day, "by_level_tier_mode_kind": by, "by_game": doc["games"], "cache_note": doc.get("cache_note"),
                "requests_by_level_kind": doc.get("requests", {}), "requests_by_game_level": doc.get("request_games", {})}

    def breakers(self):
        """The models that are being skipped now, with the time left and the reason."""
        now = self.now_fn().timestamp()
        out = []
        for doc, _ in self.store.find("usage"):
            if str(doc.get("id", "")).startswith("breaker:") and doc.get("until", 0) > now:
                out.append({"model": doc.get("model"), "seconds_left": int(doc["until"] - now), "reason": doc.get("reason")})
        return out

    def today(self):
        out = {}
        for tier in config.GEMINI_LIMITS:
            doc = self.store.get("usage", f"{tier}:{self._day(self.now_fn(), tier)}")[0] or {}
            out[tier] = {"used_today": doc.get("count", 0), "daily_limit": config.GEMINI_LIMITS[tier]["rpd"],
                         "per_minute_limit": config.GEMINI_LIMITS[tier]["rpm"],
                         "model": {"turn": config.GEMINI_MODEL_TURN, "light": config.GEMINI_MODEL_LIGHT, "image": config.IMAGE_MODEL,
                                   "openrouter": "free models: " + ", ".join(config.OPENROUTER_STRONG_MODELS + config.OPENROUTER_LIGHT_MODELS)}.get(tier)}
        return out


class GeminiGM:
    """Routes each request to a tier. `turn` (strong) is used for closing a turn and checking a character; everything else is `light`.
    If the strong model's daily quota is used up, or it fails with a quota or server error, the request goes to the light model and
    `last["degraded"]` says so. If the strong model is only over its per-minute limit, the request is deferred (GMBusy) and the
    scheduler tries again on its next run. If the light model is out of quota, GMBusy tells the player to try later.
    A transient server error (503 "high demand", 500, 502, 504) is retried quietly with backoff before any of that (`_generate_retrying`)."""

    def __init__(self, api_key=None, usage=None, sleep=None):
        self._client = None
        self._api_key = api_key
        self.usage = usage
        self.last = {}
        self._timeout_override = None
        self._no_thinking = set()  # models that refused thinking_level
        self._breakers = {}  # model -> {"until", "reason", "checked"}: a strong model that keeps failing is left alone for a while
        self._meta = {}  # token counts and retries of the call in progress
        self._structured = config.GEMINI_STRUCTURED_OUTPUT
        self._caches = {}  # cache key -> {"name", "expires"}: the provider-side copy of an instruction text
        self._cache_off = {}  # model -> {"until", "note"}: the provider's free tier offers caching for some models only
        self._sleep = sleep or __import__("time").sleep
        self._openrouter_key = None  # tests set it; production reads OPENROUTER_API_KEY
        self._chain_deadline = None
        self.route_game = None  # the game of the current call (set by the engine), for OPENROUTER_TEST_GAMES
        self.attempts = []  # the models that failed during the current call: [{model, tier, error}]
        self._no_json_mode = set()  # OpenRouter models that refused response_format

    def _get(self):
        if self._client is None:
            import os
            from google import genai
            self._client = genai.Client(api_key=self._api_key or os.environ["GEMINI_API_KEY"])
        return self._client

    def _get_beta(self):
        """A client for the provider's v1beta API. The SDK defaults to v1, which does not serve cached content (the first live run
        got 404 on creating one); a request that refers to a cached copy must go to v1beta as well."""
        if getattr(self, "_beta_client", None) is None:
            import os
            from google import genai
            from google.genai import types
            self._beta_client = genai.Client(api_key=self._api_key or os.environ["GEMINI_API_KEY"],
                                             http_options=types.HttpOptions(api_version="v1beta"))
        return self._beta_client

    # ---- OpenRouter: the second provider (config.OPENROUTER_*). An OpenAI-style chat completion over HTTPS with the standard library.
    # Errors are turned into messages the chain already understands: 429/5xx/timeouts move on to the next model, and an account or model
    # problem (401, 402, 403, 404) is reported as "unavailable" so the next model is tried instead of failing the player's request.
    _OR_EFFORT = {"minimal": "low", "low": "low", "medium": "medium", "high": "high"}

    @staticmethod
    def _read_until(resp, deadline, name):
        """The whole body, or a timeout at `deadline`. urllib's timeout covers each socket read only, and OpenRouter keeps a slow request
        alive by sending blank padding, so without this a call could hang for the whole function (seen 2026-11-11)."""
        import time
        chunks = []
        read = getattr(resp, "read1", None) or resp.read
        while True:
            if time.monotonic() > deadline:
                raise TimeoutError(f"OpenRouter {name}: no complete answer before the deadline (timed out)")
            chunk = read(65536)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)

    def _generate_openrouter(self, model, level, system, user):
        import os
        import urllib.error
        import urllib.request
        name = model[len(config.OPENROUTER_PREFIX):]
        self._meta["provider"] = "openrouter"
        if self.usage is not None:
            r = self.usage.reserve("openrouter")
            if r != "ok":  # the account-wide free allowance; the wording lets the breaker leave the model alone for the right time
                raise Exception(f"429 RESOURCE_EXHAUSTED: OpenRouter free-model quota {'PerDay' if r == 'day' else 'PerMinute'} used up")
        body = {"model": name, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "reasoning": {"effort": self._OR_EFFORT.get(level, "medium"), "exclude": True}, "max_tokens": config.OPENROUTER_MAX_TOKENS}
        if name not in self._no_json_mode:
            body["response_format"] = {"type": "json_object"}
        timeout = self._timeout_override and config.OPENROUTER_QUICK_TIMEOUT_SECONDS or config.OPENROUTER_TIMEOUT_SECONDS
        if self._chain_deadline:
            timeout = max(1, min(timeout, self._chain_deadline - __import__("time").monotonic()))
        deadline = __import__("time").monotonic() + timeout
        while True:
            req = urllib.request.Request(config.OPENROUTER_URL, data=json.dumps(body).encode("utf-8"), method="POST", headers={
                "Authorization": "Bearer " + (self._openrouter_key or os.environ.get("OPENROUTER_API_KEY", "")),
                "Content-Type": "application/json", "HTTP-Referer": "https://fabula-rpg.vercel.app", "X-Title": "FabulA"})
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(self._read_until(resp, deadline, name).decode("utf-8"))
                break
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", "replace")[:300]
                if e.code == 400 and "response_format" in body and ("response_format" in detail or "json" in detail.lower()):
                    self._no_json_mode.add(name)  # this model has no JSON mode: ask without it (the prompt already demands JSON)
                    body.pop("response_format")
                    continue
                if e.code in (400, 401, 402, 403, 404):
                    raise ModelSkip(f"OpenRouter {e.code} for {name}: {detail}") from None
                raise Exception(f"{e.code} OpenRouter {name}: {detail}") from None
            except (TimeoutError, OSError) as e:
                raise Exception(f"timeout or connection error from OpenRouter {name}: {e}") from None
        if data.get("error"):  # some upstream failures arrive with HTTP 200: skip the model, do not retry it
            err = data["error"]
            raise ModelSkip(f"OpenRouter {name} error {err.get('code', '?')}: {str(err.get('message', ''))[:200]}")
        try:
            choice = data["choices"][0]
            text = choice["message"].get("content") or ""
            finish = choice.get("finish_reason") or choice.get("native_finish_reason")
        except (KeyError, IndexError, TypeError):
            text, finish = "", None
        self._meta["finish_reason"] = finish
        if not text.strip():
            raise ModelSkip(f"OpenRouter {name}: empty answer (finish_reason={finish})")
        u = data.get("usage") or {}
        self._meta.update(tokens_in=u.get("prompt_tokens", 0) or 0,
                          tokens_cached=(u.get("prompt_tokens_details") or {}).get("cached_tokens", 0) or 0,
                          tokens_out=u.get("completion_tokens", 0) or 0,
                          tokens_thought=(u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0) or 0)
        return text

    def _generate(self, model, level, system, user):
        if model.startswith(config.OPENROUTER_PREFIX):
            return self._generate_openrouter(model, level, system, user)
        from google.genai import types
        name = self._cached(model, system)
        base = dict(
            response_mime_type="application/json",
            http_options=types.HttpOptions(timeout=(self._timeout_override or config.GEMINI_TIMEOUT_SECONDS) * 1000),
        )

        def run(use_cache, structured):
            cfg = dict(base)
            if model not in self._no_thinking:  # a model without thinking_level (older or open models) is asked without it
                cfg["thinking_config"] = types.ThinkingConfig(thinking_level=level)
            if use_cache:  # TLR-03-011: the instructions are already at the provider; they cannot be sent again as a system instruction
                cfg["cached_content"] = name
            else:
                cfg["system_instruction"] = system
            if structured:  # TLR-03-015: the provider enforces the response's shape
                cfg["response_json_schema"] = schema.for_envelope(user)
            client = self._get_beta() if use_cache else self._get()
            return client.models.generate_content(model=model, contents=user, config=types.GenerateContentConfig(**cfg))

        use_cache = name is not None
        while True:
            try:
                resp = run(use_cache, self._structured)
                break
            except Exception as e:
                if use_cache and "cache" in f"{type(e).__name__} {e}".lower():  # expired or removed: send the text this once and make a new copy later
                    self._forget_cache(model, system)
                    self._meta["cache"] = "stale: " + str(e)[:80]
                    use_cache = False
                elif model not in self._no_thinking and self._thinking_rejected(e):  # this model has no thinking_level: remember, and ask without
                    self._no_thinking.add(model)
                    self._meta["thinking"] = "not supported by " + model
                elif self._structured and self._schema_rejected(e):  # the provider does not accept the schema: play on without it, and say so
                    self._structured = False
                    self._meta["schema_disabled"] = str(e)[:200]
                else:
                    raise
        um = getattr(resp, "usage_metadata", None)
        if um is not None:
            self._meta.update(tokens_in=getattr(um, "prompt_token_count", 0) or 0, tokens_cached=getattr(um, "cached_content_token_count", 0) or 0,
                              tokens_out=getattr(um, "candidates_token_count", 0) or 0, tokens_thought=getattr(um, "thoughts_token_count", 0) or 0)
        return resp.text or ""

    # ---- TLR-03-011: the instructions are the same for every request of a game (and mostly for every game), so they are stored once at the
    # provider (explicit context caching) and each request refers to the copy. Where the provider does not offer it (the free tier, a model
    # without it) the first attempt is refused, the server notes that, sends the text as before, and tries again after CACHE_OFF_SECONDS.
    @staticmethod
    def _cache_key(model, system):
        import hashlib
        return hashlib.sha256((model + "\0" + system).encode("utf-8")).hexdigest()[:32]

    def _forget_cache(self, model, system):
        key = self._cache_key(model, system)
        self._caches.pop(key, None)
        if self.usage is not None:
            try:
                doc, ver = self.usage.store.get("usage", f"cache:{key}")
                if doc is not None:
                    doc["expires"] = 0
                    self.usage.store.put("usage", f"cache:{key}", doc, ver)
            except Exception:
                pass

    def _cached(self, model, system):
        """The name of a provider-side copy of `system` for `model` (made now if there is none), or None to send the text."""
        import time
        if config.GEMINI_CONTEXT_CACHE == "off" or len(system) < config.CACHE_MIN_CHARS:
            return None
        now = time.time()
        off = self._cache_off.get(model)
        if (off is None or now >= off["until"]) and self.usage is not None:  # another instance may already have been refused for this model
            try:
                note = self.usage.store.get("usage", f"cache:off:{model}")[0]
                if note and note.get("until", 0) > now:
                    off = self._cache_off[model] = {"until": note["until"], "note": note.get("reason", "")}
            except Exception:
                pass
        if off is not None and now < off["until"]:
            self._meta.setdefault("cache", "off" + (": " + off["note"] if off["note"] else ""))
            return None
        key = self._cache_key(model, system)
        entry = self._caches.get(key)
        if entry is None and self.usage is not None:  # another instance may have made it
            try:
                doc = self.usage.store.get("usage", f"cache:{key}")[0]
                if doc:
                    entry = {"name": doc["name"], "expires": doc["expires"]}
            except Exception:
                entry = None
        if entry and entry["expires"] - now > config.CACHE_REFRESH_SECONDS:
            self._caches[key] = entry
            self._meta["cache"] = "hit"
            return entry["name"]
        from google.genai import types
        try:
            made = self._get_beta().caches.create(model=model, config=types.CreateCachedContentConfig(
                system_instruction=system, ttl=f"{config.GEMINI_CACHE_TTL_SECONDS}s", display_name="fabula-" + key[:12]))
        except Exception as e:
            until = now + (60 if self._transient(e) else config.CACHE_OFF_SECONDS)
            note = f"{type(e).__name__} {e}"[:120]
            self._cache_off[model] = {"until": until, "note": note}
            self._meta["cache"] = "off: " + note
            if self.usage is not None and not self._transient(e):  # tell the other instances, so each does not ask again
                try:
                    doc, ver = self.usage.store.get("usage", f"cache:off:{model}")
                    self.usage.store.put("usage", f"cache:off:{model}", {"id": f"cache:off:{model}", "until": until, "reason": note}, ver)
                except Exception:
                    pass
            return None
        entry = {"name": made.name, "expires": now + config.GEMINI_CACHE_TTL_SECONDS}
        self._caches[key] = entry
        if self.usage is not None:
            try:
                doc, ver = self.usage.store.get("usage", f"cache:{key}")
                self.usage.store.put("usage", f"cache:{key}", {"id": f"cache:{key}", "model": model, **entry}, ver)
            except Exception:
                pass
        self._meta["cache"] = "created"
        return entry["name"]

    @staticmethod
    def _thinking_rejected(e):
        m = f"{type(e).__name__} {e}".lower()
        return "thinking" in m and ("400" in m or "invalid_argument" in m or "not supported" in m or "unsupported" in m)

    @staticmethod
    def _schema_rejected(e):
        m = f"{type(e).__name__} {e}".lower()
        # the provider's refusal of a schema is often a bare "400 INVALID_ARGUMENT: Request contains an invalid argument" (seen 2026-11-09),
        # and the schema is the only argument that changes with this setting, so any such 400 counts
        return "400" in m or "invalid_argument" in m or "invalid argument" in m

    @staticmethod
    def _retryable(e):
        if isinstance(e, ModelSkip):
            return True
        m = f"{type(e).__name__} {e}".lower()
        return any(x in m for x in ("429", "resource_exhausted", "quota", "500", "502", "503", "504", "unavailable", "overloaded", "high demand", "deadline", "timeout", "timed out"))

    @staticmethod
    def _transient(e):
        """A short-lived server-side failure (503 "high demand", 500, 502, 504) that is worth retrying quietly.
        Quota errors (429) and timeouts are NOT transient: a retry would not help or would outlive the function."""
        if isinstance(e, ModelSkip):
            return False
        code = getattr(e, "code", None) or getattr(e, "status_code", None)
        if code in (500, 502, 503, 504):
            return True
        m = f"{type(e).__name__} {e}".lower()
        if any(x in m for x in ("429", "resource_exhausted", "quota", "deadline", "timeout", "timed out")):
            return False
        return bool(re.search(r"\b(500|502|503|504)\b", m)) or any(x in m for x in ("unavailable", "overloaded", "high demand", "internal error"))

    def _generate_retrying(self, model, level, system, user, retries=None, budget=None):
        """One model call, retried with exponential backoff and jitter on transient errors, within a total waiting budget."""
        retries = config.GEMINI_RETRIES if retries is None else retries
        budget = config.GEMINI_RETRY_BUDGET_SECONDS if budget is None else budget
        import random
        import time
        waited = 0.0
        attempt = 0
        while True:
            started = time.monotonic()
            try:
                return self._generate(model, level, system, user)
            except Exception as e:
                took = time.monotonic() - started
                if attempt >= retries or not self._transient(e):
                    raise
                if took > config.GEMINI_RETRY_MAX_CALL_SECONDS:  # a 504 that came back after ~100 s is a timeout: retrying costs another 100 s
                    raise
                delay = config.GEMINI_RETRY_BASE_SECONDS * (3 ** attempt) * (1 + random.random() * 0.25)
                if waited + took + delay > budget:  # the budget is total time, calls included
                    raise
                self._sleep(delay)
                waited += took + delay
                attempt += 1

    supports_effort = True  # call() accepts `effort`, the thinking level for this request (TLR-03-018)

    def call(self, system: str, user: str, tier: str = "light", effort: str | None = None) -> str:
        import time
        self._meta = {}
        t0 = time.monotonic()
        try:
            return self._call(system, user, tier, effort)
        finally:
            self._meta["latency_ms"] = int((time.monotonic() - t0) * 1000)
            self.last_meta = dict(self._meta)

    last_meta = {}

    # ---- circuit breaker: when the strong model times out or answers 5xx, every request would wait for its full timeout (100 s) before the
    # light model answers, which is longer than a player's client waits. After one such failure the strong model is skipped for
    # STRONG_BREAKER_SECONDS, by every server instance (the note is in the database), and the light model answers at once.
    def _breaker(self, model):
        """The open breaker of `model` as {"until", "reason"}, or None."""
        import time
        now = time.time()
        b = self._breakers.get(model)
        if b is None or b["checked"] < now - 20:  # the shared note is read at most every 20 seconds
            note = None
            if self.usage is not None:
                try:
                    note = self.usage.store.get("usage", f"breaker:{model}")[0]
                except Exception:
                    note = None
            b = self._breakers[model] = {"until": (note or {}).get("until", 0), "reason": (note or {}).get("reason", ""), "checked": now}
        return b if b["until"] > now else None

    def _trip_breaker(self, model, e, seconds=None):
        import time
        seconds = config.STRONG_BREAKER_SECONDS if seconds is None else seconds
        if seconds <= 0:
            return
        quota = self._quota_kind(e)
        if quota == "day":  # the daily quota is gone: nothing helps until the provider's day changes
            seconds = self.usage.seconds_to_reset() if self.usage is not None else 3600
            if self.usage is not None:
                try:
                    self.usage.model_record(model, exhausted=True)
                except Exception:
                    pass
        elif quota == "minute":  # a per-minute limit: the provider says when to come back (default a little over a minute)
            m = re.search(r"retrydelay\W+(\d+(?:\.\d+)?)s", str(e).lower())
            seconds = min(seconds, int(float(m.group(1))) + 2) if m else min(seconds, 65)
        now = time.time()
        reason = f"{type(e).__name__} {e}"[:120]
        self._breakers[model] = {"until": now + seconds, "reason": reason, "checked": now}
        self._meta["breaker"] = "tripped"
        self._write_breaker(model, now + seconds, reason)

    @staticmethod
    def _quota_kind(e):
        """'day' or 'minute' when the error is a quota (429) answer that names the limit that was hit, else None."""
        m = f"{type(e).__name__} {e}".lower().replace(" ", "")
        if "429" not in m and "resource_exhausted" not in m and "quota" not in m:
            return None
        if "perday" in m:
            return "day"
        if "perminute" in m:
            return "minute"
        return None

    def _close_breaker(self, model):
        """The strong model answered: forget an earlier failure."""
        if self._breakers.get(model, {}).get("until", 0) or self._breakers.get(model) is None:
            self._breakers[model] = {"until": 0, "reason": "", "checked": __import__("time").time()}
            self._write_breaker(model, 0, "", only_if_present=True)

    def _write_breaker(self, model, until, reason, only_if_present=False):
        if self.usage is None:
            return
        try:
            doc, ver = self.usage.store.get("usage", f"breaker:{model}")
            if doc is None and only_if_present:
                return
            self.usage.store.put("usage", f"breaker:{model}", {"id": f"breaker:{model}", "model": model, "until": until, "reason": reason,
                                                                "at": __import__("time").time()}, ver)
        except Exception:
            pass

    def _call(self, system: str, user: str, tier: str = "light", effort: str | None = None) -> str:
        self.attempts = []
        self._chain_deadline = None  # set by the first _answer: the strong and the light list share one time budget
        effort = effort if effort in config.THINKING_LEVELS else None
        degraded = None
        if tier == "turn":
            chain = config.GEMINI_STRONG_MODELS
            if all(self._breaker(m) for m in chain):  # every strong model has just failed: do not wait for them again, and do not spend their quota
                self._meta["breaker"] = "open"
                br = self._breaker(chain[0])
                degraded = f"strong models skipped for {int(br['until'] - __import__('time').time())} more seconds after: {br['reason']}"
            else:
                r = self.usage.reserve("turn") if self.usage else "ok"
                if r == "minute":
                    raise GMBusy("the strong AI Master model is at its per-minute limit; the turn will be retried shortly")
                if r == "ok":
                    out, note = self._answer(chain, "turn", effort or config.GEMINI_THINKING_LEVEL_TURN, system, user, config.STRONG_BREAKER_SECONDS, degraded)
                    if out is not None:
                        return out
                    degraded = note
                else:
                    degraded = "strong model daily quota used up"
        r = (self.usage.reserve_waiting("light") if self.usage else "ok")
        if r != "ok":
            raise GMBusy("the AI Master is busy right now (request quota). Please try again in a few minutes"
                         if r == "minute" else "the AI Master has reached its daily request quota. Please try again tomorrow")
        out, note = self._answer(config.GEMINI_LIGHT_MODELS, "light", effort or config.GEMINI_THINKING_LEVEL, system, user, config.LIGHT_BREAKER_SECONDS, degraded, final=True)
        return out

    # ---- an ordered list of models per tier. The first one that answers is used. A model that times out, answers a 5xx or is over its quota
    # is left alone for `seconds` (a note in the database, shared by every instance) and the next one is tried; a model that has another behind
    # it gives up fast (one quick retry, a shorter timeout); models that were just skipped are tried last. Found 2026-11-09: three 503s from
    # the light model failed a player's step, and the strong model had not answered anything for a day.
    def _answer(self, chain, tier, level, system, user, seconds, degraded, final=False):
        """(answer, degraded note), or (None, note) when every model of the list failed in a way another model might not (`final`: raise)."""
        chain = list(chain)
        if self.route_game and self.route_game in config.OPENROUTER_TEST_GAMES:  # live test: OpenRouter first for this game only
            chain = [m for m in chain if m.startswith(config.OPENROUTER_PREFIX)] + [m for m in chain if not m.startswith(config.OPENROUTER_PREFIX)]
            self._meta["routing"] = "openrouter_test_game"
        self._meta["thinking_level"] = level
        tokens = int((len(system) + len(user)) / config.CHARS_PER_TOKEN)
        over = {}
        for m in chain:  # a model that has passed its own limits is tried after the ones that have room, like a skipped one
            try:
                over[m] = self.usage.model_headroom(m, tokens) if self.usage is not None else "ok"
            except Exception:
                over[m] = "ok"
        free = [m for m in chain if not self._breaker(m) and over[m] == "ok"]
        order = free + [m for m in chain if m not in free and not self._breaker(m)] + [m for m in chain if self._breaker(m)]
        if order[0] != chain[0] and over[chain[0]] != "ok" and not self._breaker(chain[0]):
            self._meta["limit"] = f"{chain[0]} out of {over[chain[0]]} headroom"
        last_error = None
        import time as _t
        self._chain_deadline = self._chain_deadline or (_t.monotonic() + config.CHAIN_TOTAL_SECONDS)
        for i, model in enumerate(order):
            left = self._chain_deadline - _t.monotonic()
            if left < config.CHAIN_MIN_SECONDS:  # no time for another model: stop here rather than outlive the function
                self.attempts.append({"model": model, "tier": tier, "error": f"not tried: {int(left)} s left of the call's time budget"})
                last_error = last_error or TimeoutError("the call's time budget ran out")
                break
            quick = i < len(order) - 1
            self._timeout_override = config.CHAIN_TIMEOUT_SECONDS if quick else None
            if not model.startswith(config.OPENROUTER_PREFIX) and left < (self._timeout_override or config.GEMINI_TIMEOUT_SECONDS):
                self._timeout_override = max(5, int(left))  # Gemini: never wait longer than the call's time budget allows
            try:
                out = self._generate_retrying(model, level, system, user,
                                              retries=config.CHAIN_QUICK_RETRIES if quick else None,
                                              budget=config.CHAIN_QUICK_BUDGET_SECONDS if quick else None)
            except Exception as e:
                if not self._retryable(e):
                    raise
                last_error = e
                self.attempts.append({"model": model, "tier": tier, "error": f"{type(e).__name__}: {str(e)[:160]}"})
                if len(chain) > 1 or tier == "turn":  # a lone light model has nothing to be skipped for; the strong tier skips to the light models
                    self._trip_breaker(model, e, seconds=seconds)
                continue
            finally:
                self._timeout_override = None
            if len(chain) > 1 or tier == "turn":
                self._close_breaker(model)
            if self.usage is not None:
                try:
                    self.usage.model_record(model, self._meta.get("tokens_in") or tokens)
                except Exception:
                    pass
            # 2026-11-11 (owner): any strong model is a full answer and a light model is normal for a light request; only a strong request
            # answered by a light model is `degraded` (the note carried in from the strong chain). Another model of the same list is `fallback`.
            fallback = None
            if model != chain[0]:
                self._meta["fallback"] = "used"
                fallback = f"{tier} model {chain[0]} unavailable, answered by {model}"
            provider = "openrouter" if model.startswith(config.OPENROUTER_PREFIX) else "gemini"
            self._meta["provider"] = provider
            self.last = {"tier": tier, "model": model, "provider": provider, "degraded": degraded, "fallback": fallback,
                         "failed_before": [a["model"] for a in self.attempts]}
            return out, degraded
        note = (degraded + "; " if degraded else "") + f"{tier} models unavailable ({type(last_error).__name__})"
        if final:
            raise GMUnavailable(type(last_error).__name__ + ": " + str(last_error)[:200]) from last_error
        return None, note


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.I)


def parse(text: str) -> dict:
    t = _FENCE.sub("", (text or "").strip())
    try:
        data = json.loads(t)
    except json.JSONDecodeError as e:
        raise GMError(f"GM returned invalid JSON: {e}")
    if not isinstance(data, dict):
        raise GMError("GM response is not an object")
    data.setdefault("status", "ok")
    for k in ("state_changes", "events", "decisions", "messages", "dice_log", "errors", "shared_digest"):
        data.setdefault(k, [])
    data.setdefault("results", {})
    if not isinstance(data["results"], dict):
        raise GMError("results must be an object keyed by recipient")
    return data
