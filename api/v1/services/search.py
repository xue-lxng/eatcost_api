from typing import List, Dict, Any
from typing import TypedDict

from config import CONSUMER_KEY, CONSUMER_SECRET, BASE_URL
from core.caching.in_redis import AsyncRedisCache
from core.utils.woocommerce import WooCommerceUtils


class AggregatedProduct(TypedDict, total=False):
    id: int
    name: str
    slug: str
    permalink: str
    type: str
    status: str
    description: str
    short_description: str
    price: float
    regular_price: float
    sale_price: float
    on_sale: bool
    purchasable: bool
    stock_status: str
    average_rating: float
    rating_count: int
    image: str | None
    categories: list[dict[str, Any]]
    attributes: list[dict[str, Any]]
    featured: bool


def aggregate_product_data(product: dict[str, Any]) -> AggregatedProduct:
    """
    Агрегирует самые важные данные из WooCommerce продукта

    Args:
        product: Словарь с данными продукта из WooCommerce API

    Returns:
        Словарь с агрегированными данными продукта
    """
    # Получаем первое изображение или None
    first_image = None
    images = product.get("images", [])
    if (
        images
        and isinstance(images, list)
        and images[0]
        and isinstance(images[0], dict)
    ):
        first_image = images[0].get("src")

    # Получаем категории
    categories = [
        {"id": cat.get("id"), "name": cat.get("name")}
        for cat in product.get("categories", [])
        if cat
    ]

    # Получаем атрибуты (для вариативных товаров)
    attributes = [
        {"name": attr.get("name"), "options": attr.get("options", [])}
        for attr in product.get("attributes", [])
        if attr
    ]

    # Обработка цены продажи с учетом пустой строки
    sale_price = product.get("sale_price", "")
    sale_price = (
        float(sale_price) if sale_price else float(product.get("regular_price", 0))
    )

    return {
        "id": product.get("id"),
        "name": product.get("name"),
        "slug": product.get("slug"),
        "permalink": product.get("permalink"),
        "type": product.get("type"),
        "status": product.get("status"),
        "description": product.get("description"),
        "short_description": product.get("short_description"),
        "price": float(product.get("price", 0)),
        "regular_price": float(product.get("regular_price", 0)),
        "sale_price": sale_price,
        "on_sale": product.get("on_sale", False),
        "purchasable": product.get("purchasable", False),
        "stock_status": product.get("stock_status"),
        "average_rating": product.get("average_rating"),
        "rating_count": product.get("rating_count", 0),
        "image": first_image,
        "categories": categories,
        "attributes": attributes,
        "featured": product.get("featured", False),
    }


def aggregate_products_list(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Агрегирует список продуктов

    Args:
        products: Список продуктов из WooCommerce API

    Returns:
        Список агрегированных продуктов
    """
    return [aggregate_product_data(product) for product in products]


async def search_products_service(
    query: str, redis: AsyncRedisCache, ttl: int = 3600
) -> List[Dict[str, Any]]:
    """
    Поиск продуктов с кэшированием результатов

    Args:
        query: Поисковый запрос
        redis: Экземпляр AsyncRedisCache для кэширования
        ttl: Время жизни кэша в секундах (по умолчанию 1 час)

    Returns:
        Список агрегированных продуктов
    """
    normalized_query = query.lower()
    cache_key = f"search:products:{normalized_query}"
    cache_tag = f"search:query:{normalized_query}"

    cached_result = await redis.get(cache_key, compressed=True)
    if cached_result is not None:
        return cached_result
    async with WooCommerceUtils(
        consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET, base_url=BASE_URL
    ) as woocommerce:
        products_data = await woocommerce.search_products(query)

    await redis.set(cache_key, products_data, ttl=ttl, tags=[cache_tag], compress=True)

    return products_data


async def search_autocomplete_service(
    redis: AsyncRedisCache, search_query: str
) -> dict:
    """
    Provide search autocomplete suggestions from Redis cache.

    Args:
        redis: AsyncRedisCache instance for accessing cached autocomplete data
        woocommerce: WooCommerceUtils instance
        search_query: User's search input string

    Returns:
        Dictionary with suggestions list containing text, display, and type fields
    """
    try:
        if not search_query or len(search_query) < 2:
            return {"suggestions": []}

        result = await redis.search_with_word_completion(
            "autocomplete:products", search_query, limit=10
        )

        suggestions = result["suggestions"]

        if result["mode"] == "next_word":
            next_words = result.get("next_words_only", [])
            formatted_suggestions = [
                {"text": text, "display": word, "type": "next_word"}
                for text, word in zip(suggestions, next_words)
            ]
        else:
            formatted_suggestions = [
                {"text": text, "display": text, "type": "full"} for text in suggestions
            ]

        return {"suggestions": formatted_suggestions}
    except Exception as e:
        print(f"Error in search_autocomplete_service: {e}")
