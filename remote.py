"""Zeabur / remote Streamable-HTTP entrypoint for Nowhere.

Keeps the original project untouched:
- original 30 MCP tools are imported from nowhere.server
- MCP is exposed at /mcp
- the existing observer web UI remains at /
- journey data defaults to /data for a Zeabur persistent volume
- optional NOWHERE_TOKEN protects MCP and raw action API routes
"""

from __future__ import annotations

import hmac
import os
from urllib.parse import parse_qs

# IMPORTANT: NOWHERE_HOME is read by several modules at import time.
os.environ.setdefault("NOWHERE_HOME", "/data")

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from nowhere import server as nowhere_server
from nowhere import state as state_mod
from nowhere.web import app as observer_app

# Reuse the project's existing FastMCP server and all of its tools.
mcp = nowhere_server.mcp

# Restore the last saved position automatically after a container restart.
try:
    saved = state_mod.WorldState.load()
    if saved is not None and saved.pos is not None:
        nowhere_server._state = saved
        nowhere_server._postcard_counter = max(
            (card.get("id", 0) for card in saved.postcards),
            default=0,
        )
except Exception:
    # Never block startup just because an old state file is malformed.
    pass

public_url = os.environ.get("NOWHERE_PUBLIC_URL", "").strip().rstrip("/")
if public_url:
    mcp.instructions = (
        "你正在使用乌有乡（Nowhere）旅行。"
        f"网页旁观者地址：{public_url}/ 。"
        "可以把这个地址告诉用户，让对方实时看你走到哪里。"
    )

# FastMCP 3.x remote transport. The project keeps its own world state in
# nowhere.server._state; stateless_http only removes protocol-session affinity.
mcp_app = mcp.http_app(path="/mcp", stateless_http=True)

_PRIVATE_API_PATHS = {
    "/open_door",
    "/walk",
    "/listen",
    "/look_around",
    "/ask",
    "/postcard",
    "/where_am_i",
    "/continue",
    "/mark",
    "/walk_to",
    "/wait",
}


def _request_token(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()

    if os.environ.get("NOWHERE_ALLOW_QUERY_TOKEN", "1").lower() in {
        "1", "true", "yes", "on"
    }:
        raw = request.scope.get("query_string", b"").decode("utf-8", "ignore")
        values = parse_qs(raw).get("token", [])
        if values:
            return values[0].strip()

    return ""


class TokenGuardMiddleware(BaseHTTPMiddleware):
    """Protect MCP and direct action APIs without changing the upstream code."""

    async def dispatch(self, request: Request, call_next):
        expected = os.environ.get("NOWHERE_TOKEN", "").strip()
        path = request.url.path.rstrip("/") or "/"

        protected = (
            path == "/mcp"
            or path.startswith("/mcp/")
            or path in _PRIVATE_API_PATHS
        )

        if expected and protected:
            supplied = _request_token(request)
            if not supplied or not hmac.compare_digest(supplied, expected):
                return JSONResponse(
                    {"error": "unauthorized"},
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                )

        return await call_next(request)


async def health(_request: Request) -> JSONResponse:
    state = nowhere_server._state
    return JSONResponse(
        {
            "status": "ok",
            "service": "nowhere",
            "mcp": "/mcp",
            "observer": "/",
            "has_saved_position": state.pos is not None,
        }
    )


# Keep the original observer/API routes first, then let FastMCP handle /mcp.
# Mounting FastMCP at "/" preserves its own internal /mcp route.
app = Starlette(
    routes=[
        Route("/health", health),
        *observer_app.routes,
        Mount("/", app=mcp_app),
    ],
    lifespan=mcp_app.lifespan,
)

app.add_middleware(TokenGuardMiddleware)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080")),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
