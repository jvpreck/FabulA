"""OpenRouter as a second provider (2026-11-11): used only after every Gemini model of a tier failed, counted against the account-wide free
allowance, and any account or model problem moves on to the next model instead of failing the player's request."""
import io
import json
import urllib.error

import pytest

from server import config
from server.db import MemoryStore
from server.gm import GeminiGM, GMUnavailable, Usage

OR_S = config.OPENROUTER_PREFIX + "nvidia/nemotron-3-ultra-550b-a55b:free"
OR_L = config.OPENROUTER_PREFIX + "minimax/minimax-m3.1-flash:free"


@pytest.fixture(autouse=True)
def chains(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_STRONG_MODELS", ["g-strong", OR_S])
    monkeypatch.setattr(config, "GEMINI_LIGHT_MODELS", ["g-light", OR_L])
    monkeypatch.setattr(config, "GEMINI_MODEL_TURN", "g-strong")
    monkeypatch.setattr(config, "GEMINI_MODEL_LIGHT", "g-light")


class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def ok_body(content='{"status": "ok"}'):
    return {"choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 1200, "completion_tokens": 80, "prompt_tokens_details": {"cached_tokens": 1000},
                      "completion_tokens_details": {"reasoning_tokens": 30}}}


class GM(GeminiGM):
    """Gemini always fails (an outage); OpenRouter answers through a fake urlopen."""

    def __init__(self, store=None):
        super().__init__(usage=Usage(store or MemoryStore()), sleep=lambda s: None)
        self._openrouter_key = "test-key"
        self.gemini_calls = 0

    def _generate(self, model, level, system, user):
        if not model.startswith(config.OPENROUTER_PREFIX):
            self.gemini_calls += 1
            raise Exception("503 UNAVAILABLE: high demand")
        return super()._generate(model, level, system, user)


@pytest.fixture
def http(monkeypatch):
    """Scripted answers for urlopen: each item is a dict (JSON body) or an int (HTTP error code)."""
    script, seen = [], []

    def urlopen(req, timeout=None):
        seen.append({"body": json.loads(req.data), "headers": dict(req.header_items()), "timeout": timeout})
        item = script.pop(0)
        if isinstance(item, int):
            raise urllib.error.HTTPError(req.full_url, item, "err", {}, io.BytesIO(b'{"error": {"message": "nope response_format"}}'))
        return Resp(json.dumps(item).encode())
    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    return script, seen


def test_when_gemini_is_down_the_turn_close_is_answered_by_openrouter(http):
    script, seen = http
    script.append(ok_body())
    gm = GM()
    assert gm.call("sys", '{"request":{}}', tier="turn", effort="high") == '{"status": "ok"}'
    assert gm.gemini_calls >= 1 and gm.last["model"] == OR_S and "answered by " + OR_S in gm.last["fallback"]
    assert gm.last["degraded"] is None and gm.last["provider"] == "openrouter"
    sent = seen[0]
    assert sent["body"]["model"] == "nvidia/nemotron-3-ultra-550b-a55b:free"
    assert sent["body"]["messages"][0] == {"role": "system", "content": "sys"} and sent["body"]["reasoning"] == {"effort": "high", "exclude": True}
    assert sent["body"]["max_tokens"] == config.OPENROUTER_MAX_TOKENS
    assert sent["body"]["response_format"] == {"type": "json_object"}
    assert sent["headers"]["Authorization"] == "Bearer test-key"
    assert gm.last_meta["provider"] == "openrouter" and gm.last_meta["tokens_in"] == 1200 and gm.last_meta["tokens_cached"] == 1000
    assert gm.last_meta["tokens_thought"] == 30 and gm.last_meta["fallback"] == "used"


def test_gemini_answering_means_openrouter_is_never_called(http):
    script, seen = http

    class Up(GM):
        def _generate(self, model, level, system, user):
            return "{}" if not model.startswith(config.OPENROUTER_PREFIX) else super()._generate(model, level, system, user)
    gm = Up()
    assert gm.call("s", "{}", tier="light") == "{}" and not seen


