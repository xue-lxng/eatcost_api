import asyncio

from loguru import logger

from api.v1.services.products import get_all_products, get_products_by_category
from config import CONSUMER_KEY, CONSUMER_SECRET, BASE_URL
from core.caching.in_redis import AsyncRedisCache
from core.task_locking.in_redis import DistributedLock
from core.utils.woocommerce import WooCommerceUtils


async def get_app_products_periodically(redis: AsyncRedisCache) -> None:
    while True:
        async with DistributedLock(
            "task:get_all_products", skip_if_locked=True
        ) as lock:
            if not lock.acquired:
                await asyncio.sleep(1800)
                continue
            try:
                logger.info("Fetching products from API and caching them...")
                await get_all_products(redis)
            except Exception as e:
                logger.error(f"Error fetching products: {e}")
            else:
                logger.info("Products fetched and cached successfully.")
        await asyncio.sleep(3600)


async def get_products_by_category_periodically(redis: AsyncRedisCache) -> None:
    while True:
        async with DistributedLock(
            "task:get_products_by_category", skip_if_locked=True
        ) as lock:
            if not lock.acquired:
                await asyncio.sleep(1800)
                continue
            try:
                logger.info(
                    "Fetching products by category from API and caching them..."
                )
                async with WooCommerceUtils(
                    CONSUMER_KEY, CONSUMER_SECRET, BASE_URL
                ) as woocommerce:
                    categories = await woocommerce.get_categories()
                    for category in categories:
                        await get_products_by_category(redis, category)
            except Exception as e:
                logger.error(f"Error fetching products by category: {e}")
            else:
                logger.info("Products by category fetched and cached successfully.")
        await asyncio.sleep(3600)
