# from unittest.mock import Mock
#
# import pytest
# from pytest_mock import MockerFixture
#
# from src.bd.memory_storage.enum_states import State
# from src.handlers.track import track_handler
#
# pytestmark = pytest.mark.asyncio
#
#
# @pytest.fixture
# def mock_track_memory_storage(mock_memory_storage: Mock, mocker: MockerFixture) -> Mock:
#     return mocker.patch("src.handlers.track.MemoryStorage", return_value=mock_memory_storage)
#
#
# @pytest.fixture
# def mock_track_build_key(mock_build_key: Mock, mocker: MockerFixture) -> Mock:
#     return mocker.patch(
#         "src.handlers.track.build_storage_key",
#         return_value=mock_build_key.return_value,
#     )
#
#
# async def test_track_handler_unregistered_user(
#     mock_event: Mock,
# ) -> None:
#     """Тест для незарегистрированного пользователя."""
#     expected_response = "Вы не зарегистрированы. Пожалуйста, введите /start для начала работы."
#
#     await track_handler(mock_event)
#
#     mock_event.respond.assert_called_once_with(expected_response)
#
#
# @pytest.mark.parametrize(
#     ("message_text", "expected_response", "expect_state_set"),
#     [
#         (
#             "/track https://example.com",
#             "Введите тэги (опционально, разделённые пробелами):",
#             True,
#         ),
#         (
#             "/track",
#             "Сообщение для начала отслеживания ссылки должно иметь вид '/track <ваша ссылка>', "
#             "например:\n/track https://example.com",
#             False,
#         ),
#         (
#             "/track https://example.com extra",
#             "Сообщение для начала отслеживания ссылки должно иметь вид '/track <ваша ссылка>', "
#             "например:\n/track https://example.com",
#             False,
#         ),
#     ],
#     ids=["correct_format", "incorrect_format_single_part", "incorrect_format_too_many_parts"],
# )
# async def test_track_handler_registered_user(
#     mock_event: Mock,
#     mock_track_memory_storage: Mock,
#     mock_track_build_key: Mock,
#     message_text: str,
#     expected_response: str,
#     expect_state_set: bool,
# ) -> None:
#     """Тест для зарегистрированного пользователя c разными форматами сообщения."""
#     mock_event.message.message = message_text
#     mock_track_build_key.return_value = "key_123"
#
#     await track_handler.__wrapped__(mock_event)
#
#     mock_event.respond.assert_called_once_with(expected_response)
#     if expect_state_set:
#         mock_track_memory_storage.return_value.set_state.assert_awaited_once_with(
#             "key_123",
#             State.WAITING_FOR_TAGS,
#         )
#         mock_track_memory_storage.return_value.set_data.assert_awaited_once_with(
#             "key_123",
#             {"url": "https://example.com"},
#         )
#     else:
#         mock_track_memory_storage.return_value.set_state.assert_not_called()
#         mock_track_memory_storage.return_value.set_data.assert_not_called()