def test_a_model_without_json_mode_is_asked_again_without_it_and_remembered(http):
    script, seen = http
    script.extend([400, ok_body(), ok_body()])
    gm = GM()
    gm.call("s", "{}", tier="light")
    assert "response_format" in seen[0]["body"] and "response_format" not in seen[1]["body"]
    gm.call("s", "{}", tier="light")
    assert "response_format" not in seen[2]["body"]


@pytest.mark.parametrize("code", [401, 402, 403, 404, 429, 503])
def test_an_openrouter_failure_moves_on_and_the_last_one_reports_the_ai_master_unavailable(http, code):
    script, seen = http
    script.extend([code] * 10)
    gm = GM()
    with pytest.raises(GMUnavailable):
        gm.call("s", "{}", tier="light")


def test_an_error_inside_a_200_answer_and_an_empty_answer_are_failures(http):
    script, seen = http
    script.extend([{"error": {"code": 502, "message": "upstream"}}] * 5 + [ok_body("")] * 5)
    with pytest.raises(GMUnavailable):
        GM().call("s", "{}", tier="light")


def test_the_free_allowance_is_counted_for_the_whole_account(http, monkeypatch):
    monkeypatch.setitem(config.GEMINI_LIMITS, "openrouter", {"rpd": 2, "rpm": 18})
    script, seen = http
    script.extend([ok_body()] * 5)
    store = MemoryStore()
    gm = GM(store)
    gm.call("s", "{}", tier="light")
    gm.call("s", "{}", tier="light")
    with pytest.raises(GMUnavailable):
        gm.call("s", "{}", tier="light")
    assert len(seen) == 2, "the third request never reached OpenRouter"
    assert Usage(store).today()["openrouter"]["used_today"] == 2


def test_the_quick_and_final_timeouts(http):
    script, seen = http
    script.extend([503, 503, 503, 503, ok_body()])
    monkeypatch_chain = [OR_S, OR_L]
    config.GEMINI_STRONG_MODELS[:] = monkeypatch_chain  # only OpenRouter models: the first is quick, the last gets the full timeout
    GM().call("s", "{}", tier="turn")
    assert seen[0]["timeout"] == config.OPENROUTER_QUICK_TIMEOUT_SECONDS and seen[-1]["timeout"] == config.OPENROUTER_TIMEOUT_SECONDS


# ---- 2026-11-11: every engine answer names the model that answered each AI Master call made for it
from test_engine import start_solo, world  # noqa: E402,F401  (the fixture)
from test_ready import party, ready  # noqa: E402,F401


def with_model(gm, model, provider, tier="light", degraded=None, fallback=None):
    orig = gm.call

    def call(system, user, tier_=tier, **kw):
        out = orig(system, user, tier_)
        gm.last = {"tier": tier_, "model": model, "provider": provider, "degraded": degraded, "fallback": fallback}
        return out
    gm.call = lambda system, user, tier="light", **kw: call(system, user, tier)


