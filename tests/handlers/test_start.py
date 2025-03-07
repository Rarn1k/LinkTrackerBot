from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from src.handlers.start import start_handler
from src.settings import settings

pytestmark = pytest.mark.asyncio


async def test_start_handler_success(mock_event: Mock, mock_httpx_client: AsyncMock) -> None:
    """Успешная обработка команды /start c регистрацией чата."""
    mock_response = Mock(spec=httpx.Response)
    mock_httpx_client.post.return_value = mock_response
    expected_message = (
        "Добро пожаловать в LinkTracker!\n"
        "Введите команду /track <url>, чтобы подписаться на обновления.\n"
        "Список команд можно получить по команде /help."
    )

    await start_handler(mock_event)

    mock_httpx_client.post.assert_called_once_with(f"{settings.scrapper_api_url}/tg-chat/123456789")
    mock_event.client.send_message.assert_called_once_with(
        entity=mock_event.input_chat,
        message=expected_message,
    )


@pytest.mark.parametrize(
    ("status_code", "error_detail"),
    [
        (400, "Неверный ID чата"),
        (500, "Ошибка сервера"),
    ],
    ids=["http_400", "http_500"],
)
async def test_start_handler_http_error(
    mock_event: Mock,
    mock_httpx_client: AsyncMock,
    status_code: int,
    error_detail: str,
) -> None:
    """Обработка команды /start c HTTP-ошибкой при регистрации чата."""
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.json.return_value = {"detail": error_detail}
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message=f"{status_code} Ошибка",
        request=Mock(),
        response=mock_response,
    )
    mock_httpx_client.post.return_value = mock_response
    mock_event.respond = AsyncMock()

    expected_response = f"Ошибка регистрации чата: {error_detail}"

    await start_handler(mock_event)

    mock_httpx_client.post.assert_called_once_with(f"{settings.scrapper_api_url}/tg-chat/123456789")
    mock_event.respond.assert_called_once_with(expected_response)
