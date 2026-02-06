import asyncio
from typing import Dict, Any

from litestar import Router, Request, post
from litestar.exceptions import HTTPException

from api.v1.services.payments import PaymentService
from api.v1.services.users import logger
from config import TERMINAL_ID
from core.caching.in_redis import AsyncRedisCache


@post(
    "",
    tags=["Callbacks"],
    summary="Callbacks receiver",
    description="Callbacks receiver",
    status_code=200,
)
async def callback(
        request: Request, redis: AsyncRedisCache
) -> Dict[str, Any]:
    """Add a product to the cart."""
    data = await request.json()
    ip = request.client.host
    if TERMINAL_ID != data.get("TerminalKey"):
        logger.critical(f"Fake callback from {ip}")
        raise HTTPException(status_code=403, detail="Invalid TerminalKey")

    logger.info(f"Callback received from {ip} with data: {data}")

    order_id = data.get("OrderId")
    status = data.get("Status")
    success = data.get("Success")
    rebill_id = data.get("RebillId")

    if not success:
        logger.error(f"Failed order {order_id} with status {status}")
        raise HTTPException(status_code=200, detail="Failed order")

    if status == "AUTHORIZED":
        logger.info(f"Order {order_id} authorized")
        return {"status": "success"}

    asyncio.create_task(
        PaymentService.confirm_order_payment(
            order_id=order_id,
            callback_status=status,
            rebill_id=rebill_id,
        )
    )

    return {"status": "success"}


router = Router(
    path="/callbacks",
    route_handlers=[callback],
)
