import asyncio
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.bot_api.models import UpdateEvent
from src.api.scrapper_api.models import LinkResponse
from src.clients.client_factory import ClientFactory
from src.db.db_manager.manager_factory import db_manager
from src.db.factory.data_access_factory import db_service
from src.scheduler.notification.notification_service import NotificationService
from src.settings import settings

logger = logging.getLogger(__name__)


class Scheduler:
    """Планировщик обновлений: собирает обновления и отправляет дайджесты в Telegram-чаты."""

    def __init__(self, notification_service: NotificationService) -> None:
        """:param notification_service: Сервис уведомлений, который
        отвечает за отправку сообщений.
        """
        self.notification_service = notification_service

    @staticmethod
    async def process_subscription(
        sub: LinkResponse,
        dependency: AsyncSession | asyncpg.Pool,
    ) -> UpdateEvent | None:
        """Обрабатывает одну подписку и возвращает событие обновления, если оно найдено.

        :param sub: Объект подписки c полями URL, chat_id, last_updated.
        :param dependency: Сессия SQLAlchemy или пул подключений asyncpg.
        :return: Объект обновления или None, если изменений нет.
        """
        url: str = str(sub.url)
        parsed_url = urlparse(url)
        try:
            client = ClientFactory.create_client(service_name=parsed_url.netloc)
        except ValueError:
            logger.warning("Неподдерживаемый URL: %s", url)
            return None

        updated = await client.check_updates(parsed_url, sub.last_updated)
        if updated:
            await db_service.link_service.set_last_updated(
                link_id=sub.id,
                last_updated=updated.created_at,
                dependency=dependency,
            )
            return updated

        logger.info("Не было обновлений для %s", url)
        return None

    async def collect_updates(
        self,
        chat_id: int,
        dependency: AsyncSession | asyncpg.Pool,
    ) -> list[UpdateEvent]:
        """Сканирует все подписки указанного чата и собирает события обновлений.

        :param chat_id: Идентификатор Telegram-чата.
        :param dependency: Сессия SQLAlchemy или пул подключений asyncpg.
        :return: Список событий обновлений (может быть пустым).
        """
        try:
            all_subs: list[LinkResponse] = await db_service.link_service.get_links(
                dependency=dependency,
                chat_id=chat_id,
            )
            if not all_subs:
                logger.info("Подписки не найдены для chat_id: %s", chat_id)
                return []

            tasks = [self.process_subscription(sub, dependency) for sub in all_subs]
            results = await asyncio.gather(*tasks, return_exceptions=False)

            return [result for result in results if result]

        except Exception:
            logger.exception("Ошибка при получении подписок")
            return []

    async def send_digest(self) -> None:
        """Запускает цикл, который проверяет наступление времени отправки дайджеста и,
        если оно наступило, собирает и отправляет обновления для всех чатов.
        """
        while True:
            now = datetime.now(timezone.utc)
            logger.info("Начало просмотра обновлений %s:%s", now.time().hour, now.time().minute)

            if (
                now.time().hour == settings.hour_digest
                and now.time().minute == settings.minute_digest
            ):
                async for dependency in db_manager.get_dependency():
                    offset = 0
                    limit = settings.db.limit_batching

                    while True:
                        logger.info("Запрос в БД с offset=%s, limit=%s", offset, limit)
                        chat_ids = await db_service.chat_service.get_chats(
                            dependency=dependency,
                            limit=limit,
                            offset=offset,
                        )
                        if not chat_ids:
                            break

                        for chat_id in chat_ids:
                            updates = await self.collect_updates(chat_id, dependency)
                            await self.notification_service.send_digest(chat_id, updates)

                        offset += limit
                        if len(chat_ids) < limit:
                            break

            await asyncio.sleep(60)
