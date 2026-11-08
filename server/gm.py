"""The AI Master call. Gemini runs at thinking level `medium`. The client is injectable for tests."""
import json
import re

from . import config


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

    def today(self):
        out = {}
        for tier in config.GEMINI_LIMITS:
            doc = self.store.get("usage", f"{tier}:{self._day(self.now_fn(), tier)}")[0] or {}
            out[tier] = {"used_today": doc.get("count", 0), "daily_limit": config.GEMINI_LIMITS[tier]["rpd"],
                         "per_minute_limit": config.GEMINI_LIMITS[tier]["rpm"],
                         "model": {"tick": config.GEMINI_MODEL_TICK, "light": config.GEMINI_MODEL_LIGHT, "image": config.IMAGE_MODEL}[tier]}
        return out


class GeminiGM:
    """Routes each request to a tier. `tick` (strong) is used for closing a tick and checking a character; everything else is `light`.
    If the strong model's daily quota is used up, or it fails with a quota or server error, the request goes to the light model and
    `last["degraded"]` says so. If the strong model is only over its per-minute limit, the request is deferred (GMBusy) and the
    scheduler tries again on its next run. If the light model is out of quota, GMBusy tells the player to try later.
    A transient server error (503 "high demand", 500, 502, 504) is retried quietly with backoff before any of that (`_generate_retrying`)."""

    def __init__(self, api_key=None, usage=None, sleep=None):
        self._client = None
        self._api_key = api_key
        self.usage = usage
        self.last = {}
        self._sleep = sleep or __import__("time").sleep

    def _get(self):
        if self._client is None:
            import os
            from google import genai
            self._client = genai.Client(api_key=self._api_key or os.environ["GEMINI_API_KEY"])
        return self._client

    def _generate(self, model, level, system, user):
        from google.genai import types
        cfg = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            thinking_config=types.ThinkingConfig(thinking_level=level),
            http_options=types.HttpOptions(timeout=config.GEMINI_TIMEOUT_SECONDS * 1000),
        )
        return self._get().models.generate_content(model=model, contents=user, config=cfg).text or ""

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
        degraded = None
        if tier == "tick":
            r = self.usage.reserve("tick") if self.usage else "ok"
            if r == "minute":
                raise GMBusy("the strong AI Master model is at its per-minute limit; the tick will be retried shortly")
            if r == "ok":
                try:
                    out = self._generate_retrying(config.GEMINI_MODEL_TICK, config.GEMINI_THINKING_LEVEL_TICK, system, user)
                    self.last = {"tier": "tick", "model": config.GEMINI_MODEL_TICK, "degraded": None}
                    return out
                except Exception as e:
                    if not self._retryable(e):
                        raise
                    degraded = "strong model unavailable (" + type(e).__name__ + ")"
            else:
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
