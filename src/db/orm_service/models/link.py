from datetime import datetime

from sqlalchemy import ARRAY, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.orm_service.models.base import Base


class Link(Base):
    """Модель подписки для хранения информации o6 отслеживаемых ссылках.

    :param id: Уникальный идентификатор подписки, первичный ключ.
    :param chat_id: Идентификатор чата (внешний ключ к Chat.id).
    :param url: URL отслеживаемой ссылки.
    :param tags: Массив тегов (опционально).
    :param filters: Массив фильтров (опционально).
    :param last_updated: Время последнего обновления.
    :param chat: Обратная связь c чатом.
    """

    __tablename__ = "links"

    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    filters: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    chat = relationship("Chat", back_populates="links")
