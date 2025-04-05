from typing import Any, Generator

import pytest

from src.db.in_memory.memory_storage.enum_states import State
from src.db.in_memory.memory_storage.memory import MemoryStorage, StorageKey

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def memory_storage() -> Generator[MemoryStorage, None, None]:
    """Фикстура для создания чистого экземпляра MemoryStorage."""
    storage = MemoryStorage()
    yield storage
    storage.storage.clear()


@pytest.mark.parametrize(
    ("chat_id", "user_id", "state_input", "expected_state"),
    [
        (1, 123, State.WAITING_FOR_TAGS, State.WAITING_FOR_TAGS),
        (2, 456, State.WAITING_FOR_FILTERS, State.WAITING_FOR_FILTERS),
        (3, 789, None, None),
    ],
    ids=["active_state", "inactive_state", "none_state"],
)
async def test_set_and_get_state(
    chat_id: int,
    user_id: int,
    state_input: State,
    expected_state: State,
) -> None:
    """Проверяет установку и получение состояния для заданного ключа."""
    storage = MemoryStorage()
    key = StorageKey(chat_id=chat_id, user_id=user_id)
    await storage.set_state(key, state_input)
    result = await storage.get_state(key)
    assert result == expected_state


@pytest.mark.parametrize(
    ("chat_id", "user_id", "data_input", "expected_data"),
    [
        (1, 123, {"key1": "value1", "key2": 42}, {"key1": "value1", "key2": 42}),
        (2, 456, {}, {}),
        (3, 789, {"a": [1, 2, 3]}, {"a": [1, 2, 3]}),
    ],
    ids=["non_empty_data", "empty_data", "list_in_data"],
)
async def test_set_and_get_data(
    chat_id: int,
    user_id: int,
    data_input: dict[str, Any],
    expected_data: dict[str, Any],
) -> None:
    """Проверяет сохранение и получение данных для заданного ключа."""
    storage = MemoryStorage()
    key = StorageKey(chat_id=chat_id, user_id=user_id)
    await storage.set_data(key, data_input)
    result = await storage.get_data(key)
    assert result == expected_data
    assert result is not data_input


@pytest.mark.parametrize(
    ("chat_id", "user_id", "initial_state", "initial_data", "expected_state", "expected_data"),
    [
        (1, 123, State.WAITING_FOR_TAGS, {"key": "value"}, None, {}),
        (2, 456, State.WAITING_FOR_FILTERS, {"a": 1}, None, {}),
        (3, 789, None, {"a": 1, "b": 2}, None, {}),
    ],
    ids=["clear_active", "clear_inactive", "clear_with_data"],
)
async def test_clear(
    chat_id: int,
    user_id: int,
    initial_state: State,
    initial_data: dict[str, Any],
    expected_state: State,
    expected_data: dict[str, Any],
) -> None:
    """Проверяет метод clear, который сбрасывает состояние в None и очищает данные."""
    storage = MemoryStorage()
    key = StorageKey(chat_id=chat_id, user_id=user_id)
    await storage.set_state(key, initial_state)
    await storage.set_data(key, initial_data)
    await storage.clear(key)
    result_state = await storage.get_state(key)
    result_data = await storage.get_data(key)
    assert result_state == expected_state
    assert result_data == expected_data


async def test_multiple_keys() -> None:
    """Проверяет работу c разными ключами."""
    storage = MemoryStorage()
    key1 = StorageKey(chat_id=1, user_id=123)
    key2 = StorageKey(chat_id=2, user_id=123)
    await storage.set_state(key1, State.WAITING_FOR_TAGS)
    await storage.set_data(key1, {"url": "https://example1.com"})
    await storage.set_state(key2, State.WAITING_FOR_FILTERS)
    await storage.set_data(key2, {"url": "https://example2.com"})

    state1 = await storage.get_state(key1)
    data1 = await storage.get_data(key1)
    state2 = await storage.get_state(key2)
    data2 = await storage.get_data(key2)

    assert state1 == State.WAITING_FOR_TAGS
    assert data1 == {"url": "https://example1.com"}
    assert state2 == State.WAITING_FOR_FILTERS
    assert data2 == {"url": "https://example2.com"}
