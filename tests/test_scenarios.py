"""Recorded scenarios for the AI Master (TLR-03-016). See tests/scenarios/scenarios.json.

Every test run replays the recorded answers through the engine and runs the structure, dice and secrecy checks (no network).
Before releasing a change to the AI Master's instructions, run the live scenarios against the real model:

    FABULA_LIVE_SCENARIOS=1 GEMINI_API_KEY=... pytest tests/test_scenarios.py -k live -s
"""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from server import config, prompt, schema
from server.db import MemoryStore
from server.engine import Engine, EngineError
from server.gm import GeminiGM, parse
from scenario_checks import run_checks
from test_engine import ADV, PG, ScriptedGM, standard_gm, new_game, char_pkg, CHECK

DATA = json.loads((Path(__file__).parent / "scenarios" / "scenarios.json").read_text(encoding="utf-8"))
SCENARIOS = [s for s in DATA["scenarios"] if not s.get("live_only")]  # live_only ones need the real model
LIVE_SCENARIOS = [s for s in DATA["scenarios"] if s.get("live")]
D = {"d6": [3, 5, 2, 6, 4, 1] * 12, "d10": [7, 2, 9, 4, 10, 1] * 8, "d20": [14, 3, 19, 8, 12, 20] * 6}  # fixed, so the checks are deterministic
PLAYER = "p_jorge"


def fill(x, ids, env):
    """Replaces the $ tokens in a recorded answer (keys included)."""
    if isinstance(x, dict):
        return {fill(k, ids, env): fill(v, ids, env) for k, v in x.items()}
    if isinstance(x, list):
        return [fill(v, ids, env) for v in x]
    if isinstance(x, str):
        m = re.fullmatch(r"\$D(6|10|20)\[(\d+)\]", x)
        if m:
            return env["dice"][f"d{m.group(1)}"][int(m.group(2))]
        if x == "$TURN":
            return ids["turn"]
        return x.replace("$CID", ids["cid"]).replace("$GID", ids["gid"]).replace("$PID", PLAYER)
    return x


def start(eng, lethality=None):
    settings = {"lethality": lethality} if lethality else None
    gid = new_game(eng, PLAYER, ADV, language="en", settings=settings)["game_id"]
    cid = eng.generate_character(PLAYER, gid, "pregen", pregen_id=PG[PLAYER])["deliveries"][0]["character_id"]
    eng.submit_action(PLAYER, gid, "character_confirm", "yes", cid, {"approved": True})
    return gid, cid


def player_facing(eng, gid, cid, out):
    """Everything the players receive after a request: the reply, what get_results returns, and the resynced character."""
    return [out, eng.get_results(PLAYER, gid), eng.get_character(PLAYER, gid, cid)]


@pytest.fixture(autouse=True)
def fixed_dice(monkeypatch):
    monkeypatch.setattr("server.engine.make_dice", lambda *a, **k: json.loads(json.dumps(D)))
    CHECK["fail_next"] = 0


@pytest.mark.parametrize("sc", SCENARIOS, ids=[s["name"] for s in SCENARIOS])
def test_recorded_scenario(sc):
    seen = {}

    def rule(env, n):
        req = env.get("request") or {}
        if env["mode"] == "intake" and req.get("kind") == sc["request"]["kind"] and req.get("text") == sc["request"]["text"]:
            ids = {"gid": env["game"]["id"], "cid": req["character_id"], "turn": env["game"]["clock"]["turn"]}
            resp = fill(sc["recorded"], ids, env)
            seen["env"], seen["resp"] = env, resp
            return resp
        return standard_gm(env, n)

    store = MemoryStore()
    eng = Engine(store, ScriptedGM(rule), now_fn=lambda: datetime(2026, 11, 1, 9, tzinfo=timezone.utc))
    gid, cid = start(eng, sc.get("lethality"))

    if sc["expect_engine"] == "rejects":
        with pytest.raises(EngineError):
            eng.submit_action(PLAYER, gid, sc["request"]["kind"], sc["request"]["text"], cid)
        out = None
    else:
        out = eng.submit_action(PLAYER, gid, sc["request"]["kind"], sc["request"]["text"], cid)

    problems = run_checks(seen["resp"], seen["env"], sc.get("never_reaches_players", ()),
                          player_facing(eng, gid, cid, out) if out is not None else None)
    expected_bad = set(sc.get("expect_failures", []))
    for group, found in problems.items():
        if group in expected_bad:
            assert found, f"{sc['name']}: the {group} check should have found a problem and found none"
        else:
            assert not found, f"{sc['name']}: {group}: {found}"
    if out is not None:  # a good answer is also applied: the game moved on and nobody saw the GM-only text
        assert out.get("handling") or out.get("deliveries") is not None


