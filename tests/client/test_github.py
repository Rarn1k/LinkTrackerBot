from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from urllib.parse import urlparse

import httpx
import pytest
from pytest_mock import MockerFixture

from src.api.bot_api.models import UpdateEvent
from src.clients.client_settings import ClientSettings
from src.clients.github import GitHubClient

pytestmark = pytest.mark.asyncio


@pytest.fixture
def settings() -> ClientSettings:
    """Фикстура для настроек клиентов."""
    return ClientSettings()


@pytest.fixture
def mock_http_client_ok(mocker: MockerFixture) -> AsyncMock:
    """Фикстура для успешного ответа HTTP-клиента."""
    mock_response = Mock()
    mock_response.status_code = httpx.codes.OK
    mock_response.json = Mock(
        return_value=[
            {
                "type": "PullRequestEvent",
                "created_at": "2024-01-02T12:00:00Z",
                "payload": {
                    "pull_request": {
                        "title": "New PR",
                        "user": {"login": "octocat"},
                        "body": "This is a pull request",
                    },
                },
            },
        ],
    )
    return mocker.patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(return_value=mock_response),
    )


@pytest.fixture
def mock_http_client_not_found(mocker: MockerFixture) -> AsyncMock:
    """Фикстура для ответа 404."""
    mock_response = Mock()
    mock_response.status_code = httpx.codes.NOT_FOUND
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="404 Error",
        request=Mock(),
        response=mock_response,
    )
    return mocker.patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(return_value=mock_response),
    )


async def test_get_repo_events_success(
    mock_http_client_ok: AsyncMock,
    settings: ClientSettings,
) -> None:
    """Успешное получение событий репозитория."""
    owner = "octocat"
    repo = "Hello-World"
    client = GitHubClient(settings)
    events = await client.get_repo_events(owner, repo)

    assert events == [
        {
            "type": "PullRequestEvent",
            "created_at": "2024-01-02T12:00:00Z",
            "payload": {
                "pull_request": {
                    "title": "New PR",
                    "user": {"login": "octocat"},
                    "body": "This is a pull request",
                },
            },
        },
    ]
    mock_http_client_ok.assert_awaited_once_with(
        f"{client.base_url}/repos/{owner}/{repo}/events",
        timeout=client.timeout,
    )


async def test_get_repo_events_timeout(mocker: MockerFixture, settings: ClientSettings) -> None:
    """Тестирует обработку таймаута при запросе списка событий репозитория."""
    owner = "octocat"
    repo = "Hello-World"
    client = GitHubClient(settings)

    mocker.patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(side_effect=httpx.TimeoutException("Timeout")),
    )

    with pytest.raises(
        TimeoutError,
        match=f"Превышено время ожидания запроса к {client.base_url}/repos/{owner}/{repo}/events",
    ):
        await client.get_repo_events(owner, repo)


async def test_get_repo_events_not_found(
    mock_http_client_not_found: AsyncMock,
    settings: ClientSettings,
) -> None:
    """Репозиторий не найден (статус 404)."""
    owner = "octocat"
    repo = "Non-Existent-Repo"
    client = GitHubClient(settings)
    _ = mock_http_client_not_found

    with pytest.raises(ValueError, match=f"Репозиторий {owner}/{repo} не найден"):
        await client.get_repo_events(owner, repo)


async def test_parse_repo_path_valid(settings: ClientSettings) -> None:
    """Проверяет корректный разбор URL."""
    client = GitHubClient(settings)
    parsed_url = urlparse("https://github.com/octocat/Hello-World")
    result = await client._parse_repo_path(parsed_url)  # noqa: SLF001
    assert result == ("octocat", "Hello-World")


async def test_parse_repo_path_invalid(settings: ClientSettings) -> None:
    """Проверяет возврат None при некорректном URL."""
    client = GitHubClient(settings)
    parsed_url = urlparse("https://github.com/octocat")
    result = await client._parse_repo_path(parsed_url)  # noqa: SLF001
    assert result is None


async def test_create_update_event_pull_request(settings: ClientSettings) -> None:
    """Проверяет создание UpdateEvent для PullRequestEvent."""
    client = GitHubClient(settings)
    event = {
        "type": "PullRequestEvent",
        "created_at": "2024-01-02T12:00:00Z",
        "payload": {
            "pull_request": {
                "title": "New PR",
                "user": {"login": "octocat"},
                "body": "This is a pull request",
            },
        },
    }
    parsed_url = urlparse("https://github.com/octocat/Hello-World")
    result = await client._create_update_event(event, parsed_url)  # noqa: SLF001

    assert result == UpdateEvent(
        description="Новый Pull Request в https://github.com/octocat/Hello-World",
        title="New PR",
        username="octocat",
        created_at=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
        preview="This is a pull request",
    )


