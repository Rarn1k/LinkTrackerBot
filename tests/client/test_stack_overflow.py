from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from pytest_mock import MockerFixture

from src.clients.stack_overflow import StackOverflowClient

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_http_client_ok(mocker: MockerFixture) -> AsyncMock:
    """Фикстура для успешного HTTP-запроса."""
    mock_response = Mock()
    mock_response.status_code = httpx.codes.OK
    mock_response.json = Mock(
        return_value={
            "items": [{"question_id": 123, "last_activity_date": 1709470800}],  # 2024-03-03
        },
    )
    mock_response.raise_for_status = Mock()
    return mocker.patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(return_value=mock_response),
    )


@pytest.fixture
def mock_http_client_not_found(mocker: MockerFixture) -> AsyncMock:
    """Фикстура для запроса c ошибкой 400 (Bad Request)."""
    mock_response = Mock()
    mock_response.status_code = httpx.codes.BAD_REQUEST
    mock_response.raise_for_status = Mock(
        side_effect=httpx.HTTPStatusError(
            message="Bad Request",
            request=Mock(),
            response=mock_response,
        ),
    )
    return mocker.patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(return_value=mock_response),
    )


async def test_get_question_success(mock_http_client_ok: AsyncMock) -> None:
    """Успешное получение информации o вопросе."""
    question_id = "123"
    client = StackOverflowClient(api_key="test_key")

    question = await client.get_question(question_id)

    assert question == {"question_id": 123, "last_activity_date": 1709470800}
    mock_http_client_ok.assert_awaited_once_with(
        f"{client.BASE_URL}/questions/{question_id}",
        params={"site": "stackoverflow", "key": "test_key"},
    )


async def test_get_question_no_items(mocker: MockerFixture) -> None:
    """Запрос успешен, но items пустой."""
    question_id = "456"
    client = StackOverflowClient()

    mock_response = Mock()
    mock_response.status_code = httpx.codes.OK
    mock_response.json = Mock(return_value={"items": []})
    mock_response.raise_for_status = Mock()
    mock_get = mocker.patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(return_value=mock_response),
    )

    question = await client.get_question(question_id)

    assert question is None
    mock_get.assert_awaited_once_with(
        f"{client.BASE_URL}/questions/{question_id}",
        params={"site": "stackoverflow"},
    )


async def test_get_question_bad_request(mock_http_client_not_found: AsyncMock) -> None:
    """Ошибка запроса c кодом 400 (Bad Request)."""
    question_id = "invalid_id"
    client = StackOverflowClient()

    with pytest.raises(ValueError, match=f"Некорректный запрос для вопроса {question_id}"):
        await client.get_question(question_id)

    mock_http_client_not_found.assert_awaited_once_with(
        f"{client.BASE_URL}/questions/{question_id}",
        params={"site": "stackoverflow"},
    )


async def test_get_question_not_found(mocker: MockerFixture) -> None:
    """Запрос c кодом 404 возвращает None."""
    question_id = "789"
    client = StackOverflowClient()

    mock_response = Mock()
    mock_response.status_code = httpx.codes.NOT_FOUND
    mock_response.raise_for_status = Mock(
        side_effect=httpx.HTTPStatusError(
            message="Not Found",
            request=Mock(),
            response=mock_response,
        ),
    )
    mock_get = mocker.patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(return_value=mock_response),
    )

    question = await client.get_question(question_id)

    assert question is None
    mock_get.assert_awaited_once_with(
        f"{client.BASE_URL}/questions/{question_id}",
        params={"site": "stackoverflow"},
    )


async def test_check_updates_true(mock_http_client_ok: AsyncMock) -> None:
    """Есть обновления после последней проверки."""
    question_id = "123"
    last_check = datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc)  # 2024-03-01
    client = StackOverflowClient()

    has_updates = await client.check_updates(question_id, last_check)

    assert has_updates is True
    mock_http_client_ok.assert_awaited_once_with(
        f"{client.BASE_URL}/questions/{question_id}",
        params={"site": "stackoverflow"},
    )


async def test_check_updates_false(mocker: MockerFixture) -> None:
    """Нет обновлений после последней проверки."""
    question_id = "123"
    last_check = datetime(2024, 3, 4, 0, 0, 0, tzinfo=timezone.utc)  # 2024-03-04
    client = StackOverflowClient()

    mock_response = Mock()
    mock_response.status_code = httpx.codes.OK
    mock_response.json = Mock(
        return_value={
            "items": [{"question_id": 123, "last_activity_date": 1709470800}],  # 2024-03-03
        },
    )
    mock_response.raise_for_status = Mock()
    mock_get = mocker.patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(return_value=mock_response),
    )

    has_updates = await client.check_updates(question_id, last_check)

    assert has_updates is False  # last_activity_date: 2024-03-03 < last_check
    mock_get.assert_awaited_once_with(
        f"{client.BASE_URL}/questions/{question_id}",
        params={"site": "stackoverflow"},
    )


async def test_check_updates_no_question(mock_http_client_not_found: AsyncMock) -> None:
    """Вопрос не найден, обновлений нет."""
    question_id = "invalid_id"
    last_check = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    client = StackOverflowClient()

    with pytest.raises(ValueError, match=f"Некорректный запрос для вопроса {question_id}"):
        await client.check_updates(question_id, last_check)

    mock_http_client_not_found.assert_awaited_once_with(
        f"{client.BASE_URL}/questions/{question_id}",
        params={"site": "stackoverflow"},
    )
