from typing import Optional, Literal

from api.v1.response_models.payments import PaymentResponse
from api.v1.response_models.users import UserMembershipPurchaseResponse
from api.v1.services.subscriptions import send_subscription_data
from api.v1.services.users import logger
from config import (
    TERMINAL_ID,
    TERMINAL_PASSWORD,
    CONSUMER_KEY,
    CONSUMER_SECRET,
    BASE_URL,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
)
from core.utils.tbank import TBankUtils
from core.utils.woocommerce import WooCommerceUtils


class PaymentService:
    """Сервис для работы с платежами."""

    @staticmethod
    async def confirm_order_payment(
        order_id: int,
        callback_status: str,
        rebill_id: Optional[int] = None,
    ):
        """Подтверждает платеж на заказе."""
        try:
            async with TBankUtils(
                terminal_id=TERMINAL_ID,
                password=TERMINAL_PASSWORD,
            ) as tbank:
                status = await tbank.check_order_status(order_id)
                order_payments_data = status.get("Payments", [])
                if len(order_payments_data) < 1:
                    return False

                if callback_status != order_payments_data[0].get("Status"):
                    return False

                if not status.get("Success"):
                    return False

            async with WooCommerceUtils(
                consumer_key=CONSUMER_KEY,
                consumer_secret=CONSUMER_SECRET,
                base_url=BASE_URL,
            ) as wc:
                status_map = {"REFUNDED": "refunded", "CONFIRMED": "completed"}
                jwt_token = await wc.login_user(
                    email=ADMIN_EMAIL, password=ADMIN_PASSWORD
                )
                order_data = await wc.get_order_data(order_id)
                await wc.change_order_status(
                    order_id, status_map.get(callback_status), jwt_token.get("jwt")
                )

            if rebill_id:
                await send_subscription_data(
                    user_id=order_data.get("customer_id"), rebill=rebill_id
                )

        except Exception as e:
            logger.error(f"Error confirming order payment: {e}")
            return False

    @staticmethod
    async def confirm_subscription_payment(
        order_id: int,
        callback_status: str,
        rebill_id: Optional[int] = None,
    ):
        """Подтверждает платеж на заказе."""
        try:
            async with TBankUtils(
                terminal_id=TERMINAL_ID,
                password=TERMINAL_PASSWORD,
            ) as tbank:
                status = await tbank.check_order_status(order_id)
                order_payments_data = status.get("Payments", [])
                if len(order_payments_data) < 1:
                    return False

                if callback_status != order_payments_data[0].get("Status"):
                    return False

                if not status.get("Success"):
                    return False

            async with WooCommerceUtils(
                consumer_key=CONSUMER_KEY,
                consumer_secret=CONSUMER_SECRET,
                base_url=BASE_URL,
            ) as wc:
                status_map = {"REFUNDED": "refunded", "CONFIRMED": "completed"}
                jwt_token = await wc.login_user(
                    email=ADMIN_EMAIL, password=ADMIN_PASSWORD
                )
                order_data = await wc.get_order_data(order_id)
                await wc.change_order_status(
                    order_data.get("parent_id"), status_map.get(callback_status), jwt_token.get("jwt")
                )

            if rebill_id:
                await send_subscription_data(
                    user_id=order_data.get("customer_id"), rebill=rebill_id
                )

        except Exception as e:
            logger.error(f"Error confirming order payment: {e}")
            return False

    @staticmethod
    async def create_checkout(
        user_id: int, jwt_token: str, delivery_type: Literal["delivery", "pickup"]
    ) -> PaymentResponse:
        try:
            async with WooCommerceUtils(
                consumer_key=CONSUMER_KEY,
                consumer_secret=CONSUMER_SECRET,
                base_url=BASE_URL,
            ) as woocommerce:
                payment = await woocommerce.create_checkout(
                    jwt_token=jwt_token, user_id=user_id, delivery_type=delivery_type
                )
            amount = float(payment.get("data", {}).get("total"))
            order_id = payment.get("data", {}).get("id")
            async with TBankUtils(
                terminal_id=TERMINAL_ID,
                password=TERMINAL_PASSWORD,
            ) as tbank:
                payment_data = await tbank.create_checkout(
                    user_id=user_id,
                    order_id=order_id,
                    amount=amount,
                )
                return PaymentResponse(payment_url=payment_data)
        except Exception as e:
            logger.error(f"Failed to get payment link {user_id}: {str(e)}")
            raise Exception(f"Failed to get payment link: {str(e)}")

    @staticmethod
    async def get_user_membership_payment_url(
        user_id: int, jwt_token: str
    ) -> UserMembershipPurchaseResponse:
        try:
            async with WooCommerceUtils(
                consumer_key=CONSUMER_KEY,
                consumer_secret=CONSUMER_SECRET,
                base_url=BASE_URL,
            ) as woocommerce:
                user_membership_payment = await woocommerce.create_subscription(
                    jwt_token=jwt_token, user_id=user_id
                )
            amount = float(user_membership_payment.get("data", {}).get("total"))
            order_id = user_membership_payment.get("data", {}).get("id")
            async with TBankUtils(
                terminal_id=TERMINAL_ID,
                password=TERMINAL_PASSWORD,
            ) as tbank:
                payment_data = await tbank.create_subscription(
                    user_id=user_id,
                    order_id=order_id,
                    amount=amount,
                )
                return UserMembershipPurchaseResponse(payment_url=payment_data)

        except Exception as e:
            logger.error(
                f"Error creating user subscription payment URL {user_id}: {str(e)}"
            )
            raise Exception(f"Error creating user subscription payment URL: {str(e)}")
