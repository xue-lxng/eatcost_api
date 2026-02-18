import asyncio

from api.v1.services.auth import AuthService
from config import CONSUMER_KEY, CONSUMER_SECRET, BASE_URL, logger
from core.caching.in_redis import AsyncRedisCache
from core.utils.woocommerce import WooCommerceUtils


class CartService:
    """
    Cart service for managing products in the cart.
    """

    @staticmethod
    async def get_cart(jwt_token: str, redis: AsyncRedisCache):
        try:
            try:
                decoded_token = AuthService.decode_jwt_token(
                    jwt_token.replace("Bearer ", "")
                )
                if not decoded_token or not decoded_token.get("id"):
                    return {
                        "error": "Invalid JWT token",
                        "message": "Token decoding failed",
                    }
                user = decoded_token.get("id")
            except ValueError as e:
                return {"error": "Invalid JWT token", "message": str(e)}
            cache_key = f"cart:{user}"
            cart_items = await redis.get(cache_key, compressed=True)
            if cart_items:
                return cart_items
            async with WooCommerceUtils(
                CONSUMER_KEY, CONSUMER_SECRET, BASE_URL
            ) as woocommerce:
                data = await woocommerce.get_user_cart(jwt_token)
                if data and data.get("items"):
                    await redis.set(
                        cache_key, data.get("items", []), ttl=300, compress=True
                    )
                    await redis.set(
                        f"cart_token:{user}",
                        data.get("cart_token"),
                        ttl=3600,
                        compress=True,
                    )
                return data.get("items", [])
        except Exception as e:
            logger.error(f"CartService: Error getting cart - {str(e)}")

    @staticmethod
    async def add_to_cart(
        jwt_token: str, product_id: int, quantity: int, redis: AsyncRedisCache
    ):
        try:
            try:
                decoded_token = AuthService.decode_jwt_token(
                    jwt_token.replace("Bearer ", "")
                )
                if not decoded_token or not decoded_token.get("id"):
                    return {
                        "error": "Invalid JWT token",
                        "message": "Token decoding failed",
                    }
                user = decoded_token.get("id")
            except ValueError as e:
                return {"error": "Invalid JWT token", "message": str(e)}
            cache_key = f"cart_token:{user}"
            cart_token = await redis.get(cache_key, compressed=True)
            if not cart_token:
                for _ in range(3):
                    await CartService.get_cart(jwt_token, redis)
                    cart_token = await redis.get(cache_key, compressed=True)
                    if cart_token:
                        break
                else:
                    return {
                        "error": "Cart token not found",
                        "message": "Please log in again",
                    }
            async with WooCommerceUtils(
                CONSUMER_KEY, CONSUMER_SECRET, BASE_URL
            ) as woocommerce:
                for _ in range(3):
                    data = await woocommerce.add_item_to_cart(
                        cart_token, product_id, quantity, jwt_token
                    )
                    if data.get("status") in [200, 201, 409]:
                        await redis.delete(f"cart:{user}")
                        break
                    await asyncio.sleep(1)
                return data
        except Exception as e:
            logger.error(f"CartService: Error getting cart - {str(e)}")

    @staticmethod
    async def update_item_in_cart(
        jwt_token: str, product_key: str, quantity: int, redis: AsyncRedisCache
    ):
        try:
            try:
                decoded_token = AuthService.decode_jwt_token(
                    jwt_token.replace("Bearer ", "")
                )
                if not decoded_token or not decoded_token.get("id"):
                    return {
                        "error": "Invalid JWT token",
                        "message": "Token decoding failed",
                    }
                user = decoded_token.get("id")
            except ValueError as e:
                return {"error": "Invalid JWT token", "message": str(e)}
            cache_key = f"cart_token:{user}"
            cart_token = await redis.get(cache_key, compressed=True)
            if not cart_token:
                for _ in range(3):
                    await CartService.get_cart(jwt_token, redis)
                    cart_token = await redis.get(cache_key, compressed=True)
                    if cart_token:
                        break
                else:
                    return {
                        "error": "Cart token not found",
                        "message": "Please log in again",
                    }
            async with WooCommerceUtils(
                CONSUMER_KEY, CONSUMER_SECRET, BASE_URL
            ) as woocommerce:
                for _ in range(3):
                    data = await woocommerce.update_item_in_cart(
                        cart_token, product_key, quantity, jwt_token
                    )
                    if data.get("status") in [200, 201, 409]:
                        await redis.delete(f"cart:{user}")
                        break
                    await asyncio.sleep(1)
                return data
        except Exception as e:
            logger.error(f"CartService: Error getting cart - {str(e)}")

    @staticmethod
    async def remove_from_cart(
        jwt_token: str, product_key: str, redis: AsyncRedisCache
    ):
        try:
            try:
                decoded_token = AuthService.decode_jwt_token(
                    jwt_token.replace("Bearer ", "")
                )
                if not decoded_token or not decoded_token.get("id"):
                    return {
                        "error": "Invalid JWT token",
                        "message": "Token decoding failed",
                    }
                user = decoded_token.get("id")
            except ValueError as e:
                return {"error": "Invalid JWT token", "message": str(e)}
            cache_key = f"cart_token:{user}"
            cart_token = await redis.get(cache_key, compressed=True)
            if not cart_token:
                for _ in range(3):
                    await CartService.get_cart(jwt_token, redis)
                    cart_token = await redis.get(cache_key, compressed=True)
                    if cart_token:
                        break
                else:
                    return {
                        "error": "Cart token not found",
                        "message": "Please log in again",
                    }
            async with WooCommerceUtils(
                CONSUMER_KEY, CONSUMER_SECRET, BASE_URL
            ) as woocommerce:
                for _ in range(3):
                    data = await woocommerce.delete_item_from_cart(
                        cart_token, product_key, jwt_token
                    )
                    if data.get("status") in [200, 201, 409]:
                        await redis.delete(f"cart:{user}")
                        break
                    await asyncio.sleep(1)
                return data
        except Exception as e:
            logger.error(f"CartService: Error getting cart - {str(e)}")
