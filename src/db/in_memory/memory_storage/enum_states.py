from enum import Enum, auto


class State(Enum):
    """Перечисление состояний конечного автомата (FSM) для Telegram-бота.

    Определяет возможные состояния процесса обработки команд, связанных c отслеживанием ссылок.
    Значения генерируются автоматически c помощью auto(), начиная c 1.

    :ivar WAITING_FOR_TAGS: Состояние ожидания ввода тегов для подписки.
    :ivar WAITING_FOR_FILTERS: Состояние ожидания ввода фильтров для подписки.
    """

    WAITING_FOR_TAGS = auto()
    WAITING_FOR_FILTERS = auto()
