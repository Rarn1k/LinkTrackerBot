from datetime import datetime
from typing import List, Optional

import httpx


class GitHubClient:
    """HTTP-клиент для обращения к GitHub API.

    Использует базовый URL, который можно задать при инициализации.
    Если базовый URL не указан, используется значение по умолчанию (https://api.github.com).

    Методы клиента выполняют запросы к GitHub API для получения обновлений репозитория,
    например, для проверки активности (новые коммиты, pull request'ы, и т.д.).
    """

    BASE_URL = "https://api.github.com"

    async def get_repo_events(self, owner: str, repo: str) -> Optional[List]:
        """Получает список событий репозитория."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/events"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:  # type: ignore[attr-defined] # noqa: PLR2004
                return response.json()
            return None

    async def check_updates(self, owner: str, repo: str, last_check: datetime) -> bool:
        """Проверяет, были ли новые события после последней проверки."""
        events = await self.get_repo_events(owner, repo)
        if events:
            latest_event_date = datetime.fromisoformat(
                events[0]["created_at"].replace("Z", "+00:00"),
            )
            return latest_event_date > last_check
        return False
