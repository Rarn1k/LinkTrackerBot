import httpx
from pydantic import HttpUrl
from telethon.events import NewMessage

from src.api.scrapper_api.models import AddLinkRequest
from src.db.in_memory.memory_storage.enum_states import State
from src.db.in_memory.memory_storage.key_builder import build_storage_key
from src.db.in_memory.memory_storage.memory import MemoryStorage
from src.settings import settings

__all__ = ("msg_handler",)


async def _send_scrapper_request(
    event: NewMessage.Event,
    url: str,
    tags: list[str],
    filters: list[str],
) -> None:
    """
    Отправляет HTTP-запрос в scrapper API для добавления новой подписки на ссылку.

    :param event: Событие Telethon с данными Telegram-сообщения.
    :param url: Ссылка, которую необходимо отслеживать.
    :param tags: Список тегов, которые пользователь указал для ссылки.
    :param filters: Список фильтров, применяемых к обновлениям по ссылке.
    :return: None
    :raises httpx.HTTPStatusError: В случае ошибки HTTP-запроса.
    """
    payload = AddLinkRequest(link=HttpUrl(url), tags=tags, filters=filters)
    headers = {"Tg-Chat-Id": str(event.chat_id)}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.scrapper_api_url}/links",
                json=payload.model_dump(mode="json"),
                headers=headers,
            )
            response.raise_for_status()
            await event.respond(f"Ссылка {url} добавлена для отслеживания.")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == httpx.codes.UNPROCESSABLE_ENTITY:
                await event.respond("Введён некорректный формат ссылки")
            else:
                await event.respond(
                    f"Ошибка при добавлении подписки: "
                    f"{e.response.json().get('exceptionMessage')!s}\n"
                    f"Для корректной работы данной команды необходимо сначала "
                    f"зарегистрировать чат с помощью команды /start.",
                )


async def msg_handler(event: NewMessage.Event) -> None:
    """Обрабатывает входящие сообщения, связанные c диалогом добавления подписки.

    B зависимости от состояния FSM:
      - Если состояние WAITING_FOR_TAGS: сообщение интерпретируется как список тегов, данные
        обновляются, состояние переводится в WAITING_FOR_FILTERS и запрашиваются фильтры.
      - Если состояние WAITING_FOR_FILTERS: сообщение интерпретируется как фильтры, после
        чего данные отправляются в сервис scrapper через HTTP-запрос для добавления подписки,
        и FSM сбрасывается.
      - Если состояние None: сообщение игнорируется.

    :param event: Событие Telegram c текстом сообщения.
    :return: None
    """
    if event.raw_text.startswith("/"):
        return

    key = await build_storage_key(event)
    memory_storage = MemoryStorage()
    current_state = await memory_storage.get_state(key)
    msg_to_start = (
        "Для корректной работы данной команды необходимо "
        "сначала зарегистрировать чат с помощью команды /start."
    )

    if current_state == State.WAITING_FOR_TAGS:
        tags = event.raw_text.split()
        data = await memory_storage.get_data(key) or {}
        if not data:
            await event.respond(msg_to_start)
            return
        data["tags"] = tags
        await memory_storage.set_data(key, data)
        await memory_storage.set_state(key, State.WAITING_FOR_FILTERS)
        await event.respond(
            "Введите фильтры (опционально, формат key:value, разделённые пробелами):",
        )
        return

    if current_state == State.WAITING_FOR_FILTERS:
        filters = event.raw_text.split()
        data = await memory_storage.get_data(key) or {}
        if not data:
            await event.respond(msg_to_start)
            return
        data["filters"] = filters
        await memory_storage.set_data(key, data)

        url = data.get("url")
        if not url:
            await event.respond(msg_to_start)
            return

        await _send_scrapper_request(event, url, data.get("tags", []), filters)
        await memory_storage.clear(key)
