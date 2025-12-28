import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from litestar import Litestar
from litestar.di import Provide
from litestar.openapi import OpenAPIConfig

import api
from config import REDIS_URL
from core.dependencies.redis import get_redis
from core.scheduled_tasks.products import (
    get_app_products_periodically,
    get_products_by_category_periodically,
)
from core.scheduled_tasks.search import update_search_autocomplete_periodically
from core.task_locking.in_redis import DistributedLock


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    print("Starting application")
    await DistributedLock.init_redis(REDIS_URL)

    asyncio.create_task(get_app_products_periodically(get_redis()))
    asyncio.create_task(get_products_by_category_periodically(get_redis()))
    asyncio.create_task(update_search_autocomplete_periodically(get_redis()))
    yield


app = Litestar(
    route_handlers=[api.router],
    dependencies={"redis": Provide(get_redis, sync_to_thread=False)},
    openapi_config=OpenAPIConfig(
        title="WooCommerce Manage API",
        version="0.1.0",
    ),
    lifespan=[lifespan],
)

if __name__ == "__main__":
    print("Starting server")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=4)
