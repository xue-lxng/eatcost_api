import hashlib
from typing import Dict, Any, List

import aiohttp

from config import logger


class TBankUtils:
    def __init__(self, terminal_id: str, password: str):
        self.terminal_id = terminal_id
        self.password = password
        self.base_url = "https://securepay.tinkoff.ru"
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures session is closed."""
        if self.session:
            await self.session.close()
        return False

    def __del__(self):
        """Fallback cleanup if context manager is not used."""
        if self.session and not self.session.closed:
            import asyncio

            try:
                asyncio.run(self.session.close())
            except RuntimeError:
                pass

    @staticmethod
    def generate_token(params: Dict[str, Any], password: str) -> str:
        filtered = {k: v for k, v in params.items() if not isinstance(v, (dict, list))}
        filtered["Password"] = password
        concatenated = "".join(str(filtered[key]) for key in sorted(filtered))
        return hashlib.sha256(concatenated.encode("utf-8")).hexdigest()

    async def add_card_to_user(self, user_id: str) -> Dict[str, str]:
        """
        Метод инициирует привязку карты к покупателю.

        :param user_id:
        :return: Возвращает ссылку на привязку карты
        """
        params = {
            "TerminalKey": self.terminal_id,
            "CustomerKey": user_id,
            "CheckType": "NO",
        }
        token = self.generate_token(params, self.password)
        params["Token"] = token
        async with self.session.post(
            f"{self.base_url}/v2/AddCard",
            json=params,
        ) as response:
            response.raise_for_status()
            result = await response.json()
            return {"link": result["PaymentURL"]}

    async def remove_card_from_user(self, user_id: str, card_id: str) -> Dict[str, str]:
        params = {
            "TerminalKey": self.terminal_id,
            "CustomerKey": user_id,
            "CardID": card_id,
            "CheckType": "NO",
        }
        token = self.generate_token(params, self.password)
        params["Token"] = token
        async with self.session.post(
            f"{self.base_url}/v2/RemoveCard",
            json=params,
        ) as response:
            response.raise_for_status()
            result = await response.json()
            return {"success": result["Success"], "details": result["Details"]}

    @staticmethod
    def aggregate_cards(cards: list[dict]) -> list[dict]:
        return [
            {"CardId": card["CardId"], "Pan": card["Pan"], "ExpDate": card["ExpDate"]}
            for card in cards
            if card["Status"] == "A"
        ]

    async def get_user_cards(self, user_id: str) -> List[Dict[str, str]]:
        params = {
            "TerminalKey": self.terminal_id,
            "CustomerKey": str(user_id),
        }
        token = self.generate_token(params, self.password)
        params["Token"] = token
        async with self.session.post(
            f"{self.base_url}/v2/GetCardList",
            json=params,
        ) as response:
            response.raise_for_status()
            result = await response.json()
            logger.info(f"Cards retrieved: {result}")
            return self.aggregate_cards(
                result
            )  # Assuming the response contains a list of cards

    async def create_customer(self, user_id: int):
        params = {
            "TerminalKey": self.terminal_id,
            "CustomerKey": str(user_id),
        }
        token = self.generate_token(params, self.password)
        params["Token"] = token
        async with self.session.post(
            f"{self.base_url}/v2/AddCustomer",
            json=params,
        ) as response:
            logger.info(f"Params: {params}")
            response.raise_for_status()
            result = await response.json()
            logger.info(f"Customer created: {result}")
            return {
                "customer_id": result["CustomerKey"]
            }  # Assuming the response contains a customer ID

    async def create_subscription(
        self, user_id: int, order_id: str, amount: float
    ) -> str:
        params = {
            "TerminalKey": self.terminal_id,
            "CustomerKey": str(user_id),
            "OrderId": order_id,
            "Amount": int(amount * 100),
            "Recurrent": "Y",
            "NotificationURL": "https://eatcost.ru/api/v1/callbacks",
        }
        token = self.generate_token(params, self.password)
        params["Token"] = token
        async with self.session.post(
            f"{self.base_url}/v2/Init",
            json=params,
        ) as response:
            response.raise_for_status()
            result = await response.json()
            logger.info(f"Subscription created: {result}")
            return result["PaymentURL"]

    async def create_checkout(self, user_id: int, order_id: str, amount: float) -> str:
        params = {
            "TerminalKey": self.terminal_id,
            "CustomerKey": str(user_id),
            "OrderId": order_id,
            "Amount": int(amount * 100),
            "NotificationURL": "https://eatcost.ru/api/v1/callbacks",
        }
        token = self.generate_token(params, self.password)
        params["Token"] = token
        logger.info(f"{params=}")
        async with self.session.post(
            f"{self.base_url}/v2/Init",
            json=params,
        ) as response:
            response.raise_for_status()
            result = await response.json()
            return result["PaymentURL"]

    async def check_order_status(self, order_id: str) -> Dict[str, str]:
        params = {
            "TerminalKey": self.terminal_id,
            "OrderId": order_id,
        }
        token = self.generate_token(params, self.password)
        params["Token"] = token
        async with self.session.post(
            f"{self.base_url}/v2/CheckOrder",
            json=params,
        ) as response:
            response.raise_for_status()
            result = await response.json()
            return result
