from telethon.events import NewMessage

from src.bd.repository import Repository

__all__ = ("list_handler",)

from src.handlers.utils.registration_required import require_registration


@require_registration
async def list_handler(
    event: NewMessage.Event,
) -> None:
    """Обработчик команды /list для отображения списка отслеживаемых ссылок в Telegram-боте.

    Получает список подписок пользователя из репозитория и отправляет этот список
    в форматированном виде.
    Если подписок нет, отправляет сообщение o6 их отсутствии. Декоратор @require_registration
    обеспечивает выполнение только для зарегистрированных пользователей.

    :param event: Событие сообщения Telegram, содержащее данные o пользователе и чате.
    :return: None
    """
    repository = Repository()
    user_id = event.sender_id
    subs = await repository.get_subscriptions(user_id)
    if not subs:
        await event.respond("У вас нет активных подписок.")
    else:
        lines = []
        for sub in subs:
            line = f"{sub.url}\nТэги: {' '.join(sub.tags)}\nФильтры: {sub.filters}\n"
            lines.append(line)
        await event.respond("Ваши подписки:\n" + "\n".join(lines))
