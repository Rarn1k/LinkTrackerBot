from unittest.mock import AsyncMock, Mock

import pytest
from pytest_mock import MockerFixture

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_untrack_repository(mock_repository: Mock, mocker: MockerFixture) -> Mock:
    return mocker.patch(
        "src.handlers.utils.registration_required.Repository",
        return_value=mock_repository,
        autospec=True,
    )


async def test_require_registration_unregistered_user(
    mock_event: Mock,
    mock_untrack_repository: Mock,
) -> None:
    """Проверяет поведение декоратора для незарегистрированного пользователя."""
    from src.handlers.utils.registration_required import require_registration

    handler = AsyncMock()
    decorated_handler = require_registration(handler)
    mock_untrack_repository.return_value.users = {}

    await decorated_handler(mock_event)

    handler.assert_not_called()
    mock_event.respond.assert_called_once_with(
        "Вы не зарегистрированы. Пожалуйста, введите /start для начала работы.",
    )


async def test_require_registration_registered_user(
    mock_event: Mock,
    mock_untrack_repository: Mock,
) -> None:
    """Проверяет поведение декоратора для зарегистрированного пользователя."""
    from src.handlers.utils.registration_required import require_registration

    handler = AsyncMock()
    decorated_handler = require_registration(handler)
    mock_untrack_repository.return_value.users = {123: []}

    await decorated_handler(mock_event)

    handler.assert_called_once_with(mock_event)
    mock_event.respond.assert_not_called()
