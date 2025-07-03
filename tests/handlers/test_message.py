from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from pytest_mock import MockerFixture

from src.bd.memory_storage.enum_states import State
from src.handlers.message import msg_handler
from src.settings import settings

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_message_memory_storage(mock_memory_storage: Mock, mocker: MockerFixture) -> Mock:
    return mocker.patch("src.handlers.message.MemoryStorage", return_value=mock_memory_storage)


@pytest.fixture
def mock_message_build_key(mocker: MockerFixture) -> Mock:
    return mocker.patch(
        "src.handlers.message.build_storage_key",
        return_value="key_123",
    )


async def test_ignore_commands(mock_event: Mock) -> None:
    """Игнорирование сообщений, начинающихся c '/'."""
    mock_event.raw_text = "/start"

    await msg_handler(mock_event)

    mock_event.respond.assert_not_called()


async def test_waiting_for_tags(
    mock_event: Mock,
    mock_message_memory_storage: Mock,
    mock_message_build_key: Mock,  # noqa: ARG001
) -> None:
    """Обработка состояния WAITING_FOR_TAGS."""
    mock_event.raw_text = "tag1 tag2"
    mock_message_memory_storage.return_value.get_state.return_value = State.WAITING_FOR_TAGS
    mock_message_memory_storage.return_value.get_data.return_value = {"url": "http://example.com"}

    await msg_handler(mock_event)

    mock_message_memory_storage.return_value.set_data.assert_called_with(
        "key_123",
        {"url": "http://example.com", "tags": ["tag1", "tag2"]},
    )
    mock_message_memory_storage.return_value.set_state.assert_called_with(
        "key_123",
        State.WAITING_FOR_FILTERS,
    )
    mock_event.respond.assert_called_with(
        "Введите фильтры (опционально, формат key:value, разделённые пробелами):",
    )


async def test_waiting_for_filters_success(
    mock_event: Mock,
    mock_message_memory_storage: Mock,
    mock_httpx_client: AsyncMock,
    mock_message_build_key: Mock,  # noqa: ARG001
) -> None:
    """Обработка состояния WAITING_FOR_FILTERS c разными входными данными."""
    mock_event.raw_text = "key1:value1 key2:value2"
    mock_message_memory_storage.return_value.get_state.return_value = State.WAITING_FOR_FILTERS
    mock_message_memory_storage.return_value.get_data.return_value = {
        "url": "http://example.com",
        "tags": ["tag1"],
    }
    mock_response = Mock(spec=httpx.Response)
    mock_httpx_client.post.return_value = mock_response

    await msg_handler(mock_event)

    mock_message_memory_storage.return_value.set_data.assert_called_with(
        "key_123",
        {"url": "http://example.com", "tags": ["tag1"], "filters": ["key1:value1", "key2:value2"]},
    )
    mock_httpx_client.post.assert_called_once_with(
        f"{settings.scrapper_api_url}/links",
        json={
            "link": "http://example.com",
            "tags": ["tag1"],
            "filters": ["key1:value1", "key2:value2"],
        },
        headers={"Tg-Chat-Id": "123456789"},
    )
    mock_event.respond.assert_called_with("Ссылка http://example.com добавлена для отслеживания.")
    mock_message_memory_storage.return_value.clear.assert_called_with("key_123")


@pytest.mark.parametrize(
    ("status_code", "error_detail", "expected_response"),
    [
        (422, "Invalid link format", "Введён некорректный формат ссылки"),
        (
            500,
            "Server error",
            "Ошибка при добавлении подписки: Server error\n"
            "Для корректной работы данной команды необходимо сначала "
            "зарегистрировать чат с помощью команды /start.",
        ),
    ],
    ids=["invalid_link_422", "server_error_500"],
)
async def test_waiting_for_filters_invalid_link(
    mock_event: Mock,
    mock_message_memory_storage: Mock,
    mock_httpx_client: AsyncMock,
    status_code: int,
    error_detail: str,
    expected_response: str,
) -> None:
    """Обработка состояния WAITING_FOR_FILTERS c ошибкой 422 (некорректная ссылка)."""
    mock_event.raw_text = "key1:value1 key2:value2"
    mock_message_memory_storage.return_value.get_state.return_value = State.WAITING_FOR_FILTERS
    mock_message_memory_storage.return_value.get_data.return_value = {
        "url": "http://example.com",
        "tags": ["tag1"],
    }
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.json.return_value = {"exceptionMessage": error_detail}
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="Unprocessable Entity",
        request=Mock(),
        response=mock_response,
    )
    mock_httpx_client.post.return_value = mock_response

    await msg_handler(mock_event)

    mock_event.respond.assert_called_with(expected_response)
    mock_message_memory_storage.clear.assert_not_called()


async def test_no_state(
    mock_event: Mock,
    mock_message_memory_storage: Mock,
) -> None:
    """Отсутствие состояния."""
    mock_event.raw_text = "some message"
    mock_message_memory_storage.return_value.get_state.return_value = None

    await msg_handler(mock_event)

    mock_message_memory_storage.return_value.set_data.assert_not_called()
    mock_message_memory_storage.return_value.set_state.assert_not_called()
    mock_event.respond.assert_not_called()
