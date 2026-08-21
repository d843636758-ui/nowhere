"""Zeabur / ChatGPT Streamable-HTTP entrypoint for Nowhere 1.0."""
from __future__ import annotations

import hmac
import os
from pathlib import Path
from urllib.parse import parse_qs

os.environ.setdefault("NOWHERE_HOME", "/data")
os.environ.setdefault("NOWHERE_GRID_PATH", "/data/grid.npz")
os.environ.setdefault("NOWHERE_TILES_DIR", "/data/tiles")

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from nowhere import server as nowhere_server
from nowhere import state as state_mod
from nowhere.web import app as observer_app

mcp = nowhere_server.mcp

try:
    saved = state_mod.WorldState.load()
    if saved is not None and saved.pos is not None:
        nowhere_server._state = saved
        nowhere_server._postcard_counter = max(
            (card.get("id", 0) for card in saved.postcards),
            default=0,
        )
except Exception:
    pass

public_url = os.environ.get("NOWHERE_PUBLIC_URL", "").strip().rstrip("/")
if public_url:
    mcp.instructions = (
        "你正在使用乌有乡（Nowhere）旅行。"
        f"网页旁观者地址：{public_url}/ 。"
        "可以把这个地址告诉用户，让对方实时看你走到哪里。"
    )

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
        "1",
        "true",
        "yes",
        "on",
    }:
        raw = request.scope.get("query_string", b"").decode("utf-8", "ignore")
        values = parse_qs(raw).get("token", [])
        if values:
            return values[0].strip()

    return ""


class TokenGuardMiddleware(BaseHTTPMiddleware):
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

    grid_path = Path(
        os.environ.get(
            "NOWHERE_GRID_PATH",
            "/app/nowhere/data/grid.npz",
        )
    )

    tiles_dir = Path(
        os.environ.get(
            "NOWHERE_TILES_DIR",
            "/data/tiles",
        )
    )

    tile_index = tiles_dir / "index.json"

    try:
        tile_count = (
            len(list(tiles_dir.glob("*.npz")))
            if tiles_dir.exists()
            else 0
        )
    except OSError:
        tile_count = 0

    grid_size = (
        grid_path.stat().st_size
        if grid_path.exists()
        else 0
    )

    online_enabled = (
        os.environ.get(
            "NOWHERE_ONLINE_ELEVATION",
            "1",
        ).lower()
        not in {
            "0",
            "false",
            "no",
            "off",
        }
    )

    return JSONResponse(
        {
            "status": "ok",
            "service": "nowhere",
            "version": "1.0.0-merged-online-90m",
            "mcp": "/mcp",
            "observer": "/",
            "has_saved_position": state.pos is not None,
            "high_precision": {
                "mode": (
                    "online-90m+local-fallback"
                    if online_enabled
                    else "local-only"
                ),
                "online_elevation": online_enabled,
                "online_source": "Open-Meteo Copernicus GLO-90",
                "full_grid": grid_path.exists(),
                "grid_path": str(grid_path),
                "grid_bytes": grid_size,
                "tiles_index": tile_index.exists(),
                "tiles_dir": str(tiles_dir),
                "tile_count": tile_count,
            },
        }
    )


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
