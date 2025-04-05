from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from urllib.parse import urlparse

import httpx
import pytest
from pytest_mock import MockerFixture

from src.api.bot_api.models import UpdateEvent
from src.clients.client_settings import ClientSettings
from src.clients.stack_overflow import StackOverflowClient

pytestmark = pytest.mark.asyncio


@pytest.fixture
def settings() -> ClientSettings:
    """Фикстура для настроек клиентов."""
    return ClientSettings()


@pytest.fixture
def stackoverflow_client(settings: ClientSettings) -> StackOverflowClient:
    """Фикстура для создания StackOverflowClient."""
    return StackOverflowClient(settings=settings)


@pytest.fixture
def mock_http_client_ok(mocker: MockerFixture) -> AsyncMock:
    """Фикстура для успешного HTTP-запроса."""
    mock_response = Mock()
    mock_response.status_code = httpx.codes.OK
    mock_response.json = Mock(
        return_value={
            "items": [
                {
                    "question_id": 123,
                    "title": "Test Question",
                    "last_activity_date": 1709470800,  # 2024-03-03 13:00:00 UTC
                    "answers": [
                        {
                            "body": "This is an answer",
                            "creation_date": 1709470800,
                            "owner": {"display_name": "test_user"},
                        },
                    ],
                },
            ],
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


async def test_get_question_success(
    mock_http_client_ok: AsyncMock,
    stackoverflow_client: StackOverflowClient,
) -> None:
    """Успешное получение информации o вопросе."""
    question_id = "123"
    question = await stackoverflow_client.get_question(question_id)

    assert question == {
        "question_id": 123,
        "title": "Test Question",
        "last_activity_date": 1709470800,
        "answers": [
            {
                "body": "This is an answer",
                "creation_date": 1709470800,
                "owner": {"display_name": "test_user"},
            },
        ],
    }
    mock_http_client_ok.assert_awaited_once_with(
        f"{stackoverflow_client.base_url}/questions/{question_id}",
        params={"site": stackoverflow_client.site},
        timeout=stackoverflow_client.timeout,
    )


async def test_get_question_no_items(
    mocker: MockerFixture,
    stackoverflow_client: StackOverflowClient,
) -> None:
    """Запрос успешен, но items пустой."""
    question_id = "456"
    mock_response = Mock()
    mock_response.status_code = httpx.codes.OK
    mock_response.json = Mock(return_value={"items": []})
    mock_response.raise_for_status = Mock()
    mock_get = mocker.patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(return_value=mock_response),
    )

    question = await stackoverflow_client.get_question(question_id)

    assert question is None
    mock_get.assert_awaited_once_with(
        f"{stackoverflow_client.base_url}/questions/{question_id}",
        params={"site": stackoverflow_client.site},
        timeout=stackoverflow_client.timeout,
    )


async def test_get_question_bad_request(
    mock_http_client_not_found: AsyncMock,
    stackoverflow_client: StackOverflowClient,
) -> None:
    """Ошибка запроса c кодом 400 (Bad Request)."""
    question_id = "invalid_id"
    with pytest.raises(ValueError, match=f"Некорректный запрос для вопроса {question_id}"):
        await stackoverflow_client.get_question(question_id)

    mock_http_client_not_found.assert_awaited_once_with(
        f"{stackoverflow_client.base_url}/questions/{question_id}",
        params={"site": stackoverflow_client.site},
        timeout=stackoverflow_client.timeout,
    )


async def test_get_question_not_found(
    mocker: MockerFixture,
    stackoverflow_client: StackOverflowClient,
) -> None:
    """Запрос c кодом 404 возвращает None."""
    question_id = "789"
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

    question = await stackoverflow_client.get_question(question_id)

    assert question is None
    mock_get.assert_awaited_once_with(
        f"{stackoverflow_client.base_url}/questions/{question_id}",
        params={"site": stackoverflow_client.site},
        timeout=stackoverflow_client.timeout,
    )


async def test_parse_question_id_valid(stackoverflow_client: StackOverflowClient) -> None:
    """Проверяет корректный разбор URL."""
    parsed_url = urlparse("https://stackoverflow.com/questions/123/test-question")
    result = await stackoverflow_client._parse_question_id(parsed_url)  # noqa: SLF001
    assert result == "123"


async def test_parse_question_id_invalid(stackoverflow_client: StackOverflowClient) -> None:
    """Проверяет возврат None при некорректном URL."""
    parsed_url = urlparse("https://stackoverflow.com/questions")
    result = await stackoverflow_client._parse_question_id(parsed_url)  # noqa: SLF001
    assert result is None


async def test_create_update_event_with_answer(stackoverflow_client: StackOverflowClient) -> None:
    """Проверяет создание UpdateEvent c ответом."""
    question = {
        "title": "Test Question",
        "answers": [
            {
                "body": "This is an answer",
                "creation_date": 1709470800,
                "owner": {"display_name": "test_user"},
            },
        ],
    }
    parsed_url = urlparse("https://stackoverflow.com/questions/123/test-question")
    last_activity_date = datetime(2024, 3, 3, 13, 0, 0, tzinfo=timezone.utc)
    result = await stackoverflow_client._create_update_event(  # noqa: SLF001
        question,
        parsed_url,
        last_activity_date,
    )

    assert result == UpdateEvent(
        description="Новый ответ на https://stackoverflow.com/questions/123/test-question",
        title="Test Question",
        username="test_user",
        created_at=last_activity_date,
        preview="This is an answer",
    )


async def test_create_update_event_with_comment(stackoverflow_client: StackOverflowClient) -> None:
    """Проверяет создание UpdateEvent c комментарием."""
    question = {
        "title": "Test Question",
        "comments": [
            {
                "body": "This is a comment",
                "creation_date": 1709470800,
                "owner": {"display_name": "commenter"},
            },
        ],
    }
    parsed_url = urlparse("https://stackoverflow.com/questions/123/test-question")
    last_activity_date = datetime(2024, 3, 3, 13, 0, 0, tzinfo=timezone.utc)
    result = await stackoverflow_client._create_update_event(  # noqa: SLF001
        question,
        parsed_url,
        last_activity_date,
    )

    assert result == UpdateEvent(
        description="Новый комментарий на https://stackoverflow.com/questions/123/test-question",
        title="Test Question",
        username="commenter",
        created_at=last_activity_date,
        preview="This is a comment",
    )


async def test_create_update_event_no_content(stackoverflow_client: StackOverflowClient) -> None:
    """Проверяет создание UpdateEvent без ответов и комментариев."""
    question = {"title": "Test Question"}
    last_activity_date = datetime(2024, 3, 3, 13, 0, 0, tzinfo=timezone.utc)
    parsed_url = urlparse("https://stackoverflow.com/questions/123/test-question")
    result = await stackoverflow_client._create_update_event(  # noqa: SLF001
        question,
        parsed_url,
        last_activity_date,
    )

    assert result is None


async def test_check_updates_true(
    mock_http_client_ok: AsyncMock,
    stackoverflow_client: StackOverflowClient,
) -> None:
    """Есть обновления после последней проверки."""
    parsed_url = urlparse("https://stackoverflow.com/questions/123/test-question")
    last_check = datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc)  # 2024-03-01
    result = await stackoverflow_client.check_updates(parsed_url, last_check)

    assert result == UpdateEvent(
        description="Новый ответ на https://stackoverflow.com/questions/123/test-question",
        title="Test Question",
        username="test_user",
        created_at=datetime(2024, 3, 3, 13, 0, 0, tzinfo=timezone.utc),
        preview="This is an answer",
    )
    mock_http_client_ok.assert_awaited_once_with(
        f"{stackoverflow_client.base_url}/questions/123",
        params={"site": stackoverflow_client.site},
        timeout=stackoverflow_client.timeout,
    )