def test_the_checks_themselves_catch_what_they_claim_to():
    from scenario_checks import dice_problems, secrecy_problems
    env = {"dice": {"d6": [3, 5, 2], "d10": [], "d20": []}}
    assert dice_problems({"dice_log": [{"die": "d6", "value": 3}, {"die": "d6", "value": 5}]}, env) == []
    assert dice_problems({"dice_log": [{"die": "d6", "value": 5}]}, env), "skipping the first die"
    assert dice_problems({"dice_log": [{"die": "d6", "value": 9}]}, env), "not a d6"
    assert dice_problems({"dice_log": [{"die": "d20", "value": 4}]}, env), "stream is empty"
    assert dice_problems({"dice_log": [], "results": {"c": [{"roll_report": [{"die": "d6", "value": 3}]}]}}, env), "roll not logged"
    assert secrecy_problems({"facts": ["The BODY is hidden"]}, ["body"]) and not secrecy_problems({"facts": ["ok"]}, ["body"])


# ------------------------------------------------------------------------ live: the real model, the current instructions
LIVE = os.environ.get("FABULA_LIVE_SCENARIOS") == "1" and os.environ.get("GEMINI_API_KEY")


class HybridGM:
    """Game setup is scripted, exactly as in the offline run, so it costs no quota and cannot vary. Only the scenario's own request goes to
    the real model, with the real instructions (the profile, the sections and the cache are all in play)."""

    def __init__(self, real, sc):
        self.real, self.sc = real, sc
        self.usage, self.last, self.last_meta, self.recorded = None, {}, {}, None

    supports_effort = True  # TLR-03-018: the thinking level the engine chose for the request is passed on to the real model

    def call(self, system, user, tier="light", effort=None):
        env = json.loads(user)
        req = env.get("request") or {}
        turn_close = self.sc["request"]["kind"] == "resolve_turn" and env["mode"] == "resolve_turn"
        if turn_close or (env["mode"] == "intake" and req.get("kind") == self.sc["request"]["kind"] and req.get("text") == self.sc["request"]["text"]):
            raw = self.real.call(system, user, tier, effort)
            self.last, self.last_meta, self.recorded = self.real.last, self.real.last_meta, (user, raw, system, tier)
            return raw
        return json.dumps(standard_gm(env, 0))


@pytest.mark.skipif(not LIVE, reason="set FABULA_LIVE_SCENARIOS=1 and GEMINI_API_KEY to run the scenarios against the real model")
@pytest.mark.parametrize("sc", LIVE_SCENARIOS, ids=[s["name"] for s in LIVE_SCENARIOS])
def test_live_scenario(sc, monkeypatch):
    real = prompt.adventure_text
    extra = sc.get("live_adventure_extra", "")
    monkeypatch.setattr(prompt, "adventure_text", lambda adv: real(adv) + ("\n\n## Secret (GM only)\n\n" + extra if extra else ""))
    gm = HybridGM(GeminiGM(usage=None), sc)
    eng = Engine(MemoryStore(), gm, now_fn=lambda: datetime(2026, 11, 1, 9, tzinfo=timezone.utc))
    monkeypatch.setattr("server.engine.make_dice", lambda *a, **k: json.loads(json.dumps(D)))  # known dice, so the dice check is exact
    if sc["request"]["kind"] == "character_submission":  # a new character is checked: no game start, the package flow of a real client
        gid = new_game(eng, PLAYER, ADV, language="en")["game_id"]
        pkg = eng.generate_character(PLAYER, gid, "generate", concept=sc["request"]["text"])["package"]
        try:
            out = eng.submit_package(PLAYER, pkg["task_id"], char_pkg(concept=sc["request"]["text"]))
        except EngineError as e:
            pytest.fail(f"the engine could not use the AI Master's answers to the character check: {e}")
        cid = eng.store.find("character", game_id=gid)[0][0]["id"]
    else:
        gid, cid = start(eng, sc.get("lethality"))
    if sc["request"]["kind"] == "character_submission":
        pass
    elif sc["request"]["kind"] == "resolve_turn":  # the player acts (scripted), then the turn closes: that call goes to the strong model
        eng.submit_action(PLAYER, gid, "action", sc["setup_action"], cid)
        out = eng.resolve_turn(gid)
    else:
        out = eng.submit_action(PLAYER, gid, sc["request"]["kind"], sc["request"]["text"], cid)
    user, raw, system, tier = gm.recorded
    print(f"\n[{sc['name']}] tier={tier} instructions={len(system)} characters, cache={gm.last_meta.get('cache')}, "
          f"model={gm.last.get('model')} degraded={gm.last.get('degraded')}, "
          f"tokens in={gm.last_meta.get('tokens_in')} cached={gm.last_meta.get('tokens_cached')} out={gm.last_meta.get('tokens_out')} "
          f"thinking={gm.last_meta.get('tokens_thought')} retries={gm.last_meta.get('retries')}, "
          f"{gm.last_meta.get('latency_ms')} ms, structured output={'on' if config.GEMINI_STRUCTURED_OUTPUT else 'off'}"
          f"{' (REFUSED by the provider)' if gm.last_meta.get('schema_disabled') else ''}")
    resp = parse(raw)
    problems = run_checks(resp, json.loads(user), list(sc.get("live_secrets", ())) + list(sc.get("never_reaches_players", ())),
                          player_facing(eng, gid, cid, out))
    assert not any(problems.values()), json.dumps(problems, indent=2)
    assert schema.check(resp) == []
