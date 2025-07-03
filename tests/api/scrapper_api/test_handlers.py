from datetime import datetime, timezone
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import HttpUrl
from pytest_mock import MockerFixture

from src.api.scrapper_api.models import AddLinkRequest, LinkResponse, RemoveLinkRequest
from src.db.factory.data_access_factory import db_service
from src.db.in_memory.repository import Repository
from src.settings import settings

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_chat_service(mocker: MockerFixture) -> MagicMock:
    """Фикстура для мокирования chat_service."""
    mock_service = mocker.patch.object(db_service, "chat_service", autospec=True)
    mock_service.register_chat = AsyncMock()
    return mock_service


@pytest.fixture
def mock_link_service(mocker: MockerFixture) -> MagicMock:
    """Фикстура для мокирования chat_service."""
    mock_service = mocker.patch.object(db_service, "link_service", autospec=True)
    mock_service.register_chat = AsyncMock()
    return mock_service


async def test_register_chat_success(
    test_client: TestClient,
    mock_chat_service: MagicMock,
    mocker: MockerFixture,
) -> None:
    """Успешная регистрация чата."""
    tg_chat_id = 123456789

    response = test_client.post(f"{settings.scrapper_api_url}/tg-chat/{tg_chat_id}")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"description": "Чат зарегистрирован"}
    mock_chat_service.register_chat.assert_awaited_once_with(tg_chat_id, mocker.ANY)


async def test_register_chat_invalid_id(test_client: TestClient, mocker: MockerFixture) -> None:
    """Ошибка при некорректном ID чата."""
    tg_chat_id = -1
    mock_repo = mocker.patch.object(Repository, "register_chat", new_callable=AsyncMock)
    mock_repo.side_effect = ValueError(
        f"Некорректный идентификатор чата: {tg_chat_id}. Должен быть >= 0.",
    )

    response = test_client.post(f"{settings.scrapper_api_url}/tg-chat/{tg_chat_id}")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {
        "description": "Некорректные параметры запроса",
        "code": "400",
        "exceptionName": "ValueError",
        "exceptionMessage": f"Некорректный идентификатор чата: {tg_chat_id}. Должен быть >= 0.",
        "stacktrace": response.json()["stacktrace"],
    }
    assert isinstance(response.json()["stacktrace"], list)
    assert len(response.json()["stacktrace"]) > 0


async def test_delete_chat_success(
    test_client: TestClient,
    mock_chat_service: MagicMock,
    mocker: MockerFixture,
) -> None:
    """Успешное удаления чата."""
    tg_chat_id = 123456789

    response = test_client.delete(f"{settings.scrapper_api_url}/tg-chat/{tg_chat_id}")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"description": "Чат успешно удалён"}
    mock_chat_service.delete_chat.assert_awaited_once_with(tg_chat_id, mocker.ANY)


async def test_delete_chat_invalid_id(test_client: TestClient, mocker: MockerFixture) -> None:
    """Ошибка при некорректном ID чата."""
    tg_chat_id = -1
    mock_repo = mocker.patch.object(Repository, "delete_chat", new_callable=AsyncMock)
    mock_repo.side_effect = ValueError(
        f"Некорректный идентификатор чата: {tg_chat_id}. Должен быть >= 0.",
    )

    response = test_client.delete(f"{settings.scrapper_api_url}/tg-chat/{tg_chat_id}")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {
        "description": "Некорректные параметры запроса",
        "code": "400",
        "exceptionName": "ValueError",
        "exceptionMessage": f"Некорректный идентификатор чата: {tg_chat_id}. Должен быть >= 0.",
        "stacktrace": response.json()["stacktrace"],
    }
    assert isinstance(response.json()["stacktrace"], list)
    assert len(response.json()["stacktrace"]) > 0


