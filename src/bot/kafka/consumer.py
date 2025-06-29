import asyncio
import contextlib
import json
import logging
from typing import Any, Optional

import httpx
from confluent_kafka import Consumer, KafkaError, Message, Producer

from src.api.bot_api.models import DigestUpdate
from src.settings import settings

logger = logging.getLogger(__name__)


class KafkaNotificationReceiver:
    def __init__(self) -> None:
        self.topics = [
            settings.kafka.topic_updates,
            settings.kafka.topic_digest,
        ]
        self.consumer = Consumer(
            {
                "bootstrap.servers": settings.kafka.bootstrap_servers,
                "group.id": "bot-consumer-group",
                "auto.offset.reset": "earliest",
            },
        )
        self.dlq_topic = settings.kafka.topic_dlq
        self.producer = Producer({"bootstrap.servers": settings.kafka.bootstrap_servers})
        self._running = False
        self._task: Optional[asyncio.Task[None]] = None

    async def start(self) -> None:
        """Асинхронный запуск Kafka-потока."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._consume_messages())
        logger.info("Kafka consumer started")

    async def stop(self) -> None:
        """Корректное завершение работы Kafka-потока."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        self.consumer.close()
        logger.info("Kafka consumer stopped")

    async def _consume_messages(self) -> None:
        """Основной цикл обработки сообщений."""
        self.consumer.subscribe(self.topics)
        logger.info("Kafka consumer subscribed to topics: %s", self.topics)

        while self._running:
            try:
                msg = await asyncio.to_thread(self.consumer.poll, 1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:  # noqa: SLF001
                        continue
                    logger.error("Kafka error: %s", msg.error())
                    break

                try:
                    payload = json.loads(msg.value().decode("utf-8"))
                    await self._handle_message(msg.topic(), payload, msg)
                except Exception:
                    logger.exception("Ошибка обработки Kafka-сообщения")
                    await self._send_to_dlq(msg)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Unexpected error in Kafka consumer")
                await asyncio.sleep(1)

    async def _handle_message(self, topic: str, payload: dict[str, Any], msg: Message) -> None:
        """Обработка полученного сообщения в зависимости от топика."""
        try:
            update = DigestUpdate(**payload)
            async with httpx.AsyncClient() as client:
                telegram_api_url = f"{settings.tg_api_url}/bot{settings.token}/sendMessage"
                message_text = f"{update.description}\n" + "\n".join(update.updates)
                message_payload = {
                    "chat_id": update.tg_chat_id,
                    "text": message_text,
                    "parse_mode": "Markdown" if topic == settings.kafka.topic_digest else None,
                }
                try:
                    response = await client.post(telegram_api_url, json=message_payload)
                    response.raise_for_status()
                    logger.info("Сообщение отправлено в чат %s", update.tg_chat_id)
                except httpx.HTTPError:
                    logger.exception("Ошибка при отправке сообщения в чат %s", update.tg_chat_id)
                    await self._send_to_dlq(msg)
        except Exception:
            logger.exception("Ошибка при обработке сообщения: %s")
            await self._send_to_dlq(msg)

    async def _send_to_dlq(self, msg: Message) -> None:
        """Отправка сообщения в Dead Letter Queue (DLQ)."""
        dlq_payload: dict[str, Any] = {
            "original_topic": msg.topic(),
            "partition": msg.partition(),
            "offset": msg.offset(),
            "timestamp": msg.timestamp(),
            "error": "Message could not be processed",
            "payload": msg.value().decode("utf-8"),
        }

        try:
            await asyncio.to_thread(
                self.producer.produce,
                topic=self.dlq_topic,
                value=json.dumps(dlq_payload).encode("utf-8"),
            )
            await asyncio.to_thread(self.producer.flush)
            logger.info("Сообщение отправлено в DLQ: %s", self.dlq_topic)
        except Exception:
            logger.exception("Ошибка при отправке сообщения в DLQ")
