from src.db.base_service.chat_service import BaseChatService
from src.db.base_service.link_service import BaseLinkService
from src.db.factory.abstract_factory import DataAccessFactory
from src.db.sql_service.chat_service import SqlChatService
from src.db.sql_service.link_service import SqlLinkService


class SqlDataAccessFactory(DataAccessFactory):
    """Фабрика для создания сервисов доступа к данным через чистый SQL (asyncpg)."""

    @staticmethod
    def create_chat_service() -> BaseChatService:
        """Создает сервис управления чатами через SQL (asyncpg).

        :return: Экземпляр `SqlChatService`.
        """
        return SqlChatService()

    @staticmethod
    def create_link_service() -> BaseLinkService:
        """Создает сервис управления подписками через SQL (asyncpg).

        :return: Экземпляр `SqlLinkService`.
        """
        return SqlLinkService()
