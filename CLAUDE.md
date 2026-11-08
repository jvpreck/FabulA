# FabulA: working notes (not in the repo docs)

Project: FabulA, an asynchronous RPG run by a Gemini AI Master, played through MCP.
Repos: jvpreck/FabulA (engine, public) and jvpreck/rpg_adventures (adventures and seeds, private).
Read first: README.md, TOP_LEVEL_REQUIREMENTS.md, gm/protocol.md, gm/state_and_messages.md.

This repository is public: never write secrets, keys or private game data in it.

## Infrastructure
- Vercel project "fabula", production https://fabula-rpg.vercel.app, deploys from main on push. Hobby plan: runtime logs are kept for 1 hour only. Find the project and team ids with the Vercel tools (list_teams, list_projects).
- Supabase project for FabulA (find it with list_projects). Tables gm_* (id, data jsonb, version, index columns). gm_games.turn_closes and gm_submit_actions.turn are real columns.
- Cloudflare Worker "ai-master-turn" runs every 5 minutes and calls /internal/resolve_turn. Its secrets SERVER_URL and CRON_SECRET are set in the Worker. CRON_SECRET was rotated on 2026-11-08 and its value lives in the Vercel env.
- Vercel env: MCP_API_KEY (the connector key), CRON_SECRET, ADMIN_SECRET, GEMINI_API_KEY, SUPABASE_*, GITHUB_TOKEN, CLOUDFLARE_*.
- Gemini: strong model for turn closing and character checks (gemini-3.8-flash), light model for everything else (gemini-3.5-flash-lite).

## Conventions
- Tests: pip install -r requirements.txt pytest; PYTHONPATH=<deps>:. python3 -m pytest tests -q (106 pass).
- "tick" was renamed to "turn" everywhere on 2026-11-08, including data keys and DB columns. Never reintroduce "tick".
- Requirement IDs: TLR-xx-yyy (xx chapter, yyy sequence). Unbuilt ones carry "-Pending", dropped only when deployed. 17 are pending (four-level request answering, name knowledge and short NPC descriptions).
- Commits end with the Co-Authored-By and Claude-Session lines given by the session.
- For data changes, use SQL migrations and verify with queries. Stored JSON keys follow the code names.

## Open items
- Remove the legacy alias /internal/resolve_tick in server/app.py (the Worker now uses resolve_turn).
- Update the GitHub Actions secret CRON_SECRET (repo settings) to the new value; delete the old Worker "ai-master-tick" and its cron trigger.
- Test game g_a3d4c094: player 3 holds Wendy Shawl; Roberta Caroll and Bobby Wiseman are free. Swap only if the user asks.
- Test game g_6117dfc7: the user may want turn 4 to close at 03:00 Madrid time.
- Unknown cause: two characters created within a fraction of a second for one player (probably overlapping client requests). Mitigated, not prevented.
- Idea: route pregen and character checks to the light model if the strong model keeps timing out.

## Working with the owner
The owner writes in English here. He wants proposals and drafts first, and decisions confirmed before anything is pushed or deployed. He prefers not to keep permanent local copies of his GitHub repos: use one working clone in your own working folder, keep it current with git pull, and delete any extra clones after use.
