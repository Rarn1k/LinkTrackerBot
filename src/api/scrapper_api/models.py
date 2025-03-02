from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ApiErrorResponse(BaseModel):
    """Модель ответа для ошибок API.

    :param description: Описание ошибки.
    :param code: Код ошибки.
    :param exceptionName: Имя исключения.
    :param exceptionMessage: Сообщение исключения.
    :param stacktrace: Список строк co stacktrace.
    """

    description: str = Field(..., example="Некорректные параметры запроса")
    code: str = Field(..., example="400")
    exceptionName: str = Field(..., example="ValidationError")  # noqa: N815
    exceptionMessage: str = Field(..., example="Ошибка валидации")  # noqa: N815
    stacktrace: list[str] = Field(default_factory=list, example=["line1", "line2"])


class LinkResponse(BaseModel):
    """Модель ответа для ссылки.

    :param id: Идентификатор ссылки.
    :param url: URL ссылки.
    :param tags: Список тегов.
    :param filters: Список фильтров.
    """

    id: int = Field(..., example=1)
    url: HttpUrl = Field(..., example="https://example.com")
    tags: list[str] = Field(..., example=["news", "tech"])
    filters: list[str] = Field(..., example=["filter1", "filter2"])
    last_updated: Optional[datetime] = Field(None, example="2023-10-01T12:00:00Z")


class AddLinkRequest(BaseModel):
    """Модель запроса для добавления ссылки.

    :param link: URL ссылки для отслеживания.
    :param tags: Список тегов (опционально).
    :param filters: Список фильтров (опционально).
    """

    link: HttpUrl = Field(..., example="https://example.com")
    tags: list[str] = Field(default_factory=list, example=["news", "tech"])
    filters: list[str] = Field(default_factory=list, example=["filter1", "filter2"])


class ListLinksResponse(BaseModel):
    """Модель ответа для списка ссылок.

    :param links: Список ссылок.
    :param size: Общее количество ссылок.
    """

    links: list[LinkResponse] = Field(..., example=[])
    size: int = Field(..., example=0)


class RemoveLinkRequest(BaseModel):
    """Модель запроса для удаления ссылки.

    :param link: URL ссылки, которую нужно прекратить отслеживать.
    """

    link: HttpUrl = Field(..., example="https://example.com")
