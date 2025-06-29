import logging
import time

import httpx

from src.api.bot_api.models import DigestUpdate, UpdateEvent
from src.scheduler.notification.notification_service import NotificationService

logger = logging.getLogger(__name__)


class HTTPNotificationService(NotificationService):
    """Реализация сервиса уведомлений через HTTP-запросы к bot-сервису."""

    def __init__(self, bot_api_url: str) -> None:
        """:param bot_api_url: Базовый URL bot-сервиса."""
        self.bot_api_url = bot_api_url

    async def send_update(self, chat_id: int, updates: list[str]) -> None:
        """Формирует и отправляет обычные обновления (строки).

        :param chat_id: Идентификатор чата.
        :param updates: Список текстовых обновлений.
        """
        if not updates:
            return

        payload = DigestUpdate(
            id=int(time.time()),
            description="Полученные обновления:",
            tg_chat_id=chat_id,
            updates=updates,
        )
        await self._send_notification(payload, path="/updates", chat_id=chat_id)

    async def send_digest(self, chat_id: int, updates: list[UpdateEvent]) -> None:
        """Формирует и отправляет дайджест по обновлениям.

        :param chat_id: Идентификатор чата.
        :param updates: Список событий обновлений.
        """
        if not updates:
            return

        updates_text = [
            (
                f"Описание:  {update.description}\n"
                f"Заголовок: *{update.title}*\n"
                f"Автор:     {update.username}\n"
                f"Дата:      {update.created_at:%Y-%m-%d %H:%M}\n"
                f"Описание:  {update.preview}\n"
                f"{'=' * 50}"
            )
            for update in updates
        ]

        payload = DigestUpdate(
            id=int(time.time()),
            description="Полученные обновления:",
            tg_chat_id=chat_id,
            updates=updates_text,
        )
        await self._send_notification(payload, path="/digest", chat_id=chat_id)

    async def _send_notification(self, payload: DigestUpdate, path: str, chat_id: int) -> None:
        """Отправляет уведомление по указанному пути.

        :param payload: Объект DigestUpdate.
        :param path: Путь запроса (например, '/digest' или '/updates').
        :param chat_id: Идентификатор чата (для логов).
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.bot_api_url}{path}",
                    json=payload.model_dump(),
                )
                response.raise_for_status()
            logger.info("Уведомление успешно отправлено на %s для чата %s", path, chat_id)
        except httpx.HTTPError:
            logger.exception("Не удалось отправить уведомление на %s для чата %s", path, chat_id)
