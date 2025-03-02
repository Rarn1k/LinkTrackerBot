import httpx
from telethon.events import NewMessage

from src.bd.memory_storage.enum_states import State
from src.bd.memory_storage.key_builder import build_storage_key
from src.bd.memory_storage.memory import MemoryStorage
from src.settings import settings

__all__ = ("msg_handler",)


EXPECTED_TRACK_PARTS: int = 2


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

    if current_state == State.WAITING_FOR_TAGS:
        tags = event.raw_text.split()
        data = await memory_storage.get_data(key)
        data["tags"] = tags
        await memory_storage.set_data(key, data)
        await memory_storage.set_state(key, State.WAITING_FOR_FILTERS)
        await event.respond(
            "Введите фильтры (опционально, формат key:value, разделённые пробелами):",
        )

    elif current_state == State.WAITING_FOR_FILTERS:
        filters_input = event.raw_text.split()

        data = await memory_storage.get_data(key)
        data["filters"] = filters_input
        await memory_storage.set_data(key, data)

        url = data.get("url")
        tags = data.get("tags", [])

        payload = {
            "link": url,
            "tags": tags,
            "filters": filters_input,
        }
        headers = {"Tg-Chat-Id": str(event.chat_id)}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.scrapper_api_url}/links",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 422:  # type: ignore[attr-defined] # noqa: PLR2004
                    await event.respond("Введён некорректный формат ссылки")
                else:
                    await event.respond(
                        f"Ошибка при добавлении подписки: {e.response.json().get("detail")!s}.\n"
                        f"Для корректной работы данной команды необходимо сначала "
                        f"зарегистрировать чат с помощью команды /start.",
                    )
                return
        await event.respond(f"Ссылка {url} добавлена для отслеживания.")
        await memory_storage.clear(key)
