# from unittest.mock import Mock
#
# import pytest
# from pytest_mock import MockerFixture
#
# from src.bd.memory_storage.enum_states import State
# from src.bd.repository import Subscription
# from src.handlers.message import msg_handler
#
# pytestmark = pytest.mark.asyncio
#
#
# @pytest.fixture
# def mock_message_memory_storage(mock_memory_storage: Mock, mocker: MockerFixture) -> Mock:
#     return mocker.patch("src.handlers.message.MemoryStorage", return_value=mock_memory_storage)
#
#
# @pytest.fixture
# def mock_message_repository(mock_repository: Mock, mocker: MockerFixture) -> Mock:
#     return mocker.patch(
#         "src.handlers.message.Repository",
#         return_value=mock_repository,
#         autospec=True,
#     )
#
#
# @pytest.fixture
# def mock_message_build_key(mock_build_key: Mock, mocker: MockerFixture) -> Mock:
#     return mocker.patch(
#         "src.handlers.message.build_storage_key",
#         return_value=mock_build_key.return_value,
#     )
#
#
# async def test_ignore_commands(mock_event: Mock) -> None:
#     """Тест: игнорирование сообщений, начинающихся c '/'."""
#     mock_event.raw_text = "/start"
#
#     await msg_handler.__wrapped__(mock_event)
#
#     mock_event.respond.assert_not_called()
#
#
# async def test_unregistered_user(mock_event: Mock, mock_message_repository: Mock) -> None:
#     """Тест: обработка незарегистрированного пользователя."""
#     mock_event.raw_text = "tag1 tag2"
#
#     await msg_handler(mock_event)
#
#     mock_event.respond.assert_called_with(
#         "Вы не зарегистрированы. Пожалуйста, введите /start для начала работы.",
#     )
#     mock_message_repository.return_value.add_subscription.assert_not_called()
#
#
# async def test_waiting_for_tags(
#     mock_event: Mock,
#     mock_message_memory_storage: Mock,
#     mock_message_build_key: Mock,
# ) -> None:
#     """Тест: обработка состояния WAITING_FOR_TAGS."""
#     mock_event.raw_text = "tag1 tag2"
#     mock_message_memory_storage.return_value.get_state.return_value = State.WAITING_FOR_TAGS
#     mock_message_memory_storage.return_value.get_data.return_value = {"url": "http://example.com"}
#     mock_message_build_key.return_value = "key_123"
#
#     await msg_handler.__wrapped__(mock_event)
#
#     mock_message_memory_storage.return_value.set_data.assert_called_with(
#         "key_123",
#         {"url": "http://example.com", "tags": ["tag1", "tag2"]},
#     )
#     mock_message_memory_storage.return_value.set_state.assert_called_with(
#         "key_123",
#         State.WAITING_FOR_FILTERS,
#     )
#     mock_event.respond.assert_called_with(
#         "Введите фильтры (опционально, формат key:value, разделённые пробелами):",
#     )
#
#
# @pytest.mark.parametrize(
#     ("input_text", "expected_filters"),
#     [
#         ("key1:value1 key2:value2", {"key1": "value1", "key2": "value2"}),
#         ("invalid_filter", {}),
#     ],
#     ids=["valid_filters", "invalid_filters"],
# )
# async def test_waiting_for_filters(
#     mock_event: Mock,
#     mock_message_memory_storage: Mock,
#     mock_message_repository: Mock,
#     mock_message_build_key: Mock,
#     input_text: str,
#     expected_filters: dict,
# ) -> None:
#     """Тест: обработка состояния WAITING_FOR_FILTERS c разными входными данными."""
#     mock_event.raw_text = input_text
#     mock_message_memory_storage.return_value.get_state.return_value = State.WAITING_FOR_FILTERS
#     mock_message_memory_storage.return_value.get_data.return_value = {
#         "url": "http://example.com",
#         "tags": ["tag1"],
#     }
#     mock_message_repository.return_value.add_subscription.return_value = True
#     mock_message_build_key.return_value = "key_123"
#
#     await msg_handler.__wrapped__(mock_event)
#
#     mock_message_memory_storage.return_value.set_data.assert_called_with(
#         "key_123",
#         {"url": "http://example.com", "tags": ["tag1"], "filters": expected_filters},
#     )
#     mock_message_repository.return_value.add_subscription.assert_called_with(
#         123,
#         Subscription(url="http://example.com", tags=["tag1"], filters=expected_filters),
#     )
#     mock_event.respond.assert_called_with("Ссылка http://example.com добавлена для отслеживания.")
#     mock_message_memory_storage.return_value.clear.assert_called_with("key_123")
#
#
# async def test_no_state(
#     mock_event: Mock,
#     mock_message_memory_storage: Mock,
# ) -> None:
#     """Тест: отсутствие состояния."""
#     mock_event.raw_text = "some message"
#     mock_message_memory_storage.return_value.get_state.return_value = None
#
#     await msg_handler.__wrapped__(mock_event)
#
#     mock_message_memory_storage.return_value.set_data.assert_not_called()
#     mock_message_memory_storage.return_value.set_state.assert_not_called()
#     mock_event.respond.assert_not_called()
