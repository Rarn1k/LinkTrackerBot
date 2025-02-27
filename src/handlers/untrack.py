from telethon.events import NewMessage

from src.bd.repository import Repository
from src.handlers.utils.registration_required import require_registration

__all__ = ("untrack_handler",)

EXPECTED_TRACK_PARTS: int = 2


@require_registration
async def untrack_handler(
    event: NewMessage.Event,
) -> None:
    """Обработчик команды для прекращения отслеживания ссылки в Telegram-боте.

    Проверяет формат команды, извлекает URL из сообщения и удаляет подписку пользователя на этот
    URL, если она существует. Если пользователь не зарегистрирован, декоратор @require_registration
    отправляет сообщение o необходимости регистрации.

    :param event: Событие сообщения Telegram, содержащее текст команды и информацию o пользователе.
    :return: None
    """
    message_text = event.message.message
    parts = message_text.split()

    if len(parts) != EXPECTED_TRACK_PARTS:
        await event.respond(
            "Сообщение для прекращения отслеживания ссылки должно иметь вид "
            "'/track <ваша ссылка>', например:\n/track https://example.com",
        )
        return

    repository = Repository()
    url = parts[1].strip()
    user_id = event.sender_id
    if await repository.is_user_have_url(user_id, url):
        await repository.remove_subscription(user_id, url)
        await event.respond(f"Ссылка {url} удалена из отслеживаемых.")
    else:
        await event.respond(f"Ссылка {url} не найдена в ваших подписках.")
