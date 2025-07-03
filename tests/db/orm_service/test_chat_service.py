import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.orm_service.chat_service import OrmChatService
from src.db.orm_service.models.chat import Chat

pytestmark = pytest.mark.asyncio


@pytest.fixture
def chat_service() -> OrmChatService:
    """Фикстура для создания экземпляра OrmChatService."""
    return OrmChatService()


async def test_register_chat_success(
    chat_service: OrmChatService,
    db_session: AsyncSession,
) -> None:
    """Проверяет успешную регистрацию нового чата."""
    chat_id = 123
    await chat_service.register_chat(chat_id, db_session)

    chat = await db_session.get(Chat, chat_id)
    assert chat is not None
    assert chat.id == chat_id


async def test_register_chat_existing(
    chat_service: OrmChatService,
    db_session: AsyncSession,
) -> None:
    """Проверяет регистрацию уже существующего чата (без дублирования)."""
    chat_id = 123

    chat = Chat(id=chat_id)
    db_session.add(chat)
    await db_session.commit()

    await chat_service.register_chat(chat_id, db_session)

    result = await db_session.execute(select(Chat).where(Chat.id == chat_id))
    chats: list[Chat] = list(result.scalars())
    assert len(chats) == 1
    assert chats[0].id == chat_id


async def test_register_chat_negative_id(
    chat_service: OrmChatService,
    db_session: AsyncSession,
) -> None:
    """Проверяет выброс исключения при отрицательном chat_id."""
    chat_id = -1

    with pytest.raises(ValueError, match=f"Некорректный идентификатор чата: {chat_id}"):
        await chat_service.register_chat(chat_id, db_session)


async def test_delete_chat_success(
    chat_service: OrmChatService,
    db_session: AsyncSession,
) -> None:
    """Проверяет успешное удаление существующего чата."""
    chat_id = 123

    chat = Chat(id=chat_id)
    db_session.add(chat)
    await db_session.commit()

    await chat_service.delete_chat(chat_id, db_session)

    result = await db_session.get(Chat, chat_id)
    assert result is None


async def test_delete_chat_not_found(
    chat_service: OrmChatService,
    db_session: AsyncSession,
) -> None:
    """Проверяет выброс KeyError при удалении несуществующего чата."""
    chat_id = 123

    with pytest.raises(KeyError, match=f"Чат с идентификатором {chat_id} не найден"):
        await chat_service.delete_chat(chat_id, db_session)


async def test_delete_chat_negative_id(
    chat_service: OrmChatService,
    db_session: AsyncSession,
) -> None:
    """Проверяет выброс ValueError при отрицательном chat_id."""
    chat_id = -1

    with pytest.raises(ValueError, match=f"Некорректный идентификатор чата: {chat_id}"):
        await chat_service.delete_chat(chat_id, db_session)


async def test_get_chats_success(
    chat_service: OrmChatService,
    db_session: AsyncSession,
) -> None:
    """Проверяет успешное получение списка чатов c limit и offset."""
    chats = [Chat(id=i) for i in range(1, 4)]
    for chat in chats:
        db_session.add(chat)
    await db_session.commit()

    chat_ids = await chat_service.get_chats(db_session, limit=2, offset=1)
    assert chat_ids == [2, 3]


async def test_get_chats_empty(
    chat_service: OrmChatService,
    db_session: AsyncSession,
) -> None:
    """Проверяет получение пустого списка, если чатов нет."""
    chat_ids = await chat_service.get_chats(db_session, limit=10, offset=0)
    assert chat_ids == []


async def test_get_chats_pagination(
    chat_service: OrmChatService,
    db_session: AsyncSession,
) -> None:
    """Проверяет пагинацию при получении чатов."""
    chats = [Chat(id=i) for i in range(1, 6)]
    for chat in chats:
        db_session.add(chat)
    await db_session.commit()

    page1 = await chat_service.get_chats(db_session, limit=2, offset=0)
    page2 = await chat_service.get_chats(db_session, limit=2, offset=2)
    page3 = await chat_service.get_chats(db_session, limit=2, offset=4)

    assert page1 == [1, 2]
    assert page2 == [3, 4]
    assert page3 == [5]
