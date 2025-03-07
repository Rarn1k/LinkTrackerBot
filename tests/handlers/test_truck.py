from unittest.mock import AsyncMock, Mock

import pytest
from pytest_mock import MockerFixture

from src.bd.memory_storage.enum_states import State
from src.handlers.track import track_handler

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_track_memory_storage(mock_memory_storage: Mock, mocker: MockerFixture) -> Mock:
    return mocker.patch("src.handlers.track.MemoryStorage", return_value=mock_memory_storage)


@pytest.fixture
def mock_track_build_key(mocker: MockerFixture) -> AsyncMock:
    return mocker.patch(
        "src.handlers.track.build_storage_key",
        return_value="key_123",
    )


@pytest.mark.parametrize(
    ("message_text", "expected_url"),
    [
        ("/track https://example.com", "https://example.com"),
        ("/track http://test.org", "http://test.org"),
    ],
    ids=["https_url", "http_url"],
)
async def test_track_handler_positive(
    mock_event: Mock,
    mock_track_memory_storage: Mock,
    mock_track_build_key: AsyncMock,  # noqa: ARG001
    message_text: str,
    expected_url: str,
) -> None:
    """Обработка команды /track c правильным форматом сообщения."""
    mock_event.message.message = message_text
    expected_response = "Введите тэги (опционально, разделённые пробелами):"

    await track_handler(mock_event)

    mock_event.respond.assert_called_once_with(expected_response)
    mock_track_memory_storage.return_value.set_state.assert_awaited_once_with(
        "key_123",
        State.WAITING_FOR_TAGS,
    )
    mock_track_memory_storage.return_value.set_data.assert_awaited_once_with(
        "key_123",
        {"url": expected_url},
    )


@pytest.mark.parametrize(
    "message_text",
    [
        "/track",
        "/track https://example.com extra",
        "/track   ",
    ],
    ids=["single_part", "too_many_parts", "only_spaces"],
)
async def test_track_handler_negative(
    mock_event: Mock,
    mock_track_memory_storage: Mock,
    mock_track_build_key: AsyncMock,  # noqa: ARG001
    message_text: str,
) -> None:
    """Тест обработки команды /track c неверным форматом сообщения."""
    mock_event.message.message = message_text
    expected_response = (
        "Сообщение для начала отслеживания ссылки должно иметь вид '/track <ваша ссылка>', "
        "например:\n/track https://example.com"
    )

    await track_handler(mock_event)

    mock_event.respond.assert_called_once_with(expected_response)
    mock_track_memory_storage.return_value.set_state.assert_not_called()
    mock_track_memory_storage.return_value.set_data.assert_not_called()
