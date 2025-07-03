import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import ParseResult

import httpx

from src.clients.base_client import BaseClient
from src.clients.client_settings import ClientSettings, default_settings

logger = logging.getLogger(__name__)


class StackOverflowClient(BaseClient):
    """HTTP-клиент для обращения к StackOverflow API.

    Использует базовый URL, который можно задать при инициализации.
    Если базовый URL не указан, используется значение по умолчанию.

    Клиент предназначен для получения данных o вопросах, ответах или комментариях c
    помощью StackExchange API.
    """

    def __init__(
        self,
        settings: ClientSettings = default_settings,
        api_key: str | None = None,
    ) -> None:
        """Инициализирует клиент c опциональным API-ключом и сайтом.

        :param settings: Настройки c URL-адресами и тайм-аутами.
        :param api_key: Ключ API для увеличения лимита запросов.
        """
        self.base_url = settings.stackoverflow_api_url
        self.timeout = settings.client_timeout
        self.api_key = api_key
        self.site = settings.stackoverflow_default_site

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
                response = await client.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()

                data = response.json() or {}
                if not data.get("items"):
                    return None
                return data["items"][0]
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Превышено время ожидания запроса к {url}") from e
            except httpx.HTTPStatusError as e:
                if e.response.status_code == httpx.codes.BAD_REQUEST:
                    raise ValueError(f"Некорректный запрос для вопроса {question_id}") from e
                return None

    async def check_updates(self, parsed_url: ParseResult, last_check: datetime | None) -> bool:
        """Проверяет, были ли обновления вопроса после последней проверки.

        :param parsed_url: Ссылка на вопрос.
        :param last_check: Время последней проверки.
        :return: True, если есть обновления, иначе False.
        """
        if last_check is None:
            return True
        try:
            question_id = parsed_url.path.split("/")[-2] or "0"
        except IndexError:
            logger.warning("Некорректный path в StackOverflow URL: %s", parsed_url.path)
            return False
        question = await self.get_question(question_id)
        if question and "last_activity_date" in question:
            last_activity_date = datetime.fromtimestamp(
                question["last_activity_date"],
                tz=timezone.utc,
            )
            return last_activity_date > last_check
        return False
