from datetime import datetime, timezone

import pytest
from pydantic import HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.scrapper_api.models import AddLinkRequest, LinkResponse, RemoveLinkRequest
from src.db.orm_service.link_service import OrmLinkService
from src.db.orm_service.models.chat import Chat
from src.db.orm_service.models.link import Link

pytestmark = pytest.mark.asyncio


@pytest.fixture
def link_service() -> OrmLinkService:
    """Фикстура для создания экземпляра OrmLinkService."""
    return OrmLinkService()


@pytest.fixture
def sample_add_request() -> AddLinkRequest:
    """Фикстура для создания тестового запроса добавления ссылки."""
    return AddLinkRequest(
        link=HttpUrl("https://example.com"), tags=["tag1", "tag2"], filters=["filter1"],
    )


@pytest.fixture
def sample_remove_request() -> RemoveLinkRequest:
    """Фикстура для создания тестового запроса удаления ссылки."""
    return RemoveLinkRequest(link=HttpUrl("https://example.com"))


async def test_add_link_success(
    link_service: OrmLinkService,
    db_session: AsyncSession,
    sample_add_request: AddLinkRequest,
) -> None:
    """Проверяет успешное добавление новой ссылки."""
    chat_id = 123
    chat = Chat(id=chat_id)
    db_session.add(chat)
    await db_session.commit()

    response = await link_service.add_link(chat_id, sample_add_request, db_session)

    assert isinstance(response, LinkResponse)
    assert response.url == sample_add_request.link
    assert response.tags == sample_add_request.tags
    assert response.filters == sample_add_request.filters
    assert response.last_updated is not None

    link = await db_session.get(Link, response.id)
    assert link is not None
    assert link.chat_id == chat_id
    assert link.url == str(sample_add_request.link)


async def test_add_link_chat_not_found(
    link_service: OrmLinkService,
    db_session: AsyncSession,
    sample_add_request: AddLinkRequest,
) -> None:
    """Проверяет выброс KeyError, если чат не найден."""
    chat_id = 123

    with pytest.raises(KeyError, match=f"Чат с идентификатором {chat_id} не найден"):
        await link_service.add_link(chat_id, sample_add_request, db_session)


async def test_add_link_duplicate(
    link_service: OrmLinkService,
    db_session: AsyncSession,
    sample_add_request: AddLinkRequest,
) -> None:
    """Проверяет выброс ValueError при добавлении дублирующей ссылки."""
    chat_id = 123
    chat = Chat(id=chat_id)
    db_session.add(chat)
    link = Link(
        chat_id=chat_id,
        url=str(sample_add_request.link),
        last_updated=datetime.now(timezone.utc),
    )
    db_session.add(link)
    await db_session.commit()

    with pytest.raises(ValueError, match=f"Ссылка {sample_add_request.link} уже отслеживается"):
        await link_service.add_link(chat_id, sample_add_request, db_session)


async def test_remove_link_success(
    link_service: OrmLinkService,
    db_session: AsyncSession,
    sample_remove_request: RemoveLinkRequest,
) -> None:
    """Проверяет успешное удаление существующей ссылки."""
    chat_id = 123
    chat = Chat(id=chat_id)
    link = Link(
        chat_id=chat_id,
        url=str(sample_remove_request.link),
        last_updated=datetime.now(timezone.utc),
        tags=["tag1"],
        filters=["key1:value1", "key2:value2"],
    )
    db_session.add(chat)
    db_session.add(link)
    await db_session.commit()

    response = await link_service.remove_link(chat_id, sample_remove_request, db_session)

    assert isinstance(response, LinkResponse)
    assert response.url == sample_remove_request.link
    assert await db_session.get(Link, response.id) is None


async def test_remove_link_chat_not_found(
    link_service: OrmLinkService,
    db_session: AsyncSession,
    sample_remove_request: RemoveLinkRequest,
) -> None:
    """Проверяет выброс KeyError, если чат не найден."""
    chat_id = 123

    with pytest.raises(KeyError, match=f"Чат с идентификатором {chat_id} не найден"):
        await link_service.remove_link(chat_id, sample_remove_request, db_session)


async def test_remove_link_not_found(
    link_service: OrmLinkService,
    db_session: AsyncSession,
    sample_remove_request: RemoveLinkRequest,
) -> None:
    """Проверяет выброс KeyError, если ссылка не найдена."""
    chat_id = 123
    chat = Chat(id=chat_id)
    db_session.add(chat)
    await db_session.commit()

    with pytest.raises(KeyError, match=f"Ссылка {sample_remove_request.link} не найдена"):
        await link_service.remove_link(chat_id, sample_remove_request, db_session)


async def test_get_links_success(
    link_service: OrmLinkService,
    db_session: AsyncSession,
) -> None:
    """Проверяет успешное получение списка ссылок."""
    chat_id = 123
    chat = Chat(id=chat_id)
    n_links = 3
    links = [
        Link(
            chat_id=chat_id,
            url=f"https://example.com/{i}",
            last_updated=datetime.now(timezone.utc),
            tags=["tag1"],
            filters=["key1:value1", "key2:value2"],
        )
        for i in range(n_links)
    ]
    db_session.add(chat)
    for link in links:
        db_session.add(link)
    await db_session.commit()

    result = await link_service.get_links(chat_id, db_session)

    assert len(result) == n_links
    assert all(isinstance(link, LinkResponse) for link in result)
    assert [str(link.url) for link in result] == [link.url for link in links]


async def test_get_links_empty(
    link_service: OrmLinkService,
    db_session: AsyncSession,
) -> None:
    """Проверяет получение пустого списка, если ссылок нет."""
    chat_id = 123
    chat = Chat(id=chat_id)
    db_session.add(chat)
    await db_session.commit()

    result = await link_service.get_links(chat_id, db_session)
    assert result == []


async def test_get_links_negative_chat_id(
    link_service: OrmLinkService,
    db_session: AsyncSession,
) -> None:
    """Проверяет выброс ValueError при отрицательном chat_id."""
    chat_id = -1

    with pytest.raises(ValueError, match=f"Некорректный идентификатор чата: {chat_id}"):
        await link_service.get_links(chat_id, db_session)


async def test_set_last_updated_success(
    link_service: OrmLinkService,
    db_session: AsyncSession,
) -> None:
    """Проверяет успешное обновление last_updated."""
    chat_id = 123
    link_id = 1
    chat = Chat(id=chat_id)
    old_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
    new_date = datetime(2023, 1, 2, tzinfo=timezone.utc)
    link = Link(
        id=link_id,
        chat_id=chat_id,
        url="https://example.com",
        last_updated=old_date,
        tags=["tag1"],
        filters=["key1:value1", "key2:value2"],
    )
    db_session.add(chat)
    db_session.add(link)
    await db_session.commit()

    await link_service.set_last_updated(link_id, new_date, db_session)

    updated_link = await db_session.get(Link, link_id)
    assert updated_link is not None
    assert updated_link.last_updated == new_date


async def test_set_last_updated_not_found(
    link_service: OrmLinkService,
    db_session: AsyncSession,
) -> None:
    """Проверяет выброс KeyError, если подписка не найдена."""
    link_id = 1
    new_date = datetime(2023, 1, 2, tzinfo=timezone.utc)

    with pytest.raises(KeyError, match=f"Подписка с идентификатором {link_id} не найдена"):
        await link_service.set_last_updated(link_id, new_date, db_session)