async def test_delete_chat_not_found(
    test_client: TestClient,
    mock_chat_service: MagicMock,
) -> None:
    """Ошибки, если чат не существует."""
    tg_chat_id = 999999999
    mock_chat_service.delete_chat.side_effect = KeyError(
        f"Чат с идентификатором {tg_chat_id} не найден.",
    )

    response = test_client.delete(f"{settings.scrapper_api_url}/tg-chat/{tg_chat_id}")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        "description": "Некорректные параметры запроса",
        "code": "404",
        "exceptionName": "KeyError",
        "exceptionMessage": f"Чат с идентификатором {tg_chat_id} не найден.",
        "stacktrace": response.json()["stacktrace"],
    }
    assert isinstance(response.json()["stacktrace"], list)
    assert len(response.json()["stacktrace"]) > 0


async def test_get_links_success(
    test_client: TestClient,
    mock_link_service: MagicMock,
    mocker: MockerFixture,
) -> None:
    """Успешное получения списка ссылок."""
    tg_chat_id = 123456789
    mock_link_service.return_value = []

    response = test_client.get(
        f"{settings.scrapper_api_url}/links",
        headers={"Tg-Chat-Id": str(tg_chat_id)},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"links": [], "size": 0}
    mock_link_service.get_links.assert_awaited_once_with(tg_chat_id, mocker.ANY)


