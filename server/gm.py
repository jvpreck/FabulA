"""The AI Master call. Gemini runs at thinking level `medium`. The client is injectable for tests."""
import json
import re

from . import config, schema


class GMError(Exception):
    pass


class GMBusy(Exception):
    """The AI Master cannot be called right now because of a quota. Nothing was sent. Try again later."""


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

    # ---- call statistics (TLR-08-006): what every AI Master call cost, by level, tier, request type and game
    STAT_FIELDS = ("calls", "ok", "invalid_json", "rejected", "needs_dice", "failed", "retries", "cache_hit", "cache_created", "cache_off", "cache_stale", "breaker_open", "breaker_tripped",
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

    def stats(self, day=None):
        """The day's call statistics (default today), with the share of input served from the provider's cache per level."""
        day = day or self._day(self.now_fn())
        doc = self.store.get("usage", f"stats:{day}")[0] or {"day": day, "by": {}, "games": {}}
        by = {}
        for label, b in doc["by"].items():
            row = dict(b)
            row["cached_share"] = round(b["tokens_cached"] / b["tokens_in"], 3) if b.get("tokens_in") else 0
            by[label] = row
        return {"day": day, "by_level_tier_mode_kind": by, "by_game": doc["games"], "cache_note": doc.get("cache_note")}

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
                         "model": {"turn": config.GEMINI_MODEL_TURN, "light": config.GEMINI_MODEL_LIGHT, "image": config.IMAGE_MODEL}[tier]}
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
        self._breakers = {}  # model -> {"until", "reason", "checked"}: a strong model that keeps failing is left alone for a while
        self._meta = {}  # token counts and retries of the call in progress
        self._structured = config.GEMINI_STRUCTURED_OUTPUT
        self._caches = {}  # cache key -> {"name", "expires"}: the provider-side copy of an instruction text
        self._cache_off = {}  # model -> {"until", "note"}: the provider's free tier offers caching for some models only
        self._sleep = sleep or __import__("time").sleep

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

    def _generate(self, model, level, system, user):
        from google.genai import types
        name = self._cached(model, system)
        base = dict(
            response_mime_type="application/json",
            thinking_config=types.ThinkingConfig(thinking_level=level),
            http_options=types.HttpOptions(timeout=config.GEMINI_TIMEOUT_SECONDS * 1000),
        )

        def run(use_cache, structured):
            cfg = dict(base)
            if use_cache:  # TLR-03-011: the instructions are already at the provider; they cannot be sent again as a system instruction
                cfg["cached_content"] = name
            else:
                cfg["system_instruction"] = system
            if structured:  # TLR-03-015: the provider enforces the response's shape
                cfg["response_json_schema"] = schema.RESPONSE_SCHEMA
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
    def _schema_rejected(e):
        m = f"{type(e).__name__} {e}".lower()
        return ("400" in m or "invalid_argument" in m or "invalid argument" in m) and ("schema" in m or "response_json" in m)

    @staticmethod
    def _retryable(e):
        m = f"{type(e).__name__} {e}".lower()
        return any(x in m for x in ("429", "resource_exhausted", "quota", "500", "502", "503", "504", "unavailable", "overloaded", "high demand", "deadline", "timeout", "timed out"))

    @staticmethod
    def _transient(e):
        """A short-lived server-side failure (503 "high demand", 500, 502, 504) that is worth retrying quietly.
        Quota errors (429) and timeouts are NOT transient: a retry would not help or would outlive the function."""
        code = getattr(e, "code", None) or getattr(e, "status_code", None)
        if code in (500, 502, 503, 504):
            return True
        m = f"{type(e).__name__} {e}".lower()
        if any(x in m for x in ("429", "resource_exhausted", "quota", "deadline", "timeout", "timed out")):
            return False
        return bool(re.search(r"\b(500|502|503|504)\b", m)) or any(x in m for x in ("unavailable", "overloaded", "high demand", "internal error"))

    def _generate_retrying(self, model, level, system, user):
        """One model call, retried with exponential backoff and jitter on transient errors, within a total waiting budget."""
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
                if attempt >= config.GEMINI_RETRIES or not self._transient(e):
                    raise
                if took > config.GEMINI_RETRY_MAX_CALL_SECONDS:  # a 504 that came back after ~100 s is a timeout: retrying costs another 100 s
                    raise
                delay = config.GEMINI_RETRY_BASE_SECONDS * (3 ** attempt) * (1 + random.random() * 0.25)
                if waited + took + delay > config.GEMINI_RETRY_BUDGET_SECONDS:  # the budget is total time, calls included
                    raise
                self._sleep(delay)
                waited += took + delay
                attempt += 1

    def call(self, system: str, user: str, tier: str = "light") -> str:
        import time
        self._meta = {}
        t0 = time.monotonic()
        try:
            return self._call(system, user, tier)
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

    def _trip_breaker(self, model, e):
        import time
        if config.STRONG_BREAKER_SECONDS <= 0:
            return
        now = time.time()
        reason = f"{type(e).__name__} {e}"[:120]
        self._breakers[model] = {"until": now + config.STRONG_BREAKER_SECONDS, "reason": reason, "checked": now}
        self._meta["breaker"] = "tripped"
        self._write_breaker(model, now + config.STRONG_BREAKER_SECONDS, reason)

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

    def _call(self, system: str, user: str, tier: str = "light") -> str:
        degraded = None
        if tier == "turn":
            br = self._breaker(config.GEMINI_MODEL_TURN)
            if br:
                self._meta["breaker"] = "open"
                degraded = f"strong model skipped for {int(br['until'] - __import__('time').time())} more seconds after: {br['reason']}"
                r = None
            else:
                r = self.usage.reserve("turn") if self.usage else "ok"
            if r == "minute":
                raise GMBusy("the strong AI Master model is at its per-minute limit; the turn will be retried shortly")
            if r == "ok":
                try:
                    out = self._generate_retrying(config.GEMINI_MODEL_TURN, config.GEMINI_THINKING_LEVEL_TURN, system, user)
                    self.last = {"tier": "turn", "model": config.GEMINI_MODEL_TURN, "degraded": None}
                    self._close_breaker(config.GEMINI_MODEL_TURN)
                    return out
                except Exception as e:
                    if not self._retryable(e):
                        raise
                    degraded = "strong model unavailable (" + type(e).__name__ + ")"
                    self._trip_breaker(config.GEMINI_MODEL_TURN, e)
            elif r == "day":
                degraded = "strong model daily quota used up"
        r = (self.usage.reserve_waiting("light") if self.usage else "ok")
        if r != "ok":
            raise GMBusy("the AI Master is busy right now (request quota). Please try again in a few minutes"
                         if r == "minute" else "the AI Master has reached its daily request quota. Please try again tomorrow")
        try:
            out = self._generate_retrying(config.GEMINI_MODEL_LIGHT, config.GEMINI_THINKING_LEVEL, system, user)
        except Exception as e:
            if self._retryable(e):  # overloaded, unavailable, quota or timeout: Gemini is not answering
                raise GMUnavailable(type(e).__name__ + ": " + str(e)[:200]) from e
            raise
        self.last = {"tier": "light", "model": config.GEMINI_MODEL_LIGHT, "degraded": degraded}
        return out


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
