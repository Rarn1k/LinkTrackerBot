from datetime import datetime, timezone

import asyncpg

from src.api.scrapper_api.models import AddLinkRequest, LinkResponse, RemoveLinkRequest
from src.db.base_service.link_service import BaseLinkService


class SqlLinkService(BaseLinkService):
    """Реализация сервиса работы c подписками через чистый SQL c использованием asyncpg.

    Методы:
        add_link: Добавляет новую подписку для заданного чата.
        remove_link: Удаляет подписку для заданного чата.
        get_links: Возвращает список всех подписок для чата.
        set_last_updated: Обновляет дату последнего обновления подписки.
    """

    async def add_link(
        self,
        chat_id: int,
        add_req: AddLinkRequest,
        dependency: asyncpg.Pool,
    ) -> LinkResponse:
        """Добавляет новую подписку для заданного чата.

        :param chat_id: Идентификатор Telegram-чата.
        :param add_req: Объект запроса для добавления ссылки (URL, теги, фильтры).
        :param dependency: Пул соединений asyncpg.
        :return: Объект LinkResponse c данными добавленной подписки.
        :raises KeyError: Если чат c данным chat_id не найден.
        :raises ValueError: Если подписка c данным URL уже существует.
        """
        async with dependency.acquire() as conn:
            chat_exists = await conn.fetchval("SELECT 1 FROM chats WHERE id = $1", chat_id)
            if not chat_exists:
                raise KeyError(f"Чат с идентификатором {chat_id} не найден.")

            existing = await conn.fetchval(
                "SELECT id FROM links WHERE chat_id = $1 AND url = $2",
                chat_id,
                str(add_req.link),
            )
            if existing:
                raise ValueError("Ссылка уже отслеживается.")

            row = await conn.fetchrow(
                """
                INSERT INTO links (chat_id, url, tags, filters, last_updated)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, url, tags, filters, last_updated
                """,
                chat_id,
                str(add_req.link),
                add_req.tags,
                add_req.filters,
                datetime.now(timezone.utc),
            )
        return LinkResponse(
            id=row["id"],
            url=row["url"],
            tags=row["tags"],
            filters=row["filters"],
            last_updated=row["last_updated"],
        )

    async def remove_link(
        self,
        chat_id: int,
        remove_req: RemoveLinkRequest,
        dependency: asyncpg.Pool,
    ) -> LinkResponse:
        """Удаляет подписку для заданного чата.

        :param chat_id: Идентификатор Telegram-чата.
        :param remove_req: Объект запроса для удаления ссылки (URL).
        :param dependency: Пул соединений asyncpg.
        :return: Объект LinkResponse c данными удалённой подписки.
        :raises KeyError: Если чат не найден или подписка отсутствует.
        """
        async with dependency.acquire() as conn:
            chat_exists = await conn.fetchval("SELECT 1 FROM chats WHERE id = $1", chat_id)
            if not chat_exists:
                raise KeyError(f"Чат с идентификатором {chat_id} не найден.")

            row = await conn.fetchrow(
                """
                DELETE FROM links
                WHERE chat_id = $1 AND url = $2
                RETURNING id, url, tags, filters, last_updated
                """,
                chat_id,
                str(remove_req.link),
            )

            if not row:
                raise KeyError(f"Ссылка {remove_req.link} не найдена.")

        return LinkResponse(
            id=row["id"],
            url=row["url"],
            tags=row["tags"],
            filters=row["filters"],
            last_updated=row["last_updated"],
        )

    async def get_links(self, chat_id: int, dependency: asyncpg.Pool) -> list[LinkResponse]:
        """Возвращает список всех подписок для заданного чата.

        :param chat_id: Идентификатор Telegram-чата.
        :param dependency: Пул соединений asyncpg.
        :return: Список объектов LinkResponse.
        :raises ValueError: Если chat_id меньше 0.
        """
        if chat_id < 0:
            raise ValueError(f"Некорректный идентификатор чата: {chat_id}. Должен быть >= 0.")

        async with dependency.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, url, tags, filters, last_updated FROM links WHERE chat_id = $1",
                chat_id,
            )

        return [
            LinkResponse(
                id=row["id"],
                url=row["url"],
                tags=row["tags"],
                filters=row["filters"],
                last_updated=row["last_updated"],
            )
            for row in rows
        ]

    async def set_last_updated(
        self,
        link_id: int,
        last_updated: datetime,
        dependency: asyncpg.Pool,
    ) -> None:
        """Обновляет дату последнего изменения для подписки.

        :param link_id: Идентификатор подписки.
        :param last_updated: Новая дата последнего обновления.
        :param dependency: Пул соединений asyncpg.
        :raises KeyError: Если подписка не найдена.
        """
        async with dependency.acquire() as conn:
            result = await conn.execute(
                "UPDATE links SET last_updated = $1 WHERE id = $2",
                last_updated,
                link_id,
            )
            updated_rows = int(result.split()[-1])
            if updated_rows == 0:
                raise KeyError(f"Подписка с идентификатором {link_id} не найдена.")
