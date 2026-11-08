# FabulA

**FabulA** stands for **F**ederated **A**synchronous **B**atch-processed **U**ser-driven **L**ore **AI**.

- **Federated:** each player brings their own AI client (Claude, ChatGPT, Grok and others) through an MCP connector, and the engine federates them into one shared game.
- **Asynchronous:** players act whenever they like; nobody has to be online at the same time.
- **Batch-processed:** the world advances in turns, and the AI Master resolves everyone's actions together when a turn closes.
- **User-driven:** the players' choices drive the story; the AI Master keeps the secrets and the rules.
- **Lore AI:** the AI Master (Google Gemini) holds the adventure's lore and runs the world.

**New player? See [gm/setup_guide.md](gm/setup_guide.md)** for a step-by-step guide to connecting a Claude client and starting a first game.

**What must the engine do?** See [TOP_LEVEL_REQUIREMENTS.md](TOP_LEVEL_REQUIREMENTS.md).

FabulA was previously named `multi-player-mcp-engine` (this repository was renamed; the old address redirects here).

An asynchronous, multi-player (or solo) tabletop RPG run by an AI Master.

- Each player uses their own free Claude account with an MCP connector, on Claude desktop, web or Android, as the front end.
- Game, character and world state live in Supabase.
- The MCP server runs on Vercel (Python, FastMCP).
- The AI Master is Google Gemini, in two tiers (see "The two AI Master models"), always at thinking level `medium` by default.

## How a request flows

1. **Claude to Vercel** (HTTP POST, optionally SSE): a standard MCP JSON-RPC 2.0 call to `/mcp`.
2. **Vercel to Supabase**: the server reads the records it needs (Supabase Python client, REST).
3. **Vercel to Gemini**: the server sends one JSON "envelope" (a state snapshot, server-generated dice, the request) with the AI Master's instructions as the system prompt: protocol, oracles, state contract, the game's ruleset, and the game's adventure.
4. **Gemini to Vercel**: one JSON response: per-character result facts, state changes, events, decisions, messages. The AI Master is stateless and never writes narration.
5. **Vercel to Supabase**: the server validates the response in memory, then saves it. Events and decisions are duplicated into the game record and into each concerned character record. Witnesses of an event get their own result item.
6. **Vercel to Claude**: the server returns only the results for the calling player's characters, plus a `sync` block (player-safe current state) so the client can keep its artifacts.
7. **Claude**: narrates from the facts and keeps three artifacts (character state, knowledge and plans, story so far). The server data is always the truth.

## Play model

