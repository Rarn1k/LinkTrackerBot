from http import HTTPStatus
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from src.bd.repository import Repository

pytestmark = pytest.mark.asyncio


async def test_register_chat_success(test_client: TestClient, mocker: MockerFixture) -> None:
    """Успешная регистрация чата."""
    tg_chat_id = 123456789
    mock_repo = mocker.patch.object(Repository, "register_chat", new_callable=AsyncMock)
    mock_repo.return_value = None

    response = test_client.post(f"/api/v1/scrapper/tg-chat/{tg_chat_id}")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"message": "Чат зарегистрирован"}
    mock_repo.assert_awaited_once_with(tg_chat_id)


async def test_register_chat_invalid_id(test_client: TestClient, mocker: MockerFixture) -> None:
    """Ошибка при некорректном ID чата."""
    tg_chat_id = -1
    mock_repo = mocker.patch.object(Repository, "register_chat", new_callable=AsyncMock)
    mock_repo.side_effect = ValueError(
        f"Некорректный идентификатор чата: {tg_chat_id}. Должен быть >= 0.",
    )

    response = test_client.post(f"/api/v1/scrapper/tg-chat/{tg_chat_id}")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": "Некорректные параметры запроса"}


async def test_delete_chat_success(test_client: TestClient, mocker: MockerFixture) -> None:
    """Успешное удаления чата."""
    tg_chat_id = 123456789
    mock_repo = mocker.patch.object(Repository, "delete_chat", new_callable=AsyncMock)
    mock_repo.return_value = None

    response = test_client.delete(f"/api/v1/scrapper/tg-chat/{tg_chat_id}")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"message": "Чат успешно удалён"}
    mock_repo.assert_awaited_once_with(tg_chat_id)


async def test_delete_chat_invalid_id(test_client: TestClient, mocker: MockerFixture) -> None:
    """Ошибка при некорректном ID чата."""
    tg_chat_id = -1
    mock_repo = mocker.patch.object(Repository, "delete_chat", new_callable=AsyncMock)
    mock_repo.side_effect = ValueError(
        f"Некорректный идентификатор чата: {tg_chat_id}. Должен быть >= 0.",
    )

    response = test_client.delete(f"/api/v1/scrapper/tg-chat/{tg_chat_id}")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": "Некорректные параметры запроса"}


async def test_delete_chat_not_found(test_client: TestClient, mocker: MockerFixture) -> None:
    """Ошибки, если чат не существует."""
    tg_chat_id = 999999999
    mock_repo = mocker.patch.object(Repository, "delete_chat", new_callable=AsyncMock)
    mock_repo.side_effect = KeyError(f"Чат с идентификатором {tg_chat_id} не найден.")

    response = test_client.delete(f"/api/v1/scrapper/tg-chat/{tg_chat_id}")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"detail": "Чат не существует"}


async def test_get_links_success(test_client: TestClient, mocker: MockerFixture) -> None:
    """Успешное получения списка ссылок."""
    tg_chat_id = 123456789
    mock_repo = mocker.patch.object(Repository, "get_links", new_callable=AsyncMock)
    mock_repo.return_value = []

    response = test_client.get("/api/v1/scrapper/links", headers={"Tg-Chat-Id": str(tg_chat_id)})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"links": [], "size": 0}
    mock_repo.assert_awaited_once_with(tg_chat_id)


async def test_get_links_invalid_header(test_client: TestClient, mocker: MockerFixture) -> None:
    """Ошибка при некорректном ID чата."""
    tg_chat_id = -1
    mock_repo = mocker.patch.object(Repository, "get_links", new_callable=AsyncMock)
    mock_repo.side_effect = ValueError(
        f"Некорректный идентификатор чата: {tg_chat_id}. Должен быть >= 0.",
    )

    response = test_client.get("/api/v1/scrapper/links", headers={"Tg-Chat-Id": str(tg_chat_id)})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "detail" in response.json()


