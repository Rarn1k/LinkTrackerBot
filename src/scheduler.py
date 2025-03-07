import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import httpx

from src.api.scrapper_api.handlers import repo
from src.api.scrapper_api.models import LinkResponse
from src.clients.github import GitHubClient
from src.clients.stack_overflow import StackOverflowClient
from src.settings import settings

logger = logging.getLogger(__name__)
EXPECTED_PATH_PARTS: int = 2


async def notify_bot(chat_id: int, url: str, message: str) -> None:
    """Асинхронная функция для отправки уведомлений в бот через HTTP.

    :param chat_id: ID Telegram-чата для отправки уведомления.
    :param url: URL, связанный c уведомлением.
    :param message: Сообщение для отправки.
    :return: None
    """
    payload = {"id": 1, "url": url, "description": message, "tgChatIds": [chat_id]}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{settings.bot_api_url}/updates", json=payload)
            response.raise_for_status()
    except httpx.HTTPError:
        logger.exception("Не удалось отправить уведомление для чата %s", chat_id)
    else:
        logger.info("Уведомление отправлено для чата %s: %s", chat_id, message)


async def process_subscription(
    chat_id: int,
    sub: LinkResponse,
    gh_client: GitHubClient,
    so_client: StackOverflowClient,
) -> None:
    """Обрабатывает одну подписку: проверяет обновления и отправляет уведомление при необходимости.

    :param chat_id: Идентификатор чата.
    :param sub: Объект подписки c полями url, chat_id, last_updated.
    :param gh_client: Клиент для GitHub API.
    :param so_client: Клиент для StackOverflow API.
    :return: None
    """
    url = str(sub.url)
    parsed_url = urlparse(url)
    if "stackoverflow.com" in parsed_url.netloc:
        question_id = parsed_url.path.split("/")[-2] or "0"
        logger.info("Запрос на stackoverflow.com")
        updated = await so_client.check_updates(question_id, sub.last_updated)
        if updated:
            await notify_bot(chat_id, url, "Обновление на StackOverflow!")
            sub.last_updated = datetime.now(timezone.utc)
    elif "github.com" in parsed_url.netloc:
        path_parts = parsed_url.path.strip("/").split("/")
        if len(path_parts) >= EXPECTED_PATH_PARTS:
            owner, repo_name = path_parts[0], path_parts[1]
            logger.info(
                "Запрос на github.com",
            )
            updated = await gh_client.check_updates(owner, repo_name, sub.last_updated)
            if updated:
                await notify_bot(sub.chat_id, url, "Обновление на GitHub!")
                sub.last_updated = datetime.now(timezone.utc)
        else:
            logger.warning("Некорректный GitHub URL: %s", url)
    else:
        logger.warning("Неподдерживаемый URL: %s", url)


async def check_updates(chat_id: Optional[int] = None) -> None:
    """Планировщик, который каждые 60 секунд проверяет обновления по всем подпискам
    и отправляет уведомление через notify_bot, если обнаружены изменения.

    Для каждого URL:
      - Если это StackOverflow, использует StackOverflowClient.
      - Если это GitHub, использует GitHubClient.
    После проверки обновления записываются в поле last_updated.

    :return: None
    """
    gh_client = GitHubClient()
    so_client = StackOverflowClient()

    while True:
        logger.info("Начало просмотра обновлений")
        try:
            all_subs = await repo.get_links(chat_id)
            if not all_subs:
                logger.info("Подписки не найдены для chat_id: %s", chat_id)
                await asyncio.sleep(600)
                continue

            tasks = [process_subscription(chat_id, sub, gh_client, so_client) for sub in all_subs]
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception:
            logger.exception("Ошибка при получении подписок")

        await asyncio.sleep(600)
