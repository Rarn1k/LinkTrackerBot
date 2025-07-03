from abc import ABC, abstractmethod
from datetime import datetime

import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.scrapper_api.models import AddLinkRequest, LinkResponse, RemoveLinkRequest


class BaseLinkService(ABC):
    """Абстрактный базовый класс для работы c подписками."""

    @abstractmethod
    async def add_link(
        self,
        chat_id: int,
        add_req: AddLinkRequest,
        dependency: AsyncSession | asyncpg.Pool,
    ) -> LinkResponse:
        """Добавляет подписку для указанного чата.

        :param chat_id: Идентификатор Telegram-чата.
        :param add_req: Объект запроса на добавление подписки.
        :param dependency: Зависимость для работы c базой данных (Pool или AsyncSession).
        :return: Объект LinkResponse c данными добавленной подписки.
        """

    @abstractmethod
    async def remove_link(
        self,
        chat_id: int,
        remove_req: RemoveLinkRequest,
        dependency: AsyncSession | asyncpg.Pool,
    ) -> LinkResponse:
        """Удаляет подписку для указанного чата по URL.

        :param chat_id: Идентификатор Telegram-чата.
        :param remove_req: Объект запроса для удаления ссылки (URL).
        :param dependency: Зависимость для работы c базой данных (Pool или AsyncSession).
        :return: Объект LinkResponse c данными удаленной подписки.
        """

    @abstractmethod
    async def get_links(
        self,
        chat_id: int,
        dependency: AsyncSession | asyncpg.Pool,
    ) -> list[LinkResponse]:
        """Возвращает список подписок для указанного чата.

        :param chat_id: Идентификатор Telegram-чата.
        :param dependency: Зависимость для работы c базой данных (Pool или AsyncSession).
        :return: Список подписок в формате LinkResponse.
        """

    @abstractmethod
    async def set_last_updated(
        self,
        link_id: int,
        last_updated: datetime,
        dependency: AsyncSession | asyncpg.Pool,
    ) -> None:
        """Обновляет дату последнего обновления подписки.

        :param link_id: Уникальный идентификатор подписки.
        :param last_updated: Новая дата последнего обновления.
        :param dependency: Зависимость для работы c базой данных (Pool или AsyncSession).
        :return: None.
        """
