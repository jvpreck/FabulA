# Tick Worker (Cloudflare)

A tiny Worker that calls the engine's `/internal/resolve_tick` every 5 minutes, on time (GitHub's schedule is best effort and can skip hours).
It closes ticks that are due (party games, absent players, deadlines) and draws any pictures still waiting.

## Set up in the dashboard (no tools needed)
1. Cloudflare dashboard → **Workers & Pages** → **Create** → **Create Worker** → name it `ai-master-tick` → **Deploy**.
2. **Edit code**, replace everything with the contents of `src/index.js`, **Deploy**.
3. Worker → **Settings** → **Variables and Secrets** → add two **Secrets**: `SERVER_URL` (for example `https://fabula-rpg.vercel.app`, no trailing slash) and `CRON_SECRET` (the same value as the server's `CRON_SECRET`).
4. Worker → **Settings** → **Trigger Events** → **Add** → **Cron Triggers** → `*/5 * * * *`.
5. Check: Worker → **Observability / Logs** after five minutes: a line `tick HTTP 200 checked=...`. Or run it once from the Triggers tab.

## Or with the command line
```
cd cloudflare/tick-worker
npx wrangler deploy
npx wrangler secret put SERVER_URL
npx wrangler secret put CRON_SECRET
```

## Limits (free plan)
5 cron triggers per account, 100,000 requests a day (this uses about 288), 15 minutes maximum per scheduled run (the engine answers within 300 s).

## GitHub
The GitHub workflow `.github/workflows/tick.yml` no longer has a schedule; it only runs by hand (Actions > tick > Run workflow).
