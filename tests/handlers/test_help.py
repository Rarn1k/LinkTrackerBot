from unittest.mock import Mock

import pytest

from src.handlers.help import help_handler

pytestmark = pytest.mark.asyncio


async def test_help_registered_user(mock_event: Mock) -> None:
    """Тест: успешная отправка сообщения помощи зарегистрированному пользователю."""
    expected_help_text = (
        "Доступные команды:\n"
        "/start - начало работы бота\n"
        "/help - помощь\n"
        "/track <url> - начать отслеживание ссылки\n"
        "/untrack <url> - прекратить отслеживание ссылки\n"
        "/list - список отслеживаемых ссылок"
    )

    await help_handler(mock_event)

    mock_event.respond.assert_called_once_with(expected_help_text)
