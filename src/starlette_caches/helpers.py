# ruff: noqa: FA100
import typing
from collections.abc import Mapping

from starlette.datastructures import URL, Headers
from starlette.requests import Request

from .exceptions import MissingCaching
from .middleware import SCOPE_NAME, CacheMiddleware
from .utils.cache import delete_from_cache


class _BaseCacheMiddlewareHelper:
    """Base class for helpers that need access to the `CacheMiddleware` instance."""

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


class CacheHelper(_BaseCacheMiddlewareHelper):
    """Helper class for the `CacheMiddleware`.

    This helper class provides a way to maniuplate the cache middleware.

    If using FastAPI, you can use the `CacheHelper` as a dependency in your endpoint.

    Example:
        ```python
        async def invalidate_cache(helper: Annotated[CacheHelper, Depends()]) -> None:
            await helper.invalidate_cache_for("my_route")
        ```

    """

    async def invalidate_cache_for(
        self,
        url: typing.Union[str, URL],
        *,
        headers: typing.Union[Mapping[str, str], None] = None,
    ) -> None:
        """Invalidate the cache for a given named route or full url.

        `headers` will be used to generate the cache key. The `Vary` header from the
        cached response will determine which headers will be used.

        Args:
            url: The URL to invalidate or name of a starlette route.
            headers: The headers used to generate the cache key.

        """
        if not isinstance(url, URL):
            url = self.request.url_for(url)

        if not isinstance(headers, Headers):
            headers = Headers(headers)

        await delete_from_cache(url, vary=headers, cache=self.middleware.cache)
