import asyncpg
import pytest

from src.db.sql_service.chat_service import SqlChatService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def chat_service() -> SqlChatService:
    """Фикстура для создания экземпляра SqlChatService."""
    return SqlChatService()


async def test_register_chat_success(
    chat_service: SqlChatService,
    db_pool: asyncpg.Pool,
) -> None:
    """Проверяет успешную регистрацию нового чата."""
    chat_id = 123

    await chat_service.register_chat(chat_id, db_pool)

    async with db_pool.acquire() as conn:
        result = await conn.fetchval("SELECT id FROM chats WHERE id = $1", chat_id)
    assert result == chat_id


async def test_register_chat_existing(
    chat_service: SqlChatService,
    db_pool: asyncpg.Pool,
) -> None:
    """Проверяет, что повторная регистрация существующего чата не создаёт дубликат."""
    chat_id = 123

    await chat_service.register_chat(chat_id, db_pool)
    await chat_service.register_chat(chat_id, db_pool)

    async with db_pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM chats WHERE id = $1", chat_id)
    assert count == 1


async def test_delete_chat_success(
    chat_service: SqlChatService,
    db_pool: asyncpg.Pool,
) -> None:
    """Проверяет успешное удаление существующего чата."""
    chat_id = 123

    async with db_pool.acquire() as conn:
        await conn.execute("INSERT INTO chats (id) VALUES ($1)", chat_id)

    await chat_service.delete_chat(chat_id, db_pool)

    async with db_pool.acquire() as conn:
        result = await conn.fetchval("SELECT id FROM chats WHERE id = $1", chat_id)
    assert result is None


async def test_delete_chat_not_found(
    chat_service: SqlChatService,
    db_pool: asyncpg.Pool,
) -> None:
    """Проверяет удаление несуществующего чата (без ошибки)."""
    chat_id = 123

    await chat_service.delete_chat(chat_id, db_pool)

    async with db_pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM chats")
    assert count == 0


async def test_get_chats_success(
    chat_service: SqlChatService,
    db_pool: asyncpg.Pool,
) -> None:
    chat_ids = [1, 2, 3, 4, 5]

    async with db_pool.acquire() as conn:
        for chat_id in chat_ids:
            await conn.execute("INSERT INTO chats (id) VALUES ($1)", chat_id)

    result = await chat_service.get_chats(db_pool, limit=2, offset=1)
    assert result == [2, 3]


async def test_get_chats_empty(
    chat_service: SqlChatService,
    db_pool: asyncpg.Pool,
) -> None:
    """Проверяет получение пустого списка, если чатов нет."""
    result = await chat_service.get_chats(db_pool, limit=10, offset=0)
    assert result == []


async def test_get_chats_pagination(
    chat_service: SqlChatService,
    db_pool: asyncpg.Pool,
) -> None:
    """Проверяет пагинацию при получении чатов."""
    chat_ids = [1, 2, 3, 4, 5]

    async with db_pool.acquire() as conn:
        for chat_id in chat_ids:
            await conn.execute("INSERT INTO chats (id) VALUES ($1)", chat_id)

    page1 = await chat_service.get_chats(db_pool, limit=2, offset=0)
    page2 = await chat_service.get_chats(db_pool, limit=2, offset=2)
    page3 = await chat_service.get_chats(db_pool, limit=2, offset=4)

    assert page1 == [1, 2]
    assert page2 == [3, 4]
    assert page3 == [5]
