import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from src.api.scrapper_api.handlers import repo
from src.api.scrapper_api.models import LinkResponse
from src.clients.client_factory import ClientFactory
from src.settings import settings

logger = logging.getLogger(__name__)


async def notify_bot(chat_id: int, updates_storage: dict[int, list[str]]) -> None:
    """Асинхронно отправляет уведомление c обновлениями в указанный Telegram-чат.

    :param chat_id: ID Telegram-чата, в который будет отправлено уведомление.
    :param updates_storage: Хранилище обновлений, где ключ — chat_id, a значение — список
    строк c сообщениями.
    :return: None
    """
    messages = updates_storage.get(chat_id, [])
    if not messages:
        return
    payload = {
        "id": 1,
        "description": "Полученные обновления: ",
        "tg_chat_id": chat_id,
        "updates": messages,
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{settings.bot_api_url}/digest", json=payload)
            response.raise_for_status()
    except httpx.HTTPError:
        logger.exception("Не удалось отправить уведомление для чата %s", chat_id)
    else:
        logger.info("Уведомление отправлено для чата %s", chat_id)


async def process_subscription(sub: LinkResponse) -> str | None:
    """Обрабатывает одну подписку и возвращает сообщение, если есть обновления.

    :param sub: Объект подписки c полями url, chat_id, last_updated.
    :return: Строка c сообщением o6 обновлении или None, если обновлений нет.
    """
    url = str(sub.url)
    parsed_url = urlparse(url)
    try:
        client = ClientFactory.create_client(service_name=parsed_url.netloc)
    except ValueError:
        logger.warning("Неподдерживаемый URL: %s", url)
        return None
    updated = await client.check_updates(parsed_url, sub.last_updated)
    if updated:
        sub.last_updated = datetime.now(timezone.utc)
        return f"Обновление на {url}!"
    return None


async def collect_updates(chat_id: int, updates_storage: dict[int, list[str]]) -> None:
    """Собирает обновления по всем подпискам указанного чата и сохраняет их в хранилище.

    :param chat_id: ID чата, для которого выполняется проверка подписок.
    :param updates_storage: Хранилище обновлений, где ключ — chat_id, a значение — список
    строк c сообщениями.
    :return: None
    """
    try:
        all_subs = await repo.get_links(chat_id)
        if not all_subs:
            logger.info("Подписки не найдены для chat_id: %s", chat_id)
            updates_storage[chat_id] = ["Подписки не найдены"]
            return

        tasks = [process_subscription(sub) for sub in all_subs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        new_messages = [msg for msg in results if isinstance(msg, str)]
        if not new_messages:
            updates_storage[chat_id] = ["Обновлений на отслеживаемых сайтах не найдены"]
            return
        updates_storage[chat_id].extend(new_messages)

    except Exception:
        logger.exception("Ошибка при получении подписок")


async def send_digest() -> None:
    """Периодически, в указанное время, собирает и отправляет обновления в Telegram-чаты.

    Цикл выполняется бесконечно и проверяет каждую минуту, настало ли уже указанное временя.
    B указанное время все найденные обновления отправляются в соответствующие Telegram-чаты.

    :return: None
    """
    updates_storage: dict[int, list[str]] = defaultdict(list)

    while True:
        logger.info("Начало просмотра обновлений")

        now = datetime.now(timezone.utc)
        if now.time().hour == settings.hour_digest and now.time().minute == settings.minute_digest:
            chat_ids = [chat_id for chat_id in list(repo.chats.keys()) if repo.chats[chat_id]]
            tasks = [collect_updates(chat_id, updates_storage) for chat_id in chat_ids]
            await asyncio.gather(*tasks)
            for chat_id in chat_ids:
                await notify_bot(chat_id, updates_storage)

        await asyncio.sleep(60)
