import asyncio
import logging
from datetime import datetime, timezone

import httpx

from src.api.scrapper_api.handlers import repo
from src.clients.github import GitHubClient
from src.clients.stack_overflow import StackOverflowClient
from src.settings import settings


async def notify_bot(chat_id: int, url: str, message: str) -> None:
    """Асинхронная функция для отправки уведомлений в бот через HTTP."""
    payload = {"id": 1, "url": url, "description": message, "tgChatIds": [chat_id]}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{settings.scrapper_api_url}/bot/updates", json=payload)
            response.raise_for_status()
    except httpx.HTTPError:
        logging.exception("Не удалось отправить уведомление: %s")
    else:
        logging.info("Уведомление отправлено для чата %s: %s", chat_id, message)


async def check_updates() -> None:
    """Планировщик, который каждые 60 секунд проверяет обновления по всем подпискам
    и отправляет уведомление через notify_bot, если обнаружены изменения.

    Для каждого URL:
      - Если это StackOverflow, использует StackOverflowClient.
      - Если это GitHub, использует GitHubClient.
    После проверки обновления записываются в поле last_updated.

    :return: None
    """
    while True:
        all_subs = await repo.get_links(362682717)
        for sub in all_subs:
            url = str(sub.url)
            if "stackoverflow.com" in url:
                question_id = url.split("/")[-1]
                so_client = StackOverflowClient()
                updated = await so_client.check_updates(question_id, sub.last_updated)
                if updated:
                    await notify_bot(sub.chat_id, url, "Обновление на StackOverflow!")
                sub.last_updated = datetime.now(timezone.utc)
            elif "github.com" in url:
                parts = url.split("/")
                owner, repo_name = parts[-2], parts[-1]
                gh_client = GitHubClient()
                updated = await gh_client.check_updates(owner, repo_name, sub.last_updated)
                if updated:
                    await notify_bot(sub.chat_id, url, "Обновление на GitHub!")
                sub.last_updated = datetime.now(timezone.utc)
        await asyncio.sleep(60)
