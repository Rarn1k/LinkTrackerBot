import httpx
from telethon.events import NewMessage

from src.bot.redis_cache import redis_cache
from src.settings import settings

__all__ = ("list_handler",)


async def list_handler(event: NewMessage.Event) -> None:
    """Обработчик команды /list для отображения списка отслеживаемых ссылок.

    Отправляет GET-запрос к scrapper-сервису для получения подписок пользователя. Если подписок нет,
    уведомляет o6 этом, иначе выводит список подписок в формате:
      URL, Тэги и Фильтры.

    :param event: Событие Telegram c данными o пользователе.
    :return: None
    """
    cached_links = await redis_cache.get_list_cache(event.chat_id)
    if cached_links is not None:
        if not cached_links:
            await event.respond("У вас нет активных подписок.")
        else:
            lines = []
            for link in cached_links:
                line = (
                    f"{link['url']}\nТэги: {' '.join(link.get('tags', []))}\n"
                    f"Фильтры: {' '.join(link.get('filters', []))}\n"
                )
                lines.append(line)
            await event.respond("Ваши подписки:\n" + "\n".join(lines))
        return

    headers = {"Tg-Chat-Id": str(event.chat_id)}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{settings.scrapper_api_url}/links", headers=headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            await event.respond(
                f"Ошибка при получении подписок: {e.response.json().get('exceptionMessage')!s}",
            )
            return

        data = response.json()
    await redis_cache.set_list_cache(event.chat_id, data.get("links", []))
    if data.get("size", 0) == 0:
        await event.respond("У вас нет активных подписок.")
    else:
        lines = []
        for link in data.get("links", []):
            line = (
                f"{link['url']}\nТэги: {' '.join(link.get('tags', []))}\n"
                f"Фильтры: {' '.join(link.get('filters', []))}\n"
            )
            lines.append(line)
        await event.respond("Ваши подписки:\n" + "\n".join(lines))
