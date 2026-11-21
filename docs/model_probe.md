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

## Cost

Each model tested uses one real request: one of the 20 daily requests of a strong Gemini model, one of the light model's, one of the 50 free
OpenRouter requests (shared by the whole account). A full run is about 5 Gemini and 3 to 5 OpenRouter requests.

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
| `sched-20261123T1500Z` | Mon 2026-11-23 15:00 | Scheduled: busy weekday afternoon. |
| `sched-20261124T0200Z` | Tue 2026-11-24 02:00 (03:00 Madrid) | Scheduled: the hour at which turns of whole days close. |
