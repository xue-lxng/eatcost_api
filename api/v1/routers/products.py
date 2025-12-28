from litestar import Router, get
from litestar.params import Parameter

from api.v1.response_models.products import CategoryProducts, Category
from api.v1.response_models.search import SearchResponse, AutocompleteResponse
from api.v1.services.products import (
    get_all_products,
    get_products_by_category,
    get_categories,
)
from api.v1.services.search import search_products_service, search_autocomplete_service
from core.caching.in_redis import AsyncRedisCache


@get("/search-autocomplete", tags=["Search"])
async def search_autocomplete(
    redis: AsyncRedisCache,
    search_query: str = Parameter(
        title="query", description="Поисковый запрос", query="query"
    ),
) -> AutocompleteResponse:
    """Retrieve autocomplete suggestions for a given search query.

    Args:
        redis: Async Redis cache instance for data retrieval.
        search_query: The search query string to autocomplete.

    Returns:
        AutocompleteResponse containing formatted suggestions.
    """
    result = await search_autocomplete_service(redis, search_query.lower())
    return AutocompleteResponse(
        suggestions=result["suggestions"],
        query=result.get("prefix", search_query),
        mode=result.get("mode", "full"),
        prefix=result.get("prefix", ""),
    )


@get("/search", tags=["Search"])
async def search_products(
    redis: AsyncRedisCache,
    search_query: str = Parameter(
        title="query", description="Поисковый запрос", query="query"
    ),
) -> SearchResponse:
    """Search for products based on a normalized query string.

    Args:
        redis: Async Redis cache instance for storing/retrieving results.
        search_query: The search query string from the request parameter.

    Returns:
        SearchResponse containing query, count, and results.
    """
    normalized_query = search_query.lower().strip()
    results = await search_products_service(normalized_query, redis)
    return SearchResponse(query=normalized_query, count=len(results), results=results)


@get("/category", tags=["Products"])
async def get_category(
    redis: AsyncRedisCache,
    parent_category_id: str | None = Parameter(
        title="parent_category_id",
        description="Идентификатор родительской категории",
        query="parent_category_id",
        required=False,
    ),
) -> list[Category]:
    """Retrieve a list of categories from the cache."""
    return await get_categories(redis, parent_category_id=parent_category_id)


@get("", tags=["Products"])
async def get_products(
    redis: AsyncRedisCache,
    category_id: str | None = Parameter(
        title="category_id",
        description="Идентификатор категории",
        query="category_id",
        required=False,
    ),
) -> list[CategoryProducts]:
    """Retrieve products from cache, optionally filtered by category."""
    return (
        await get_products_by_category(redis, category_id)
        if category_id
        else await get_all_products(redis)
    )


router = Router(
    path="/products",
    route_handlers=[search_products, get_products, search_autocomplete, get_category],
)
