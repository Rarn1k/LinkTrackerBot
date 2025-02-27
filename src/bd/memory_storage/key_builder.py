from telethon.events import NewMessage

from src.bd.memory_storage.memory import StorageKey


async def build_storage_key(event: NewMessage.Event) -> StorageKey:
    """Формирует ключ для хранилища конечного автомата (FSM) на основе события Telegram.

    Извлекает идентификатор чата (chat_id) и идентификатор пользователя (user_id) из события,
    создавая неизменяемый объект StorageKey, который используется как ключ в MemoryStorage.

    :param event: Событие сообщения Telegram, содержащее данные щ чате и пользователе.
    :return: Объект StorageKey c chat_id и user_id из события.
    """
    return StorageKey(chat_id=event.chat_id, user_id=event.sender_id)