async def test_get_links_invalid_header(
    test_client: TestClient,
    mock_link_service: MagicMock,
    mocker: MockerFixture,
) -> None:
    """Ошибка при некорректном ID чата."""
    tg_chat_id = -1
    mock_link_service.get_links.side_effect = ValueError(
        f"Некорректный идентификатор чата: {tg_chat_id}. Должен быть >= 0.",
    )

    response = test_client.get(
        f"{settings.scrapper_api_url}/links",
        headers={"Tg-Chat-Id": str(tg_chat_id)},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {
        "description": "Некорректные параметры запроса",
        "code": "400",
        "exceptionName": "ValueError",
        "exceptionMessage": "Некорректный идентификатор чата: -1. Должен быть >= 0.",
        "stacktrace": response.json()["stacktrace"],
    }
    assert isinstance(response.json()["stacktrace"], list)
    assert len(response.json()["stacktrace"]) > 0
    mock_link_service.get_links.assert_awaited_once_with(tg_chat_id, mocker.ANY)


async def test_add_link_success(
    test_client: TestClient,
    mock_link_service: MagicMock,
    mocker: MockerFixture,
) -> None:
    """Успешного добавления ссылки."""
    tg_chat_id = 123456789
    link_data = AddLinkRequest(
        link=HttpUrl("https://example.com"),
        tags=["tag1"],
        filters=["filter1:value1"],
    )
    mock_link_service.add_link.return_value = LinkResponse(
        id=1,
        url=HttpUrl("https://example.com"),
        tags=["tag1"],
        filters=["filter1:value1"],
        last_updated=datetime(2023, 10, 1, 12, 0, 0, tzinfo=timezone.utc),
    )

    response = test_client.post(
        f"{settings.scrapper_api_url}/links",
        json=link_data.model_dump(mode="json"),
        headers={"Tg-Chat-Id": str(tg_chat_id)},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "id": 1,
        "url": "https://example.com/",
        "tags": ["tag1"],
        "filters": ["filter1:value1"],
        "last_updated": "2023-10-01T12:00:00Z",
    }
    mock_link_service.add_link.assert_awaited_once_with(tg_chat_id, link_data, mocker.ANY)


async def test_add_link_not_found(
    test_client: TestClient,
    mock_link_service: MagicMock,
) -> None:
    """Ошибка при добавлении ссылки к несуществующему чату."""
    tg_chat_id = 999999999
    link_data = {"link": "https://example.com", "tags": ["tag1"], "filters": ["filter1:value1"]}
    mock_link_service.add_link.side_effect = KeyError(
        f"Чат с идентификатором {tg_chat_id} не найден.",
    )

    response = test_client.post(
        f"{settings.scrapper_api_url}/links",
        json=link_data,
        headers={"Tg-Chat-Id": str(tg_chat_id)},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {
        "description": "Некорректные параметры запроса",
        "code": "400",
        "exceptionName": "KeyError",
        "exceptionMessage": f"Чат с идентификатором {tg_chat_id} не найден.",
        "stacktrace": response.json()["stacktrace"],
    }
    assert isinstance(response.json()["stacktrace"], list)
    assert len(response.json()["stacktrace"]) > 0


async def test_add_link_already_exists(
    test_client: TestClient,
    mock_link_service: MagicMock,
) -> None:
    """Ошибка, если ссылка уже добавлена."""
    tg_chat_id = 123456789
    link_data = {"link": "https://example.com"}
    mock_link_service.add_link.side_effect = ValueError("Ссылка уже отслеживается")

    response = test_client.post(
        f"{settings.scrapper_api_url}/links",
        json=link_data,
        headers={"Tg-Chat-Id": str(tg_chat_id)},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {
        "description": "Некорректные параметры запроса",
        "code": "400",
        "exceptionName": "ValueError",
        "exceptionMessage": "Ссылка уже отслеживается",
        "stacktrace": response.json()["stacktrace"],
    }
    assert isinstance(response.json()["stacktrace"], list)
    assert len(response.json()["stacktrace"]) > 0


async def test_remove_link_success(
    test_client: TestClient,
    mock_link_service: MagicMock,
    mocker: MockerFixture,
) -> None:
    """Успешное удаления ссылки."""
    tg_chat_id = 123456789
    link_data = RemoveLinkRequest(link=HttpUrl("https://example.com"))
    mock_link_service.remove_link.return_value = {
        "id": 1,
        "url": "https://example.com",
        "tags": [],
        "filters": [],
    }

    response = test_client.request(
        "DELETE",
        f"{settings.scrapper_api_url}/links",
        json=link_data.model_dump(mode="json"),
        headers={"Tg-Chat-Id": str(tg_chat_id)},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "id": 1,
        "url": "https://example.com/",
        "tags": [],
        "filters": [],
        "last_updated": None,
    }
    mock_link_service.remove_link.assert_awaited_once_with(tg_chat_id, link_data, mocker.ANY)


async def test_remove_link_chat_not_found(
    test_client: TestClient,
    mock_link_service: MagicMock,
) -> None:
    """Ошибка, если чат не найден."""
    tg_chat_id = 123456789
    link_data = {"link": "https://example.com"}
    mock_link_service.remove_link.side_effect = ValueError(
        f"Чат с идентификатором {tg_chat_id} не найден.",
    )

    response = test_client.request(
        "DELETE",
        f"{settings.scrapper_api_url}/links",
        json=link_data,
        headers={"Tg-Chat-Id": str(tg_chat_id)},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {
        "description": "Некорректные параметры запроса",
        "code": "400",
        "exceptionName": "ValueError",
        "exceptionMessage": f"Чат с идентификатором {tg_chat_id} не найден.",
        "stacktrace": response.json()["stacktrace"],
    }
    assert isinstance(response.json()["stacktrace"], list)
    assert len(response.json()["stacktrace"]) > 0


async def test_remove_link_not_found(
    test_client: TestClient,
    mock_link_service: MagicMock,
) -> None:
    """Ошибка, если ссылка не найдена."""
    tg_chat_id = 123456789
    link_data = {"link": "https://nonexistent.com"}
    mock_link_service.remove_link.side_effect = KeyError(f"Ссылка {link_data['link']} не найдена.")

    response = test_client.request(
        "DELETE",
        f"{settings.scrapper_api_url}/links",
        json=link_data,
        headers={"Tg-Chat-Id": str(tg_chat_id)},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        "description": "Ссылка не найдена",
        "code": "404",
        "exceptionName": "KeyError",
        "exceptionMessage": f"Ссылка {link_data['link']} не найдена.",
        "stacktrace": response.json()["stacktrace"],
    }
    assert isinstance(response.json()["stacktrace"], list)
    assert len(response.json()["stacktrace"]) > 0
