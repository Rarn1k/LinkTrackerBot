import httpx
from telethon.events import NewMessage

from src.settings import settings

__all__ = ("start_handler",)


async def start_handler(
    event: NewMessage.Event,
) -> None:
    """Обработчик команды /start для регистрации пользователя.

    Вместо сохранения в локальный репозиторий, отправляет HTTP-запрос в сервис scrapper,
    который регистрирует Telegram-чат. При успешной регистрации отправляется приветственное
    сообщение.

    :param event: Событие Telegram, содержащее данные o пользователе и чате.
    :return: None
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{settings.scrapper_api_url}/tg-chat/{event.chat_id}")
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            await event.respond(f"Ошибка регистрации чата: {e.response.json().get("detail")!s}")
            return
    await event.client.send_message(
        entity=event.input_chat,
        message=(
            "Добро пожаловать в LinkTracker!\n"
            "Введите команду /track <url>, чтобы подписаться на обновления.\n"
            "Список команд можно получить по команде /help."
        ),
    )
