import asyncio

from loguru import logger

from api.v1.services.products import get_all_products_names
from core.caching.in_redis import AsyncRedisCache
from core.task_locking.in_redis import DistributedLock


async def update_search_autocomplete_periodically(cache: AsyncRedisCache) -> None:
    """
    Periodically update search autocomplete data in Redis cache.

    This coroutine is designed to run as a background task, refreshing
    autocomplete suggestions at regular intervals.

    Args:
        cache: An AsyncRedisCache instance for storing and retrieving autocomplete data.
    """
    while True:
        async with DistributedLock(
            "task:update_search_autocomplete", skip_if_locked=True
        ) as lock:
            if not lock.acquired:
                await asyncio.sleep(1800)
                continue
            try:
                logger.info("Updating search autocomplete index...")
                products = await get_all_products_names(cache)
                await cache.build_word_autocomplete_index(
                    index_key="autocomplete:products", suggestions=products, ttl=3600
                )
            except Exception as e:
                logger.error(f"Error updating search autocomplete: {e}")
            else:
                logger.info("Search autocomplete index updated successfully.")
        await asyncio.sleep(1800)
