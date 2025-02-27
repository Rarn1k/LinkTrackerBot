import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from telethon.events import NewMessage

from src.bd.repository import Repository

T = TypeVar("T")


def require_registration(
    handler: Callable[[NewMessage.Event], Any],
) -> Callable[[NewMessage.Event], Any]:
    """Декоратор для проверки регистрации пользователя в Telegram-боте.

    Проверяет, зарегистрирован ли пользователь в репозитории (Repository.users).
    Если пользователь не зарегистрирован, записывает информацию в лог и отправляет
    сообщение c инструкцией зарегистрироваться через команду /start. Если пользователь
    зарегистрирован, вызывает исходный обработчик.

    :param handler: Асинхронная функция-обработчик события Telegram, которую нужно декорировать.
    :return: Декорированная функция-обработчик, сохраняющая асинхронное поведение.
    """

    @wraps(handler)
    async def wrapper(event: NewMessage.Event) -> Optional[T]:
        """Внутренняя функция-обёртка для проверки регистрации.

        :param event: Событие сообщения Telegram, содержащее данные o пользователе и чате.
        :return: None (если пользователь не зарегистрирован) или результат вызова handler.
        """
        user_id = event.sender_id
        if user_id not in Repository().users:
            logging.info(
                "Unregistered user attempted to use a command.",
                extra={"user_id": user_id},
            )
            await event.respond(
                "Вы не зарегистрированы. Пожалуйста, введите /start для начала работы.",
            )
            return None
        return await handler(event)

    return wrapper
