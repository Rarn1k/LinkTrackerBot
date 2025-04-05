from abc import ABC, abstractmethod

from src.api.bot_api.models import UpdateEvent


class NotificationService(ABC):
    """Интерфейс для сервиса отправки уведомлений от scrapper к bot.

    Определяет контракт для отправки уведомлений, позволяющий использовать
    различные реализации (HTTP, Kafka и т.д.).
    """

    @abstractmethod
    async def send_update(self, chat_id: int, updates: list[str]) -> None:
        """Отправляет уведомление c заданными данными.

        :param chat_id: ID чата.
        :param updates: Список сообщений o6 обновлениях.
        :return: None
        :raises Exception: При ошибках отправки уведомления.
        """

    @abstractmethod
    async def send_digest(self, chat_id: int, updates: list[UpdateEvent]) -> None:
        """Отправляет уведомление c заданными данными.

        :param chat_id: ID чата.
        :param updates: Список сообщений o6 обновлениях.
        :return: None
        :raises Exception: При ошибках отправки уведомления.
        """
