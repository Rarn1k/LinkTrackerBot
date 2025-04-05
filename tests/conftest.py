import asyncio
from collections.abc import Generator
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, Mock

import asyncpg
import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from telethon import TelegramClient
from telethon.events import NewMessage
from testcontainers.postgres import PostgresContainer

from src.api import router
from src.db.orm_service.models.base import Base
from src.server import default_lifespan


@pytest.fixture
def mock_event() -> Mock:
    event = Mock(spec=NewMessage.Event)
    event.input_chat = "test_chat"
    event.chat_id = 123456789
    event.message = Mock()
    event.sender_id = 123
    event.respond = AsyncMock()
    event.client = MagicMock(spec=TelegramClient)
    return event


@pytest.fixture
def mock_httpx_client(mocker: MockerFixture) -> AsyncMock:
    client = AsyncMock()
    mocker.patch("httpx.AsyncClient", return_value=client)
    client.__aenter__.return_value = client
    client.__aexit__ = AsyncMock(return_value=None)
    return client


@pytest.fixture
def mock_memory_storage(mocker: MockerFixture) -> Mock:
    storage = Mock()
    storage.get_state = mocker.AsyncMock(return_value=None)
    storage.set_state = mocker.AsyncMock()
    storage.get_data = mocker.AsyncMock(return_value={})
    storage.set_data = mocker.AsyncMock()
    storage.clear = mocker.AsyncMock()
    return storage


@pytest.fixture(scope="session")
def fast_api_application() -> FastAPI:
    app = FastAPI(
        title="telegram_bot_app",
        lifespan=default_lifespan,
    )
    app.include_router(router=router, prefix="/api/v1")
    return app


@pytest.fixture(scope="session")
def test_client(fast_api_application: FastAPI) -> Generator[TestClient, None, None]:
    with TestClient(
        fast_api_application,
        backend_options={"loop_factory": asyncio.new_event_loop},
    ) as test_client:
        yield test_client


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[dict[str, AsyncSession | asyncpg.Pool], None]:
    with PostgresContainer("postgres:15", driver="asyncpg") as postgres:
        db_url = postgres.get_connection_url()
        engine = create_async_engine(db_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        sql_url = db_url.replace(
            "postgresql+asyncpg://",
            "postgresql://",
        )
        pg_pool = await asyncpg.create_pool(dsn=sql_url)

        yield {
            "sa_session_factory": session_factory,
            "pg_pool": pg_pool,
        }

        await pg_pool.close()
        await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_db: dict[str, Any]) -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для создания сессии для каждого теста."""
    async with test_db["sa_session_factory"]() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def db_pool(test_db: dict[str, Any]) -> asyncpg.Pool:
    """Фикстура для создания сессии для каждого теста."""
    return test_db["pg_pool"]
