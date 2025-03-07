from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from src.handlers.untrack import untrack_handler
from src.settings import settings

pytestmark = pytest.mark.asyncio


async def test_untrack_handler_success(
    mock_event: Mock,
    mock_httpx_client: AsyncMock,
) -> None:
    """Успешное удаление подписки c помощью команды /untrack."""
    mock_event.message.message = "/untrack https://example.com"
    mock_response = Mock(spec=httpx.Response)
    mock_httpx_client.request.return_value = mock_response
    expected_response = "Ссылка https://example.com удалена из отслеживаемых."

    await untrack_handler(mock_event)

    mock_httpx_client.request.assert_called_once_with(
        "DELETE",
        f"{settings.scrapper_api_url}/links",
        content='{"link": "https://example.com"}',
        headers={"Tg-Chat-Id": "123456789"},
    )
    mock_event.respond.assert_called_once_with(expected_response)


@pytest.mark.parametrize(
    "message_text",
    [
        "/untrack",
        "/untrack https://example.com extra",
        "/untrack   ",
    ],
    ids=["single_part", "too_many_parts", "only_spaces"],
)
async def test_untrack_handler_invalid_format(
    mock_event: Mock,
    mock_httpx_client: AsyncMock,
    message_text: str,
) -> None:
    """Обработка команды /untrack c неверным форматом."""
    mock_event.message.message = message_text
    expected_response = (
        "Сообщение для прекращения отслеживания ссылки должно иметь вид "
        "'/untrack <ваша ссылка>', например:\n/untrack https://example.com"
    )

    await untrack_handler(mock_event)

    mock_event.respond.assert_called_once_with(expected_response)
    mock_httpx_client.request.assert_not_called()


@pytest.mark.parametrize(
    ("status_code", "error_detail", "expected_response"),
    [
        (422, "Invalid link format", "Введён некорректный формат ссылки"),
        (500, "Server error", "Ошибка при удалении подписки: Server error"),
    ],
    ids=["invalid_link_422", "server_error_500"],
)
async def test_untrack_handler_http_error(
    mock_event: Mock,
    mock_httpx_client: AsyncMock,
    status_code: int,
    error_detail: str,
    expected_response: str,
) -> None:
    """Обработка HTTP-ошибок при удалении подписки."""
    mock_event.message.message = "/untrack https://example.com"
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.json.return_value = {"detail": error_detail}
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message=f"{status_code} Error",
        request=Mock(),
        response=mock_response,
    )
    mock_httpx_client.request.return_value = mock_response

    await untrack_handler(mock_event)

    mock_httpx_client.request.assert_called_once_with(
        "DELETE",
        f"{settings.scrapper_api_url}/links",
        content='{"link": "https://example.com"}',
        headers={"Tg-Chat-Id": "123456789"},
    )
    mock_event.respond.assert_called_once_with(expected_response)