def test_an_action_answer_names_the_model_that_answered(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    with_model(gm, OR_L, "openrouter", fallback="light model g-light unavailable, answered by " + OR_L)
    out = eng.submit_action("p_jorge", gid, "action", "search the desk", cid)
    assert out["ai_models"] == [{"mode": "intake", "kind": "action", "model": OR_L, "provider": "openrouter", "tier": "light",
                                 "fallback": "light model g-light unavailable, answered by " + OR_L}]


def test_a_database_answer_names_no_model(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    with_model(gm, "g-light", "gemini")
    out = eng.submit_action("p_jorge", gid, "free_query", "", cid, {"topic": "time"})
    assert "ai_models" not in out


def test_a_turn_close_records_the_model_provider_and_degradation_on_the_turn(world):
    eng, store, gm, clock = world
    gid, c = party(eng)
    with_model(gm, "g-light", "gemini", degraded="turn models unavailable")
    ready(eng, "p_a", gid, c["p_a"])
    out = ready(eng, "p_b", gid, c["p_b"])
    assert out["handling"] == "resolved_turn" and any(m["mode"] == "resolve_turn" and m["degraded"] for m in out["ai_models"])
    t1 = store.get("game", gid)[0]["turns"][0]
    assert t1["gm_model"] == "g-light" and t1["gm_provider"] == "gemini" and t1["gm_degraded"] == "turn models unavailable"



# ---- 2026-11-11 evening: models that cannot be used are skipped at once (never retried), the models tried are reported,
# and a game listed in OPENROUTER_TEST_GAMES tries OpenRouter first.
def test_an_empty_answer_skips_the_model_without_retrying_it(http, monkeypatch):
    monkeypatch.setattr(config, "GEMINI_LIGHT_MODELS", ["g-light", OR_L, OR_S])
    script, seen = http
    script.extend([ok_body(""), ok_body()])
    gm = GM()
    gm.call("s", "{}", tier="light")
    assert len(seen) == 2 and gm.last["model"] == OR_S, "the empty model is not asked twice"
    assert "empty answer" in gm.attempts[-1]["error"]


@pytest.mark.parametrize("code", [401, 404])
def test_a_model_that_is_gone_is_tried_once_only(http, code, monkeypatch):
    monkeypatch.setattr(config, "GEMINI_LIGHT_MODELS", ["g-light", OR_L, OR_S])
    script, seen = http
    script.extend([code, ok_body()])
    gm = GM()
    assert gm.call("s", "{}", tier="light") == '{"status": "ok"}'
    assert len(seen) == 2 and gm.last["model"] == OR_S
    assert [a["model"] for a in gm.attempts] == ["g-light", OR_L] and gm.last["failed_before"] == ["g-light", OR_L]


def test_the_attempts_list_every_failed_model_when_all_fail(http):
    script, seen = http
    script.extend([404] * 5)
    gm = GM()
    with pytest.raises(GMUnavailable):
        gm.call("s", "{}", tier="light")
    assert {a["model"] for a in gm.attempts} == {"g-light", OR_L} and all(a["error"] for a in gm.attempts)


def test_a_test_game_tries_openrouter_first(http, monkeypatch):
    monkeypatch.setattr(config, "OPENROUTER_TEST_GAMES", {"g_test"})
    script, seen = http
    script.append(ok_body())
    gm = GM()
    gm.route_game = "g_test"
    gm.call("s", "{}", tier="light")
    assert gm.gemini_calls == 0 and gm.last["model"] == OR_L and gm.last_meta["routing"] == "openrouter_test_game"
    gm.route_game = "g_other"
    script.append(ok_body())
    gm.call("s", "{}", tier="light")
    assert gm.gemini_calls >= 1


def test_an_engine_answer_names_the_models_that_failed_before(world):
    eng, store, gm, clock = world
    gid, cid = start_solo(eng)
    with_model(gm, OR_L, "openrouter")
    orig = gm.call

    def call(system, user, tier="light", **kw):
        out = orig(system, user, tier)
        gm.last["failed_before"] = ["g-light"]
        return out
    gm.call = call
    out = eng.submit_action("p_jorge", gid, "action", "search the desk", cid)
    assert out["ai_models"][0]["failed_before"] == ["g-light"]


def test_an_outage_error_lists_the_models_tried(monkeypatch):
    from server import tools
    from server.engine import GeminiTrouble

    class E:
        class gm:
            attempts = [{"model": "g-light", "tier": "light", "error": "ServerError: 503"}]
    monkeypatch.setattr(tools, "_ENGINE", [E])

    @tools._safe
    def boom():
        raise GeminiTrouble("down")
    out = boom()
    assert out["gemini_unavailable"] and out["models_tried"] == E.gm.attempts
