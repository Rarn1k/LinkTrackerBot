from collections import defaultdict
from datetime import datetime, timezone
from typing import Generator
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from pydantic import HttpUrl

from src.api.scrapper_api.models import LinkResponse
from src.clients.client_factory import ClientFactory
from src.scheduler import collect_updates, notify_bot, process_subscription
from src.settings import settings

pytestmark = pytest.mark.asyncio


@pytest.fixture
def updates_storage() -> dict[int, list[str]]:
    """Фикстура для создания хранилища обновлений."""
    return defaultdict(list)


@pytest.fixture
def mock_client_factory() -> Generator[Mock, None, None]:
    """Фикстура для мокирования ClientFactory."""
    with patch.object(ClientFactory, "create_client", new_callable=Mock) as mock_factory:
        yield mock_factory


@pytest.fixture
def sample_link_response() -> LinkResponse:
    """Фикстура c тестовыми данными подписки."""
    return LinkResponse(
        id=1,
        url=HttpUrl("https://github.com/user/repo"),
        tags=["tag1"],
        filters=["key1:value1"],
        last_updated=datetime.now(timezone.utc),
    )


async def test_notify_bot_success(
    updates_storage: dict[int, list[str]],
    mock_httpx_client: AsyncMock,
) -> None:
    """Проверяет успешную отправку уведомления в notify_bot."""
    chat_id = 123
    updates_storage[chat_id] = ["Обновление 1", "Обновление 2"]
    mock_response = Mock(spec=httpx.Response)
    mock_response.raise_for_status = Mock()
    mock_httpx_client.post.return_value = mock_response

    await notify_bot(chat_id, updates_storage)

    mock_httpx_client.post.assert_awaited_once_with(
        f"{settings.bot_api_url}/digest",
        json={
            "id": 1,
            "description": "Полученные обновления: ",
            "tg_chat_id": chat_id,
            "updates": ["Обновление 1", "Обновление 2"],
        },
    )


async def test_notify_bot_no_messages(
    updates_storage: dict[int, list[str]],
    mock_httpx_client: AsyncMock,
) -> None:
    """Проверяет, что при отсутствии обновлений запрос не отправляется."""
    chat_id = 123

    await notify_bot(chat_id, updates_storage)

    mock_httpx_client.assert_not_awaited()


async def test_notify_bot_only_for_subscribed_users(
    updates_storage: dict[int, list[str]],
    mock_httpx_client: AsyncMock,
) -> None:
    """Проверяет, что уведомления отправляются только пользователям, подписанным на ссылки."""
    updates_storage[123] = ["Обновление 1"]
    updates_storage[456] = []
    updates_storage[789] = ["Обновление 2", "Обновление 3"]
    mock_response = Mock(spec=httpx.Response)
    mock_response.raise_for_status = Mock()
    mock_httpx_client.post.return_value = mock_response

    await notify_bot(123, updates_storage)
    await notify_bot(456, updates_storage)
    await notify_bot(789, updates_storage)

    mock_httpx_client.post.assert_any_await(
        f"{settings.bot_api_url}/digest",
        json={
            "id": 1,
            "description": "Полученные обновления: ",
            "tg_chat_id": 123,
            "updates": ["Обновление 1"],
        },
    )

    mock_httpx_client.post.assert_any_await(
        f"{settings.bot_api_url}/digest",
        json={
            "id": 1,
            "description": "Полученные обновления: ",
            "tg_chat_id": 789,
            "updates": ["Обновление 2", "Обновление 3"],
        },
    )


async def test_process_subscription_success(
    mock_client_factory: Mock,
    sample_link_response: LinkResponse,
) -> None:
    """Проверяет корректную обработку подписки c найденными обновлениями."""
    mock_client = AsyncMock()
    mock_client.check_updates.return_value = True
    mock_client_factory.return_value = mock_client

    result = await process_subscription(sample_link_response)

    assert result == "Обновление на https://github.com/user/repo!"


async def test_process_subscription_no_updates(
    mock_client_factory: Mock,
    sample_link_response: LinkResponse,
) -> None:
    """Проверяет обработку подписки без обновлений."""
    mock_client = AsyncMock()
    mock_client.check_updates.return_value = False
    mock_client_factory.return_value = mock_client

    result = await process_subscription(sample_link_response)

    assert result is None


async def test_process_subscription_invalid_url(
    mock_client_factory: Mock,
    sample_link_response: LinkResponse,
) -> None:
    """Проверяет случай неподдерживаемого URL."""
    sample_link_response.url = HttpUrl("https://unsupported.com/repo")

    mock_client_factory.side_effect = ValueError("Неподдерживаемый URL")

    result = await process_subscription(sample_link_response)

    assert result is None


@patch("src.api.scrapper_api.handlers.repo.get_links", new_callable=AsyncMock)
async def test_collect_updates_success(
    mock_get_links: AsyncMock,
    updates_storage: dict[int, list[str]],
    sample_link_response: LinkResponse,
) -> None:
    """Проверяет успешное добавление обновлений в хранилище."""
    mock_get_links.return_value = [sample_link_response]

    with patch(
        "src.scheduler.process_subscription",
        new_callable=AsyncMock,
    ) as mock_process_subscription:
        mock_process_subscription.return_value = "Новое обновление!"
        await collect_updates(123, updates_storage)

    assert updates_storage[123] == ["Новое обновление!"]


@patch("src.api.scrapper_api.handlers.repo.get_links", new_callable=AsyncMock)
async def test_collect_updates_no_subscriptions(
    mock_get_links: AsyncMock,
    updates_storage: dict[int, list[str]],
) -> None:
    """Проверяет случай отсутствия подписок."""
    mock_get_links.return_value = []

    await collect_updates(123, updates_storage)

    assert updates_storage[123] == ["Подписки не найдены"]


@patch("src.api.scrapper_api.handlers.repo.get_links", new_callable=AsyncMock)
async def test_collect_updates_no_updates(
    mock_get_links: AsyncMock,
    updates_storage: dict[int, list[str]],
    sample_link_response: LinkResponse,
) -> None:
    """Проверяет случай, когда в подписках нет обновлений."""
    mock_get_links.return_value = [sample_link_response]

    with patch(
        "src.scheduler.process_subscription",
        new_callable=AsyncMock,
    ) as mock_process_subscription:
        mock_process_subscription.return_value = None
        await collect_updates(123, updates_storage)

    assert updates_storage[123] == ["Обновлений на отслеживаемых сайтах не найдены"]
