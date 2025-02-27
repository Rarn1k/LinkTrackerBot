from typing import List
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from src.bd.repository import Subscription
from src.handlers.get_list import list_handler

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_message_repository(mock_repository: Mock, mocker: MockerFixture) -> Mock:
    """Фикстура для патчинга Repository в модуле src.handlers.get_list."""
    return mocker.patch(
        "src.handlers.get_list.Repository",
        return_value=mock_repository,
        autospec=True,
    )


async def test_list_handler_unregistered_user(
    mock_event: Mock,
    mock_message_repository: Mock,
) -> None:
    """Тест: незарегистрированный пользователь получает запрос на регистрацию."""
    mock_message_repository.return_value.users = {}
    expected_response = "Вы не зарегистрированы. Пожалуйста, введите /start для начала работы."

    await list_handler(mock_event)

    mock_event.respond.assert_called_once_with(expected_response)
    mock_message_repository.return_value.get_subscriptions.assert_not_called()


@pytest.mark.parametrize(
    ("subscriptions", "expected_response"),
    [
        (
            [],
            "У вас нет активных подписок.",
        ),
        (
            [
                Subscription(
                    url="https://example.com",
                    tags=["tag1", "tag2"],
                    filters={"key": "value"},
                ),
                Subscription(url="https://example.org", tags=[], filters={}),
            ],
            "Ваши подписки:\n"
            "https://example.com\nТэги: tag1 tag2\nФильтры: {'key': 'value'}\n\n"
            "https://example.org\nТэги: \nФильтры: {}\n",
        ),
    ],
    ids=["no_subscriptions", "with_subscriptions"],
)
async def test_list_handler_registered_user(
    mock_event: Mock,
    mock_message_repository: Mock,
    subscriptions: List[Subscription],
    expected_response: str,
) -> None:
    """Тест: зарегистрированный пользователь получает сообщение в зависимости от наличия подписок.

    Проверяет логику функции для случаев c пустым и непустым списком подписок.

    :param mock_event: Мок-объект события Telegram.
    :param mock_message_repository: Мок-объект Repository.
    :param subscriptions: Список подписок пользователя.
    :param expected_response: Ожидаемое сообщение в ответе.
    """
    mock_message_repository.return_value.users = {123: subscriptions}
    mock_message_repository.return_value.get_subscriptions.return_value = subscriptions

    await list_handler.__wrapped__(mock_event)

    mock_event.respond.assert_called_once_with(expected_response)
    mock_message_repository.return_value.get_subscriptions.assert_called_once_with(123)
