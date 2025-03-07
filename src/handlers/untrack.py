import json

import httpx
from telethon.events import NewMessage

__all__ = ("untrack_handler",)

from src.settings import settings

EXPECTED_TRACK_PARTS: int = 2


async def untrack_handler(event: NewMessage.Event) -> None:
    """Обработчик команды /untrack для прекращения отслеживания ссылки.

    Если формат команды корректный (два элемента: команда и URL), отправляет HTTP-запрос
    в scrapper-сервис, который удаляет подписку. Если подписка не найдена, уведомляет пользователя.

    :param event: Событие Telegram c текстом команды.
    :return: None
    """
    message_text = event.message.message
    parts = message_text.split()

    if len(parts) != EXPECTED_TRACK_PARTS:
        await event.respond(
            "Сообщение для прекращения отслеживания ссылки должно иметь вид "
            "'/untrack <ваша ссылка>', например:\n/untrack https://example.com",
        )
        return

    url = parts[1].strip()
    headers = {"Tg-Chat-Id": str(event.chat_id)}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                "DELETE",
                f"{settings.scrapper_api_url}/links",
                content=json.dumps({"link": url}),
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == httpx.codes.UNPROCESSABLE_ENTITY:
                await event.respond("Введён некорректный формат ссылки")
            else:
                await event.respond(
                    f"Ошибка при удалении подписки: {e.response.json().get('detail')!s}",
                )
            return
    await event.respond(f"Ссылка {url} удалена из отслеживаемых.")
