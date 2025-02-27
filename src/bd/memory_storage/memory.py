from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, DefaultDict, Optional

from src.bd.memory_storage.enum_states import State
from src.singleton import SingletonMeta


@dataclass(frozen=True)
class StorageKey:
    """Ключ для хранения данных в MemoryStorage.

    Представляет уникальный идентификатор записи, состоящий из ID чата и ID пользователя.
    Используется как неизменяемый ключ в словаре хранения.

    :param chat_id: Идентификатор чата (int).
    :param user_id: Идентификатор пользователя (int).
    """

    chat_id: int
    user_id: int


@dataclass
class MemoryStorageRecord:
    """Запись для хранения данных и состояния в MemoryStorage.

    Содержит данные (словарь) и состояние (State), которые могут быть связаны c ключом StorageKey.
    Используется как значение по умолчанию в defaultdict.

    :param data: Словарь c пользовательскими данными (dict[str, Any]).
    :param state: Состояние записи (State или None).
    """

    data: dict[str, Any] = field(default_factory=dict)
    state: Optional[State] = None


class MemoryStorage(metaclass=SingletonMeta):
    """Хранилище данных в памяти c асинхронными методами.

    Реализует синглтон для управления состоянием и данными пользователей в виде
    словаря c ключами StorageKey и значениями MemoryStorageRecord.
    Предоставляет методы для установки, получения и очистки данных и состояния.

    :ivar storage: Словарь хранения c ключами StorageKey и значениями MemoryStorageRecord.
    :type storage: DefaultDict[StorageKey, MemoryStorageRecord]
    """

    def __init__(self) -> None:
        """Инициализирует хранилище c пустым defaultdict."""
        self.storage: DefaultDict[StorageKey, MemoryStorageRecord] = defaultdict(
            MemoryStorageRecord,
        )

    async def set_state(self, key: StorageKey, state: Optional[State] = None) -> None:
        """Устанавливает состояние для указанного ключа.

        :param key: Ключ для доступа к записи (StorageKey).
        :param state: Состояние для установки (State или None).
        :return: None
        """
        self.storage[key].state = state

    async def get_state(self, key: StorageKey) -> Optional[State]:
        """Получает состояние для указанного ключа.

        :param key: Ключ для доступа к записи (StorageKey).
        :return: Текущее состояние записи (State) или None, если ключ отсутствует.
        """
        if key not in self.storage:
            return None
        return self.storage[key].state

    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        """Устанавливает данные для указанного ключа.

        :param key: Ключ для доступа к записи (StorageKey).
        :param data: Словарь данных для установки (dict[str, Any]).
        :return: None
        """
        self.storage[key].data = data.copy()

    async def get_data(self, key: StorageKey) -> Optional[dict[str, Any]]:
        """Получает данные для указанного ключа.

        :param key: Ключ для доступа к записи (StorageKey).
        :return: Копия данных записи (dict[str, Any]) или None, если ключ отсутствует.
        """
        if key not in self.storage:
            return None
        return self.storage[key].data.copy()

    async def clear(self, key: StorageKey) -> None:
        """Очищает состояние и данные для указанного ключа.

        Устанавливает состояние в None и заменяет данные пустым словарём.

        :param key: Ключ для доступа к записи (StorageKey).
        :return: None
        """
        await self.set_state(key, None)
        await self.set_data(key, {})
