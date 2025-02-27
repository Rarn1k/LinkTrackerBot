from unittest.mock import Mock

import pytest

from src.handlers.unknown import unknown_command_handler

pytestmark = pytest.mark.asyncio


async def test_unknown_command_handler_unregistered_user(
    mock_event: Mock,
) -> None:
    """Проверяет, что незарегистрированному пользователю отправляется запрос на регистрацию."""
    mock_event.raw_text = "/unknown"
    expected_response = "Вы не зарегистрированы. Пожалуйста, введите /start для начала работы."

    await unknown_command_handler(mock_event)

    mock_event.respond.assert_called_once_with(expected_response)


@pytest.mark.parametrize(
    "command",
    ["/help", "/unknown", "/start", "/foo"],
    ids=["known_help", "unknown_command", "known_start", "unknown_foo"],
)
async def test_unknown_command_handler_registered_user(
    mock_event: Mock,
    command: str,
) -> None:
    """Проверяет поведение для зарегистрированного пользователя c известными и
    неизвестными командами.
    """
    mock_event.raw_text = command
    expected_response = "Неизвестная команда. Используйте /help для списка доступных команд."

    await unknown_command_handler.__wrapped__(mock_event)

    mock_event.respond.assert_called_once_with(expected_response)
