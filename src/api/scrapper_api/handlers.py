import traceback

import asyncpg
from fastapi import APIRouter, Depends, Header, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.bot_api.models import ApiErrorResponse
from src.api.scrapper_api.models import (
    AddLinkRequest,
    LinkResponse,
    ListLinksResponse,
    RemoveLinkRequest,
)
from src.db.db_manager.manager_factory import db_manager
from src.db.factory.data_access_factory import db_service

router = APIRouter(tags=["Scrapper API"])


@router.post(
    "/tg-chat/{tg_chat_id}",
    response_model=dict[str, str],
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
    dependency: asyncpg.Pool | AsyncSession = Depends(db_manager.get_dependency),
) -> dict[str, str] | JSONResponse:
    """Регистрирует чат по указанному ID.

    :param dependency: Зависимость для работы c базой данных (Pool или AsyncSession).
    :param tg_chat_id: Идентификатор чата (integer).
    :return: Сообщение o регистрации чата.
    """
    try:
        await db_service.chat_service.register_chat(tg_chat_id, dependency)
    except ValueError as e:
        error_response = ApiErrorResponse(
            description="Некорректные параметры запроса",
            code="400",
            exception_name=e.__class__.__name__,
            exception_message=str(e),
            stacktrace=traceback.format_exc().split("\n"),
        )
        return JSONResponse(status_code=400, content=error_response.model_dump(by_alias=True))
    return {"description": "Чат зарегистрирован"}


@router.delete(
    "/tg-chat/{tg_chat_id}",
    response_model=dict[str, str],
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
    dependency: asyncpg.Pool | AsyncSession = Depends(db_manager.get_dependency),
) -> dict[str, str] | JSONResponse:
    """Удаляет зарегистрированный чат по указанному ID.

    :param dependency: Зависимость для работы c базой данных (Pool или AsyncSession).
    :param tg_chat_id: Идентификатор чата.
    :return: Сообщение o6 успешном удалении чата.
    :raises HTTPException: Если чат не найден или параметры запроса некорректны.
    """
    try:
        await db_service.chat_service.delete_chat(tg_chat_id, dependency)
    except ValueError as e:
        error_response = ApiErrorResponse(
            description="Некорректные параметры запроса",
            code="400",
            exception_name=e.__class__.__name__,
            exception_message=str(e),
            stacktrace=traceback.format_exc().split("\n"),
        )
        return JSONResponse(status_code=400, content=error_response.model_dump(by_alias=True))
    except KeyError as e:
        error_response = ApiErrorResponse(
            description="Некорректные параметры запроса",
            code="404",
            exception_name=e.__class__.__name__,
            exception_message=str(e).strip("'"),
            stacktrace=traceback.format_exc().split("\n"),
        )
        return JSONResponse(status_code=404, content=error_response.model_dump(by_alias=True))
    return {"description": "Чат успешно удалён"}


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
    dependency: asyncpg.Pool | AsyncSession = Depends(db_manager.get_dependency),
) -> ListLinksResponse | JSONResponse:
    """Возвращает список отслеживаемых ссылок для чата.

    :param dependency: Зависимость для работы c базой данных (Pool или AsyncSession).
    :param tg_chat_id: Идентификатор Telegram-чата (передаётся в заголовке).
    :return: Объект ListLinksResponse co списком ссылок и их количеством.
    """
    try:
        links = await db_service.link_service.get_links(tg_chat_id, dependency)
    except ValueError as e:
        error_response = ApiErrorResponse(
            description="Некорректные параметры запроса",
            code="400",
            exception_name=e.__class__.__name__,
            exception_message=str(e),
            stacktrace=traceback.format_exc().split("\n"),
        )
        return JSONResponse(status_code=400, content=error_response.model_dump(by_alias=True))
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
    dependency: asyncpg.Pool | AsyncSession = Depends(db_manager.get_dependency),
) -> LinkResponse | JSONResponse:
    """Добавляет отслеживаемую ссылку для заданного чата.

    :param dependency: Зависимость для работы c базой данных (Pool или AsyncSession).
    :param add_link_req: Данные запроса для добавления ссылки.
    :param tg_chat_id: Идентификатор Telegram-чата (из заголовка).
    :return: Объект LinkResponse c данными добавленной ссылки.
    """
    try:
        new_link = await db_service.link_service.add_link(tg_chat_id, add_link_req, dependency)
    except (KeyError, ValueError) as e:
        error_response = ApiErrorResponse(
            description="Некорректные параметры запроса",
            code="400",
            exception_name=e.__class__.__name__,
            exception_message=str(e).strip("'"),
            stacktrace=traceback.format_exc().split("\n"),
        )
        return JSONResponse(status_code=400, content=error_response.model_dump(by_alias=True))
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
    dependency: asyncpg.Pool | AsyncSession = Depends(db_manager.get_dependency),
) -> LinkResponse | JSONResponse:
    """Убирает отслеживание ссылки для заданного чата.

    :param dependency: Зависимость для работы c базой данных (Pool или AsyncSession).
    :param remove_link_req: Данные запроса для удаления ссылки.
    :param tg_chat_id: Идентификатор Telegram-чата (из заголовка).
    :return: Объект LinkResponse c данными удалённой ссылки.
    :raises HTTPException: Если ссылка не найдена или параметры некорректны.
    """
    try:
        removed_link = await db_service.link_service.remove_link(
            tg_chat_id,
            remove_link_req,
            dependency,
        )
    except ValueError as e:
        error_response = ApiErrorResponse(
            description="Некорректные параметры запроса",
            code="400",
            exception_name=e.__class__.__name__,
            exception_message=str(e),
            stacktrace=traceback.format_exc().split("\n"),
        )
        return JSONResponse(status_code=400, content=error_response.model_dump(by_alias=True))
    except KeyError as e:
        error_response = ApiErrorResponse(
            description="Ссылка не найдена",
            code="404",
            exception_name=e.__class__.__name__,
            exception_message=str(e).strip("'"),
            stacktrace=traceback.format_exc().split("\n"),
        )
        return JSONResponse(status_code=404, content=error_response.model_dump(by_alias=True))
    return removed_link
