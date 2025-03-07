from http import HTTPStatus
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

pytestmark = pytest.mark.asyncio


async def test_send_update_success(mocker: MockerFixture, test_client: TestClient) -> None:
    """Успешная отправка обновления в чаты."""
    update_data = {
        "id": 1,
        "url": "https://example.com",
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
    assert response.json() == {
        "message": f"Обновление для {update_data['url']}/ обработано",
    }
    calls = mock_post.call_args_list
    assert len(calls) == len(update_data["tgChatIds"])
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
    assert response.json() == {"detail": "Некорректный id обновления"}
