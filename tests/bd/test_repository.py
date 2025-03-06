import pytest

from src.api.scrapper_api.models import LinkResponse, AddLinkRequest, RemoveLinkRequest
from src.bd.repository import Repository

pytestmark = pytest.mark.asyncio


@pytest.fixture
def repository() -> Repository:
    """Фикстура для создания чистого экземпляра Repository."""
    repo = Repository()
    yield repo
    repo.chats = {}
    repo.links = {}


@pytest.mark.parametrize(
    ("chats", "links", "expected_chats_after", "expected_links_after"),
    [
        ({}, {}, {123: True}, {123: []}),
        (
            {123: True},
            {123: [LinkResponse(id=1, url="https://example.com", tags=[], filters=[])]},
            {123: True},
            {123: [LinkResponse(id=1, url="https://example.com", tags=[], filters=[])]},
        ),
        (
            {123: False},
            {123: [LinkResponse(id=1, url="https://example.com", tags=[], filters=[])]},
            {123: True},
            {123: [LinkResponse(id=1, url="https://example.com", tags=[], filters=[])]},
        ),
        ({1: True}, {1: []}, {1: True, 123: True}, {1: [], 123: []}),
    ],
    ids=["first_chat", "existing_chat_true", "existing_chat_false", "new_chat"],
)
async def test_register_chat_success(
    repository: Repository,
    chats: dict[int, bool],
    links,
    expected_chats_after: dict[int, bool],
    expected_links_after,
) -> None:
    """Проверяет регистрацию чата."""
    repository.chats = chats
    repository.links = links

    await repository.register_chat(123)

    assert repository.chats == expected_chats_after
    assert repository.links == expected_links_after


async def test_register_chat_invalid_id(repository: Repository) -> None:
    """Проверяет, что регистрация с некорректным ID выбрасывает ValueError."""
    with pytest.raises(ValueError, match="Некорректный идентификатор чата: -123. Должен быть >= 0."):
        await repository.register_chat(-123)
    assert repository.chats == {}


@pytest.mark.parametrize(
    ("chats", "links", "expected_chats_after", "expected_links_after"),
    [
        ({123: True}, {123: []}, {}, {}),
        (
            {1: True, 123: True},
            {1: [], 123: [LinkResponse(id=1, url="https://example.com", tags=[], filters=[])]},
            {1: True},
            {1: []},
        ),
    ],
    ids=["chat_without_links", "chat_with_links"],
)
async def test_delete_chat(
    repository: Repository,
    chats: dict[int, bool],
    links: dict[int, list[LinkResponse]],
    expected_chats_after: dict[int, bool],
    expected_links_after: dict[int, list[LinkResponse]],
) -> None:
    """Проверяет удаление чата и связанных с ним ссылок."""
    repository.chats = chats
    repository.links = links
    await repository.delete_chat(123)
    assert repository.chats == expected_chats_after
    assert repository.links == expected_links_after


async def test_delete_chat_invalid_id(repository: Repository) -> None:
    """Проверяет, что удаление чата с некорректным ID выбрасывает ValueError."""
    repository.chats = {123: True}
    with pytest.raises(ValueError, match="Некорректный идентификатор чата: -123. Должен быть >= 0."):
        await repository.delete_chat(-123)
    assert repository.chats == {123: True}


async def test_delete_chat_nonexistent(repository: Repository) -> None:
    """Проверяет, что удаление несуществующего чата выбрасывает KeyError."""
    repository.chats = {1: True}
    with pytest.raises(KeyError, match="Чат с идентификатором 123 не найден."):
        await repository.delete_chat(123)
    assert repository.chats == {1: True}


@pytest.mark.parametrize(
    ("chats", "links", "add_req", "expected_links_after"),
    [
        (
            {123: True},
            {},
            AddLinkRequest(link="https://example.com", tags=[], filters=[]),
            {
                123: [
                    LinkResponse(
                        id=1, url="https://example.com", tags=[], filters=[], last_updated=None
                    )
                ]
            },
        ),
        (
            {123: True},
            {
                123: [
                    LinkResponse(
                        id=1,
                        url="https://another.com",
                        tags=["tag"],
                        filters=["filter"],
                        last_updated=None,
                    )
                ]
            },
            AddLinkRequest(link="https://example.com", tags=["new"], filters=["new_filter"]),
            {
                123: [
                    LinkResponse(
                        id=1,
                        url="https://another.com",
                        tags=["tag"],
                        filters=["filter"],
                        last_updated=None,
                    ),
                    LinkResponse(
                        id=2,
                        url="https://example.com",
                        tags=["new"],
                        filters=["new_filter"],
                        last_updated=None,
                    ),
                ]
            },
        ),
    ],
    ids=["first_link", "additional_link"],
)
async def test_add_link_success(
    repository: Repository,
    chats: dict[int, bool],
    links: dict[int, list[LinkResponse]],
    add_req: AddLinkRequest,
    expected_links_after: dict[int, list[LinkResponse]],
) -> None:
    """Проверяет успешное добавление ссылки для чата."""
    repository.chats = chats
    repository.links = links

    result = await repository.add_link(123, add_req)

    assert isinstance(result, LinkResponse)
    assert repository.links == expected_links_after


