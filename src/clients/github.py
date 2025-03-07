from datetime import datetime
from typing import Any, Optional

import httpx


class GitHubClient:
    """HTTP-клиент для обращения к GitHub API.

    Использует базовый URL, который можно задать при инициализации.
    Если базовый URL не указан, используется значение по умолчанию (https://api.github.com).

    Методы клиента выполняют запросы к GitHub API для получения обновлений репозитория,
    например, для проверки активности (новые коммиты, pull request'ы, и т.д.).
    """

    BASE_URL: str = "https://api.github.com"
    ACCEPT_HEADER: str = "application/vnd.github+json"

    def __init__(self, token: Optional[str] = None) -> None:
        """Инициализирует клиент c опциональным токеном авторизации.

        :param token: Токен доступа GitHub для аутентифицированных запросов.
                      Если указан, добавляется в заголовок Authorization.
        """
        self.headers = {"Accept": self.ACCEPT_HEADER}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    async def get_repo_events(self, owner: str, repo: str) -> Optional[Any]:  # noqa: ANN401
        """Получает список событий репозитория.

        Запрашивает данные через эндпоинт /repos/{owner}/{repo}/events.
        Возвращает список событий, таких как PushEvent, PullRequestEvent и т.д.

        :param owner: Имя владельца репозитория (например, "octocat").
        :param repo: Имя репозитория (например, "hello-world").
        :return: Список словарей c данными событий или None, если запрос неуспешен.
        :raises ValueError: Если репозиторий не найден (статус 404).
        :raises httpx.HTTPStatusError: Если сервер вернул другую ошибку (например, 403, 429).
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/events"
        async with httpx.AsyncClient(headers=self.headers) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == httpx.codes.NOT_FOUND:
                    raise ValueError(f"Репозиторий {owner}/{repo} не найден") from e
                return None

    async def check_updates(self, owner: str, repo: str, last_check: Optional[datetime]) -> bool:
        """Проверяет, были ли новые события в репозитории после последней проверки.

        Сравнивает время создания последнего события (created_at) c указанным временем проверки.

        :param owner: Имя владельца репозитория (например, "octocat").
        :param repo: Имя репозитория (например, "hello-world").
        :param last_check: Время последней проверки для сравнения.
        :return: True, если есть новые события после last_check, иначе False.
        """
        if last_check is None:
            return True
        events = await self.get_repo_events(owner, repo)
        if events and isinstance(events, list):
            latest_event = max(events, key=lambda e: e.get("created_at", "1970-01-01T00:00:00"))
            latest_event_date = datetime.fromisoformat(
                latest_event["created_at"].replace("Z", "+00:00"),
            )
            return latest_event_date > last_check
        return False
