import logging

import httpx
from fastapi import APIRouter, HTTPException

from src.api.bot_api.models import ApiErrorResponse, LinkUpdate
from src.settings import settings

router = APIRouter(tags=["Bot API"])


@router.post(
    "/updates",
    response_model=dict,
    responses={
        200: {"description": "Обновление обработано"},
        400: {
            "description": "Некорректные параметры запроса",
            "content": {"application/json": {"model_json_schema": ApiErrorResponse.schema()}},
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
    token = settings.token
    telegram_api_url = f"https://api.telegram.org/bot{token}/sendMessage"

    async with httpx.AsyncClient() as client:
        for chat_id in update.tgChatIds:
            payload = {
                "chat_id": chat_id,
                "text": f"Обновление для {update.url}: {update.description}",
            }
            try:
                resp = await client.post(telegram_api_url, json=payload)
                resp.raise_for_status()
                logging.info("Уведомление отправлено для чата %s", chat_id)
            except httpx.HTTPError:
                logging.exception("Ошибка при отправке уведомления для чата %s", chat_id)

    return {"message": f"Обновление для {update.url} обработано и уведомления отправлены"}
