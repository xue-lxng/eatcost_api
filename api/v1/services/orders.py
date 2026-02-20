from config import CONSUMER_SECRET, CONSUMER_KEY, BASE_URL
from core.utils.woocommerce import WooCommerceUtils


class OrderService:

    @staticmethod
    async def get_user_orders(
        user_id: int,
        status: str = "any",
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        async with WooCommerceUtils(CONSUMER_KEY, CONSUMER_SECRET, BASE_URL) as wc:
            orders = await wc.get_user_orders(
                user_id=user_id,
                status=status,
                page=page,
                per_page=per_page,
            )
        return {"orders": orders, "count": len(orders)}
