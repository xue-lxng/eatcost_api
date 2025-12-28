import asyncio
from typing import List

import msgspec
from config import logger

from api.v1.response_models.products import CategoryProducts, Category
from config import CONSUMER_KEY, CONSUMER_SECRET, BASE_URL
from core.caching.in_redis import AsyncRedisCache
from core.utils.woocommerce import WooCommerceUtils


async def get_all_products(redis: AsyncRedisCache) -> List[CategoryProducts]:
    """
    Возвращает список CategoryProducts, сгруппированных по категориям.
    """

    cache_key = "products:by_category_list_struct"
    ttl = 3600
    try:
        cached = await redis.get(cache_key, compressed=True)
        if cached is None:
            async with WooCommerceUtils(CONSUMER_KEY, CONSUMER_SECRET, BASE_URL) as woocommerce:
                categories = await woocommerce.get_categories()
                tasks = [
                    woocommerce.get_products(category_id) for category_id in categories
                ]
                products = await asyncio.gather(*tasks)
                cached = [
                    item[0] for item in products
                ]
            await redis.set(cache_key, cached, ttl=ttl, compress=True)

        # cached: List[Dict[str, Any]] -> List[CategoryProducts]
        encoder = msgspec.json.Encoder()
        decoder = msgspec.json.Decoder(type=List[CategoryProducts])

        # перекодируем через JSON, чтобы строго соответствовать структурам
        data_bytes = encoder.encode(cached)
        result: List[CategoryProducts] = decoder.decode(data_bytes)
    except Exception as e:
        result = []
        logger.error(f"Error fetching products: {e}")
    return result

async def get_products_by_category(redis: AsyncRedisCache, category_id: str) -> List[CategoryProducts]:
    """
    Возвращает список CategoryProducts для указанной категории.
    """
    cache_key = f"products:by_category:{category_id}"
    ttl = 3600
    try:
        cached = await redis.get(cache_key, compressed=True)
        if cached is None:
            cached = []
            basic_page = 1
            while True:
                async with WooCommerceUtils(CONSUMER_KEY, CONSUMER_SECRET, BASE_URL) as woocommerce:
                    tasks = [
                        woocommerce.get_products(category_id, page) for page in range(basic_page, basic_page + 10)
                    ]
                    products = await asyncio.gather(*tasks)

                products_filtered = [product[0] for product in products if product]
                cached += products_filtered
                if not products_filtered or any(len(p) == 0 for p in products):
                    break
                basic_page += 10
            await redis.set(cache_key, cached, ttl=ttl, compress=True)
        return cached
    except Exception as e:
        logger.error(f"Error fetching products by category: {e}")
        return []


async def get_all_products_names(redis: AsyncRedisCache) -> List[str]:
    cache_key = "products:names"
    ttl = 3600
    try:
        cached = await redis.get(cache_key, compressed=True)
        if cached:
            return cached
        data = []
        async with WooCommerceUtils(CONSUMER_KEY, CONSUMER_SECRET, BASE_URL) as woocommerce:
            categories = await woocommerce.get_categories()
            for category in categories:
                result = await get_products_by_category(redis, category)
                if result:
                    items = result[0].get("items", [])
                    data += [item["name"] for item in items]
        await redis.set(cache_key, data, ttl=ttl, compress=True)
        return data
    except Exception as e:
        logger.error(f"Error fetching products names: {e}")
        return []


async def get_categories(redis: AsyncRedisCache, parent_category_id: int = None):
    cache_key = "categories"
    if parent_category_id:
        cache_key += f":{parent_category_id}"

    logger.info(cache_key)
    ttl = 3600
    try:
        cached = await redis.get(cache_key, compressed=True)
        if cached:
            return cached
        async with WooCommerceUtils(CONSUMER_KEY, CONSUMER_SECRET, BASE_URL) as woocommerce:
            cached = await woocommerce.get_categories(parent_category_id=parent_category_id, simplified=False)
        await redis.set(cache_key, cached, ttl=ttl, compress=True)

        encoder = msgspec.json.Encoder()
        decoder = msgspec.json.Decoder(type=List[Category])

        # перекодируем через JSON, чтобы строго соответствовать структурам
        data_bytes = encoder.encode(cached)
        result: List[Category] = decoder.decode(data_bytes)

        return result
    except Exception as e:
        logger.error(f"Error fetching products names: {e}")
        return []
