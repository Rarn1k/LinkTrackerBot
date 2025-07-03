from datetime import datetime, timezone

from pydantic import HttpUrl
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.api.scrapper_api.models import AddLinkRequest, LinkResponse, RemoveLinkRequest
from src.db.base_service.link_service import BaseLinkService
from src.db.orm_service.models.chat import Chat
from src.db.orm_service.models.link import Link


class OrmLinkService(BaseLinkService):
    """Реализация работы c подписками через ORM."""

    async def add_link(
        self,
        chat_id: int,
        add_req: AddLinkRequest,
        dependency: AsyncSession,
    ) -> LinkResponse:
        """Добавляет новую подписку для заданного чата через ORM.

        :param chat_id: Идентификатор Telegram-чата.
        :param add_req: Объект запроса для добавления ссылки, содержащий:
                        - link: URL ссылки,
                        - tags: список тегов (опционально),
                        - filters: список фильтров (опционально).
        :param dependency: Асинхронная сессия SQLAlchemy.
        :return: Объект LinkResponse c данными добавленной подписки.
        :raises KeyError: Если чат c данным chat_id не найден.
        :raises ValueError: Если подписка c данным URL уже существует.
        """
        chat = await dependency.get(Chat, chat_id)
        if not chat:
            raise KeyError(f"Чат с идентификатором {chat_id} не найден.")

        stmt = select(Link).where(Link.chat_id == chat_id, Link.url == str(add_req.link))
        result = await dependency.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError(f"Ссылка {add_req.link} уже отслеживается.")

        new_sub = Link(
            chat_id=chat_id,
            url=str(add_req.link),
            tags=add_req.tags,
            filters=add_req.filters,
            last_updated=datetime.now(timezone.utc),
        )
        dependency.add(new_sub)
        await dependency.commit()
        await dependency.refresh(new_sub)

        return LinkResponse(
            id=new_sub.id,
            url=HttpUrl(new_sub.url),
            tags=new_sub.tags or [],
            filters=new_sub.filters or [],
            last_updated=new_sub.last_updated,
        )

    async def remove_link(
        self,
        chat_id: int,
        remove_req: RemoveLinkRequest,
        dependency: AsyncSession,
    ) -> LinkResponse:
        """Удаляет подписку для заданного чата через ORM.

        :param chat_id: Идентификатор Telegram-чата.
        :param remove_req: Объект запроса для удаления ссылки, содержащий URL.
        :param dependency: Асинхронная сессия SQLAlchemy.
        :return: Объект LinkResponse c данными удалённой подписки.
        :raises KeyError: Если чат или подписка c указанными данными не найдены.
        """
        chat = await dependency.get(Chat, chat_id)
        if not chat:
            raise KeyError(f"Чат с идентификатором {chat_id} не найден.")

        stmt = select(Link).where(Link.chat_id == chat_id, Link.url == str(remove_req.link))
        result = await dependency.execute(stmt)
        sub = result.scalar_one_or_none()

        if not sub:
            raise KeyError(f"Ссылка {remove_req.link} не найдена.")

        response = LinkResponse(
            id=sub.id,
            url=HttpUrl(sub.url),
            tags=sub.tags or [],
            filters=sub.filters or [],
            last_updated=sub.last_updated,
        )

        await dependency.delete(sub)
        await dependency.commit()

        return response

    async def get_links(
        self,
        chat_id: int,
        dependency: AsyncSession,
    ) -> list[LinkResponse]:
        """Возвращает список отслеживаемых ссылок для заданного чата.

        :param chat_id: Идентификатор Telegram-чата.
        :param dependency: Асинхронная сессия SQLAlchemy.
        :return: Список объектов LinkResponse.
        :raises ValueError: Если chat_id меньше нуля.
        """
        if chat_id < 0:
            raise ValueError(f"Некорректный идентификатор чата: {chat_id}. Должен быть >= 0.")

        stmt = select(Link).where(Link.chat_id == chat_id)
        result = await dependency.execute(stmt)
        return [
            LinkResponse(
                id=link.id,
                url=HttpUrl(link.url),
                tags=link.tags or [],
                filters=link.filters or [],
                last_updated=link.last_updated,
            )
            for link in result.scalars()
        ]

    async def set_last_updated(
        self,
        link_id: int,
        last_updated: datetime,
        dependency: AsyncSession,
    ) -> None:
        """Обновляет дату последнего изменения для подписки.

        :param link_id: Идентификатор подписки.
        :param last_updated: Новая дата последнего обновления.
        :param dependency: Асинхронная сессия SQLAlchemy.
        :raises KeyError: Если подписка не найдена.
        """
        stmt = update(Link).where(Link.id == link_id).values(last_updated=last_updated)
        result = await dependency.execute(stmt)

        if result.rowcount == 0:
            raise KeyError(f"Подписка с идентификатором {link_id} не найдена.")

        await dependency.commit()
        await dependency.refresh(await dependency.get(Link, link_id))
