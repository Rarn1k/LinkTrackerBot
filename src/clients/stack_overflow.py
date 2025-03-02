from datetime import datetime, timezone
from typing import Dict, Optional

import httpx


class StackOverflowClient:
    """HTTP-клиент для обращения к StackOverflow API.

    Использует базовый URL, который можно задать при инициализации.
    Если базовый URL не указан, используется значение по умолчанию.

    Клиент предназначен для получения данных o вопросах, ответах или комментариях c
    помощью StackExchange API.
    """

    BASE_URL = "https://api.stackexchange.com/2.3"

    async def get_question(self, question_id: str) -> Optional[Dict]:
        """Получает информацию o вопросе по ID вопроса."""
        url = f"{self.BASE_URL}/questions/{question_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:  # type: ignore[attr-defined] # noqa: PLR2004
                data = response.json()
                if data.get("items"):
                    return data["items"][0]
            return None

    async def check_updates(self, question_id: str, last_check: datetime) -> bool:
        """Проверяет, были ли обновления после последней проверки."""
        question = await self.get_question(question_id)
        if question:
            last_activity_date = datetime.fromtimestamp(
                question["last_activity_date"],
                tz=timezone.utc,
            )
            return last_activity_date > last_check
        return False
