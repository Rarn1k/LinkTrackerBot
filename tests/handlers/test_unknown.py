from unittest.mock import Mock

import pytest

from src.handlers.unknown import unknown_command_handler

pytestmark = pytest.mark.asyncio


async def test_unknown_command_handler(mock_event: Mock) -> None:
    """Тест обработки любой команды в unknown_command_handler."""
    expected_response = "Неизвестная команда. Используйте /help для списка доступных команд."

    await unknown_command_handler(mock_event)

    mock_event.respond.assert_called_once_with(expected_response)
