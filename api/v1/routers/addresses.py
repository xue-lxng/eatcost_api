from typing import List

from litestar import get, Router
from litestar.params import Parameter

from api.v1.response_models.addresses import (
    AddressSuggestions,
    AddressCheckResponse,
    AddressDelivery,
)
from api.v1.services.addresses import AddressService
from core.caching.in_redis import AsyncRedisCache


@get("/address-autocomplete", tags=["Addresses"])
async def search_autocomplete(
    redis: AsyncRedisCache,
    search_query: str = Parameter(
        title="query", description="Поисковый запрос", query="query"
    ),
) -> List[AddressSuggestions]:
    """Retrieve autocomplete suggestions for a given search query.

    Args:
        redis: Async Redis cache instance for data retrieval.
        search_query: The search query string to autocomplete.

    Returns:
        AutocompleteResponse containing formatted suggestions.
    """
    result = await AddressService.find_addresses_starting_with(search_query, redis)
    return [AddressSuggestions(text=addr) for addr in result]


@get(
    "/address-check",
    tags=["Addresses"],
    summary="Add item to cart",
    description="Add a product to the cart.",
)
async def address_check(
    redis: AsyncRedisCache,
    search_query: str = Parameter(
        title="query", description="Поисковый запрос", query="query"
    ),
) -> AddressCheckResponse:
    """Add a product to the cart."""
    result = await AddressService.check_address_exists(search_query, redis)

    delivery = [
        AddressDelivery("Бесплатная доставка", "free_delivery", result),
        AddressDelivery("Самовывоз", "local_pickup", True),
    ]

    return AddressCheckResponse(address=search_query, delivery_types=delivery)


router = Router(
    path="/address",
    route_handlers=[search_autocomplete, address_check],
)
