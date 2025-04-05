import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from src.api.bot_api.models import DigestUpdate, UpdateEvent
from src.scheduler.notification.http_notification_service import HTTPNotificationService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def notifier() -> HTTPNotificationService:
    """Фикстура для создания экземпляра HTTPNotificationService c тестовым URL."""
    return HTTPNotificationService(bot_api_url="http://test-bot-api.com")


async def test_send_digest_success(
    notifier: HTTPNotificationService,
    mock_httpx_client: AsyncMock,
) -> None:
    """Проверяет успешную отправку дайджеста через HTTPNotificationService.

    Фикстура задаёт, что y чата есть обновления, и проверяется,
    что POST-запрос отправляется c корректным payload.
    """
    chat_id = 123
    updates = [
        UpdateEvent(
            description="Обновление на https://example.com",
            title="Тестовая новость",
            username="User123",
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            preview="Краткое описание.",
        ),
    ]

    mock_response = AsyncMock(spec=httpx.Response)
    mock_httpx_client.post.return_value = mock_response

    await notifier.send_digest(chat_id, updates)

    expected_payload = DigestUpdate(
        id=int(time.time()),
        description="Полученные обновления:",
        tg_chat_id=chat_id,
        updates=[
            (
                "Описание:  Обновление на https://example.com\n"
                "Заголовок: *Тестовая новость*\n"
                "Автор:     User123\n"
                "Дата:      2024-01-01 00:00\n"
                "Описание:  Краткое описание.\n"
                "=================================================="
            ),
        ],
    ).model_dump()
    mock_httpx_client.post.assert_awaited_once_with(
        "http://test-bot-api.com/digest",
        json=expected_payload,
    )


async def test_send_digest_no_updates(
    notifier: HTTPNotificationService,
    mock_httpx_client: AsyncMock,
) -> None:
    """Проверяет, что если список обновлений пуст, то HTTP-запрос не отправляется."""
    chat_id = 123
    updates: list[UpdateEvent] = []

    await notifier.send_digest(chat_id, updates)
    mock_httpx_client.post.assert_not_awaited()


async def test_send_digest_http_error(
    notifier: HTTPNotificationService,
    mock_httpx_client: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Проверяет, что при возникновении HTTP-ошибки в методе send_digest ошибка логируется.

    Используется патчинг метода post, который вызывает исключение.
    """
    chat_id = 123
    updates = [
        UpdateEvent(
            description="Обновление на https://example.com",
            title="Ошибка запроса",
            username="User456",
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            preview="Ошибка при отправке.",
        ),
    ]
    mock_response = Mock(spec=httpx.Response)
    mock_response.raise_for_status.side_effect = httpx.HTTPError("HTTP error")
    mock_httpx_client.post.return_value = mock_response

    await notifier.send_digest(chat_id, updates)
    assert "Не удалось отправить уведомление на /digest для чата 123" in caplog.text
