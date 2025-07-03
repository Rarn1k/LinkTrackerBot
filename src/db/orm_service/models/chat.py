from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.orm_service.models.base import Base


class Chat(Base):
    """Модель чата для хранения информации o зарегистрированных Telegram-чатах.

    :param id: Уникальный идентификатор чата.
    :param links: Связь c подписками данного чата.
    """

    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)

    links = relationship("Link", back_populates="chat", cascade="all, delete-orphan")
