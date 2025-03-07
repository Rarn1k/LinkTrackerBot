import asyncio
import logging

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import HttpUrl

from src.api.bot_api.models import ApiErrorResponse, LinkUpdate
from src.settings import settings

router = APIRouter(tags=["Bot API"])


async def send_notification(
    client: httpx.AsyncClient,
    chat_id: int,
    url: HttpUrl,
    description: str,
) -> None:
    """Отправляет уведомление в конкретный Telegram-чат.

    :param client: HTTP-клиент для выполнения запроса.
    :param chat_id: ID Telegram-чата.
    :param url: Ссылка, для которой отправляется уведомление.
    :param description: Описание обновления.
    """
    token = settings.token
    telegram_api_url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": f"Обновление для {url}: {description}",
    }

    try:
        response = await client.post(telegram_api_url, json=payload)
        response.raise_for_status()
        logging.info("Уведомление отправлено в чат %s", chat_id)
    except httpx.HTTPError:
        logging.exception("Ошибка при отправке уведомления для чата %s", chat_id)


@router.post(
    "/updates",
    response_model=None,
    summary="Отправить обновление",
    responses={
        200: {"description": "Обновление обработано"},
        400: {
            "description": "Некорректные параметры запроса",
            "model": ApiErrorResponse,
        },
    },
)
async def send_update(update: LinkUpdate) -> dict:
    """Отправляет обновление (LinkUpdate) в указанные Telegram-чаты.

    :param update: Объект обновления, содержащий id, url, описание и список tgChatIds.
    :return: Сообщение o6 успешной обработке обновления.
    :raises HTTPException: Если параметры запроса некорректны.
    """
    if update.id <= 0:
        raise HTTPException(status_code=400, detail="Некорректный id обновления")

    logging.info("Получено обновление для ссылки: %s", update.url)

    async with httpx.AsyncClient() as client:
        await asyncio.gather(
            *(
                send_notification(client, chat_id, update.url, update.description)
                for chat_id in update.tgChatIds
            ),
        )

    return {"message": f"Обновление для {update.url} обработано"}
