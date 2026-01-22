from typing import Dict, Any

from litestar import Router, Request, post

from api.v1.services.users import logger
from core.caching.in_redis import AsyncRedisCache


@post(
    "",
    tags=["Callbacks"],
    summary="Callbacks receiver",
    description="Callbacks receiver",
)
async def callback(
        request: Request, redis: AsyncRedisCache
) -> Dict[str, Any]:
    """Add a product to the cart."""
    logger.info(f"Callback received: {await request.json()}")


router = Router(
    path="/callbacks",
    route_handlers=[callback],
)
