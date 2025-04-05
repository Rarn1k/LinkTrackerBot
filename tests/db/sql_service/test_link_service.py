from datetime import datetime, timezone

import asyncpg
import pytest
from pydantic import HttpUrl

from src.api.scrapper_api.models import AddLinkRequest, LinkResponse, RemoveLinkRequest
from src.db.sql_service.link_service import SqlLinkService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def link_service() -> SqlLinkService:
    """Фикстура для создания экземпляра SqlLinkService."""
    return SqlLinkService()


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
    link_service: SqlLinkService,
    db_pool: asyncpg.Pool,
    sample_add_request: AddLinkRequest,
) -> None:
    """Проверяет успешное добавление новой ссылки."""
    chat_id = 123

    async with db_pool.acquire() as conn:
        await conn.execute("INSERT INTO chats (id) VALUES ($1)", chat_id)

    response = await link_service.add_link(chat_id, sample_add_request, db_pool)

    assert isinstance(response, LinkResponse)
    assert response.url == sample_add_request.link
    assert response.tags == sample_add_request.tags
    assert response.filters == sample_add_request.filters
    assert response.last_updated is not None

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM links WHERE id = $1", response.id)
    assert row["chat_id"] == chat_id
    assert row["url"] == str(sample_add_request.link)


async def test_add_link_chat_not_found(
    link_service: SqlLinkService,
    db_pool: asyncpg.Pool,
    sample_add_request: AddLinkRequest,
) -> None:
    """Проверяет выброс KeyError, если чат не найден."""
    chat_id = 123

    with pytest.raises(KeyError, match=f"Чат с идентификатором {chat_id} не найден"):
        await link_service.add_link(chat_id, sample_add_request, db_pool)


async def test_add_link_duplicate(
    link_service: SqlLinkService,
    db_pool: asyncpg.Pool,
    sample_add_request: AddLinkRequest,
) -> None:
    """Проверяет выброс ValueError при добавлении дублирующей ссылки."""
    chat_id = 123

    async with db_pool.acquire() as conn:
        await conn.execute("INSERT INTO chats (id) VALUES ($1)", chat_id)
        await conn.execute(
            "INSERT INTO links (chat_id, url, last_updated) VALUES ($1, $2, $3)",
            chat_id,
            str(sample_add_request.link),
            datetime.now(timezone.utc),
        )

    with pytest.raises(ValueError, match="Ссылка уже отслеживается"):
        await link_service.add_link(chat_id, sample_add_request, db_pool)


async def test_remove_link_success(
    link_service: SqlLinkService,
    db_pool: asyncpg.Pool,
    sample_remove_request: RemoveLinkRequest,
) -> None:
    """Проверяет успешное удаление существующей ссылки."""
    chat_id = 123
    link_url = str(sample_remove_request.link)

    async with db_pool.acquire() as conn:
        await conn.execute("INSERT INTO chats (id) VALUES ($1)", chat_id)
        await conn.execute(
            "INSERT INTO links (chat_id, url, tags, filters, last_updated) "
            "VALUES ($1, $2, $3, $4, $5)",
            chat_id,
            link_url,
            ["tag1"],
            ["key1:value1"],
            datetime.now(timezone.utc),
        )

    response = await link_service.remove_link(chat_id, sample_remove_request, db_pool)

    assert isinstance(response, LinkResponse)
    assert str(response.url) == link_url

    async with db_pool.acquire() as conn:
        result = await conn.fetchval("SELECT COUNT(*) FROM links WHERE url = $1", link_url)
    assert result == 0


async def test_remove_link_chat_not_found(
    link_service: SqlLinkService,
    db_pool: asyncpg.Pool,
    sample_remove_request: RemoveLinkRequest,
) -> None:
    """Проверяет выброс KeyError, если чат не найден."""
    chat_id = 123

    with pytest.raises(KeyError, match=f"Чат с идентификатором {chat_id} не найден"):
        await link_service.remove_link(chat_id, sample_remove_request, db_pool)


