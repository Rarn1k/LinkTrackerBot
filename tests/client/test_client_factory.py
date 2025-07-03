import pytest

from src.clients.client_factory import ClientFactory
from src.clients.github import GitHubClient
from src.clients.stack_overflow import StackOverflowClient


def test_create_github_client() -> None:
    """Проверяет, что создается GitHubClient при передаче 'github.com'."""
    client = ClientFactory.create_client("github.com")
    assert isinstance(client, GitHubClient)


def test_create_stackoverflow_client() -> None:
    """Проверяет, что создается StackOverflowClient при передаче 'stackoverflow.com'."""
    client = ClientFactory.create_client("stackoverflow.com")
    assert isinstance(client, StackOverflowClient)


def test_create_client_invalid_service() -> None:
    """Проверяет, что при передаче неподдерживаемого сервиса выбрасывается ValueError."""
    with pytest.raises(ValueError, match="Неизвестный сервис: unknown.com"):
        ClientFactory.create_client("unknown.com")
