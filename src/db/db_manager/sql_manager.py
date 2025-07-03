from typing import AsyncGenerator

import asyncpg

from src.db.db_manager.base import DBManager
from src.settings import settings


class SQLDBManager(DBManager):
    """Менеджер базы данных для работы c asyncpg."""

    def __init__(self) -> None:
        """Инициализирует менеджер базы данных без пула соединений."""
        self.pool: asyncpg.Pool | None = None

    async def start(self) -> None:
        """Создает пул соединений c базой данных."""
        self.pool = await asyncpg.create_pool(str(settings.db.sql_url))

    async def close(self) -> None:
        """Закрывает пул соединений c базой данных, если он был создан."""
        if self.pool:
            await self.pool.close()

    async def get_dependency(self) -> AsyncGenerator[asyncpg.Pool, None]:
        """Возвращает существующий пул соединений как генератор для FastAPI Depends.

        :yield: Пул соединений `asyncpg.Pool`.
        :raises RuntimeError: Если пул соединений не инициализирован.
        """
        if not self.pool:
            raise RuntimeError("Пул соединений не инициализирован")
        yield self.pool
