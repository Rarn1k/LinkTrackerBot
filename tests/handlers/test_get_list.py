from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from src.handlers.get_list import list_handler
from src.settings import settings

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("mock_response_data", "expected_response"),
    [
        ({"size": 0, "links": []}, "У вас нет активных подписок."),
        (
            {
                "size": 2,
                "links": [
                    {
                        "url": "https://example.com",
                        "tags": ["tag1", "tag2"],
                        "filters": ["filter1"],
                    },
                    {"url": "https://example.org", "tags": [], "filters": []},
                ],
            },
            "Ваши подписки:\n"
            "https://example.com\nТэги: tag1 tag2\nФильтры: filter1\n\n"
            "https://example.org\nТэги: \nФильтры: \n",
        ),
    ],
    ids=["empty_subscriptions", "with_subscriptions"],
)
async def test_list_handler_success(
    mock_event: Mock,
    mock_httpx_client: AsyncMock,
    mock_response_data: dict,
    expected_response: str,
) -> None:
    """Успешное получение списка подписок."""
    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = mock_response_data
    mock_httpx_client.get.return_value = mock_response

    await list_handler(mock_event)

    mock_httpx_client.get.assert_called_once_with(
        f"{settings.scrapper_api_url}/links",
        headers={"Tg-Chat-Id": "123456789"},
    )
    mock_event.respond.assert_called_once_with(expected_response)


@pytest.mark.parametrize(
    ("status_code", "error_detail"),
    [
        (400, "Invalid request parameters"),
        (500, "Internal server error"),
    ],
    ids=["http_400", "http_500"],
)
async def test_list_handler_http_error(
    mock_event: Mock,
    mock_httpx_client: AsyncMock,
    status_code: int,
    error_detail: str,
) -> None:
    """Обработка HTTP-ошибок при получении подписок."""
    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = {"detail": error_detail}
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message=f"{status_code} Error",
        request=Mock(),
        response=mock_response,
    )
    mock_httpx_client.get.return_value = mock_response
    expected_response = f"Ошибка при получении подписок: {error_detail}"

    await list_handler(mock_event)

    mock_httpx_client.get.assert_called_once_with(
        f"{settings.scrapper_api_url}/links",
        headers={"Tg-Chat-Id": "123456789"},
    )
    mock_event.respond.assert_called_once_with(expected_response)
