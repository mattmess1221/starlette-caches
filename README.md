# asgi-caches

[![Build Status](https://github.com/mattmess1221/asgi-caches/actions/workflows/ci.yml/badge.svg)](https://github.com/mattmess1221/asgi-caches/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/mattmess1221/asgi-caches/branch/main/graph/badge.svg)](https://codecov.io/gh/mattmess1221/asgi-caches)
[![Package version](https://badge.fury.io/py/asgi-caches.svg)](https://pypi.org/project/asgi-caches)

`asgi-caches` provides middleware and utilities for adding server-side HTTP caching to ASGI applications. It is powered by [`aiocache`](https://aiocache.aio-libs.org/en/latest/), and inspired by Django's cache framework.

Documentation is available at: https://mattmess1221.github.io/asgi-caches/

**Note**: this project is in an "alpha" status. Several features still need to be implemented, and you should expect breaking API changes across minor versions.

## Features

- Compatibility with any ASGI application (e.g. Starlette, FastAPI, Quart, etc.).
- Support for application-wide or per-endpoint caching.
- Ability to fine-tune the cache behavior (TTL, cache control) down to the endpoint level.
- Clean and explicit API enabled by a loose coupling with `aiocache`.
- Fully type annotated.
- 100% test coverage.

## Installation

```bash
pip install "asgi-caches"
```

To install with redis or memcached support, use:

```bash
pip install "asgi-caches[redis,memcached]"
```

## Quickstart

```python
from aiocache import Cache
from asgi_caches.middleware import CacheMiddleware

cache = Cache(ttl=2 * 60)

async def app(scope, receive, send):
    assert scope["type"] == "http"
    headers = [(b"content-type", "text/plain")]
    await send({"type": "http.response.start", "status": 200, "headers": headers})
    await send({"type": "http.response.body", "body": b"Hello, world!"})

app = CacheMiddleware(app, cache=cache)
```

This example:

- Sets up an in-memory cache (see the [aiocache docs](https://aiocache.aio-libs.org/en/latest/) for specifics).
- Sets up an application (in this case, a raw-ASGI 'Hello, world!' app).
- Applies caching on the entire application.

To learn more, head to the [documentation](https://mattmess1221.github.io/asgi-caches/).

## Credits

Due credit goes to the Django developers and maintainers, as a lot of the API and implementation was directly inspired by the [Django cache framework](https://docs.djangoproject.com/en/2.2/topics/cache/).

## License

MIT
