from typing import List, Set

from config import logger
from core.caching.in_redis import AsyncRedisCache
from core.utils.address_utils import read_addresses_async


class AddressService:
    """Сервис для работы с адресами с поддержкой кэширования."""

    @staticmethod
    async def get_addresses(redis: AsyncRedisCache) -> List[str]:
        """
        Получает список всех адресов. Если кэш пуст, читает из файла.

        Returns:
            List[str]: Список всех адресов.
        """
        cache_key = "addresses"
        ttl = 3600
        try:
            cached = await redis.get(cache_key, compressed=True)
            if cached is None:
                addresses = await read_addresses_async()
                cached = addresses
                await redis.set(cache_key, addresses, ttl=ttl, compress=True)
            return cached
        except Exception as e:
            logger.error(f"Error fetching addresses: {e}")
            return []


    @staticmethod
    async def get_addresses_set(redis: AsyncRedisCache) -> Set[str]:
        """
        Получает множество адресов для быстрой проверки.
        Если кэш пуст, читает из файла и заполняет оба кэша.

        Returns:
            Set[str]: Множество адресов.
        """
        return set(await AddressService.get_addresses(redis))

    @staticmethod
    async def find_addresses_starting_with(prefix: str, redis: AsyncRedisCache, limit: int = 10) -> List[str]:
        """
        Находит адреса, начинающиеся с указанного префикса.

        Args:
            prefix: Префикс для поиска.
            redis: Экземпляр Redis кэша.
            limit: Максимальное количество результатов.

        Returns:
            List[str]: Список адресов, начинающихся с префикса.
        """
        try:
            if not prefix:
                return []

            addresses = await AddressService.get_addresses(redis)
            logger.debug(f"Found {len(addresses)} addresses total")

            # Ищем адреса, начинающиеся с префикса (без учёта регистра)
            prefix_lower = prefix.lower()
            matching_addresses = [
                addr for addr in addresses
                if prefix_lower in addr.lower()
            ]

            # Сортируем результаты и ограничиваем лимитом
            matching_addresses.sort()
            return matching_addresses[:limit]
        except Exception as e:
            logger.error(f"Error finding addresses starting with prefix '{prefix}': {e}")
            return []

    @staticmethod
    async def check_address_exists(address: str, redis: AsyncRedisCache) -> bool:
        """
        Проверяет, существует ли указанный адрес в списке.

        Args:
            address: Адрес для проверки.

        Returns:
            bool: True если адрес существует, False в противном случае.
        """
        addresses_set = await AddressService.get_addresses_set(redis)
        return address in addresses_set

    @staticmethod
    async def get_address_count(redis: AsyncRedisCache) -> int:
        """
        Получает общее количество адресов.

        Returns:
            int: Количество адресов.
        """
        addresses = await AddressService.get_addresses(redis)
        return len(addresses)
