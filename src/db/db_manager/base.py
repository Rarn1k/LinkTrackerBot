from abc import ABC, abstractmethod
from typing import AsyncGenerator

import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession


class DBManager(ABC):
    @abstractmethod
    async def start(self) -> None:
        """Инициализация ресурсов базы данных."""

    @abstractmethod
    async def close(self) -> None:
        """Закрытие ресурсов базы данных."""

    @abstractmethod
    def get_dependency(self) -> AsyncGenerator[AsyncSession | asyncpg.Pool, None]:
        """Возвращает зависимость для использования в FastAPI."""
