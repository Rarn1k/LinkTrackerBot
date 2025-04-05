from src.db.base_service.chat_service import BaseChatService
from src.db.base_service.link_service import BaseLinkService


class DataAccessService:
    """Единый сервис доступа к данным, инкапсулирующий сервисы для работы c чатами и подписками.

    :param chat_service: Сервис для работы c чатами, реализующий интерфейс BaseChatService.
    :param link_service: Сервис для работы c подписками, реализующий интерфейс BaseLinkService.
    """

    def __init__(self, chat_service: BaseChatService, link_service: BaseLinkService) -> None:
        self.chat_service = chat_service
        self.link_service = link_service
