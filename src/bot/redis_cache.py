import json
from typing import Any

import redis.asyncio as redis

from src.settings import settings


class RedisCache:
    """Кэш для хранения и управления списками в Redis.

    Предоставляет асинхронные методы для подключения, получения, установки и инвалидирования
    кэша по chat_id.
    """

    def __init__(self, url: str) -> None:
        """:param url: URL подключения к Redis."""
        self._url = url
        self._redis: Any | None = None

    async def connect(self) -> None:
        """Асинхронно подключается к Redis, если соединение ещё не установлено."""
        if self._redis is None:
            self._redis = await redis.from_url(
                self._url,
                encoding="utf-8",
                decode_responses=True,
            )  # type: ignore

    async def get_list_cache(self, chat_id: int) -> list[Any] | None:
        """Получает закэшированный список для заданного chat_id.

        :param chat_id: Идентификатор чата.
        :return: Данные из кэша (list) или None, если кэш отсутствует.
        """
        await self.connect()
        key = settings.redis.list_key.format(chat_id=chat_id)
        if self._redis is None:
            return None
        data = await self._redis.get(key)
        if data:
            result = json.loads(data)
            if isinstance(result, list):
                return result
            return None
        return None

    async def set_list_cache(self, chat_id: int, value: list[Any], expire: int = 300) -> None:
        """Сохраняет список в кэш для заданного chat_id c истечением срока действия.

        :param chat_id: Идентификатор чата.
        :param value: Данные для кэширования (list).
        :param expire: Время жизни кэша в секундах (по умолчанию 300).
        :return: None
        """
        await self.connect()
        key = settings.redis.list_key.format(chat_id=chat_id)
        if self._redis is not None:
            await self._redis.set(key, json.dumps(value), ex=expire)

    async def invalidate_list_cache(self, chat_id: int) -> None:
        """Удаляет кэшированный список для заданного chat_id.

        :param chat_id: Идентификатор чата.
        :return: None
        """
        await self.connect()
        key = settings.redis.list_key.format(chat_id=chat_id)
        if self._redis is not None:
            await self._redis.delete(key)


redis_cache = RedisCache(settings.redis.url)
