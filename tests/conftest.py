import asyncio
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from _pytest.monkeypatch import MonkeyPatch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from telethon import TelegramClient
from telethon.events import NewMessage

from src.api import router
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


@pytest.fixture(autouse=True)
def override_settings(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_API_ID", "123456")
    monkeypatch.setenv("BOT_API_HASH", "fakehash")
    monkeypatch.setenv("BOT_TOKEN", "faketoken")


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
