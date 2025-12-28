from typing import Dict, Any, Optional
from logging import getLogger

import msgspec

from api.v1.response_models.users import UserWithMembershipResponse, UserQrResponse, UserMembershipResponse
from config import CONSUMER_KEY, BASE_URL, CONSUMER_SECRET
from core.utils.woocommerce import WooCommerceUtils

logger = getLogger(__name__)


class UsersService:
    @staticmethod
    async def get_user_by_id(user_id: int) -> UserWithMembershipResponse:
        """
        Retrieve user details by user ID.
        Args:
            user_id: User ID
        Returns:
            User details as a dictionary
        """
        try:
            async with WooCommerceUtils(consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET, base_url=BASE_URL) as woocommerce:
                user_data = await woocommerce.get_user_data(user_id=user_id)
                user_membership = await woocommerce.get_user_membership(user_id=user_id)
                user_data["membership"] = user_membership

                encoder = msgspec.json.Encoder()
                decoder = msgspec.json.Decoder(type=UserWithMembershipResponse)

                data_bytes = encoder.encode(user_data)
                result: UserWithMembershipResponse = decoder.decode(data_bytes)

                return result
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {str(e)}")
            raise Exception(f"Failed to get user: {str(e)}")

    @staticmethod
    async def get_user_qr(jwt_token: str) -> UserQrResponse:
        try:
            async with WooCommerceUtils(consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET, base_url=BASE_URL) as woocommerce:
                user_membership_qr = await woocommerce.get_user_membership_qr(jwt_token=jwt_token)
                encoder = msgspec.json.Encoder()
                decoder = msgspec.json.Decoder(type=UserQrResponse)

                data_bytes = encoder.encode(user_membership_qr)
                result: UserQrResponse = decoder.decode(data_bytes)
                return result
        except Exception as e:
            raise Exception(f"Failed to get user QR: {str(e)}")

    @staticmethod
    async def get_user_membership(user_id: int) -> UserMembershipResponse:
        """
        Get user membership details.
        Args:
            user_id: User ID
        Returns:
            Membership details
        """
        try:
            async with WooCommerceUtils(consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET, base_url=BASE_URL) as woocommerce:
                user_membership = await woocommerce.get_user_membership(user_id=user_id)
                encoder = msgspec.json.Encoder()
                decoder = msgspec.json.Decoder(type=UserMembershipResponse)

                data_bytes = encoder.encode(user_membership)
                result: UserMembershipResponse = decoder.decode(data_bytes)
                return result
        except Exception as e:
            logger.error(f"Error getting user membership {user_id}: {str(e)}")
            raise Exception(f"Failed to get user membership: {str(e)}")
