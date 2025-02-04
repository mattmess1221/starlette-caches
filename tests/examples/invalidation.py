from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from starlette.status import HTTP_204_NO_CONTENT

from asgi_caches.middleware import CacheInvalidator


class MyRoute(HTTPEndpoint):
    async def get(self, request: Request) -> Response:
        return PlainTextResponse("Hello, GET!")

    async def post(self, request: Request) -> Response:
        return PlainTextResponse("Hello, POST!")


async def invalidation_route(request: Request) -> Response:
    invalidator = CacheInvalidator(request)
    # invalidate a named route
    await invalidator.invalidate_cache_for("my_route")
    return Response(status_code=HTTP_204_NO_CONTENT)


routes = [
    Route("/", MyRoute, name="my_route"),
    Route("/invalidate", invalidation_route, methods=["POST"]),
]
