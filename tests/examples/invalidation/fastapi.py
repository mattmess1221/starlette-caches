from typing import Annotated

from aiocache import Cache
from fastapi import Depends, FastAPI, status
from fastapi.responses import PlainTextResponse

from starlette_caches.helpers import CacheHelper
from starlette_caches.middleware import CacheMiddleware

app = FastAPI(default_response_class=PlainTextResponse)
app.add_middleware(CacheMiddleware, cache=Cache())


@app.get("/")
async def read_root() -> str:
    return "Hello, GET!"


@app.post("/")
async def create_root() -> str:
    return "Hello, POST!"


@app.post("/invalidate", status_code=status.HTTP_204_NO_CONTENT)
async def invalidate_cache(helper: Annotated[CacheHelper, Depends()]) -> None:
    await helper.invalidate_cache_for("read_root")
