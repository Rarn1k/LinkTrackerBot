import logging

from telethon import TelegramClient, events

from src.handlers import chat_id_cmd_handler
from src.handlers.get_list import list_handler
from src.handlers.help import help_handler
from src.handlers.message import msg_handler
from src.handlers.start import start_handler
from src.handlers.track import track_handler
from src.handlers.unknown import unknown_command_handler
from src.handlers.untrack import untrack_handler
from src.handlers.utils.enum_commands import BotCommand
from src.settings import settings

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """Инициализирует и запускает Telegram-бота c использованием Telethon.

    Создаёт и настраивает TelegramClient c использованием настроек бота.
    Регистрирует обработчики событий для известных команд (определённых в BotCommand).
    Регистрирует обработчик для неизвестных команд и общий обработчик для сообщений.
    Запускает цикл получения сообщений от пользователей до отключения клиента.

    :return: None
    """
    logger.info("Run the event loop to start receiving messages")

    client = TelegramClient("bot_session", settings.api_id, settings.api_hash).start(
        bot_token=settings.token,
    )

    command_handlers = {
        BotCommand.CHAT_ID.value: chat_id_cmd_handler,
        BotCommand.START.value: start_handler,
        BotCommand.HELP.value: help_handler,
        BotCommand.TRACK.value: track_handler,
        BotCommand.UNTRACK.value: untrack_handler,
        BotCommand.LIST.value: list_handler,
    }

    for command, handler in command_handlers.items():
        client.add_event_handler(handler, events.NewMessage(pattern=rf"^{command}"))

    excluded_commands = "|".join(cmd.name.lower() for cmd in BotCommand)
    client.add_event_handler(
        unknown_command_handler,
        events.NewMessage(pattern=rf"/(?!{excluded_commands})\w+"),
    )

    client.add_event_handler(msg_handler, events.NewMessage(pattern=r"^[^/]"))

    with client:
        try:
            client.run_until_disconnected()
        except KeyboardInterrupt:
            pass
        except Exception as exc:
            logger.exception(
                "Main loop raised error.",
                extra={"exc": exc},
            )


if __name__ == "__main__":
    main()
