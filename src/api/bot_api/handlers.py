import asyncio
import logging
import traceback

import httpx
from fastapi import APIRouter
from pydantic import HttpUrl
from starlette.responses import JSONResponse

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
    telegram_api_url = f"{settings.tg_api_url}/bot{settings.token}/sendMessage"

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
    response_model=LinkUpdate,
    summary="Отправить обновление",
    responses={
        200: {"description": "Обновление обработано"},
        400: {
            "description": "Некорректные параметры запроса",
            "model": ApiErrorResponse,
        },
    },
)
async def send_update(update: LinkUpdate) -> LinkUpdate | JSONResponse:
    """Отправляет обновление (LinkUpdate) в указанные Telegram-чаты.

    :param update: Объект обновления, содержащий id, url, описание и список tgChatIds.
    :return: Сообщение o6 успешной обработке обновления.
    :raises HTTPException: Если параметры запроса некорректны.
    """
    if update.id <= 0:
        error_response = ApiErrorResponse(
            description="Некорректные параметры запроса",
            code="400",
            exception_name="ValueError",
            exception_message="Некорректный id обновления",
            stacktrace=traceback.format_exc().split("\n"),
        )
        return JSONResponse(status_code=400, content=error_response.model_dump(by_alias=True))

    logging.info("Получено обновление для ссылки: %s", update.url)

    async with httpx.AsyncClient() as client:
        await asyncio.gather(
            *(
                send_notification(client, chat_id, update.url, update.description)
                for chat_id in update.tg_chat_ids
            ),
        )

    return update
