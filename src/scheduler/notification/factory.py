from src.scheduler.notification.http_notification_service import HTTPNotificationService
from src.scheduler.notification.kafka_notification_service import KafkaNotificationService
from src.scheduler.notification.notification_service import NotificationService
from src.settings import settings


class NotificationServiceFactory:
    """Фабрика для создания нужной реализации NotificationService."""

    @staticmethod
    def create() -> NotificationService:
        transport = settings.message_transport.upper()

        match transport:
            case "HTTP":
                return HTTPNotificationService(bot_api_url=settings.bot_api_url)
            case "KAFKA":
                return KafkaNotificationService(
                    bootstrap_servers=settings.kafka.bootstrap_servers,
                    topic_updates=settings.kafka.topic_updates,
                    topic_digest=settings.kafka.topic_digest,
                )
            case _:
                raise ValueError(f"Unsupported transport: {settings.message_transport}")
