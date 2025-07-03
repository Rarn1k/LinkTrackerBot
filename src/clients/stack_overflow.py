import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import ParseResult

import httpx

from src.api.bot_api.models import UpdateEvent
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
        self.base_url = settings.stackoverflow.api_url
        self.timeout = settings.client_timeout
        self.api_key = api_key
        self.site = settings.stackoverflow.default_site

    @staticmethod
    async def _parse_question_id(parsed_url: ParseResult) -> str | None:
        """Извлекает ID вопроса из URL."""
        try:
            path_parts = parsed_url.path.strip("/").split("/")
            return path_parts[-2] or "0"
        except IndexError:
            logger.warning("Некорректный path в StackOverflow URL: %s", parsed_url.path)
            return None

    @staticmethod
    async def _create_update_event(
        question: dict[str, Any],
        parsed_url: ParseResult,
        last_activity_date: datetime,
    ) -> UpdateEvent | None:
        """Создаёт объект UpdateEvent на основе данных вопроса."""
        content_mapping = {
            "answers": (f"Новый ответ на {parsed_url.geturl()}", "body", "owner", "creation_date"),
            "comments": (
                f"Новый комментарий на {parsed_url.geturl()}",
                "body",
                "owner",
                "creation_date",
            ),
        }

        username = "Неизвестный пользователь"
        preview = ""
        description = ""

        for content_type, (desc, body_key, owner_key, date_key) in content_mapping.items():
            if content_type in question:
                latest_item = max(question[content_type], key=lambda x: x[date_key])
                preview = latest_item.get(body_key, "Нет описания")[:200]
                username = latest_item.get(owner_key, {}).get("display_name", username)
                description = desc
                break

        if preview == "":
            return None

        return UpdateEvent(
            description=description,
            title=question.get("title", "Без названия"),
            username=username,
            created_at=last_activity_date,
            preview=preview,
        )

    async def get_question(self, question_id: str) -> dict[str, Any] | None:
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
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Превышено время ожидания запроса к {url}") from e
            except httpx.HTTPStatusError as e:
                if e.response.status_code == httpx.codes.BAD_REQUEST:
                    raise ValueError(f"Некорректный запрос для вопроса {question_id}") from e
                return None
            else:
                if not data.get("items"):
                    return None
                result: dict[str, Any] = data["items"][0]
                return result

    async def check_updates(
        self,
        parsed_url: ParseResult,
        last_check: datetime | None,
    ) -> UpdateEvent | None:
        """Проверяет, были ли новые ответы или комментарии после последней проверки."""
        if last_check is None:
            return None

        question_id = await self._parse_question_id(parsed_url)
        if not question_id:
            return None

        question = await self.get_question(question_id)
        if not question or "last_activity_date" not in question:
            return None

        last_activity_date = datetime.fromtimestamp(
            question["last_activity_date"],
            tz=timezone.utc,
        )

        if last_activity_date > last_check:
            return await self._create_update_event(question, parsed_url, last_activity_date)

        return None
