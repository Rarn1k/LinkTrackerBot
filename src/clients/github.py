import logging
from datetime import datetime
from typing import Any
from urllib.parse import ParseResult

import httpx

from src.api.bot_api.models import UpdateEvent
from src.clients.base_client import BaseClient
from src.clients.client_settings import ClientSettings, default_settings

logger = logging.getLogger(__name__)
EXPECTED_PATH_PARTS: int = 2


class GitHubClient(BaseClient):
    """HTTP-клиент для обращения к GitHub API.

    Использует базовый URL, который можно задать при инициализации.
    Если базовый URL не указан, используется значение по умолчанию (https://api.github.com).

    Методы клиента выполняют запросы к GitHub API для получения обновлений репозитория,
    например, для проверки активности (новые коммиты, pull request'ы, и т.д.).
    """

    def __init__(
        self,
        settings: ClientSettings = default_settings,
        token: str | None = None,
    ) -> None:
        """Инициализирует клиент c опциональным токеном авторизации.

        :param settings: Настройки c URL-адресами и тайм-аутами.
        :param token: Токен доступа GitHub для аутентифицированных запросов.
                      Если указан, добавляется в заголовок Authorization.
        """
        self.base_url = settings.github.api_url
        self.timeout = settings.client_timeout
        self.headers = {"Accept": settings.github.accept_header}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    async def get_repo_events(self, owner: str, repo: str) -> Any | None:  # noqa: ANN401
        """Получает список событий репозитория.

        Запрашивает данные через эндпоинт /repos/{owner}/{repo}/events.
        Возвращает список событий, таких как PushEvent, PullRequestEvent и т.д.

        :param owner: Имя владельца репозитория (например, "octocat").
        :param repo: Имя репозитория (например, "hello-world").
        :return: Список словарей c данными событий или None, если запрос неуспешен.
        :raises ValueError: Если репозиторий не найден (статус 404).
        :raises httpx.HTTPStatusError: Если сервер вернул другую ошибку (например, 403, 429).
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/events"
        async with httpx.AsyncClient(headers=self.headers) as client:
            try:
                response = await client.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Превышено время ожидания запроса к {url}") from e
            except httpx.HTTPStatusError as e:
                if e.response.status_code == httpx.codes.NOT_FOUND:
                    raise ValueError(f"Репозиторий {owner}/{repo} не найден") from e
                return None

    @staticmethod
    async def _parse_repo_path(parsed_url: ParseResult) -> tuple[str, str] | None:
        """Извлекает owner и repo из URL."""
        path_parts = parsed_url.path.strip("/").split("/")
        if len(path_parts) < EXPECTED_PATH_PARTS:
            logger.warning("Некорректный path в GitHub URL: %s", parsed_url.path)
            return None
        return path_parts[0], path_parts[1]

    @staticmethod
    async def _create_update_event(
        event: dict[str, Any],
        parsed_url: ParseResult,
    ) -> UpdateEvent | None:
        """Создаёт объект UpdateEvent из события GitHub."""
        event_type = event.get("type")
        payload = event.get("payload", {})
        created_at = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))

        event_mapping = {
            "PullRequestEvent": (f"Новый Pull Request в {parsed_url.geturl()}", "pull_request"),
            "IssuesEvent": (f"Новый Issue в {parsed_url.geturl()}", "issue"),
        }

        if event_type not in event_mapping:
            return None

        description, data_key = event_mapping[event_type]
        data = payload.get(data_key, {})

        return UpdateEvent(
            description=description,
            title=data.get("title", "Без названия"),
            username=data.get("user", {}).get("login", "Неизвестный пользователь"),
            created_at=created_at,
            preview=data.get("body", "Нет описания")[:200],
        )

    async def check_updates(
        self,
        parsed_url: ParseResult,
        last_check: datetime | None,
    ) -> UpdateEvent | None:
        if last_check is None:
            return None

        repo_info = await self._parse_repo_path(parsed_url)
        if not repo_info:
            return None

        owner, repo = repo_info
        events = await self.get_repo_events(owner, repo)
        if not events or not isinstance(events, list):
            return None

        for event in events:
            created_at = datetime.fromisoformat(event["created_at"])
            if created_at <= last_check:
                continue

            update = await self._create_update_event(event, parsed_url)
            if update:
                return update
        return None
