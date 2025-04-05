from src.db.base_service.chat_service import BaseChatService
from src.db.base_service.link_service import BaseLinkService
from src.db.factory.abstract_factory import DataAccessFactory
from src.db.orm_service.chat_service import OrmChatService
from src.db.orm_service.link_service import OrmLinkService


class OrmDataAccessFactory(DataAccessFactory):
    """Фабрика для создания сервисов доступа к данным через ORM (SQLAlchemy)."""

    @staticmethod
    def create_chat_service() -> BaseChatService:
        """Создает сервис управления чатами через ORM.

        :return: Экземпляр `OrmChatService`.
        """
        return OrmChatService()

    @staticmethod
    def create_link_service() -> BaseLinkService:
        """Создает сервис управления подписками через ORM.

        :return: Экземпляр `OrmLinkService`.
        """
        return OrmLinkService()
