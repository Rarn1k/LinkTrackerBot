from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from pytest_mock import MockerFixture

from src.clients.client_settings import ClientSettings
from src.clients.github import GitHubClient

pytestmark = pytest.mark.asyncio


@pytest.fixture
def settings() -> ClientSettings:
    """Фикстура для настроек клиентов."""
    return ClientSettings()


@pytest.fixture
def mock_http_client_ok(mocker: MockerFixture) -> AsyncMock:
    mock_response = Mock()
    mock_response.status_code = httpx.codes.OK
    mock_response.json = Mock(return_value=[{"id": "123", "created_at": "2024-03-01T12:00:00Z"}])
    return mocker.patch.object(
        httpx.AsyncClient,
        "get",
        new=AsyncMock(return_value=mock_response),
    )


@pytest.fixture
def mock_http_client_not_found(mocker: MockerFixture) -> AsyncMock:
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
    """Успешное получения событий репозитория."""
    owner = "octocat"
    repo = "Hello-World"

    client = GitHubClient(settings)
    events = await client.get_repo_events(owner, repo)

    assert events == [{"id": "123", "created_at": "2024-03-01T12:00:00Z"}]
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


async def test_check_updates_true(mock_http_client_ok: AsyncMock, settings: ClientSettings) -> None:
    """Ecть обновления после last_check."""
    owner = "octocat"
    repo = "Hello-World"
    last_check = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    client = GitHubClient(settings)

    has_updates = await client.check_updates(owner, repo, last_check)

    assert has_updates is True
    mock_http_client_ok.assert_awaited_once_with(
        f"{client.base_url}/repos/{owner}/{repo}/events",
        timeout=client.timeout,
    )


async def test_check_updates_false(
    mock_http_client_ok: AsyncMock,
    settings: ClientSettings,
) -> None:
    """Нет обновлений после last_check."""
    owner = "octocat"
    repo = "Hello-World"
    last_check = datetime(2024, 3, 2, 0, 0, 0, tzinfo=timezone.utc)
    client = GitHubClient(settings)

    has_updates = await client.check_updates(owner, repo, last_check)

    assert has_updates is False
    mock_http_client_ok.assert_awaited_once_with(
        f"{client.base_url}/repos/{owner}/{repo}/events",
        timeout=client.timeout,
    )


async def test_check_updates_no_events(mocker: MockerFixture, settings: ClientSettings) -> None:
    """Ошибке запроса."""
    owner = "octocat"
    repo = "Hello-World"
    last_check = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
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
        await client.check_updates(owner, repo, last_check)


async def test_check_updates_empty_events(mocker: MockerFixture, settings: ClientSettings) -> None:
    """Пустой спискок событий."""
    owner = "octocat"
    repo = "Hello-World"
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

    has_updates = await client.check_updates(owner, repo, last_check)

    assert has_updates is False
    mock_get.assert_awaited_once_with(
        f"{client.base_url}/repos/{owner}/{repo}/events",
        timeout=client.timeout,
    )
