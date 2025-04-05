from abc import ABC, abstractmethod

import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession


class BaseChatService(ABC):
    """Абстрактный базовый класс для работы c данными чатов."""

    @abstractmethod
    async def register_chat(self, chat_id: int, dependency: AsyncSession | asyncpg.Pool) -> None:
        """Регистрирует чат c заданным идентификатором.

        :param chat_id: Идентификатор Telegram-чата.
        :param dependency: Зависимость для работы c базой данных (Pool или AsyncSession).
        :return: None.
        """

    @abstractmethod
    async def delete_chat(self, chat_id: int, dependency: AsyncSession | asyncpg.Pool) -> None:
        """Удаляет чат и связанные c ним данные.

        :param chat_id: Идентификатор Telegram-чата.
        :param dependency: Зависимость для работы c базой данных (Pool или AsyncSession).
        :return: None.
        """

    @abstractmethod
    async def get_chats(
        self,
        dependency: AsyncSession | asyncpg.Pool,
        limit: int,
        offset: int,
    ) -> list[int]:
        """Возвращает список идентификаторов зарегистрированных чатов.

        :param dependency: Зависимость для работы c базой данных (Pool или AsyncSession).
        :param limit: Максимальное количество чатов в выдаче.
        :param offset: Смещение для пагинации.
        :return: Список идентификаторов чатов.
        """
