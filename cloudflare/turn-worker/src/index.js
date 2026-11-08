// Calls the engine's /internal/resolve_turn on a schedule, so turns close on time and queued pictures get drawn.
// Needs two secrets on the Worker: SERVER_URL (https://your-app.vercel.app, no trailing slash) and CRON_SECRET (the same value as the server's).
export default {
  async scheduled(event, env, ctx) {
    if (!env.SERVER_URL || !env.CRON_SECRET) {
      console.log("SERVER_URL or CRON_SECRET is not set: nothing to do");
      return;
    }
    try {
      const res = await fetch(`${env.SERVER_URL}/internal/resolve_turn`, {
        method: "POST",
        headers: { Authorization: `Bearer ${env.CRON_SECRET}` },
        signal: AbortSignal.timeout(290000), // the server's own limit is 300 s
      });
      // Counts only: never log the body (it can name games).
      let summary = "";
      if (res.ok) {
        const j = await res.json().catch(() => ({}));
        const results = Array.isArray(j.results) ? j.results : [];
        summary = ` checked=${j.checked ?? 0} resolved=${results.filter((r) => r.resolved === true).length} pictures=${(j.images && j.images.generated) || 0}`;
      }
      console.log(`turn HTTP ${res.status}${summary}`);
    } catch (e) {
      console.log(`turn call failed: ${e && e.name}`); // a timeout is harmless: the next run takes over
    }
  },
  async fetch() {
    return new Response("Not found", { status: 404 }); // nothing is served over HTTP
  },
};