- **Player and character.** A player is a human (a random internal id, a name, a language) who proves who they are with a **secret player key** (below). A character belongs to one game and holds everything about itself in one record: sheet (maximum and current), inventory, relationships, knowledge, plans, standing orders, safety settings, decisions, events and inbox. A player can have several characters in different games.
- **Adventure and game.** An adventure is fixed content (a markdown file in the **private** repository `jvpreck/rpg_adventures`, or a generated or imported one in the database). A game is one run of it and holds everything that changes: clock, world facts, events, decisions, scheduled events, messages and turns.
- **NPCs and locations** are a fixed definition (in the adventure, or a database record scoped to a game) plus a per-game state record.
- **Turns.** Every turn (default 24 hours) the AI Master resolves all queued actions, arbitrates conflicts and returns each player their own results. Solo games can close the turn as soon as the player has acted (`early_close`).
- **Playing without waiting.** The client answers narration, rules and stat questions locally. Minor actions that affect only one character are resolved at once (they use up that character's Blocks of the turn). Characters in the same place can talk instantly (`say`, handled by the server without calling the AI). Others in the scene see what a character does.
- **Lethality** (`low`, `moderate`, `high`; default `high`) is set per game. When a character dies the player is offered a new character, a pregenerated one, or an available NPC, and carries on in the same game.

## Repository layout

| Path | Contents |
|---|---|
| `gm/` | AI Master files, independent of any ruleset or adventure: `protocol.md`, `oracles.md`, `state_and_messages.md`; `client_tasks.md` (step-by-step instructions for the work packages, sent to the player's Claude); and `player_client_brief.md` for the player's Claude (served as MCP instructions) |
| `rulesets/` | One markdown file per ruleset, with YAML front matter (`id`, `title`, ...). Currently `fear_itself.md` and `trail_of_cthulhu.md` |
| `.github/workflows/admin.yml` | Host-only administration through GitHub Actions (needs write access to this repository) |
| `server/admin.py` | The host commands behind `POST /internal/admin` |

Adventures are **not** in this repository. Players can read it, and an adventure contains its secrets. They live in the private repository `https://github.com/jvpreck/rpg_adventures`, and the server reads them with a read-only token (see Setup). `adventures/` is in `.gitignore` so one cannot be committed here by mistake.
| `server/` | The Python server: `app.py` (gateway and MCP), `tools.py`, `engine.py`, `apply.py`, `db.py`, `prompt.py`, `gm.py`, `redact.py`, `dice.py`, `files.py`, `config.py` |
| `api/index.py` | Vercel entry point |
| `supabase/schema.sql` | Tables (`gm_*`) to create in Supabase |
| `tests/` | Unit tests with an in-memory database and a scripted AI Master |

To add a ruleset, drop a markdown file with front matter into `rulesets/`. To add an adventure, commit it to the root of `jvpreck/rpg_adventures` (its README explains the format). The server picks it up within five minutes. An adventure names its ruleset in `ruleset:`.

## MCP tools (for players)

| Tool | Purpose |
|---|---|
| `start_here` | The first call in any new chat, no key needed: what the engine is, what to call for what, the list of guides |
| `import_ruleset` | Convert a game system from a document the player provides into a ruleset (a work package). It waits for the host's approval |
| `get_guide` | Guides, no key needed: `player-client-guide`, `players-guide`, `create-character`, `create-game`, `generate-adventure`, `narrator`, `mcp-guide` |
| `get_setup_guide` | The guide for a new player (how to start, choose a game, make a character, commands, turns and collaboration, autonomous actions, death, other mechanics). Needs no key |
| `register_player` | Creates a player and returns their **secret player key**, once |
| `list_games` | The player's games and the open games with free seats |
| `list_adventures` | Adventures (files and the player's generated ones) and rulesets |
| `list_takeovers` | The NPCs a late joiner (or a player whose character died) can take over: not main characters, already part of the players' world, or unclaimed pregenerated characters. `generate_character(route="from_npc", npc_id=...)` takes one. |
| `list_seeds` | Published adventure seeds (a spoiler-free summary each). `generate_adventure(seed_id=...)` writes a full adventure from one. The seeds live in the `seeds/` folder of the private adventures repository |
| `generate_adventure` | Returns a **work package** to write a new adventure locally (from a seed or a document) |
| `create_game` | Returns a work package to choose the game settings (lethality, turn, party size) locally |
| `join_game` | Join a game by id |
| `generate_character` | `generate` and `provided` return a work package to build or check the sheet locally; `pregen` and `from_npc` are handled on the server |
| `submit_package` | Sends back the finished package (`task_id` and the result). The server validates and stores it, or returns the problems to fix |
| `submit_action` | Actions, speech, setup answers, character confirmation, standing orders, decisions, messages, free queries, pause |
| `get_results` | Collect results not yet delivered |
| `list_images`, `get_image` | The pictures of a game that the player's characters could see, and a fresh short-lived link to one of them |
| `set_game_options` | The host of a game turns illustrations on or off |
| `get_character`, `get_rules`, `save_story_summary` | Resync, read the ruleset, store the client's story summary |

**Work packages.** For creative work, the server sends the client a structured package: step-by-step instructions, the ruleset and context needed, the exact schema of the result, and the instruction to return it with `submit_package`. The client does the work locally. The server checks structure and limits, stores the result and, for characters, has the AI Master cross-check the sheet against the rules. A package expires after 48 hours and allows 5 attempts. A client-written adventure is stored as data and fenced in the AI Master's prompt, so it cannot change the protocol. Only join games from hosts you trust.

## The two AI Master models

The free tier gives a strong model few requests (about 20 a day, 5 a minute) and a lighter one many (about 500 a day, 10 a minute). The server uses each where it counts:

| Tier | Model (default) | Used for |
|---|---|---|
| `turn` (strong) | `gemini-3.8-flash` | Closing a turn with every player's actions (arbitration, results for all), and cross-checking a character sheet |
| `light` | `gemini-3.5-flash-lite` | Everything a single player does between turns: autonomous actions, queries, setup, joining |

- **Counting.** Each request is counted per tier in the `gm_usage` table, per day (the provider's day, Pacific time) and per minute, so every server instance shares the count. The guards sit a little under the real limits.
- **Strong model over its per-minute limit:** the turn is **deferred**, not degraded. It stays open and the next scheduler run (every 5 minutes) retries it.
- **Strong model's daily quota used up, or it fails with a quota or server error:** the turn is resolved by the light model, and the turn record shows `gm_model` and `gm_degraded` so you can see it. Other errors (a real bug) are not hidden by the fallback.
- **Light model over its limits:** the player's request waits a few seconds, then gets a plain "the AI Master is busy, try again" message.
- **Sizing.** Three or four games with 24-hour turns use about 4 strong requests a day plus the character checks, far under the 18 a day guard. Retries after an invalid AI answer each count as a request. The host command `gm_usage` shows today's counts.

## Illustrations

Pictures are drawn during the player's own call (a character confirmation, an action or fetching results), up to `INLINE_IMAGE_SECONDS` (default 40), so they are listed in the same result; the result carries `picture_seconds` to show what that added. The server also queues, by itself, a picture of each place a character reaches for the first time and a portrait of each NPC met for the first time (`AUTO_PICTURES_PER_RESPONSE`, default 3), writing the prompt with a light model call from player-safe facts only.

Each game has a setting `illustrations` (`on` by default when the server can draw pictures, `off` otherwise; chosen when the game is created, or later by the game's host with `set_game_options`). It is only offered when the server has the image provider configured.

- **Who asks for a picture.** Only the AI Master, in a turn response, as `illustrations: [{prompt, caption, visible_to}]` (state contract §6.7, protocol §5.6). A bad proposal is dropped silently, so a picture can never block a turn.
- **Generation.** The proposal is queued as a `gm_images` record. After the scheduler has resolved turns, `/internal/resolve_turn` draws the queued pictures with **Cloudflare Workers AI, FLUX.1 schnell** (`prompt` and `steps`, base64 JPEG back). It draws at most `IMAGES_PER_RUN` (3) per run and stops when the function's time is nearly used or the day's guard (`IMAGE_RPD`, 150, under Cloudflare's roughly 170 a day at 1024x1024 and 4 steps) is reached. The rest stay queued for the next run, and are dropped after 3 days. A failure is tried once more, then marked failed.
- **Storage.** Image files live in a **private Supabase Storage bucket** (`gm-images`, created by `supabase/schema.sql`), at `<game_id>/<image_id>.jpg`. The database holds only the record: prompt, caption, who may see it, status and path. Nobody can open the bucket directly.
- **Short-lived links.** When a player asks (`get_image`), the server checks that one of that player's characters is in `visible_to`, then asks Supabase to sign a link for the file (`create_signed_url`, 15 minutes by default, `IMAGE_URL_TTL_SECONDS`). The link carries a token and stops working at expiry. Links are never stored, so a player can ask again for any old picture and gets a new one each time. `list_images` lists the pictures a player's characters could see.
- **Consistent look.** Each game has an immutable `image_style` (theme, era, place, ambience, palette) written by the client when the game is created and prefixed to every picture. Every character (when confirmed) and every NPC (the first time the AI Master reports them, with `portraits`) gets a hidden reference sheet of three 512 pictures (face, full body, in action) and then a 1024 portrait with the name written by Pillow, shown only to the characters who have met them. The AI Master is asked for one picture per turn and one for every place the characters reach that has never been drawn (the envelope lists them in `illustration_brief`; up to four per turn, `IMAGES_PER_TURN`). Scene pictures are 1024 and receive up to four of those references (`subjects`) so faces and clothes stay the same. Model: FLUX.2 klein 4B on Workers AI (multipart, up to four 512 reference images). A portrait costs about 200 Neurons, a scene about 120, of the 10,000 free per day. Progress is kept between scheduler runs.
- **Who is told.** `get_results` includes `illustrations` for pictures that are ready and that the player has not been told about yet.
- **Cleanup.** The admin command `delete_game` also deletes the game's picture files. Supabase's free tier gives 1 GB of storage, which holds several thousand pictures of this size.
- **Admin.** `generate_images` draws queued pictures now. `gm_usage` shows the picture count for the day.
- **Limits.** FLUX.1 schnell takes only a prompt and a step count (no size, no seed), so the picture size is whatever the model gives, and faces are not consistent between pictures. Claude Desktop may not show images inline, which is why pictures are links.

## Players, keys and the host

- **Player key.** A new player calls `register_player`. The server creates a player with a random id and returns a random secret key (`pk_...`) **once**. Every other player tool takes it as `player_key`. The database stores only the key's SHA-256 hash and never the key. The player's Claude keeps the key in the chat or project and never shows it to anyone. Knowing someone's internal id, or the shared connector key, is not enough to act as them.
- **Host administration is not reachable by players.** There are no admin tools in MCP. The host commands (`list_games`, `get_game`, `list_players`, `list_adventures`, `delete_game`, `close_game`, `delete_adventure`, `delete_player`, `reset_player_key`, `purge_tasks`, `gm_usage`, `generate_images`) are served at `POST /internal/admin`, which needs `Authorization: Bearer $ADMIN_SECRET`. This is a third secret, different from the players' shared key and from `CRON_SECRET`, and the endpoint is closed when it is not set.
  - **From GitHub:** Actions, `admin`, Run workflow. Only people with write access to this repository can run it (players are readers). It offers `delete_game`, `close_game`, `delete_adventure`, `delete_player` and `purge_tasks` only, because this repository is public and the output of a run is visible to everyone. Repository secrets needed: `SERVER_URL` and `ADMIN_SECRET`.
  - **From your computer:** for listings, `get_game` and `reset_player_key`, which show private data:
    ```
    curl -sS -X POST "$SERVER_URL/internal/admin" -H "Authorization: Bearer $ADMIN_SECRET" \
      -H "Content-Type: application/json" -d '{"command": "list_games", "args": {}}'
    ```
- **The host is also a player.** Register in a dedicated chat like anyone else, with a normal key and normal rights. Never put `ADMIN_SECRET` in a chat with Claude.
- **Lost key.** The host runs `reset_player_key` for that player and gives them the new key privately. The player's characters and games are unchanged.

`resolve_turn` is **not** a player tool. It is an HTTP endpoint for the server side: `GET|POST /internal/resolve_turn` (optional `?game_id=`), protected by `Authorization: Bearer $CRON_SECRET`. Without `game_id` it resolves every game whose turn is due. It is called by the `turn` GitHub Actions workflow (or any cron).

## Setup

1. Run `supabase/schema.sql` in the Supabase SQL editor (it is safe to run again: it adds the `gm_tasks`, `gm_keys`, `gm_usage` and `gm_images` tables and the private `gm-images` storage bucket). Run it again after every update of the repository: it also installs the `gm_commit` function, which saves all the records of a request in one database transaction (until it is installed the server saves them one by one, as before).
2. Environment variables on Vercel:
   - `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
   - `GEMINI_API_KEY`. Optional: `GEMINI_MODEL_TURN` (default `gemini-3.8-flash`), `GEMINI_MODEL_LIGHT` (default `gemini-3.5-flash-lite`; the old `GEMINI_MODEL` still works as its name), `GEMINI_THINKING_LEVEL` (default `medium`) and `GEMINI_THINKING_LEVEL_TURN`
   - Optional: `GEMINI_STRUCTURED_OUTPUT` (default `off`; `on` makes Gemini answer in the shape in `server/schema.py`). Keep it off: that schema leaves the contract's objects empty (see its docstring), which broke character checks when it was on.
   - Optional token controls (all default `on` or `auto`): `PROMPT_SLIM` sends the AI Master only the sections of its instructions that the kind of request needs (`gm/README.md`). `GEMINI_CONTEXT_CACHE` (`auto` or `off`) stores the instructions once at Gemini and refers to that copy: if Gemini refuses (the free tier does not offer it) the server sends the text as before, notes it in the call statistics (`cache_off`, `cache_note`) and tries again after `CACHE_OFF_SECONDS` (3600). `ENVELOPE_RELEVANT` limits what a request of one character is told about events, messages, earlier results, NPCs and places to what concerns that character (the turn close always sees everything; a world under `ENVELOPE_WORLD_NARROW_CHARS`, 12000, is sent whole).
   - Optional: `CHARACTER_CHECK_TIER` (`light` by default, or `turn`): which model cross-checks a character sheet while the player waits. `STRONG_BREAKER_SECONDS` (900; 0 turns it off): after the strong model times out or answers a server error, it is skipped for this long (by every server instance) and the light model answers at once; `gm_usage` shows `skipped_models`.
   - Optional quota guards, with headroom under the free tier: `GEMINI_TURN_RPD` (18) and `GEMINI_TURN_RPM` (4), `GEMINI_LIGHT_RPD` (450) and `GEMINI_LIGHT_RPM` (9)
   - `MCP_API_KEY`: the shared key for players (`Authorization: Bearer`, `x-api-key`, or `?key=` in the connector URL)
   - `CRON_SECRET`: for `/internal/resolve_turn`
   - `ADMIN_SECRET`: for `/internal/admin` (host commands). Use a different random value
   - Illustrations (optional): `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN` (an API token that may use Workers AI). Without them the option is simply not offered. Optional: `IMAGE_MODEL` (default `@cf/black-forest-labs/flux-2-klein-4b`), `IMAGE_SIZE` (1024), `IMAGE_REF_SIZE` (512), `IMAGE_STYLE` (only the fallback for a game without its own style), `IMAGE_RPD` (80), `IMAGE_RPM`, `IMAGE_URL_TTL_SECONDS`, `IMAGES_PER_RUN`
   - `GITHUB_TOKEN`: a **fine-grained personal access token** with *Contents: read-only* on the single repository `jvpreck/rpg_adventures`. The server uses it to read the adventures. Optional: `ADVENTURES_REPO` (default `jvpreck/rpg_adventures`), `ADVENTURES_REF` (default `main`), `ADVENTURES_CACHE_SECONDS` (default 300)
3. Players add `https://<your-app>.vercel.app/mcp?key=<MCP_API_KEY>` as a custom connector.
4. **Scheduler.** The Cloudflare Worker in `cloudflare/turn-worker/` calls `/internal/resolve_turn` every 5 minutes (setup steps in its README; it needs the `SERVER_URL` and `CRON_SECRET` secrets). The workflow `.github/workflows/turn.yml` does the same call by hand (Run workflow).

## Tests

```
pip install -r requirements.txt pytest
pytest tests
```

`tests/scenarios/scenarios.json` holds recorded scenarios for the AI Master: requests with its answers, checked for structure, dice integrity and secrecy on every run. Before releasing a change to the instructions in `gm/` or to a ruleset, run them against the real model (the live scenarios send the current instructions to Gemini and apply the same checks to what it answers):

```
FABULA_LIVE_SCENARIOS=1 GEMINI_API_KEY=... pytest tests/test_scenarios.py -k live -s
```

## Call statistics and repeated requests

- **Call statistics.** Every AI Master call is counted per day by level (3 immediate, 4 at the turn close), tier, mode, request kind and game: calls, valid and invalid answers, retries, tokens in, cached tokens, tokens out, thinking tokens and latency. The host command `gm_usage` shows them (optionally `day`).
- **Repeated requests.** `submit_action` takes an optional `request_id`. Sending the same id again (after a timeout, a double click) runs the request once and returns the first answer, marked `duplicate_request`. The server remembers the last 5 requests of a player for an hour.

## Known limits

- **Authentication is a shared connector key plus a secret key per player.** The player key is a bearer secret: whoever holds it is that player. It travels inside the MCP calls the player's Claude makes, so it is as safe as the player's chat. OAuth would be stronger.
- **Adventure secrets are private only while the token is.** The adventures repository must stay private, and the `GITHUB_TOKEN` must be read-only and limited to it. A player who generates an adventure with their own Claude sees its secrets, by design.
- **Cross-record writes are not one database transaction.** The server validates everything in memory and saves with optimistic version checks, so a rejected AI response changes nothing, but a crash in the middle of saving could leave records out of step.
- **Vercel limits.** `vercel.json` sets `maxDuration` to 300 seconds (the Hobby maximum with Fluid compute). Each model call times out after 100 s (`GEMINI_TIMEOUT_SECONDS`), no new turn starts when less than 110 s of the 240 s budget remain (the game stays due and the next run takes it), and pictures use what is left.
- **Gemini retries.** A transient Gemini error (503 "high demand", 500, 502, 504) is retried quietly with exponential backoff and jitter (waits of about 2, 6 and 18 seconds) before the request fails or, for a turn, falls back to the light model. Quota errors (429), timeouts and bad requests are never retried. Tunable with `GEMINI_RETRIES` (default 3), `GEMINI_RETRY_BASE_SECONDS` (default 2) and `GEMINI_RETRY_BUDGET_SECONDS` (default 40, the most time one request may spend waiting).
- **The AI Master is an LLM.** The server enforces structure, ownership of fields, dice, and the lethality guard, but the AI's judgement on secrecy and fairness is not machine-checked. A lite model on a long, rule-dense JSON task is unbenchmarked here, so the models can be changed with `GEMINI_MODEL_TURN` and `GEMINI_MODEL_LIGHT`. The model names `gemini-3.8-flash` and the `medium` thinking level on it were taken from your description and have not been tested against the live API.


## First contact with a client

When a client connects, the MCP handshake carries short `instructions` (`gm/mcp_instructions.md`, under 200 words): call `start_here` first, keep the secret key, the server is the truth, work packages go back with `submit_package`. Clients differ in how much they use that field, so the same guidance is also in the tool list: `start_here` is described as "CALL THIS FIRST", and every error from a tool carries a `next_step` that points back to `start_here` or the right guide. The guides are Markdown files in `gm/` (see `gm/README.md`) that you can edit without changing code.

## Pictures in other clients

`get_image` returns a short-lived link by default. With `inline=true` it returns the picture itself as an MCP image block (a JPEG reduced to `IMAGE_INLINE_SIZE`, default 768 px, with the caption as text), for clients that display images returned by tools. Pictures are always presented as links, written `[Illustration: caption](url)`; the client brief tells the model to use `inline=true` only when the player explicitly asks to see the picture in the chat. Access rules are identical for both.

## Rulesets

Rulesets are markdown files in `rulesets/` (see `rulesets/README.md` and the contract `gm/ruleset_contract.md`). A player can also import one from a document with `import_ruleset`; it is stored in `gm_rulesets` as pending and usable only after the host approves it with the admin commands `approve_ruleset`, `reject_ruleset` or `delete_ruleset` (`list_rulesets` and `review_ruleset` show what is waiting). Run `supabase/schema.sql` again (it is idempotent) to create the `gm_rulesets` table.
