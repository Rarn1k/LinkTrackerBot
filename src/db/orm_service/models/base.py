from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовая абстрактная модель для всех таблиц базы данных.

    Определяет поле `id` как первичный ключ.
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
