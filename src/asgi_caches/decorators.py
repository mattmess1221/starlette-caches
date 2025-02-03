from __future__ import annotations

import functools
import typing

from .middleware import CacheControlMiddleware, CacheMiddleware
from .utils.misc import is_asgi3

if typing.TYPE_CHECKING:
    from aiocache import BaseCache as Cache
    from starlette.types import ASGIApp


def cached(cache: Cache) -> typing.Callable:
    """Wrap an ASGI endpoint with [asgi_caches.middleware.CacheMiddleware][].

    This decorator provides the same behavior than `CacheMiddleware`,
    but at an endpoint level.

    Raises 'ValueError' if the wrapped callable isn't an ASGI application.
    """

    def wrap(app: ASGIApp) -> ASGIApp:
        _validate_asgi3(app)
        middleware = CacheMiddleware(app, cache=cache)
        return _wrap_in_middleware(app, middleware)

    return wrap


def cache_control(**kwargs: typing.Any) -> typing.Callable:
    """Wrap an ASGI endpoint with [asgi_caches.middleware.CacheControlMiddleware][]."""

    def wrap(app: ASGIApp) -> ASGIApp:
        _validate_asgi3(app)
        middleware = CacheControlMiddleware(app, **kwargs)
        return _wrap_in_middleware(app, middleware)

    return wrap


def _wrap_in_middleware(app: ASGIApp, middleware: ASGIApp) -> ASGIApp:
    # Use `updated=()` to prevent copying `__dict__` onto `middleware`.
    # (If `app` is a middleware itself and has a `.app` attribute, it would be copied
    # onto `middleware`, effectively removing `app` from the middleware chain.)
    return functools.wraps(app, updated=())(middleware)


def _validate_asgi3(app: ASGIApp) -> None:
    if not is_asgi3(app):
        raise ValueError(
            f"{app!r} does not seem to be an ASGI3 callable. "
            "Did you try to apply this decorator to a framework-specific view "
            "function? (It can only be applied to ASGI callables.)"
        )
