from config import TERMINAL_PASSWORD, TERMINAL_ID
from core.utils.tbank import TBankUtils


class CardsService:
    @staticmethod
    async def get_users_cards(self, user_id: int):
        async with TBankUtils(terminal_id=TERMINAL_ID, password=TERMINAL_PASSWORD) as tbank:
            return await tbank.get_user_cards(user_id=str(user_id))

    @staticmethod
    async def get_url_to_connect_new_card(self, user_id: int):
        async with TBankUtils(terminal_id=TERMINAL_ID, password=TERMINAL_PASSWORD) as tbank:
            return await tbank.add_card_to_user(user_id=str(user_id))

    @staticmethod
    async def remove_card_from_user(self, user_id: int, card_id: str):
        async with TBankUtils(terminal_id=TERMINAL_ID, password=TERMINAL_PASSWORD) as tbank:
            return await tbank.remove_card_from_user(user_id=str(user_id), card_id=card_id)

    @staticmethod
    async def create_customer(self, user_id: int):
        async with TBankUtils(terminal_id=TERMINAL_ID, password=TERMINAL_PASSWORD) as tbank:
            return await tbank.create_customer(user_id=str(user_id))
