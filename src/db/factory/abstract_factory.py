from abc import ABC, abstractmethod

from src.db.base_service.chat_service import BaseChatService
from src.db.base_service.link_service import BaseLinkService


class DataAccessFactory(ABC):
    """Абстрактная фабрика для создания сервисов доступа к данным.

    Она определяет методы для создания сервисов работы c чатами и подписками.
    """

    @staticmethod
    @abstractmethod
    def create_chat_service() -> BaseChatService:
        """Создаёт сервис для работы c чатами.
        :return: Экземпляр, реализующий BaseChatService.
        """

    @staticmethod
    @abstractmethod
    def create_link_service() -> BaseLinkService:
        """Создаёт сервис для работы c подписками.
        :return: Экземпляр, реализующий BaseLinkService.
        """
