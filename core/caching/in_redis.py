import asyncio
import json
import zlib
from typing import Any, Optional, List

import msgpack
import redis.asyncio as redis
from redis.exceptions import RedisError

from config import logger


class AsyncRedisCache:
    """Универсальный асинхронный класс для кэширования в Redis с инвалидацией"""

    def __init__(self, redis_url: str):
        """
        Args:
            redis_url: URL подключения к Redis (например, redis://localhost:6379/0)
        """
        self.client = redis.from_url(redis_url)
        self.pubsub = None
        self._invalidation_callbacks = []
        self._listener_task = None

    async def get(self, key: str, compressed: bool = False) -> Optional[Any]:
        """
        Получить значение из кэша

        Args:
            key: Ключ Redis
            compressed: Флаг использования сжатия

        Returns:
            Десериализованные данные или None
        """
        try:
            data = await self.client.get(key)

            if not data:
                return None

            if compressed:
                result = await self._deserialize_data_async(data)
                return result

            try:
                result = json.loads(data)
                return result
            except json.JSONDecodeError as e:
                logger.error(f"AsyncRedisCache: JSON decode error for key {key}: {e}")
                return None

        except RedisError as e:
            logger.error(f"AsyncRedisCache: Redis error getting key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"AsyncRedisCache: Unexpected error getting key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        values: Any,
        ttl: int,
        compress: bool = False,
        tags: Optional[List[str]] = None,
    ):
        """
        Сохранить значение в кэш с TTL и опциональными тегами

        Args:
            key: Ключ Redis
            values: Данные для сохранения
            ttl: Время жизни в секундах
            compress: Использовать сжатие (msgpack + zlib)
            tags: Список тегов для группировки кэша (например, ["user:123", "profile"])
        """
        if compress:
            packed = msgpack.packb(values, use_bin_type=True)
            values = zlib.compress(packed)
        else:
            values = json.dumps(values)

        await self.client.setex(key, ttl, values)

        # Сохраняем связь ключа с тегами
        if tags:
            for tag in tags:
                tag_key = f"tag:{tag}"
                await self.client.sadd(tag_key, key)
                await self.client.expire(tag_key, ttl)

    async def delete(self, key: str) -> int:
        """
        Удалить ключ из кэша (простая инвалидация)

        Returns:
            Количество удаленных ключей
        """
        return await self.client.delete(key)

    async def invalidate_by_pattern(self, pattern: str) -> int:
        """
        Инвалидация по паттерну (например, "user:*")

        Args:
            pattern: Паттерн для поиска ключей (поддерживает * и ?)

        Returns:
            Количество удаленных ключей
        """
        keys = []
        async for key in self.client.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            return await self.client.delete(*keys)
        return 0

    async def invalidate_by_tag(self, tag: str) -> int:
        """
        Инвалидация всех ключей, связанных с тегом

        Args:
            tag: Тег для инвалидации (например, "user:123")

        Returns:
            Количество удаленных ключей
        """
        tag_key = f"tag:{tag}"
        keys = await self.client.smembers(tag_key)

        count = 0
        if keys:
            # Удаляем все ключи, связанные с тегом
            count = await self.client.delete(*keys)
            # Удаляем сам тег
            await self.client.delete(tag_key)

        return count

    async def invalidate_multiple_tags(self, tags: List[str]) -> int:
        """
        Инвалидация по нескольким тегам

        Args:
            tags: Список тегов для инвалидации

        Returns:
            Общее количество удаленных ключей
        """
        total_count = 0
        for tag in tags:
            count = await self.invalidate_by_tag(tag)
            total_count += count
        return total_count

    async def publish_invalidation(self, channel: str, message: str):
        """
        Опубликовать сообщение об инвалидации в pub/sub канал
        для распределенных систем

        Args:
            channel: Канал для публикации (например, "cache_invalidation")
            message: Сообщение (например, "invalidate:user:123")
        """
        await self.client.publish(channel, message)

    async def subscribe_invalidation(
        self, channel: str, callback: Optional[callable] = None
    ):
        """
        Подписаться на канал инвалидации кэша

        Args:
            channel: Канал для подписки
            callback: Функция обратного вызова для обработки сообщений
        """
        if self.pubsub is None:
            self.pubsub = self.client.pubsub()

        await self.pubsub.subscribe(channel)

        if callback:
            self._invalidation_callbacks.append(callback)

        # Запускаем listener в фоновой задаче
        if self._listener_task is None or self._listener_task.done():
            self._listener_task = asyncio.create_task(self._listen_invalidations())

    async def _listen_invalidations(self):
        """Слушает сообщения об инвалидации в фоновом режиме"""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    data = message["data"].decode("utf-8")

                    # Обрабатываем инвалидацию
                    await self._handle_invalidation_message(data)

                    # Вызываем пользовательские колбэки
                    for callback in self._invalidation_callbacks:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(data)
                        else:
                            callback(data)
        except asyncio.CancelledError:
            pass

    async def _handle_invalidation_message(self, message: str):
        """
        Обработка сообщения об инвалидации

        Формат сообщения:
        - "key:some_key" - удалить конкретный ключ
        - "pattern:user:*" - удалить по паттерну
        - "tag:user:123" - удалить по тегу
        """
        parts = message.split(":", 1)
        if len(parts) != 2:
            return

        invalidation_type, value = parts

        if invalidation_type == "key":
            await self.delete(value)
        elif invalidation_type == "pattern":
            await self.invalidate_by_pattern(value)
        elif invalidation_type == "tag":
            await self.invalidate_by_tag(value)

    async def exists(self, key: str) -> bool:
        """Проверить существование ключа"""
        return await self.client.exists(key) > 0

    async def get_ttl(self, key: str) -> int:
        """
        Получить оставшееся время жизни ключа в секундах

        Returns:
            -2: ключ не существует
            -1: ключ существует, но без TTL
            >0: оставшееся время в секундах
        """
        return await self.client.ttl(key)

    async def refresh_ttl(self, key: str, ttl: int) -> bool:
        """
        Обновить TTL существующего ключа без изменения данных

        Args:
            key: Ключ Redis
            ttl: Новое время жизни в секундах

        Returns:
            True если TTL обновлен, False если ключ не существует
        """
        return await self.client.expire(key, ttl)

    async def get_or_set(
        self,
        key: str,
        factory: callable,
        ttl: int,
        compress: bool = False,
        tags: Optional[List[str]] = None,
    ) -> Any:
        """
        Получить значение из кэша или создать его через factory функцию

        Args:
            key: Ключ Redis
            factory: Async функция для генерации данных при отсутствии в кэше
            ttl: Время жизни в секундах
            compress: Использовать сжатие
            tags: Теги для группировки

        Returns:
            Данные из кэша или созданные через factory
        """
        # Проверяем кэш
        cached = await self.get(key, compressed=compress)
        if cached is not None:
            return cached

        # Генерируем данные
        if asyncio.iscoroutinefunction(factory):
            data = await factory()
        else:
            data = factory()

        # Сохраняем в кэш
        await self.set(key, data, ttl, compress=compress, tags=tags)

        return data

    async def close(self):
        """Закрыть соединение с Redis"""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()

        await self.client.close()

    @staticmethod
    async def _deserialize_data_async(compressed_data: bytes) -> Any:
        """Асинхронная десериализация сжатых данных"""
        if compressed_data is None:
            return None

        loop = asyncio.get_running_loop()

        def _deserialize():
            try:
                serialized_data = zlib.decompress(compressed_data)
                data = msgpack.unpackb(serialized_data, raw=False)
                return data
            except (
                zlib.error,
                msgpack.ExtraData,
                msgpack.FormatError,
                msgpack.StackError,
            ) as e:
                print(f"Ошибка декодирования: {e}")
                return None

        return await loop.run_in_executor(None, _deserialize)

    async def build_word_autocomplete_index(
        self,
        index_key: str,
        suggestions: List[str],
        min_prefix_len: int = 2,
        normalize: bool = True,
        ttl: Optional[int] = None,
    ) -> int:
        """
        Индексация с префиксами и ссылками на полные названия [web:39][web:45]

        Формат ключа: "префикс*полное_название"
        Например для "пицца маргарита":
        - "пи*пицца маргарита"
        - "пиц*пицца маргарита"
        - "пицц*пицца маргарита"
        - "пицца*пицца маргарита"
        - "пицца *пицца маргарита"
        - "пицца м*пицца маргарита"
        - ...
        - "пицца маргарита*пицца маргарита"

        Args:
            index_key: Ключ sorted set
            suggestions: Список полных названий
            min_prefix_len: Минимальная длина префикса
            normalize: Нормализация
            ttl: TTL

        Returns:
            Количество добавленных записей
        """
        temp_key = f"{index_key}:temp:{int(asyncio.get_event_loop().time())}"

        try:
            entries = {}

            for suggestion in suggestions:
                if normalize:
                    suggestion = suggestion.lower().strip()

                # Генерируем все префиксы для этого названия
                for i in range(min_prefix_len, len(suggestion) + 1):
                    prefix = suggestion[:i]
                    # Формат: "префикс*полное_название"
                    key = f"{prefix}*{suggestion}"
                    entries[key] = 0.0

            if entries:
                await self.client.zadd(temp_key, entries)

            await self.client.rename(temp_key, index_key)

            if ttl:
                await self.client.expire(index_key, ttl)

            return len(entries)

        except Exception as e:
            await self.client.delete(temp_key)
            raise e

    async def search_with_word_completion(
        self, index_key: str, prefix: str, limit: int = 10, normalize: bool = True
    ) -> dict:
        """
        Поиск с извлечением полных названий из индекса [web:39]

        Args:
            index_key: Ключ индекса
            prefix: Введенный текст
            limit: Количество результатов
            normalize: Нормализация

        Returns:
            Результаты поиска с режимом (full/next_word)
        """
        if normalize:
            prefix = prefix.lower().strip()

        if not prefix or len(prefix) < 2:
            return {"mode": "full", "suggestions": [], "prefix": prefix}

        # Ищем записи вида "prefix*..."
        search_pattern = f"{prefix}*"

        results = await self.client.zrangebylex(
            index_key,
            min=f"[{search_pattern}",
            max=f"[{prefix}\xff",
            start=0,
            num=limit * 10,
        )

        # Извлекаем полные названия (после символа *)
        full_names = []
        seen = set()

        for result in results:
            if isinstance(result, bytes):
                result = result.decode()

            # Разделяем префикс и полное название
            if "*" in result:
                parts = result.split("*", 1)
                if len(parts) == 2:
                    full_name = parts[1]

                    # Добавляем только уникальные
                    if full_name not in seen:
                        full_names.append(full_name)
                        seen.add(full_name)

                    if len(full_names) >= limit * 2:
                        break

        if not full_names:
            return {"mode": "full", "suggestions": [], "prefix": prefix}

        # Определяем режим
        if prefix.endswith(" "):
            # Режим "следующее слово"
            prefix_clean = prefix.rstrip()
            prefix_words = prefix_clean.split()

            next_words_set = set()
            matching_names = []

            for name in full_names:
                name_words = name.split()

                # Проверяем совпадение начальных слов
                if len(name_words) > len(prefix_words):
                    if name_words[: len(prefix_words)] == prefix_words:
                        next_word = name_words[len(prefix_words)]
                        if next_word not in next_words_set:
                            next_words_set.add(next_word)
                            matching_names.append(name)

            next_words = sorted(list(next_words_set))[:limit]

            return {
                "mode": "next_word",
                "suggestions": matching_names[:limit],
                "next_words_only": next_words,
                "prefix": prefix_clean,
            }

        else:
            # Режим полных названий
            return {"mode": "full", "suggestions": full_names[:limit], "prefix": prefix}