async def test_add_link_unregistered_chat(repository: Repository) -> None:
    """Проверяет, что добавление ссылки для незарегистрированного чата выбрасывает KeyError."""
    add_req = AddLinkRequest(link="https://example.com", tags=[], filters=[])

    with pytest.raises(KeyError, match="Чат с идентификатором 123 не найден."):
        await repository.add_link(123, add_req)
    assert repository.links == {}


async def test_add_link_duplicate(repository: Repository) -> None:
    """Проверяет, что добавление уже существующей ссылки выбрасывает ValueError."""
    repository.chats = {123: True}
    repository.links = {
        123: [LinkResponse(id=1, url="https://example.com", tags=[], filters=[], last_updated=None)]
    }
    add_req = AddLinkRequest(link="https://example.com", tags=["new"], filters=["new_filter"])

    with pytest.raises(ValueError, match="Ссылка уже отслеживается"):
        await repository.add_link(123, add_req)
    assert repository.links == {
        123: [LinkResponse(id=1, url="https://example.com", tags=[], filters=[], last_updated=None)]
    }


@pytest.mark.parametrize(
    ("chats", "links", "remove_req", "expected_links_after"),
    [
        (
            {123: True},
            {
                123: [
                    LinkResponse(
                        id=1, url="https://example.com", tags=[], filters=[], last_updated=None
                    )
                ]
            },
            RemoveLinkRequest(link="https://example.com"),
            {123: []},
        ),
        (
            {123: True},
            {
                123: [
                    LinkResponse(
                        id=1,
                        url="https://example.com",
                        tags=["tag"],
                        filters=["filter"],
                        last_updated=None,
                    ),
                    LinkResponse(id=2, url="https://another.com", tags=[], filters=[]),
                ]
            },
            RemoveLinkRequest(link="https://example.com"),
            {
                123: [
                    LinkResponse(
                        id=2, url="https://another.com", tags=[], filters=[], last_updated=None
                    )
                ]
            },
        ),
    ],
    ids=["single_link", "multiple_links"],
)
async def test_remove_link_success(
    repository: Repository,
    chats: dict[int, bool],
    links: dict[int, list[LinkResponse]],
    remove_req: RemoveLinkRequest,
    expected_links_after: dict[int, list[LinkResponse]],
) -> None:
    """Проверяет успешное удаление ссылки для чата."""
    repository.chats = chats
    repository.links = links

    result = await repository.remove_link(123, remove_req)

    assert isinstance(result, LinkResponse)
    assert repository.links == expected_links_after


async def test_remove_link_unregistered_chat(repository: Repository) -> None:
    """Проверяет, что удаление ссылки для незарегистрированного чата выбрасывает KeyError."""
    remove_req = RemoveLinkRequest(link="https://example.com")

    with pytest.raises(KeyError, match="Чат с идентификатором 123 не найден."):
        await repository.remove_link(123, remove_req)
    assert repository.links == {}


async def test_remove_link_nonexistent(repository: Repository) -> None:
    """Проверяет, что удаление несуществующей ссылки выбрасывает ValueError."""
    repository.chats = {123: True}
    repository.links = {123: []}
    remove_req = RemoveLinkRequest(link="https://example.com/")

    with pytest.raises(ValueError, match="Ссылка https://example.com/ не найдена."):
        await repository.remove_link(123, remove_req)
    assert repository.links == {123: []}


@pytest.mark.parametrize(
    ("chats", "links", "expected_result"),
    [
        ({123: True}, {123: []}, []),
        (
            {123: True},
            {
                123: [
                    LinkResponse(
                        id=1, url="https://example.com", tags=[], filters=[], last_updated=None
                    )
                ]
            },
            [LinkResponse(id=1, url="https://example.com", tags=[], filters=[], last_updated=None)],
        ),
        (
                {123: True},
                {
                    123: [
                        LinkResponse(
                            id=1, url="https://example.com", tags=[], filters=[], last_updated=None
                        ),
                        LinkResponse(
                            id=1, url="https://another.com", tags=[], filters=[], last_updated=None
                        )
                    ]
                },
                [
                    LinkResponse(
                        id=1, url="https://example.com", tags=[], filters=[], last_updated=None
                    ),
                    LinkResponse(
                        id=1, url="https://another.com", tags=[], filters=[], last_updated=None
                    )
                ],
        ),
        (
            {1: True},
            {
                1: [
                    LinkResponse(
                        id=1,
                        url="https://example.com",
                        tags=["tag"],
                        filters=["filter"],
                        last_updated=None,
                    )
                ]
            },
            [],
        ),
    ],
    ids=["no_links", "existing_link", "few_links", "other_chat"],
)
async def test_get_links_success(
    repository: Repository,
    chats: dict[int, bool],
    links: dict[int, list[LinkResponse]],
    expected_result: list[LinkResponse],
) -> None:
    """Проверяет успешное получение списка ссылок для чата."""
    repository.chats = chats
    repository.links = links

    result = await repository.get_links(123)

    assert result == expected_result


async def test_get_links_invalid_id(repository: Repository) -> None:
    """Проверяет, что получение ссылок с некорректным ID выбрасывает ValueError."""
    with pytest.raises(ValueError, match="Некорректный идентификатор чата: -123. Должен быть >= 0."):
        await repository.get_links(-123)
    assert repository.links == {}
