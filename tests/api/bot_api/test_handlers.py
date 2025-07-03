from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from src.settings import settings

pytestmark = pytest.mark.asyncio


async def test_send_update_success(mocker: MockerFixture, test_client: TestClient) -> None:
    """Успешная отправка обновления в чаты."""
    update_data: dict[str, Any] = {
        "id": 1,
        "url": "https://example.com/",
        "description": "Какое-то обновление",
        "tgChatIds": [123456789, 987654321],
    }
    mock_post = mocker.patch.object(
        httpx.AsyncClient,
        "post",
        new=AsyncMock(return_value=mocker.Mock(status_code=200, raise_for_status=lambda: None)),
    )

    response = test_client.post("/api/v1/bot/updates", json=update_data)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == update_data
    calls = mock_post.call_args_list
    assert mock_post.call_count == len(update_data["tgChatIds"])
    assert calls[0].kwargs["json"] == {
        "chat_id": 123456789,
        "text": "Обновление для https://example.com/: Какое-то обновление",
    }
    assert calls[1].kwargs["json"] == {
        "chat_id": 987654321,
        "text": "Обновление для https://example.com/: Какое-то обновление",
    }


async def test_send_update_invalid_id(test_client: TestClient) -> None:
    """Обработка ошибок для недействительных входных данных."""
    update_data = {
        "id": -1,
        "url": "https://example.com",
        "description": "Какое-то обновление",
        "tgChatIds": [123456789],
    }

    response = test_client.post("/api/v1/bot/updates", json=update_data)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {
        "description": "Некорректные параметры запроса",
        "code": "400",
        "exceptionName": "ValueError",
        "exceptionMessage": "Некорректный id обновления",
        "stacktrace": response.json()["stacktrace"],
    }
    assert isinstance(response.json()["stacktrace"], list)
    assert len(response.json()["stacktrace"]) > 0


async def test_send_digest_success(mocker: MockerFixture, test_client: TestClient) -> None:
    """Успешная отправка дайджеста в чат."""
    digest_data = {
        "id": 1,
        "description": "Дайджест обновлений",
        "tg_chat_id": 123456789,
        "updates": [
            "Обновление на https://example.com!",
            "Обновление на https://another.com!",
        ],
    }
    mock_post = mocker.patch.object(
        httpx.AsyncClient,
        "post",
        new=AsyncMock(return_value=mocker.Mock(status_code=200, raise_for_status=lambda: None)),
    )

    response = test_client.post("/api/v1/bot/digest", json=digest_data)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == digest_data
    mock_post.assert_called_once_with(
        f"{settings.tg_api_url}/bot{settings.token}/sendMessage",
        json={
            "chat_id": 123456789,
            "parse_mode": "Markdown",
            "text": "Дайджест обновлений\n"
            "Обновление на https://example.com!\n"
            "Обновление на https://another.com!",
        },
    )


async def test_send_digest_invalid_id(test_client: TestClient) -> None:
    """Обработка ошибок для недействительных входных данных."""
    digest_data = {
        "id": -1,
        "description": "Некорректный дайджест",
        "tg_chat_id": 123456789,
        "updates": ["Обновление на https://example.com!"],
    }

    response = test_client.post("/api/v1/bot/digest", json=digest_data)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {
        "description": "Некорректные параметры запроса",
        "code": "400",
        "exceptionName": "ValueError",
        "exceptionMessage": "Некорректный id обновления",
        "stacktrace": response.json()["stacktrace"],
    }
    assert isinstance(response.json()["stacktrace"], list)
    assert len(response.json()["stacktrace"]) > 0
