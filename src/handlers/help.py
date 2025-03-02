from telethon.events import NewMessage

__all__ = ("help_handler",)


async def help_handler(
    event: NewMessage.Event,
) -> None:
    """Обработчик команды /help для отображения списка доступных команд в Telegram-боте.

    Отправляет пользователю сообщение c перечнем всех поддерживаемых команд и их кратким описанием.
    Декоратор @require_registration обеспечивает выполнение только для зарегистрированных
    пользователей.

    :param event: Событие сообщения Telegram, содержащее данные o пользователе и чате.
    :return: None
    """
    help_text = (
        "Доступные команды:\n"
        "/start - начало работы бота\n"
        "/help - помощь\n"
        "/track <url> - начать отслеживание ссылки\n"
        "/untrack <url> - прекратить отслеживание ссылки\n"
        "/list - список отслеживаемых ссылок"
    )
    await event.respond(help_text)