async def test_create_update_event_issue(settings: ClientSettings) -> None:
    """Проверяет создание UpdateEvent для IssuesEvent."""
    client = GitHubClient(settings)
    event = {
        "type": "IssuesEvent",
        "created_at": "2024-01-02T12:00:00Z",
        "payload": {
            "issue": {
                "title": "New Issue",
                "user": {"login": "octocat"},
                "body": "This is an issue",
            },
        },
    }
    parsed_url = urlparse("https://github.com/octocat/Hello-World")
    result = await client._create_update_event(event, parsed_url)  # noqa: SLF001

    assert result == UpdateEvent(
        description="Новый Issue в https://github.com/octocat/Hello-World",
        title="New Issue",
        username="octocat",
        created_at=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
        preview="This is an issue",
    )


async def test_create_update_event_unsupported(settings: ClientSettings) -> None:
    """Проверяет возврат None для неподдерживаемого события."""
    client = GitHubClient(settings)
    event = {
        "type": "PushEvent",
        "created_at": "2024-01-02T12:00:00Z",
        "payload": {},
    }
    parsed_url = urlparse("https://github.com/octocat/Hello-World")
    result = await client._create_update_event(event, parsed_url)  # noqa: SLF001
    assert result is None


async def test_check_updates_true(mock_http_client_ok: AsyncMock, settings: ClientSettings) -> None:
    """Есть обновления после last_check."""
    parsed_url = urlparse("https://github.com/octocat/Hello-World")
    last_check = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    client = GitHubClient(settings)

    result = await client.check_updates(parsed_url, last_check)

    assert result == UpdateEvent(
        description="Новый Pull Request в https://github.com/octocat/Hello-World",
        title="New PR",
        username="octocat",
        created_at=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
        preview="This is a pull request",
    )
    mock_http_client_ok.assert_awaited_once_with(
        f"{client.base_url}/repos/octocat/Hello-World/events",
        timeout=client.timeout,
    )


async def test_check_updates_false(
    mock_http_client_ok: AsyncMock,
    settings: ClientSettings,
) -> None:
    """Нет обновлений после last_check."""
    parsed_url = urlparse("https://github.com/octocat/Hello-World")
    last_check = datetime(2024, 3, 2, 0, 0, 0, tzinfo=timezone.utc)
    client = GitHubClient(settings)

    result = await client.check_updates(parsed_url, last_check)

    assert result is None
    mock_http_client_ok.assert_awaited_once_with(
        f"{client.base_url}/repos/octocat/Hello-World/events",
        timeout=client.timeout,
    )


async def test_check_updates_timeout(mocker: MockerFixture, settings: ClientSettings) -> None:
    """Тестирует обработку таймаута в check_updates."""
    parsed_url = urlparse("https://github.com/octocat/Hello-World")
    last_check = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    client = GitHubClient(settings)

    mocker.patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(side_effect=httpx.TimeoutException("Timeout")),
    )

    with pytest.raises(
        TimeoutError,
        match=f"Превышено время ожидания запроса к "
        f"{client.base_url}/repos/octocat/Hello-World/events",
    ):
        await client.check_updates(parsed_url, last_check)


async def test_check_updates_empty_events(mocker: MockerFixture, settings: ClientSettings) -> None:
    """Пустой список событий."""
    parsed_url = urlparse("https://github.com/octocat/Hello-World")
    last_check = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    client = GitHubClient(settings)

    mock_response = Mock()
    mock_response.status_code = httpx.codes.OK
    mock_response.json = Mock(return_value=[])
    mock_get = mocker.patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(return_value=mock_response),
    )

    result = await client.check_updates(parsed_url, last_check)

    assert result is None
    mock_get.assert_awaited_once_with(
        f"{client.base_url}/repos/octocat/Hello-World/events",
        timeout=client.timeout,
    )


async def test_check_updates_invalid_url(settings: ClientSettings) -> None:
    """Некорректный URL."""
    parsed_url = urlparse("https://github.com/octocat")
    last_check = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    client = GitHubClient(settings)

    result = await client.check_updates(parsed_url, last_check)

    assert result is None
