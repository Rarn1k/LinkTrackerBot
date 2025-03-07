from fastapi import APIRouter, Header, HTTPException, Path

from src.api.bot_api.models import ApiErrorResponse
from src.api.scrapper_api.models import (
    AddLinkRequest,
    LinkResponse,
    ListLinksResponse,
    RemoveLinkRequest,
)
from src.bd.repository import Repository

router = APIRouter(tags=["Scrapper API"])

repo = Repository()


@router.post(
    "/tg-chat/{tg_chat_id}",
    response_model=None,
    summary="Зарегистрировать чат",
    responses={
        200: {"description": "Чат зарегистрирован"},
        400: {
            "description": "Некорректные параметры запроса",
            "model": ApiErrorResponse,
        },
    },
)
async def register_chat_endpoint(
    tg_chat_id: int = Path(..., title="ID чата", examples=[123456789]),
) -> dict[str, str]:
    """Регистрирует чат по указанному ID.

    :param tg_chat_id: Идентификатор чата (integer).
    :return: Сообщение o регистрации чата.
    """
    try:
        await repo.register_chat(tg_chat_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Некорректные параметры запроса") from e
    return {"message": "Чат зарегистрирован"}


@router.delete(
    "/tg-chat/{tg_chat_id}",
    response_model=None,
    summary="Удалить чат",
    responses={
        200: {"description": "Чат успешно удалён"},
        400: {
            "description": "Некорректные параметры запроса",
            "model": ApiErrorResponse,
        },
        404: {
            "description": "Чат не существует",
            "model": ApiErrorResponse,
        },
    },
)
async def delete_chat_endpoint(
    tg_chat_id: int = Path(..., title="ID чата", examples=[123456789]),
) -> dict[str, str]:
    """Удаляет зарегистрированный чат по указанному ID.

    :param tg_chat_id: Идентификатор чата.
    :return: Сообщение o6 успешном удалении чата.
    :raises HTTPException: Если чат не найден или параметры запроса некорректны.
    """
    try:
        await repo.delete_chat(tg_chat_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Некорректные параметры запроса") from e
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Чат не существует") from e
    return {"message": "Чат успешно удалён"}


@router.get(
    "/links",
    response_model=ListLinksResponse,
    summary="Получить все отслеживаемые ссылки",
    responses={
        200: {
            "description": "Ссылки успешно получены",
            "model": ListLinksResponse,
        },
        400: {
            "description": "Некорректные параметры запроса",
            "model": ApiErrorResponse,
        },
    },
)
async def get_links_endpoint(
    tg_chat_id: int = Header(..., alias="Tg-Chat-Id"),
) -> ListLinksResponse:
    """Возвращает список отслеживаемых ссылок для чата.

    :param tg_chat_id: Идентификатор Telegram-чата (передаётся в заголовке).
    :return: Объект ListLinksResponse co списком ссылок и их количеством.
    """
    try:
        links = await repo.get_links(tg_chat_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Некорректные параметры запроса") from e
    return ListLinksResponse(links=links, size=len(links))


@router.post(
    "/links",
    response_model=LinkResponse,
    summary="Добавить отслеживание ссылки",
    responses={
        200: {
            "description": "Ссылка успешно добавлена",
            "model": LinkResponse,
        },
        400: {
            "description": "Некорректные параметры запроса",
            "model": ApiErrorResponse,
        },
    },
)
async def add_link_endpoint(
    add_link_req: AddLinkRequest,
    tg_chat_id: int = Header(..., alias="Tg-Chat-Id", examples=[123456789]),
) -> LinkResponse:
    """Добавляет отслеживаемую ссылку для заданного чата.

    :param add_link_req: Данные запроса для добавления ссылки.
    :param tg_chat_id: Идентификатор Telegram-чата (из заголовка).
    :return: Объект LinkResponse c данными добавленной ссылки.
    """
    try:
        new_link = await repo.add_link(tg_chat_id, add_link_req)
    except KeyError as e:
        raise HTTPException(status_code=400, detail="Некорректные параметры запроса") from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Ссылка уже добавлена") from e
    return new_link


@router.delete(
    "/links",
    response_model=LinkResponse,
    summary="Убрать отслеживание ссылки",
    responses={
        200: {
            "description": "Ссылка успешно убрана",
            "model": LinkResponse,
        },
        400: {
            "description": "Некорректные параметры запроса",
            "model": ApiErrorResponse,
        },
        404: {
            "description": "Ссылка не найдена",
            "model": ApiErrorResponse,
        },
    },
)
async def remove_link_endpoint(
    remove_link_req: RemoveLinkRequest,
    tg_chat_id: int = Header(..., alias="Tg-Chat-Id"),
) -> LinkResponse:
    """Убирает отслеживание ссылки для заданного чата.

    :param remove_link_req: Данные запроса для удаления ссылки.
    :param tg_chat_id: Идентификатор Telegram-чата (из заголовка).
    :return: Объект LinkResponse c данными удалённой ссылки.
    :raises HTTPException: Если ссылка не найдена или параметры некорректны.
    """
    try:
        removed_link = await repo.remove_link(tg_chat_id, remove_link_req)
    except KeyError as e:
        raise HTTPException(status_code=400, detail="Чат не найден") from e
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Ссылка не найдена") from e
    return removed_link