async def test_check_updates_false(
    mock_http_client_ok: AsyncMock,
    stackoverflow_client: StackOverflowClient,
) -> None:
    """Нет обновлений после последней проверки."""
    parsed_url = urlparse("https://stackoverflow.com/questions/123/test-question")
    last_check = datetime(2024, 3, 4, 0, 0, 0, tzinfo=timezone.utc)  # 2024-03-04
    result = await stackoverflow_client.check_updates(parsed_url, last_check)

    assert result is None
    mock_http_client_ok.assert_awaited_once_with(
        f"{stackoverflow_client.base_url}/questions/123",
        params={"site": stackoverflow_client.site},
        timeout=stackoverflow_client.timeout,
    )


async def test_check_updates_no_question(
    mock_http_client_not_found: AsyncMock,
    stackoverflow_client: StackOverflowClient,
) -> None:
    """Вопрос не найден, выбрасывается исключение."""
    parsed_url = urlparse("https://stackoverflow.com/questions/invalid_id/test-question")
    last_check = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="Некорректный запрос для вопроса invalid_id"):
        await stackoverflow_client.check_updates(parsed_url, last_check)

    mock_http_client_not_found.assert_awaited_once_with(
        f"{stackoverflow_client.base_url}/questions/invalid_id",
        params={"site": stackoverflow_client.site},
        timeout=stackoverflow_client.timeout,
    )


async def test_check_updates_invalid_url(stackoverflow_client: StackOverflowClient) -> None:
    """Некорректный URL возвращает None."""
    parsed_url = urlparse("https://stackoverflow.com/questions")
    last_check = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    result = await stackoverflow_client.check_updates(parsed_url, last_check)

    assert result is None


async def test_check_updates_no_last_check(stackoverflow_client: StackOverflowClient) -> None:
    """Отсутствие last_check возвращает None."""
    parsed_url = urlparse("https://stackoverflow.com/questions/123/test-question")
    result = await stackoverflow_client.check_updates(parsed_url, None)

    assert result is None
