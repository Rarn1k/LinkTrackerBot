import asyncpg

from src.db.base_service.chat_service import BaseChatService


class SqlChatService(BaseChatService):
    """Реализация сервиса работы c чатами через чистый SQL c использованием asyncpg.

    Методы:
        register_chat: Регистрирует новый чат.
        delete_chat: Удаляет чат по идентификатору.
        get_chats: Возвращает список идентификаторов чатов c пагинацией.
    """

    async def register_chat(self, chat_id: int, dependency: asyncpg.Pool) -> None:
        """Регистрирует новый чат в базе данных.

        :param chat_id: Идентификатор Telegram-чата.
        :param dependency: Пул соединений asyncpg.
        :return: None.
        """
        async with dependency.acquire() as connection:
            await connection.fetchrow(
                """
                INSERT INTO chats (id)
                VALUES ($1)
                ON CONFLICT (id) DO NOTHING
                """,
                chat_id,
            )

    async def delete_chat(self, chat_id: int, dependency: asyncpg.Pool) -> None:
        """Удаляет чат из базы данных по идентификатору чата.

        :param chat_id: Идентификатор Telegram-чата.
        :param dependency: Пул соединений asyncpg.
        :return: None.
        """
        async with dependency.acquire() as connection:
            await connection.execute("DELETE FROM chats WHERE id = $1", chat_id)

    async def get_chats(
        self,
        dependency: asyncpg.Pool,
        limit: int,
        offset: int = 0,
    ) -> list[int]:
        """Возвращает список идентификаторов чатов c постраничной выборкой.

        :param dependency: Пул соединений asyncpg.
        :param limit: Максимальное количество чатов для выборки.
        :param offset: Смещение при выборке (по умолчанию 0).
        :return: Список идентификаторов чатов.
        """
        async with dependency.acquire() as connection:
            rows = await connection.fetch(
                "SELECT id FROM chats ORDER BY id LIMIT $1 OFFSET $2",
                limit,
                offset,
            )
        return [row["id"] for row in rows]
