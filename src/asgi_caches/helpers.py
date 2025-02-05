from __future__ import annotations

from typing import TYPE_CHECKING

from starlette.datastructures import URL, Headers

from .middleware import BaseCacheMiddlewareHelper
from .utils.cache import delete_from_cache

if TYPE_CHECKING:
    from collections.abc import Mapping


class CacheHelper(BaseCacheMiddlewareHelper):
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
        url: str | URL,
        *,
        headers: Headers | Mapping[str, str] | None = None,
    ) -> None:
        """Invalidate the cache for a given named route or full url.

        `headers` will be used to generate the cache key based on. The `Vary` header
        will determine which headers will be used.

        Args:
            url: The URL to invalidate or name of a starlette route.
            headers: The headers used to generate the cache key.

        """
        if not isinstance(url, URL):
            url = self.request.url_for(url)

        if not isinstance(headers, Headers):
            headers = Headers(headers)

        await delete_from_cache(url, vary=headers, cache=self.middleware.cache)
