"""ASGI app: the MCP endpoint (/mcp), shared-key middleware, and the protected tick endpoint (/internal/resolve_tick)."""
import hmac
import json
import os
from urllib.parse import parse_qs

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from . import admin, config, files, tools
from .engine import Engine, EngineError

MCP_KEY_ENV = "MCP_API_KEY"
CRON_ENV = "CRON_SECRET"
ADMIN_ENV = "ADMIN_SECRET"


def build_engine():
    from supabase import create_client
    from .db import SupabaseStore
    from .gm import GeminiGM, Usage
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    from .images import CloudflareFlux, ImageService, SupabaseImageStorage
    store = SupabaseStore(sb)
    usage = Usage(store)
    images = ImageService(CloudflareFlux(), SupabaseImageStorage(sb), usage)  # unavailable until the Cloudflare variables are set
    return Engine(store, GeminiGM(usage=usage), images=images)


def client_instructions() -> str:
    return files.split_front_matter(files.gm_file("mcp_instructions.md"))[1]


def _extra_hosts():
    """More public host names the server answers on (a new Vercel domain or a custom domain), from the env var EXTRA_ALLOWED_HOSTS, comma separated."""
    return [h.strip() for h in os.environ.get("EXTRA_ALLOWED_HOSTS", "").split(",") if h.strip()]


def build_mcp(engine):
    mcp = FastMCP(
        "FabulA",
        instructions=client_instructions(),
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=["fabula-rpg.vercel.app", "multi-player-mcp-engine-sand.vercel.app", "localhost:*", "127.0.0.1:*", *_extra_hosts()],
            allowed_origins=["https://fabula-rpg.vercel.app", "https://multi-player-mcp-engine-sand.vercel.app", "https://claude.ai", *[f"https://{h}" for h in _extra_hosts()]],
        ),
    )
    tools.register(mcp, engine)
    return mcp


def _headers(scope):
    return {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}


def _matches(secret, candidates):
    return bool(secret) and any(hmac.compare_digest(c.encode(), secret.encode()) for c in candidates if c)


class Gateway:
    """Authentication and the internal tick endpoint, in front of the MCP app.

    /mcp and everything else: shared key (`Authorization: Bearer`, `x-api-key` or `?key=`), MCP_API_KEY.
    /internal/resolve_tick: CRON_SECRET only (Bearer). /internal/admin: ADMIN_SECRET only (Bearer), host commands (see admin.py).
    Each secret fails closed when unset. 403, not 401, so clients do not start OAuth.
    """

    def __init__(self, mcp_app, engine):
        self.app = mcp_app
        self.engine = engine

    @staticmethod
    def _bearer(h):
        a = h.get("authorization", "")
        return a[7:].strip() if a.lower().startswith("bearer ") else ""

    def _mcp_ok(self, scope):
        h = _headers(scope)
        q = parse_qs(scope.get("query_string", b"").decode()).get("key", [])
        return _matches(os.environ.get(MCP_KEY_ENV, ""), [h.get("x-api-key", ""), self._bearer(h), *q])

    def _cron_ok(self, scope):
        return _matches(os.environ.get(CRON_ENV, ""), [self._bearer(_headers(scope))])

    @staticmethod
    async def _json(send, status, obj):
        body = json.dumps(obj).encode()
        await send({"type": "http.response.start", "status": status,
                    "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]})
        await send({"type": "http.response.body", "body": body})

    def _admin_ok(self, scope):
        return _matches(os.environ.get(ADMIN_ENV, ""), [self._bearer(_headers(scope))])

    @staticmethod
    async def _body(receive):
        data = b""
        while True:
            m = await receive()
            data += m.get("body", b"")
            if not m.get("more_body"):
                return data

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path = scope.get("path", "")
        if path == "/internal/admin":
            if not self._admin_ok(scope):
                return await self._json(send, 403, {"error": "forbidden"})
            if scope.get("method", "POST") != "POST":
                return await self._json(send, 405, {"error": "use POST"})
            try:
                req = json.loads((await self._body(receive)) or b"{}")
                out = admin.run(self.engine, req.get("command"), req.get("args") or {})
            except (ValueError, AttributeError):
                return await self._json(send, 400, {"error": "send JSON: {\"command\": ..., \"args\": {...}}"})
            except EngineError as e:
                return await self._json(send, 400, {"error": str(e)})
            except Exception as e:
                return await self._json(send, 500, {"error": str(e)[:300]})
            return await self._json(send, 200, out)
        if path.startswith("/internal/"):
            if not self._cron_ok(scope):
                return await self._json(send, 403, {"error": "forbidden"})
            if path == "/internal/resolve_tick":
                q = parse_qs(scope.get("query_string", b"").decode())
                gid = (q.get("game_id") or [None])[0]
                try:
                    out = self.engine.resolve_tick(gid) if gid else self.engine.resolve_due()
                except Exception as e:
                    return await self._json(send, 500, {"error": str(e)[:300]})
                return await self._json(send, 200, out)
            return await self._json(send, 404, {"error": "not found"})
        if not self._mcp_ok(scope):
            return await self._json(send, 403, {"error": "forbidden"})
        return await self.app(scope, receive, send)


def create_app(engine=None):
    engine = engine or build_engine()
    mcp = build_mcp(engine)
    return Gateway(mcp.streamable_http_app(), engine)
