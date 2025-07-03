from telethon.events import NewMessage

from src.bd.memory_storage.enum_states import State
from src.bd.memory_storage.key_builder import build_storage_key
from src.bd.memory_storage.memory import MemoryStorage
from src.constants import EXPECTED_TRACK_PARTS

__all__ = ("track_handler",)


async def track_handler(
    event: NewMessage.Event,
) -> None:
    """Обработчик команды для начала отслеживания ссылки в Telegram-боте.

    Проверяет формат команды '/track <URL>', инициирует процесс отслеживания ссылки,
    сохраняя URL в MemoryStorage и переключая состояние на WAITING_FOR_TAGS.
    Если формат команды неверный, отправляет сообщение c примером правильного использования.

    :param event: Событие сообщения Telegram, содержащее текст команды и данные пользователя.
    :return: None
    """
    message_text = event.message.message
    parts = message_text.split()
    if len(parts) == EXPECTED_TRACK_PARTS:
        memory_storage = MemoryStorage()
        url = parts[1].strip()
        key = await build_storage_key(event)
        await memory_storage.set_state(key, State.WAITING_FOR_TAGS)
        await memory_storage.set_data(key, {"url": url})
        await event.respond("Введите тэги (опционально, разделённые пробелами):")
    else:
        await event.respond(
            "Сообщение для начала отслеживания ссылки должно иметь вид '/track <ваша ссылка>', "
            "например:\n/track https://example.com",
        )
