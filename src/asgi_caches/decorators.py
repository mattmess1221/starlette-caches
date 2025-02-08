from __future__ import annotations

import functools
import sys
import typing

from .middleware import CacheControlMiddleware, CacheMiddleware
from .utils.misc import is_asgi3

if sys.version_info >= (3, 10):  # pragma: no cover
    from typing import ParamSpec
else:  # pragma: no cover
    from typing_extensions import ParamSpec

if typing.TYPE_CHECKING:
    from starlette.types import ASGIApp


_P = ParamSpec("_P")


class _MiddlewareFactory(typing.Protocol[_P]):
    def __call__(
        self, app: ASGIApp, *args: _P.args, **kwargs: _P.kwargs
    ) -> ASGIApp: ...


def _middleware_to_decorator(
    cls: _MiddlewareFactory[_P],
) -> typing.Callable[_P, typing.Callable[[ASGIApp], ASGIApp]]:
    def decorator(
        *args: _P.args, **kwargs: _P.kwargs
    ) -> typing.Callable[[ASGIApp], ASGIApp]:
        def wrap(app: ASGIApp) -> ASGIApp:
            _validate_asgi3(app)
            middleware = cls(app, *args, **kwargs)
            return _wrap_in_middleware(app, middleware)

        return wrap

    return decorator


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


cached = _middleware_to_decorator(CacheMiddleware)
"""Wrap an ASGI endpoint with [asgi_caches.middleware.CacheMiddleware][].

This decorator provides the same behavior as `CacheMiddleware`,
but at an endpoint level.

Raises 'ValueError' if the wrapped callable isn't an ASGI application.
"""


cache_control = _middleware_to_decorator(CacheControlMiddleware)
"""Wrap an ASGI endpoint with [asgi_caches.middleware.CacheControlMiddleware][].

This decorator provides the same behavior as `CacheControlMiddleware`,
but at an endpoint level.

Raises 'ValueError' if the wrapped callable isn't an ASGI application.
"""
