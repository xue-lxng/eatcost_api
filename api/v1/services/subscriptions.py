import asyncio

import aiohttp


async def send_subscription_data(user_id: int, rebill: int):
    async with aiohttp.ClientSession() as session:
        for _ in range(3):
            async with session.post(
                f"http://subscription_api:8000/api/v1/subscriptions/",
                json={
                    "user_id": user_id,
                    "rebill_id": rebill
                }
            ) as response:
                if response.status == 200:
                    return True
                await asyncio.sleep(1)

