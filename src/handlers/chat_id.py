from telethon.events import NewMessage

__all__ = ("chat_id_cmd_handler",)


async def chat_id_cmd_handler(
    event: NewMessage.Event,
) -> None:
    """Обработчик команды /chat_id для вывода идентификатора чата.

    Отправляет пользователю сообщение c chat_id текущего чата.

    :param event: Событие сообщения Telegram, содержащее данные пользователя и чата.
    :return: None
    """
    await event.client.send_message(
        entity=event.input_chat,
        message=f"chat_id is: {event.chat_id}",
        reply_to=event.message,
    )
