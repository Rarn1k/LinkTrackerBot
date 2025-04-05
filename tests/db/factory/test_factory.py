from unittest.mock import patch

import asyncpg
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.factory.data_access_factory import get_data_access_service
from src.db.factory.data_access_service import DataAccessService
from src.db.factory.orm_factory import OrmDataAccessFactory
from src.db.factory.sql_factory import SqlDataAccessFactory
from src.db.orm_service.chat_service import OrmChatService
from src.db.orm_service.link_service import OrmLinkService
from src.db.orm_service.models.chat import Chat
from src.db.sql_service.chat_service import SqlChatService
from src.db.sql_service.link_service import SqlLinkService


def test_get_data_access_service_orm() -> None:
    """Проверяет, что для типа 'ORM' создаются ORM-сервисы."""
    with patch("src.db.factory.data_access_factory.settings.db.access_type", "ORM"):
        service = get_data_access_service("ORM")

    assert isinstance(service, DataAccessService)
    assert isinstance(service.chat_service, OrmChatService)
    assert isinstance(service.link_service, OrmLinkService)


def test_get_data_access_service_sql() -> None:
    """Проверяет, что для типа 'SQL' создаются SQL-сервисы."""
    with patch("src.db.factory.data_access_factory.settings.db.access_type", "SQL"):
        service = get_data_access_service("SQL")

    assert isinstance(service, DataAccessService)
    assert isinstance(service.chat_service, SqlChatService)
    assert isinstance(service.link_service, SqlLinkService)


def test_get_data_access_service_invalid_type() -> None:
    """Проверяет выброс ValueError при неизвестном типе доступа."""
    invalid_type = "INVALID"
    with pytest.raises(ValueError, match=f"Неизвестный тип доступа: {invalid_type}"):
        get_data_access_service(invalid_type)


@pytest.mark.asyncio
async def test_orm_data_access_service_usage(
    db_session: AsyncSession,
) -> None:
    """Проверяет работу ORM-реализации через DataAccessService."""
    with patch("src.db.factory.data_access_factory.settings.db.access_type", "ORM"):
        service = get_data_access_service("ORM")

    chat_id = 123
    await service.chat_service.register_chat(chat_id, db_session)

    chat = await db_session.get(Chat, chat_id)
    assert chat is not None
    assert chat.id == chat_id


@pytest.mark.asyncio
async def test_sql_data_access_service_usage(
    db_pool: asyncpg.Pool,
) -> None:
    """Проверяет работу SQL-реализации через DataAccessService."""
    with patch("src.db.factory.data_access_factory.settings.db.access_type", "SQL"):
        service = get_data_access_service("SQL")

    chat_id = 123
    await service.chat_service.register_chat(chat_id, db_pool)

    async with db_pool.acquire() as conn:
        result = await conn.fetchval("SELECT id FROM chats WHERE id = $1", chat_id)
    assert result == chat_id


def test_orm_factory_creates_correct_services() -> None:
    """Проверяет, что OrmDataAccessFactory создаёт правильные сервисы."""
    factory = OrmDataAccessFactory()

    chat_service = factory.create_chat_service()
    link_service = factory.create_link_service()

    assert isinstance(chat_service, OrmChatService)
    assert isinstance(link_service, OrmLinkService)


def test_sql_factory_creates_correct_services() -> None:
    """Проверяет, что SqlDataAccessFactory создаёт правильные сервисы."""
    factory = SqlDataAccessFactory()

    chat_service = factory.create_chat_service()
    link_service = factory.create_link_service()

    assert isinstance(chat_service, SqlChatService)
    assert isinstance(link_service, SqlLinkService)
