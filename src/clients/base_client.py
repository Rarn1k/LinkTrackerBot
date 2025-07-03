from abc import ABC, abstractmethod
from datetime import datetime
from urllib.parse import ParseResult


class BaseClient(ABC):
    """Абстрактный базовый клиент для проверки обновлений на сайте."""

    @abstractmethod
    async def check_updates(self, parsed_url: ParseResult, last_check: datetime | None) -> bool:
        """Проверяет, были ли обновления на сайте после последней проверки.

        :param parsed_url: Разобранный URL сайта в формате `ParseResult`.
        :param last_check: Время последней успешной проверки на обновления.
                           Если значение None, считается, что проверка выполняется впервые.
        :return: True, если на сайте есть новые обновления c момента `last_check`, иначе False.
        """
