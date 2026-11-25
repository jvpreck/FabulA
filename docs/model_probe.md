# Model probe

A built-in tool that measures, from the production server itself, how each AI Master model answers a real-size request: whether it
answers at all, how long it takes, how long before it starts writing, and whether the answer is valid JSON. Use it to choose and order the
model lists (`GEMINI_STRONG_MODELS`, `GEMINI_LIGHT_MODELS`, `OPENROUTER_STRONG_MODELS`, `OPENROUTER_LIGHT_MODELS`), to check a provider after
an incident, or to compare times of day.

Code: `server/probe.py`. Tests: `tests/test_probe.py`. Added 2026-11-21 at the owner's request.

## What it does

- One probe **run** tests every model of both chains (Gemini and OpenRouter, strong and light, without duplicates), or the models in the env
  `PROBE_MODELS` (comma-separated, OpenRouter models written `openrouter:<id>`).
- The scheduler (`/internal/resolve_turn`, called every 5 minutes by the Cloudflare Worker) tests **one model per call**, after its normal
  work, with the time the function has left (up to about 270 s; Vercel stops a function at 300 s). A run of 8 models takes about 40 minutes.
- The request is the real `play` instructions for Fear Itself (about 156,000 characters, 40,000 tokens) plus a small `free_query` envelope:
  the size of a normal level 3 call. Reasoning effort is `medium`.
- OpenRouter is called with streaming, so the probe records when the first byte, the first reasoning token and the first text arrive, and how
  many keep-alive lines came. Gemini is called as in play (no streaming): only the total time.
- Results are written to the `gm_usage` table, record `probe:<run>`: `queue` (models still to test), `results` (one entry per model).
- It never changes a game and never blocks one: the scheduler resolves due turns first, and a failure of the probe is only reported.

### Request kinds (2026-11-25)

Env `PROBE_KINDS`, comma-separated, default `simple`. Each kind is a separate pass over its models, so `simple,action,turn_close` queues
about 3 times as many requests (about 20 with the current lists, about 100 minutes of scheduler runs).

| Kind | Request | Models |
|---|---|---|
| `simple` | the play instructions and a small `free_query` (above) | both lists |
| `action` | a real level 3 action ("I search the desk in the office for letters or notes...", from the recorded scenario `minor_action_uses_server_dice_in_order`) built by the engine from the game in env `PROBE_GAME`, exactly as in play: system prompt with that game's adventure and profile, the compact envelope, the effort for an action | light list |
| `turn_close` | a real level 4 turn close of `PROBE_GAME`, with one queued action added in memory ("I ask the person in charge here about what happened...", from `major_action_is_queued_for_the_turn`), turn profile and turn effort | strong list |

