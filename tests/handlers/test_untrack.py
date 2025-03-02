# from unittest.mock import Mock
#
# import pytest
# from pytest_mock import MockerFixture
#
# from src.handlers.untrack import untrack_handler
#
# pytestmark = pytest.mark.asyncio
#
#
# @pytest.fixture
# def mock_untrack_repository(mock_repository: Mock, mocker: MockerFixture) -> Mock:
#     return mocker.patch(
#         "src.handlers.untrack.Repository",
#         return_value=mock_repository,
#         autospec=True,
#     )
#
#
# async def test_untrack_handler_unregistered_user(
#     mock_event: Mock,
#     mock_untrack_repository: Mock,
# ) -> None:
#     """Проверяет, что незарегистрированному пользователю отправляется сообщение про
#     необходимость регистрации.
#     """
#     expected_response = "Вы не зарегистрированы. Пожалуйста, введите /start для начала работы."
#
#     await untrack_handler(mock_event)
#
#     mock_event.respond.assert_called_once_with(expected_response)
#     mock_untrack_repository.is_user_have_url.assert_not_called()
#     mock_untrack_repository.remove_subscription.assert_not_called()
#
#
# async def test_untrack_handler_invalid_format(
#     mock_event: Mock,
#     mock_untrack_repository: Mock,
# ) -> None:
#     """Проверяет, что при неправильном формате сообщения отправляется сообщение про ошибку."""
#     mock_event.message.message = "/untrack"
#     expected_response = (
#         "Сообщение для прекращения отслеживания ссылки должно иметь вид '/track <ваша ссылка>', "
#         "например:\n/track https://example.com"
#     )
#
#     await untrack_handler.__wrapped__(mock_event)
#
#     mock_event.respond.assert_called_once_with(expected_response)
#     mock_untrack_repository.is_user_have_url.assert_not_called()
#     mock_untrack_repository.remove_subscription.assert_not_called()
#
#
# async def test_untrack_handler_no_subscription(
#     mock_event: Mock,
#     mock_untrack_repository: Mock,
# ) -> None:
#     """Проверяет, что если подписка не найдена, отправляется соответствующее сообщение."""
#     mock_event.message.message = "/untrack https://example.com"
#     expected_response = "Ссылка https://example.com не найдена в ваших подписках."
#
#     await untrack_handler.__wrapped__(mock_event)
#
#     mock_event.respond.assert_called_once_with(expected_response)
#     mock_untrack_repository.return_value.is_user_have_url.assert_awaited_once_with(
#         123,
#         "https://example.com",
#     )
#     mock_untrack_repository.return_value.remove_subscription.assert_not_called()
#
#
# async def test_untrack_handler_with_subscription(
#     mock_event: Mock,
#     mock_untrack_repository: Mock,
# ) -> None:
#     """Проверяет, что при наличии подписки она удаляется, и отправляется сообщение про успех."""
#     mock_event.message.message = "/untrack https://example.com"
#     mock_untrack_repository.return_value.is_user_have_url.return_value = True
#     expected_response = "Ссылка https://example.com удалена из отслеживаемых."
#
#     await untrack_handler.__wrapped__(mock_event)
#
#     mock_event.respond.assert_called_once_with(expected_response)
#     mock_untrack_repository.return_value.is_user_have_url.assert_awaited_once_with(
#         123,
#         "https://example.com",
#     )
#     mock_untrack_repository.return_value.remove_subscription.assert_awaited_once_with(
#         123,
#         "https://example.com",
#     )
