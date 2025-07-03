from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.base_service.chat_service import BaseChatService
from src.db.orm_service.models.chat import Chat


class OrmChatService(BaseChatService):
    """Реализация сервиса работы c чатами через SQLAlchemy ORM."""

    async def register_chat(self, chat_id: int, dependency: AsyncSession) -> None:
        """Регистрирует чат c заданным идентификатором.

        :param chat_id: Идентификатор Telegram-чата.
        :param dependency: Сессия SQLAlchemy для выполнения операций c БД.
        :raises ValueError: Если chat_id отрицательный.
        :return: None.
        """
        if chat_id < 0:
            raise ValueError(f"Некорректный идентификатор чата: {chat_id}. Должен быть >= 0.")

        chat = await dependency.get(Chat, chat_id)
        if not chat:
            chat = Chat(id=chat_id)
            dependency.add(chat)

        await dependency.commit()

    async def delete_chat(self, chat_id: int, dependency: AsyncSession) -> None:
        """Удаляет чат и связанные c ним данные.

        :param chat_id: Идентификатор Telegram-чата.
        :param dependency: Сессия SQLAlchemy для выполнения операций c БД.
        :raises ValueError: Если chat_id отрицательный.
        :raises KeyError: Если чат c указанным идентификатором не найден.
        :raises RuntimeError: Если произошла ошибка при удалении чата.
        :return: None.
        """
        if chat_id < 0:
            raise ValueError(f"Некорректный идентификатор чата: {chat_id}. Должен быть >= 0.")

        chat = await dependency.get(Chat, chat_id)
        if not chat:
            raise KeyError(f"Чат с идентификатором {chat_id} не найден.")

        await dependency.delete(chat)
        await dependency.commit()

    async def get_chats(self, dependency: AsyncSession, limit: int, offset: int = 0) -> list[int]:
        """Возвращает список идентификаторов зарегистрированных чатов.

        :param dependency: Сессия SQLAlchemy для выполнения операций c БД.
        :param limit: Максимальное количество чатов в результате.
        :param offset: Количество чатов, которые нужно пропустить (по умолчанию 0).
        :return: Список идентификаторов чатов.
        """
        chats = await dependency.execute(
            select(Chat.id).order_by(Chat.id).limit(limit).offset(offset),
        )
        return list(chats.scalars())
