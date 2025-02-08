from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest
from aiocache import Cache
from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route

from asgi_caches.decorators import cached
from asgi_caches.middleware import CacheMiddleware

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.types import Receive, Scope, Send


@pytest.mark.asyncio
async def test_decorator_raw_asgi() -> None:
    cache = Cache(ttl=2 * 60)

    @cached(cache=cache)
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        response = PlainTextResponse("Hello, world!")
        await response(scope, receive, send)

    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://testserver"
    )

    async with cache, client:
        r = await client.get("/")
        assert r.status_code == 200
        assert r.text == "Hello, world!"
        assert "Expires" in r.headers
        assert "Cache-Control" in r.headers
        assert r.headers["X-Cache"] == "miss"

        r = await client.get("/")
        assert r.status_code == 200
        assert r.text == "Hello, world!"
        assert "Expires" in r.headers
        assert "Cache-Control" in r.headers
        assert r.headers["X-Cache"] == "hit"


@pytest.mark.asyncio
async def test_decorator_starlette_endpoint() -> None:
    cache = Cache(ttl=2 * 60)

    @cached(cache=cache)
    class CachedHome(HTTPEndpoint):
        async def get(self, request: Request) -> Response:
            return PlainTextResponse("Hello, world!")

    class UncachedUsers(HTTPEndpoint):
        async def get(self, request: Request) -> Response:
            return PlainTextResponse("Hello, users!")

    assert isinstance(CachedHome, CacheMiddleware)

    app = Starlette(routes=[Route("/", CachedHome), Route("/users", UncachedUsers)])
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://testserver"
    )

    async with cache, client:
        r = await client.get("/")
        assert r.status_code == 200
        assert r.text == "Hello, world!"
        assert "Expires" in r.headers
        assert "Cache-Control" in r.headers
        assert r.headers["X-Cache"] == "miss"

        r = await client.get("/")
        assert r.status_code == 200
        assert r.text == "Hello, world!"
        assert "Expires" in r.headers
        assert "Cache-Control" in r.headers
        assert r.headers["X-Cache"] == "hit"

        r = await client.get("/users")
        assert r.status_code == 200
        assert r.text == "Hello, users!"
        assert "Expires" not in r.headers
        assert "Cache-Control" not in r.headers
        assert "X-Cache" not in r.headers

        r = await client.get("/users")
        assert r.status_code == 200
        assert r.text == "Hello, users!"
        assert "Expires" not in r.headers
        assert "Cache-Control" not in r.headers
        assert "X-Cache" not in r.headers


@pytest.mark.asyncio
async def test_decorate_starlette_view() -> None:
    cache = Cache(ttl=2 * 60)

    with pytest.raises(ValueError, match="does not seem to be an ASGI3 callable"):

        @cached(cache)  # type: ignore
        async def home(request: Request) -> Response: ...  # pragma: no cover
