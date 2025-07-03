import asyncio
import json
import logging
import time
from typing import Any

from confluent_kafka import Producer

from src.api.bot_api.models import DigestUpdate, UpdateEvent
from src.scheduler.notification.notification_service import NotificationService
from src.settings import settings

logger = logging.getLogger(__name__)


class KafkaNotificationService(NotificationService):
    """Реализация сервиса уведомлений через Kafka (c использованием confluent-kafka)."""

    def __init__(self, bootstrap_servers: str, topic_updates: str, topic_digest: str) -> None:
        self.producer = Producer({"bootstrap.servers": bootstrap_servers})
        self.topic_updates = topic_updates
        self.topic_digest = topic_digest
        self.dlq_topic = settings.kafka.topic_dlq

    async def send_update(self, chat_id: int, updates: list[str]) -> None:
        """Отправляет обычные строковые обновления через Kafka."""
        if not updates:
            return

        payload = DigestUpdate(
            id=int(time.time()),
            description="Полученные обновления:",
            tg_chat_id=chat_id,
            updates=updates,
        )
        await self._produce(self.topic_updates, payload.model_dump())

    async def send_digest(self, chat_id: int, updates: list[UpdateEvent]) -> None:
        """Отправляет дайджест обновлений через Kafka."""
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
        await self._produce(self.topic_digest, payload.model_dump())

    async def _produce(self, topic: str, payload: dict[str, Any]) -> None:
        """Асинхронно публикует сообщение в Kafka."""
        try:
            await asyncio.to_thread(
                self.producer.produce,
                topic=topic,
                value=json.dumps(payload).encode("utf-8"),
            )
            # Ожидаем отправки сообщений
            await asyncio.to_thread(self.producer.flush)
            logger.info("Уведомление отправлено в Kafka [%s]", topic)
        except Exception as e:
            logger.exception("Ошибка отправки сообщения в Kafka [%s]", topic)
            await self._send_to_dlq(topic, payload, str(e))

    async def _send_to_dlq(self, original_topic: str, payload: dict[str, Any], error: str) -> None:
        """Отправляет сообщение в Dead Letter Queue."""
        try:
            dlq_payload = {
                "original_topic": original_topic,
                "error": error,
                "payload": payload,
                "timestamp": int(time.time()),
            }
            await asyncio.to_thread(
                self.producer.produce,
                topic=self.dlq_topic,
                value=json.dumps(dlq_payload).encode("utf-8"),
            )
            await asyncio.to_thread(self.producer.flush)
            logger.info("Сообщение отправлено в DLQ: %s", self.dlq_topic)
        except Exception:
            logger.exception("Ошибка при отправке сообщения в DLQ")