`PROBE_GAME` must be an active game with a living character; the probe only reads it (nothing is applied or saved). Without it the
realistic kinds are recorded as `skipped`. Use a throwaway game (e.g. the probe player's game), not a game someone is playing: its secrets
go to the free endpoints like any other request. The results carry `kind`, `envelope_chars`, `system_chars`, `effort`, `game` and `turn`.

The realistic kinds are what to run when the free models change (new models, removed models, new limits): a model that answers the small
request can still fail on a 60,000-token turn close.

## Cost

Each model tested uses one real request, and since 2026-11-25 it is **counted in the same daily guards as play** (`Usage.reserve`: tier
`turn` for a strong Gemini model or any turn close, `light` for a light Gemini model, `openrouter` for OpenRouter, 45 a day for the whole
account). When a guard is used up the request is not sent and the result says `skipped`, so a probe can never take the last strong requests a
turn close needs. A `simple` run is about 4 Gemini and 3 OpenRouter requests; all three kinds about 12 Gemini and 8 OpenRouter.

## How to start a run

Any of these (the first that applies wins: `PROBE_RUN` is checked before the schedule):

1. **Schedule (recommended, no redeploy):** host command `probe_schedule` with `times`, a list of UTC start times:
   `POST /internal/admin` with `Authorization: Bearer <ADMIN_SECRET>` and body
   `{"command": "probe_schedule", "args": {"times": ["2026-11-23T15:00Z"]}}`. A run starts at the first scheduler call after each time and
   must finish within 3 hours. `{"command": "probe_schedule"}` with no times shows the schedule.
2. **Env schedule:** Vercel env `PROBE_SCHEDULE` (comma-separated UTC times), then redeploy.
3. **Immediate run:** Vercel env `PROBE_RUN` set to a new run name, then redeploy. Clear `PROBE_RUN` afterwards (set it to a blank value),
   because while it is set the schedule is ignored.

## How to read the results

- Host command `probe_status` (summary of every run) or `probe_status` with `{"run": "<run>"}` (full records).
- SQL (Supabase, table `gm_usage`): `select data from gm_usage where id like 'probe:%' order by id;`
- Fields per model: `model`, `answered`, `total_s`, `first_content_s` and `first_reasoning_s` (OpenRouter), `first_byte_s`, `keepalives`,
  `tokens_in`, `tokens_out`, `tokens_reasoning` / `tokens_thought`, `answer_chars`, `json_ok`, `finish_reason`, `error`, `wait_s` (how long it
  was allowed), `at`.

Reading tips: a model that fails in seconds with 429 or 503 is refusing (quota or load), not slow: a longer wait does not help. A model with
`first_reasoning_s` early and `first_content_s` late spends its time thinking: lower effort or a smaller prompt helps. `keepalives` with no
tokens mean the provider has queued the request.

## For Claude (the LLM working on this repo)

When asked about model availability, speed or which models to use, check the probe results first (SQL above, or ask the owner to run
`probe_status`), and propose a run (schedule one with `probe_schedule`, or ask the owner) instead of guessing. Report the numbers per model,
and say how many samples each number rests on: one run is one sample.

## Runs so far

| Run | When (UTC) | Notes |
|---|---|---|
| `2026-11-21a` | Sat 2026-11-21 06:55 to 07:40 | Quiet time. Gemini 3.6 Flash 28 s, 3.5 Flash-Lite 7 s, 3.1 Flash-Lite 3.5 s; 3.5 and 3.8 Flash 503. OpenRouter Nemotron 3 Ultra 15 s, 3.5 Super VL 41 s, 3.5 Lightning 46 s (5k to 8k reasoning tokens); Gemma 4 31B and 26B 429 (rate-limited upstream, removed from the lists afterwards). All answers were valid JSON. |
| `sched-20261123T1500Z` | Mon 2026-11-23 15:00 | Busy weekday afternoon. Gemini 3.6 Flash 11 s, 3.5 Flash 13 s; 3.8 Flash, 3.5 Flash-Lite, 3.1 Flash-Lite 503 within 2 s. OpenRouter Ultra 30 s, Super VL 18 s, Lightning 46 s. |
| `sched-20261124T0200Z` | Tue 2026-11-24 02:00 (03:00 Madrid) | Turn-close hour. Gemini 3.6 Flash 40 s, 3.5 Flash 38 s, 3.5 Flash-Lite 10 s, 3.1 Flash-Lite 3.6 s; 3.8 Flash 503. OpenRouter Ultra 12 s, Super VL 70 s, Lightning 11 s. |

Decisions after these three runs (owner, 2026-11-25): gemini-3.8-flash removed (0 of 3, and down on 2026-11-09); gemini-3.6-flash removed
from the light list (simple requests must not spend the strong quota; if both light Gemini models and OpenRouter fail, the request waits);
long waits kept (quality over speed); OpenRouter writing time raised to 120 s with another model behind and 180 s for the last; Gemini 503
retried after 6, 12 and 18 s; failed early turn closes retried by the scheduler; turn closes spread over 02:00 to 06:00 Madrid; realistic
kinds added. Every Gemini failure seen in the probe was a fast 503 refusal and every OpenRouter start came within 2.6 s, so the OpenRouter
timeouts in play were long outputs on larger requests: that is what the realistic kinds measure.

## Draft, not implemented: recurring probe runs

Proposal kept as a draft (owner, 2026-11-25). A host command `probe_recurring` with `{"kinds": [...], "every_days": 7, "hours_utc": [15, 1]}`
would add the next start times to `probe:schedule` by itself after each run, so a weekly sample at a busy hour and at the turn-close hour
builds up without anyone remembering. It would need a cap on the share of the day's guards a run may use (for example at most a third of
the strong and OpenRouter requests) and a short summary per run in `probe_status` to compare runs over time.
