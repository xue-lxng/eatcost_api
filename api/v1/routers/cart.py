import asyncio
from typing import Dict, Any

from litestar import get, Router, Request, post
from litestar.exceptions import HTTPException

from api.v1.request_models.cart import (
    UpdateCartRequest,
    AddToCartRequest,
    RemoveFromCartRequest,
)
from api.v1.services.cart import CartService
from core.caching.in_redis import AsyncRedisCache


@get(
    "",
    tags=["Cart"],
    summary="Get cart",
    description="Retrieve products from cache, optionally filtered by category. Request headers: Authorization: Bearer <jwt_token>",
)
async def get_cart(request: Request, redis: AsyncRedisCache) -> Dict[str, Any]:
    """Retrieve products from cache, optionally filtered by category."""
    jwt_token = request.headers.get("Authorization", None)
    if jwt_token is None:
        raise HTTPException(status_code=401, detail="Authorization token is missing")
    if "Bearer " not in jwt_token:
        raise HTTPException(
            status_code=401, detail="Invalid authorization token format"
        )

    return await CartService.get_cart(jwt_token, redis)


@post(
    "/add-item",
    tags=["Cart"],
    summary="Add item to cart",
    description="Add a product to the cart.",
)
async def add_to_cart(
    data: AddToCartRequest, request: Request, redis: AsyncRedisCache
) -> Dict[str, Any]:
    """Add a product to the cart."""
    jwt_token = request.headers.get("Authorization", None)
    if jwt_token is None:
        raise HTTPException(status_code=401, detail="Authorization token is missing")
    if "Bearer " not in jwt_token:
        raise HTTPException(
            status_code=401, detail="Invalid authorization token format"
        )

    return await CartService.add_to_cart(
        jwt_token, data.product_id, data.quantity, redis
    )


@post(
    "/remove-item",
    tags=["Cart"],
    summary="Remove item from cart",
    description="Remove a product from the cart.",
)
async def remove_from_cart(
    data: RemoveFromCartRequest, request: Request, redis: AsyncRedisCache
) -> Dict[str, Any]:
    """Remove a product from the cart."""
    jwt_token = request.headers.get("Authorization", None)
    if jwt_token is None:
        raise HTTPException(status_code=401, detail="Authorization token is missing")
    if "Bearer " not in jwt_token:
        raise HTTPException(
            status_code=401, detail="Invalid authorization token format"
        )

    return await CartService.remove_from_cart(jwt_token, data.product_key, redis)


@post(
    "/edit-item",
    tags=["Cart"],
    summary="Edit cart item",
    description="Update the quantity of a product in the cart.",
)
async def update_cart_item(
    data: UpdateCartRequest, request: Request, redis: AsyncRedisCache
) -> Dict[str, Any]:
    """Update the quantity of a product in the cart."""
    jwt_token = request.headers.get("Authorization", None)
    if jwt_token is None:
        raise HTTPException(status_code=401, detail="Authorization token is missing")
    if "Bearer " not in jwt_token:
        raise HTTPException(
            status_code=401, detail="Invalid authorization token format"
        )

    asyncio.create_task(
        CartService.update_item_in_cart(jwt_token, data.key, data.quantity, redis)
    )
    return {"message": "Item updated successfully"}


router = Router(
    path="/cart",
    route_handlers=[get_cart, add_to_cart, remove_from_cart, update_cart_item],
    security=[{"Authentication": ["Bearer"]}],
)
