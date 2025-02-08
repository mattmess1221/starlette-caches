from __future__ import annotations

import typing
from functools import partial

from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.responses import Response

from .exceptions import (
    DuplicateCaching,
    MissingCaching,
    RequestNotCachable,
    ResponseNotCachable,
)
from .rules import Rule
from .utils.cache import (
    INVALIDATING_METHODS,
    delete_from_cache,
    get_from_cache,
    patch_cache_control,
    store_in_cache,
)
from .utils.logging import HIT_EXTRA, MISS_EXTRA, get_logger
from .utils.misc import eager_annotation, kvformat

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

    from aiocache.base import BaseCache as Cache
    from starlette.types import ASGIApp, Message, Receive, Scope, Send


SCOPE_NAME = "__asgi_caches__"

logger = get_logger(__name__)


class CacheMiddleware:
    """Middleware that caches responses.

    This middleware caches responses based on the request path. It can be
    configured with rules that determine which requests and responses should be
    cached. Configure the rules by passing a sequence of `Rule` instances to
    the `rules` argument. See [Rules](usage/rules.md) for more information on how to
    configure rules.

    Args:
        app: The ASGI application to wrap.
        cache: The cache instance to use.
        rules: A sequence of rules for caching behavior.

    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        cache: Cache,
        rules: Sequence[Rule] | None = None,
    ) -> None:
        if rules is None:
            rules = [Rule()]

        self.app = app
        self.cache = cache
        self.rules = rules

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if SCOPE_NAME in scope:
            raise DuplicateCaching(
                "Another `CacheMiddleware` was detected in the middleware stack.\n"
                "HINT: this exception probably occurred because:\n"
                "- You wrapped an application around `CacheMiddleware` multiple "
                "times.\n"
                "- You tried to apply `@cached()` onto an endpoint, but "
                "the application is already wrapped around a `CacheMiddleware`."
            )

        scope[SCOPE_NAME] = self

        responder = CacheResponder(
            self.app,
            cache=self.cache,
            rules=self.rules,
        )
        await responder(scope, receive, send)


class BaseCacheMiddlewareHelper:
    """Base class for helpers that need access to the `CacheMiddleware` instance."""

    @eager_annotation
    def __init__(self, request: Request) -> None:
        """Initialize the helper with the request and the cache middleware instance.

        Args:
            request: The request object.

        Raises:
            MissingCaching: If the cache middleware instance is not found in the scope
                            or if the cache middleware instance is not an instance of
                            `CacheMiddleware`.

        """
        self.request = request

        if SCOPE_NAME not in request.scope:  # pragma: no cover
            raise MissingCaching(
                "No CacheMiddleware instance found in the ASGI scope. Did you forget "
                "to wrap the ASGI application with `CacheMiddleware`?"
            )

        middleware = request.scope[SCOPE_NAME]
        if not isinstance(middleware, CacheMiddleware):  # pragma: no cover
            raise MissingCaching(
                f"A scope variable named {SCOPE_NAME!r} was found, but it does not "
                "contain a `CacheMiddleware` instance. It is likely that an "
                "incompatible middleware was added to the middleware stack."
            )

        self.middleware = middleware


class CacheResponder:
    def __init__(
        self,
        app: ASGIApp,
        *,
        cache: Cache,
        rules: Sequence[Rule],
    ) -> None:
        self.app = app
        self.cache = cache
        self.rules = rules

        self.initial_message: Message = {}
        self.is_response_cachable = True
        self.request: Request | None = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] == "http"

        self.request = request = Request(scope)

        try:
            response = await get_from_cache(request, cache=self.cache, rules=self.rules)
        except RequestNotCachable:
            if request.method in INVALIDATING_METHODS:
                send = partial(self.send_then_invalidate, send=send)
        else:
            if response is not None:
                logger.debug("cache_lookup %s", "HIT", extra=HIT_EXTRA)
                await response(scope, receive, send)
                return
            send = partial(self.send_with_caching, send=send)
            logger.debug("cache_lookup %s", "MISS", extra=MISS_EXTRA)

        await self.app(scope, receive, send)

    async def send_with_caching(self, message: Message, *, send: Send) -> None:
        if not self.is_response_cachable:
            await send(message)
            return

        if message["type"] == "http.response.start":
            # Defer sending this message until we figured out
            # whether the response can be cached.
            self.initial_message = message
            return

        assert message["type"] == "http.response.body"
        if message.get("more_body", False):
            logger.trace("response_not_cachable reason=is_streaming")
            self.is_response_cachable = False
            await send(self.initial_message)
            await send(message)
            return

        assert self.request is not None
        body = message["body"]
        response = Response(content=body, status_code=self.initial_message["status"])
        # NOTE: be sure not to mutate the original headers directly, as another Response
        # object might be holding a reference to the same list.
        response.raw_headers = list(self.initial_message["headers"])

        try:
            await store_in_cache(
                response, request=self.request, cache=self.cache, rules=self.rules
            )
        except ResponseNotCachable:
            self.is_response_cachable = False
        else:
            # Apply any headers added or modified by 'store_in_cache()'.
            self.initial_message["headers"] = list(response.raw_headers)

        await send(self.initial_message)
        await send(message)

    async def send_then_invalidate(self, message: Message, *, send: Send) -> None:
        # listen for the response start message and invalidate the cache
        # if the request method is POST, PUT, PATCH, DELETE, and if the
        # response status code is 2xx or 3xx
        assert self.request is not None
        if message["type"] == "http.response.start" and 200 <= message["status"] < 400:
            await delete_from_cache(
                self.request.url,
                vary=self.request.headers,
                cache=self.cache,
            )
        await send(message)


class CacheDirectives(typing.TypedDict, total=False):
    max_age: int
    s_maxage: int
    no_cache: bool
    no_store: bool
    no_transform: bool
    must_revalidate: bool
    proxy_revalidate: bool
    must_understand: bool
    private: bool
    public: bool
    immutable: bool
    stale_while_revalidate: int
    stale_if_error: int


class CacheControlMiddleware:
    """Middleware which handles Cache-Control headers for upstream cache proxies.

    Keyword Args:
        max_age (float): The maximum age of the response in seconds.
        public (bool): Not implemented
        private (bool): Not implemented
        **kwargs: Additional Cache-Control directives

    See Also:
    --------
    - [Cache-Control - HTTP | MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control)

    """

    def __init__(self, app: ASGIApp, **kwargs: typing.Unpack[CacheDirectives]) -> None:
        self.app = app
        self.kwargs = kwargs

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        responder = CacheControlResponder(self.app, **self.kwargs)
        await responder(scope, receive, send)


class CacheControlResponder:
    def __init__(self, app: ASGIApp, **kwargs: typing.Unpack[CacheDirectives]) -> None:
        self.app = app
        self.kwargs = kwargs

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] == "http"
        send = partial(self.send_with_caching, send=send)
        await self.app(scope, receive, send)

    async def send_with_caching(self, message: Message, *, send: Send) -> None:
        if message["type"] == "http.response.start":
            logger.trace(f"patch_cache_control {kvformat(**self.kwargs)}")
            headers = MutableHeaders(raw=list(message["headers"]))
            patch_cache_control(headers, **self.kwargs)
            message["headers"] = headers.raw

        await send(message)
