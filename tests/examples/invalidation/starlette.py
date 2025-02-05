from aiocache import Cache
from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from starlette.status import HTTP_204_NO_CONTENT

from asgi_caches.helpers import CacheHelper
from asgi_caches.middleware import CacheMiddleware


class MyRoute(HTTPEndpoint):
    async def get(self, request: Request) -> Response:
        return PlainTextResponse("Hello, GET!")

    async def post(self, request: Request) -> Response:
        return PlainTextResponse("Hello, POST!")


async def invalidation_route(request: Request) -> Response:
    helper = CacheHelper(request)
    # invalidate a named route
    await helper.invalidate_cache_for("my_route")
    return Response(status_code=HTTP_204_NO_CONTENT)


app = Starlette(
    routes=[
        Route("/", MyRoute, name="my_route"),
        Route("/invalidate", invalidation_route, methods=["POST"]),
    ],
    middleware=[
        Middleware(CacheMiddleware, cache=Cache()),
    ],
)
