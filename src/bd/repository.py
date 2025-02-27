from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.singleton import SingletonMeta


@dataclass
class Subscription:
    """Класс для представления подписки пользователя."""

    url: str
    tags: List[str] = field(default_factory=list)
    filters: Dict[str, str] = field(default_factory=dict)
    last_updated: Optional[str] = None


class Repository(metaclass=SingletonMeta):
    """Репозиторий подписок в памяти c асинхронными методами.

    Этот класс обеспечивает управление пользователями и их подписками, используя словарь в памяти.
    Реализован как синглтон для единственного экземпляра в приложении.
    """

    def __init__(self) -> None:
        """Инициализирует репозиторий c пустым словарем пользователей."""
        self.users: Dict[int, List[Subscription]] = {}

    async def add_user(self, user_id: int) -> bool:
        """Добавляет нового пользователя user_id в репозиторий.

        :param user_id: Идентификатор пользователя (int).
        :return: True, если пользователь успешно добавлен, False, если он уже существует.
        """
        if user_id not in self.users:
            self.users[user_id] = []
            return True
        return False

    async def add_subscription(self, user_id: int, subscription: Subscription) -> bool:
        """Добавляет подписку subscription для пользователя user_id.

        :param user_id: Идентификатор пользователя (int).
        :param subscription: Объект подписки (Subscription), содержащий URL и другие данные.
        :return: True, если подписка успешно добавлена, False, если пользователь не существует
        или подписка уже есть.
        """
        user_data = self.users.get(user_id)
        if user_data is None:
            return False
        if any(s.url == subscription.url for s in user_data):
            return False
        user_data.append(subscription)
        return True

    async def remove_subscription(self, user_id: int, url: str) -> None:
        """Удаляет подписку пользователя по URL, если она существует.

        :param user_id: Идентификатор пользователя (int).
        :param url: URL подписки для удаления (str).
        """
        user_data = self.users.get(user_id)
        if user_data is None:
            return
        for sub in user_data:
            if sub.url == url:
                self.users[user_id].remove(sub)

    async def get_subscriptions(self, user_id: int) -> List[Subscription]:
        """Возвращает список подписок пользователя user_id.

        :param user_id: Идентификатор пользователя (int).
        :return: Список подписок (list[Subscription]), пустой список, если пользователя нет.
        """
        return self.users.get(user_id, [])

    async def is_user_have_url(self, user_id: int, url: str) -> bool:
        """Проверяет, есть ли y пользователя user_id подписка c указанным URL.

        :param user_id: Идентификатор пользователя (int).
        :param url: URL для проверки (str).
        :return: True, если подписка существует, False, если нет или пользователь не найден.
        """
        user_data = self.users.get(user_id)
        if user_data is None:
            return False
        return any(sub.url == url for sub in user_data)
