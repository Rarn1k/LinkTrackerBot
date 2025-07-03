from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.db.db_manager.base import DBManager
from src.settings import settings


class ORMDBManager(DBManager):
    """Менеджер базы данных, использующий SQLAlchemy ORM."""

    def __init__(self) -> None:
        """Инициализирует подключение к базе данных."""
        self.engine: AsyncEngine = create_async_engine(
            url=str(settings.db.orm_url),
            echo=settings.db.echo,
            echo_pool=settings.db.echo_pool,
            pool_size=settings.db.pool_size,
            max_overflow=settings.db.max_overflow,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def start(self) -> None:
        """Инициализация ресурсов базы данных."""

    async def close(self) -> None:
        """Закрывает соединение c базой данных."""
        await self.engine.dispose()

    async def get_dependency(self) -> AsyncGenerator[AsyncSession, None]:
        """Возвращает сессию для работы c базой данных.

        :yield: Объект сессии SQLAlchemy для асинхронного взаимодействия c БД.
        """
        if not self.session_factory:
            raise RuntimeError("Фабрика сессий не инициализирована")
        async with self.session_factory() as session:
            yield session
