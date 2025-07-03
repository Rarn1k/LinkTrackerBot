from datetime import datetime, timezone
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.bot_api.models import UpdateEvent
from src.api.scrapper_api.models import LinkResponse
from src.clients.client_factory import ClientFactory
from src.db.factory.data_access_factory import db_service
from src.scheduler.notification.notification_service import NotificationService
from src.scheduler.scheduler_service import Scheduler

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_process_subscription() -> Generator[AsyncMock, None, None]:
    """Мок для process_subscription."""
    with patch.object(
        Scheduler,
        "process_subscription",
        new_callable=AsyncMock,
    ) as mock_process_subscription:
        yield mock_process_subscription


@pytest.fixture
def mock_notification_service() -> AsyncMock:
    """Мок для NotificationService."""
    return AsyncMock(spec=NotificationService)


@pytest.fixture
def scheduler(mock_notification_service: MagicMock) -> Scheduler:
    """Фикстура для создания экземпляра Scheduler."""
    return Scheduler(mock_notification_service)


@pytest.fixture
def mock_dependency() -> AsyncMock:
    """Фикстура для мокирования зависимости БД."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_client_factory() -> Generator[MagicMock, None, None]:
    """Мок для ClientFactory."""
    with patch.object(ClientFactory, "create_client", new_callable=MagicMock) as mock_factory:
        yield mock_factory


@pytest.fixture
def mock_db_service() -> Generator[AsyncMock, None, None]:
    """Мок для db_service.link_service."""
    mock_service = AsyncMock()
    mock_service.set_last_updated = AsyncMock()
    mock_service.get_links = AsyncMock()

    with patch.object(db_service, "link_service", mock_service):
        yield mock_service


@pytest.fixture
def sample_link_response() -> LinkResponse:
    """Фикстура тестовой подписки."""
    return LinkResponse(
        id=1,
        url=HttpUrl("https://github.com/user/repo"),
        tags=["tag1"],
        filters=["key1:value1"],
        last_updated=datetime.now(timezone.utc),
    )


async def test_process_subscription_success(
    mock_client_factory: MagicMock,
    sample_link_response: LinkResponse,
    mock_dependency: AsyncMock,
    mock_db_service: AsyncMock,
) -> None:
    """Проверяет корректную обработку подписки при наличии обновлений."""
    mock_client = AsyncMock()
    update_event = UpdateEvent(
        description="Обновление на https://example.com",
        title="Test PR",
        username="TestUser",
        created_at=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        preview="Превью описания тестового PR."[:200],
    )
    mock_client.check_updates.return_value = update_event
    mock_client_factory.return_value = mock_client

    result = await Scheduler.process_subscription(sample_link_response, mock_dependency)

    assert result == update_event
    mock_db_service.set_last_updated.assert_awaited_once_with(
        link_id=sample_link_response.id,
        last_updated=update_event.created_at,
        dependency=mock_dependency,
    )


async def test_process_subscription_no_updates(
    mock_client_factory: MagicMock,
    sample_link_response: LinkResponse,
    mock_dependency: AsyncMock,
    mock_db_service: AsyncMock,
) -> None:
    """Проверяет обработку подписки без обновлений."""
    mock_client = AsyncMock()
    mock_client.check_updates.return_value = None
    mock_client_factory.return_value = mock_client

    result = await Scheduler.process_subscription(sample_link_response, mock_dependency)

    assert result is None
    mock_db_service.assert_not_awaited()


async def test_process_subscription_invalid_url(
    mock_client_factory: MagicMock,
    sample_link_response: LinkResponse,
    mock_dependency: AsyncMock,
) -> None:
    """Проверяет случай неподдерживаемого URL."""
    sample_link_response.url = HttpUrl("https://unsupported.com/repo")
    mock_client_factory.side_effect = ValueError("Неподдерживаемый URL")

    result = await Scheduler.process_subscription(sample_link_response, mock_dependency)

    assert result is None


async def test_collect_updates_success(
    scheduler: Scheduler,
    mock_db_service: AsyncMock,
    mock_process_subscription: AsyncMock,
    sample_link_response: LinkResponse,
    mock_dependency: AsyncMock,
) -> None:
    """Проверяет успешное добавление обновлений в хранилище."""
    mock_db_service.get_links.return_value = [sample_link_response]
    new_update = UpdateEvent(
        description="Обновление на https://example.com",
        title="Обновление",
        username="TestUser",
        created_at=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        preview="Превью",
    )
    mock_process_subscription.return_value = new_update

    updates = await scheduler.collect_updates(123, mock_dependency)

    assert updates == [new_update]


async def test_collect_updates_no_subscriptions(
    scheduler: Scheduler,
    mock_db_service: AsyncMock,
    mock_dependency: AsyncMock,
) -> None:
    """Проверяет случай отсутствия подписок."""
    mock_db_service.get_links.return_value.return_value = []

    updates = await scheduler.collect_updates(123, mock_dependency)

    assert updates == []


async def test_collect_updates_no_updates(
    scheduler: Scheduler,
    mock_db_service: AsyncMock,
    mock_process_subscription: AsyncMock,
    sample_link_response: LinkResponse,
    mock_dependency: AsyncMock,
) -> None:
    """Проверяет случай, когда в подписках нет обновлений."""
    mock_db_service.get_links.return_value = [sample_link_response]
    mock_process_subscription.return_value = None

    updates = await scheduler.collect_updates(123, mock_dependency)

    assert updates == []


async def test_send_digest(
    scheduler: Scheduler,
    mock_notification_service: AsyncMock,
) -> None:
    """Проверяет, что дайджест отправляется корректно и хранилище очищается."""
    chat_id = 123
    updates = [
        UpdateEvent(
            description="Обновление на https://example.com",
            title="Обновление 1",
            username="User1",
            created_at=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            preview="Превью 1",
        ),
        UpdateEvent(
            description="Обновление на https://another.com",
            title="Обновление 2",
            username="User2",
            created_at=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            preview="Превью 2",
        ),
    ]

    await scheduler.notification_service.send_digest(chat_id, updates)

    mock_notification_service.send_digest.assert_awaited_once_with(
        chat_id,
        updates,
    )
