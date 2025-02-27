from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture
from telethon.events import NewMessage

from src.handlers.start import start_handler

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_start_repository(mock_repository: Mock, mocker: MockerFixture) -> Mock:
    return mocker.patch(
        "src.handlers.start.Repository",
        return_value=mock_repository,
        autospec=True,
    )


@pytest.mark.parametrize(
    "add_user_result",
    [
        True,
        False,
    ],
    ids=["new_user", "existing_user"],
)
async def test_start_handler(
    mock_event: NewMessage.Event,
    mock_start_repository: Mock,
    add_user_result: bool,
) -> None:
    """Тест: обработка команды /start для нового и существующего пользователя."""
    mock_start_repository.return_value.add_user.return_value = add_user_result
    expected_message: str = (
        "Добро пожаловать в LinkTracker! Введите команду /track <url>, "
        "чтобы подписаться на обновления. "
        "Весь список команд и их пояснения можете получить по команде /help"
    )

    await start_handler(mock_event)

    mock_start_repository.return_value.add_user.assert_called_once_with(123)
    mock_event.client.send_message.assert_called_once_with(
        entity=mock_event.input_chat,
        message=expected_message,
    )
