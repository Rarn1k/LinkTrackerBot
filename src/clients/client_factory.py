from typing import ClassVar, Type

from src.clients.base_client import BaseClient
from src.clients.github import GitHubClient
from src.clients.stack_overflow import StackOverflowClient


class ClientFactory:
    """Фабрика для создания клиентских объектов по названию сервиса."""

    _clients: ClassVar[dict[str, Type[BaseClient]]] = {
        "github.com": GitHubClient,
        "stackoverflow.com": StackOverflowClient,
    }

    @classmethod
    def create_client(cls, service_name: str) -> BaseClient:
        """Создаёт и возвращает клиент для указанного сервиса.

        :param service_name: Название сервиса (например, 'github.com' или 'stackoverflow.com').
        :return: Экземпляр класса, реализующего интерфейс `BaseClient`.
        :raises ValueError: Если указанный сервис не поддерживается.
        """
        if service_name not in cls._clients:
            raise ValueError(f"Неизвестный сервис: {service_name}")
        return cls._clients[service_name]()
