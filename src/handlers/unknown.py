from telethon.events import NewMessage

__all__ = ("unknown_command_handler",)


async def unknown_command_handler(
    event: NewMessage.Event,
) -> None:
    """Обработчик для неизвестных команд в Telegram-боте.

    Проверяет, является ли текст сообщения известной командой из перечисления BotCommand.
    Если команда неизвестна, отправляет пользователю сообщение c предложением использовать /help.
    Декоратор @require_registration гарантирует, что обработчик выполняется только
    для зарегистрированных пользователей.

    :param event: Событие сообщения Telegram, содержащее текст команды и данные пользователя.
    :return: None
    """
    await event.respond("Неизвестная команда. Используйте /help для списка доступных команд.")