async def test_add_link_success(test_client: TestClient, mocker: MockerFixture) -> None:
    """Успешного добавления ссылки."""
    tg_chat_id = 123456789
    link_data = {
        "id": 1,
        "link": "https://example.com",
        "tags": ["tag1"],
        "filters": ["filter1:value1"],
    }
    mock_repo = mocker.patch.object(Repository, "add_link", new_callable=AsyncMock)
    mock_repo.return_value = {
        "id": 1,
        "url": "https://example.com",
        "tags": ["tag1"],
        "filters": ["filter1:value1"],
    }

    response = test_client.post(
        "/api/v1/scrapper/links",
        json=link_data,
        headers={"Tg-Chat-Id": str(tg_chat_id)},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "id": 1,
        "url": "https://example.com/",
        "tags": ["tag1"],
        "filters": ["filter1:value1"],
        "last_updated": None,
    }


async def test_add_link_not_found(test_client: TestClient, mocker: MockerFixture) -> None:
    """Ошибка при добавлении ссылки к несуществующему чату."""
    tg_chat_id = 999999999
    link_data = {"link": "https://example.com", "tags": ["tag1"], "filters": ["filter1:value1"]}
    mock_repo = mocker.patch.object(Repository, "add_link", new_callable=AsyncMock)
    mock_repo.side_effect = KeyError(f"Чат с идентификатором {tg_chat_id} не найден.")

    response = test_client.post(
        "/api/v1/scrapper/links",
        json=link_data,
        headers={"Tg-Chat-Id": str(tg_chat_id)},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": "Некорректные параметры запроса"}


async def test_add_link_already_exists(test_client: TestClient, mocker: MockerFixture) -> None:
    """Ошибка, если ссылка уже добавлена."""
    tg_chat_id = 123456789
    link_data = {"link": "https://example.com"}
    mock_repo = mocker.patch.object(Repository, "add_link", new_callable=AsyncMock)
    mock_repo.side_effect = ValueError("Ссылка уже отслеживается")

    response = test_client.post(
        "/api/v1/scrapper/links",
        json=link_data,
        headers={"Tg-Chat-Id": str(tg_chat_id)},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": "Ссылка уже добавлена"}


async def test_remove_link_success(test_client: TestClient, mocker: MockerFixture) -> None:
    """Успешное удаления ссылки."""
    tg_chat_id = 123456789
    link_data = {"link": "https://example.com"}
    mock_repo = mocker.patch.object(Repository, "remove_link", new_callable=AsyncMock)
    mock_repo.return_value = {"id": 1, "url": "https://example.com", "tags": [], "filters": []}

    response = test_client.request(
        "DELETE",
        "/api/v1/scrapper/links",
        json=link_data,
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


async def test_remove_link_chat_not_found(test_client: TestClient, mocker: MockerFixture) -> None:
    """Ошибка, если чат не найден."""
    tg_chat_id = 123456789
    link_data = {"link": "https://example.com"}
    mock_repo = mocker.patch.object(Repository, "remove_link", new_callable=AsyncMock)
    mock_repo.side_effect = KeyError(f"Чат с идентификатором {tg_chat_id} не найден.")

    response = test_client.request(
        "DELETE",
        "/api/v1/scrapper/links",
        json=link_data,
        headers={"Tg-Chat-Id": str(tg_chat_id)},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": "Чат не найден"}


async def test_remove_link_not_found(test_client: TestClient, mocker: MockerFixture) -> None:
    """Ошибка, если ссылка не найдена."""
    tg_chat_id = 123456789
    link_data = {"link": "https://nonexistent.com"}
    mock_repo = mocker.patch.object(Repository, "remove_link", new_callable=AsyncMock)
    mock_repo.side_effect = ValueError(f"Ссылка {link_data['link']} не найдена.")

    response = test_client.request(
        "DELETE",
        "/api/v1/scrapper/links",
        json=link_data,
        headers={"Tg-Chat-Id": str(tg_chat_id)},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"detail": "Ссылка не найдена"}
