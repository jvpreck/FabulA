import asyncio
import json

from server.app import Gateway


class FakeEngine:
    def resolve_due(self):
        return {"checked": 0, "results": []}

    def resolve_turn(self, gid):
        return {"game_id": gid, "resolved": True}


async def call(gw, path, headers=None, query=b""):
    sent = []

    async def receive():
        return {"type": "http.request", "body": b""}

    async def send(m):
        sent.append(m)
    scope = {"type": "http", "path": path, "query_string": query,
             "headers": [(k.encode(), v.encode()) for k, v in (headers or {}).items()]}
    await gw(scope, receive, send)
    return sent


class Inner:
    async def __call__(self, scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"mcp"})


def run(*a, **k):
    return asyncio.run(call(*a, **k))


def test_gateway_auth(monkeypatch):
    monkeypatch.setenv("MCP_API_KEY", "k1")
    monkeypatch.setenv("CRON_SECRET", "c1")
    gw = Gateway(Inner(), FakeEngine())
    assert run(gw, "/mcp")[0]["status"] == 403
    assert run(gw, "/mcp", {"authorization": "Bearer k1"})[0]["status"] == 200
    assert run(gw, "/mcp", query=b"key=k1")[0]["status"] == 200
    # the player key must not open the internal endpoint, and the cron secret must not open the MCP endpoint
    assert run(gw, "/internal/resolve_turn", {"authorization": "Bearer k1"})[0]["status"] == 403
    assert run(gw, "/mcp", {"authorization": "Bearer c1"})[0]["status"] == 403
    r = run(gw, "/internal/resolve_turn", {"authorization": "Bearer c1"})
    assert r[0]["status"] == 200 and json.loads(r[1]["body"]) == {"checked": 0, "results": []}
    r = run(gw, "/internal/resolve_turn", {"authorization": "Bearer c1"}, b"game_id=g_1")
    assert json.loads(r[1]["body"])["game_id"] == "g_1"


def test_gateway_fails_closed(monkeypatch):
    monkeypatch.delenv("MCP_API_KEY", raising=False)
    monkeypatch.delenv("CRON_SECRET", raising=False)
    gw = Gateway(Inner(), FakeEngine())
    assert run(gw, "/mcp", {"authorization": "Bearer "})[0]["status"] == 403
    assert run(gw, "/internal/resolve_turn", {"authorization": "Bearer "})[0]["status"] == 403


class AdminEngine(FakeEngine):
    def __init__(self):
        self.store = None


def test_admin_endpoint_needs_its_own_secret(monkeypatch):
    from server import admin
    monkeypatch.setenv("MCP_API_KEY", "k1")
    monkeypatch.setenv("CRON_SECRET", "c1")
    monkeypatch.setenv("ADMIN_SECRET", "a1")
    seen = []
    monkeypatch.setattr(admin, "run", lambda eng, cmd, args=None: seen.append((cmd, args)) or {"ok": cmd})
    gw = Gateway(Inner(), FakeEngine())

    async def post(headers, body=b'{"command": "list_games", "args": {}}'):
        sent = []

        async def receive():
            return {"type": "http.request", "body": body}

        async def send(m):
            sent.append(m)
        await gw({"type": "http", "method": "POST", "path": "/internal/admin", "query_string": b"",
                  "headers": [(k.encode(), v.encode()) for k, v in headers.items()]}, receive, send)
        return sent
    for tok in ("k1", "c1", ""):                       # the player key and the cron secret do not open it
        assert asyncio.run(post({"authorization": f"Bearer {tok}"}))[0]["status"] == 403
    assert seen == []
    r = asyncio.run(post({"authorization": "Bearer a1"}))
    assert r[0]["status"] == 200 and json.loads(r[1]["body"]) == {"ok": "list_games"} and seen == [("list_games", {})]
    assert asyncio.run(post({"authorization": "Bearer a1"}, b"not json"))[0]["status"] == 400
    # the admin secret does not open the player endpoint or the turn endpoint
    assert run(gw, "/mcp", {"authorization": "Bearer a1"})[0]["status"] == 403
    assert run(gw, "/internal/resolve_turn", {"authorization": "Bearer a1"})[0]["status"] == 403
    monkeypatch.delenv("ADMIN_SECRET")
    assert asyncio.run(post({"authorization": "Bearer "}))[0]["status"] == 403   # fails closed
