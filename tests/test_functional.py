from __future__ import annotations

import importlib
import math
import typing

import httpx
import pytest
import pytest_asyncio

from tests.examples.resources import cache, special_cache

if typing.TYPE_CHECKING:
    from starlette.types import ASGIApp

# TIP: use 'pytest -k <id>' to run tests for a given example application only.
EXAMPLES = [
    pytest.param("tests.examples.starlette", id="starlette"),
]


@pytest_asyncio.fixture(name="app", params=EXAMPLES)
def fixture_app(request: pytest.FixtureRequest) -> ASGIApp:
    module: typing.Any = importlib.import_module(request.param)
    return module.app


@pytest_asyncio.fixture(name="client")
async def fixture_client(app: ASGIApp) -> typing.AsyncIterator[httpx.AsyncClient]:
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://testserver"
    )
    async with cache, special_cache, client:
        yield client


@pytest.mark.asyncio
async def test_caching(client: httpx.AsyncClient) -> None:
    r = await client.get("/")
    assert r.status_code == 200
    assert r.text == "Hello, world!"
    assert "Expires" not in r.headers
    assert "Cache-Control" not in r.headers
    assert "X-Cache" not in r.headers

    r = await client.get("/")
    assert "X-Cache" not in r.headers

    r = await client.get("/pi")
    assert r.status_code == 200
    assert r.json() == {"value": math.pi}
    assert r.headers["X-Cache"] == "miss"
    assert "Expires" in r.headers
    assert "Cache-Control" in r.headers
    assert r.headers["Cache-Control"] == "max-age=30, must-revalidate"

    r = await client.get("/pi")
    assert r.headers["X-Cache"] == "hit"

    r = await client.get("/sub/")
    assert r.status_code == 200
    assert r.text == "Hello, sub world!"
    assert r.headers["X-Cache"] == "miss"
    assert "Expires" in r.headers
    assert "Cache-Control" in r.headers
    assert r.headers["Cache-Control"] == "max-age=120"

    r = await client.get("/sub/")
    assert r.headers["X-Cache"] == "hit"

    r = await client.get("/exp")
    assert r.status_code == 200
    assert r.json() == {"value": math.e}
    assert r.headers["X-Cache"] == "miss"
    assert "Expires" in r.headers
    assert "Cache-Control" in r.headers
    assert r.headers["Cache-Control"] == "max-age=60"

    r = await client.get("/exp")
    assert r.headers["X-Cache"] == "hit"