async def test_remove_link_not_found(
    link_service: SqlLinkService,
    db_pool: asyncpg.Pool,
    sample_remove_request: RemoveLinkRequest,
) -> None:
    """Проверяет выброс KeyError, если ссылка не найдена."""
    chat_id = 123

    async with db_pool.acquire() as conn:
        await conn.execute("INSERT INTO chats (id) VALUES ($1)", chat_id)

    with pytest.raises(KeyError, match=f"Ссылка {sample_remove_request.link} не найдена"):
        await link_service.remove_link(chat_id, sample_remove_request, db_pool)


async def test_get_links_success(
    link_service: SqlLinkService,
    db_pool: asyncpg.Pool,
) -> None:
    """Проверяет успешное получение списка ссылок."""
    chat_id = 123
    n_links = 3
    links_data = [
        {
            "url": f"https://example.com/{i}",
            "tags": ["tag"],
            "filters": [],
            "last_updated": datetime.now(timezone.utc),
        }
        for i in range(n_links)
    ]

    async with db_pool.acquire() as conn:
        await conn.execute("INSERT INTO chats (id) VALUES ($1)", chat_id)
        for link in links_data:
            await conn.execute(
                "INSERT INTO links (chat_id, url, tags, filters, last_updated) "
                "VALUES ($1, $2, $3, $4, $5)",
                chat_id,
                link["url"],
                link["tags"],
                link["filters"],
                link["last_updated"],
            )

    result = await link_service.get_links(chat_id, db_pool)

    assert len(result) == n_links
    assert all(isinstance(link, LinkResponse) for link in result)
    assert [str(link.url) for link in result] == [link["url"] for link in links_data]


async def test_get_links_empty(
    link_service: SqlLinkService,
    db_pool: asyncpg.Pool,
) -> None:
    """Проверяет получение пустого списка, если ссылок нет."""
    chat_id = 123

    async with db_pool.acquire() as conn:
        await conn.execute("INSERT INTO chats (id) VALUES ($1)", chat_id)

    result = await link_service.get_links(chat_id, db_pool)
    assert result == []


async def test_get_links_negative_chat_id(
    link_service: SqlLinkService,
    db_pool: asyncpg.Pool,
) -> None:
    """Проверяет выброс ValueError при отрицательном chat_id."""
    chat_id = -1

    with pytest.raises(ValueError, match=f"Некорректный идентификатор чата: {chat_id}"):
        await link_service.get_links(chat_id, db_pool)


async def test_set_last_updated_success(
    link_service: SqlLinkService,
    db_pool: asyncpg.Pool,
) -> None:
    """Проверяет успешное обновление last_updated."""
    chat_id = 123
    link_id = 1
    old_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
    new_date = datetime(2023, 1, 2, tzinfo=timezone.utc)

    async with db_pool.acquire() as conn:
        await conn.execute("INSERT INTO chats (id) VALUES ($1)", chat_id)
        await conn.execute(
            "INSERT INTO links (id, chat_id, url, last_updated) VALUES ($1, $2, $3, $4)",
            link_id,
            chat_id,
            "https://example.com",
            old_date,
        )

    await link_service.set_last_updated(link_id, new_date, db_pool)

    async with db_pool.acquire() as conn:
        updated_date = await conn.fetchval("SELECT last_updated FROM links WHERE id = $1", link_id)
    assert updated_date == new_date


async def test_set_last_updated_not_found(
    link_service: SqlLinkService,
    db_pool: asyncpg.Pool,
) -> None:
    """Проверяет выброс KeyError, если подписка не найдена."""
    link_id = 1
    new_date = datetime(2023, 1, 2, tzinfo=timezone.utc)

    with pytest.raises(KeyError, match=f"Подписка с идентификатором {link_id} не найдена"):
        await link_service.set_last_updated(link_id, new_date, db_pool)
