from telethon.events import NewMessage

from src.bd.repository import Repository

__all__ = ("start_handler",)


async def start_handler(
    event: NewMessage.Event,
) -> None:
    """Обработчик команды /start для инициализации пользователя в Telegram-боте.

    Добавляет нового пользователя в репозиторий и отправляет приветственное сообщение c инструкциями
    по использованию бота.

    :param event: Событие сообщения Telegram, содержащее данные o пользователе и чате.
    :return: None
    """
    repository = Repository()
    await repository.add_user(event.sender_id)
    await event.client.send_message(
        entity=event.input_chat,
        message="Добро пожаловать в LinkTracker! Введите команду /track <url>, "
        "чтобы подписаться на обновления. "
        "Весь список команд и их пояснения можете получить по команде /help",
    )
