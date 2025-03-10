from datetime import datetime, timezone
from typing import Any

import httpx


class StackOverflowClient:
    """HTTP-клиент для обращения к StackOverflow API.

    Использует базовый URL, который можно задать при инициализации.
    Если базовый URL не указан, используется значение по умолчанию.

    Клиент предназначен для получения данных o вопросах, ответах или комментариях c
    помощью StackExchange API.
    """

    BASE_URL = "https://api.stackexchange.com/2.3"
    DEFAULT_SITE = "stackoverflow"

    def __init__(
        self, base_url: str = BASE_URL, api_key: str | None = None, site: str = DEFAULT_SITE,
    ) -> None:
        """Инициализирует клиент c опциональным API-ключом и сайтом.

        :param api_key: Ключ API для увеличения лимита запросов.
        :param site: Сайт StackExchange (по умолчанию 'stackoverflow').
        """
        self.base_url = base_url
        self.api_key = api_key
        self.site = site

    async def get_question(self, question_id: str) -> Any:  # noqa: ANN401
        """Получает информацию o вопросе по ID.

        :param question_id: ID вопроса на StackOverflow.
        :return: Словарь c данными вопроса или None, если запрос неуспешен.
        :raises httpx.HTTPStatusError: Если сервер вернул ошибку (например, 400, 403).
        """
        url = f"{self.base_url}/questions/{question_id}"
        params = {"site": self.site}
        if self.api_key:
            params["key"] = self.api_key

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                if data is None or not data.get("items"):
                    return None
                return data["items"][0]

            except httpx.HTTPStatusError as e:
                if e.response.status_code == httpx.codes.BAD_REQUEST:
                    raise ValueError(f"Некорректный запрос для вопроса {question_id}") from e
                return None

    async def check_updates(self, question_id: str, last_check: datetime | None) -> bool:
        """Проверяет, были ли обновления вопроса после последней проверки.

        :param question_id: ID вопроса на StackOverflow.
        :param last_check: Время последней проверки.
        :return: True, если есть обновления, иначе False.
        """
        if last_check is None:
            return True
        question = await self.get_question(question_id)
        if question and "last_activity_date" in question:
            last_activity_date = datetime.fromtimestamp(
                question["last_activity_date"],
                tz=timezone.utc,
            )
            return last_activity_date > last_check
        return False
