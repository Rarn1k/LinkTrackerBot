import asyncio
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
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
def mock_repository(mocker: MockerFixture) -> Mock:
    repo: Mock = mocker.Mock()
    repo.add_user = AsyncMock(return_value=True)
    repo.add_subscription = AsyncMock(return_value=True)
    repo.remove_subscription = AsyncMock()
    repo.get_subscriptions = AsyncMock(return_value=[])
    repo.is_user_have_url = AsyncMock(return_value=False)
    return repo


@pytest.fixture
def mock_memory_storage(mocker: MockerFixture) -> Mock:
    storage = mocker.Mock()
    storage.get_state = mocker.AsyncMock(return_value=None)
    storage.set_state = mocker.AsyncMock()
    storage.get_data = mocker.AsyncMock(return_value={})
    storage.set_data = mocker.AsyncMock()
    storage.clear = mocker.AsyncMock()
    return storage


@pytest.fixture
def mock_build_key(mocker: MockerFixture) -> Mock:
    build_key: Mock = mocker.Mock()
    return build_key


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
