from typing import Dict, List

from src.api.scrapper_api.models import AddLinkRequest, LinkResponse, RemoveLinkRequest
from src.singleton import SingletonMeta


class Repository(metaclass=SingletonMeta):
    """Репозиторий для хранения информации o Telegram-чатах и отслеживаемых ссылках.

    - chats: словарь, где ключ - идентификатор чата, значение - булево (флаг регистрации)
    - links: словарь, где ключ - идентификатор чата, значение - список объектов LinkResponse
    - _link_id_counter: внутренний счётчик для генерации уникальных идентификаторов ссылок.
    """

    def __init__(self) -> None:
        """Инициализирует репозиторий c пустым словарем чатов и пустым словарём ссылок."""
        self.chats: Dict[int, bool] = {}
        self.links: Dict[int, List[LinkResponse]] = {}
        self._link_id_counter: int = 1

    async def register_chat(self, chat_id: int) -> None:
        """Регистрирует чат по заданному идентификатору.

        :param chat_id: Идентификатор чата.
        """
        if chat_id < 0:
            raise ValueError(f"Некорректный идентификатор чата: {chat_id}. Должен быть >= 0.")
        self.chats[chat_id] = True
        if chat_id not in self.links:
            self.links[chat_id] = []

    async def delete_chat(self, chat_id: int) -> None:
        """Удаляет чат и связанные c ним ссылки.

        :param chat_id: Идентификатор чата.
        :raises HTTPException: Если чат не зарегистрирован.
        """
        if chat_id < 0:
            raise ValueError(f"Некорректный идентификатор чата: {chat_id}. Должен быть >= 0.")
        if chat_id not in self.chats:
            raise KeyError(f"Чат с идентификатором {chat_id} не найден.")
        del self.chats[chat_id]
        if chat_id in self.links:
            del self.links[chat_id]

    async def add_link(self, chat_id: int, add_req: AddLinkRequest) -> LinkResponse:
        """Добавляет новую отслеживаемую ссылку для заданного чата.

        :param chat_id: Идентификатор чата.
        :param add_req: Объект запроса для добавления ссылки.
        :return: Объект LinkResponse c данными добавленной ссылки.
        :raises HTTPException: Если чат не зарегистрирован или ссылка уже добавлена.
        """
        if chat_id not in self.chats:
            raise KeyError(f"Чат с идентификатором {chat_id} не найден.")
        existing_links = self.links.get(chat_id, [])
        for link in existing_links:
            if link.url == add_req.link:
                raise ValueError("Ссылка уже отслеживается")
        new_link = LinkResponse(
            id=self._link_id_counter,
            url=add_req.link,
            tags=add_req.tags,
            filters=add_req.filters,
            last_updated=None,
        )
        self._link_id_counter += 1
        existing_links.append(new_link)
        self.links[chat_id] = existing_links
        return new_link

    async def remove_link(self, chat_id: int, remove_req: RemoveLinkRequest) -> LinkResponse:
        """Убирает отслеживание ссылки для заданного чата.

        :param chat_id: Идентификатор чата.
        :param remove_req: Объект запроса для удаления ссылки.
        :return: Объект LinkResponse удалённой ссылки.
        :raises HTTPException: Если чат не зарегистрирован или ссылка не найдена.
        """
        if chat_id not in self.chats:
            raise ValueError(f"Чат с идентификатором {chat_id} не найден.")
        existing_links = self.links.get(chat_id, [])
        for link in existing_links:
            if link.url == remove_req.link:
                existing_links.remove(link)
                return link
        raise KeyError(f"Ссылка {remove_req.link} не найдена.")

    async def get_links(self, chat_id: int) -> List[LinkResponse]:
        """Возвращает список отслеживаемых ссылок для заданного чата.

        :param chat_id: Идентификатор чата.
        :return: Список объектов LinkResponse.
        """
        if chat_id < 0:
            raise ValueError(f"Некорректный идентификатор чата: {chat_id}. Должен быть >= 0.")
        return self.links.get(chat_id, [])
