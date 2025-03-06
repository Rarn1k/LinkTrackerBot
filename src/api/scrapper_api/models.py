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

    description: str = Field(...)
    code: str = Field(...)
    exceptionName: str = Field(...)  # noqa: N815
    exceptionMessage: str = Field(...)  # noqa: N815
    stacktrace: list[str] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "description": "Некорректные параметры запроса",
                    "code": "400",
                    "exceptionName": "ValidationError",
                    "exceptionMessage": "Ошибка валидации",
                    "stacktrace": ["line1", "line2"]
                }
            ]
        }
    }


class LinkResponse(BaseModel):
    """Модель ответа для ссылки.

    :param id: Идентификатор ссылки.
    :param url: URL ссылки.
    :param tags: Список тегов.
    :param filters: Список фильтров.
    :param last_updated: Последнее время обновления.
    """

    id: int = Field(...)
    url: HttpUrl = Field(...)
    tags: list[str] = Field(...)
    filters: list[str] = Field(...)
    last_updated: Optional[datetime] = Field(None)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "url": "https://example.com",
                    "tags": ["news", "tech"],
                    "filters": ["filter1:value1", "filter2:value2"],
                    "last_updated": "2023-10-01T12:00:00Z"
                }
            ]
        }
    }


class AddLinkRequest(BaseModel):
    """Модель запроса для добавления ссылки.

    :param link: URL ссылки для отслеживания.
    :param tags: Список тегов (опционально).
    :param filters: Список фильтров (опционально).
    """

    link: HttpUrl = Field(...)
    tags: list[str] = Field(default_factory=list)
    filters: list[str] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "link": "https://example.com",
                    "tags": ["news", "tech"],
                    "filters": ["filter1:value1", "filter2:value2"]
                }
            ]
        }
    }


class ListLinksResponse(BaseModel):
    """Модель ответа для списка ссылок.

    :param links: Список ссылок.
    :param size: Общее количество ссылок.
    """

    links: list[LinkResponse] = Field(...)
    size: int = Field(...)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "links": [
                        {
                            "id": 1,
                            "url": "https://example.com",
                            "tags": ["news", "tech"],
                            "filters": ["filter1:value1", "filter2:value2"],
                            "last_updated": "2023-10-01T12:00:00Z"
                        },
                        {
                            "id": 2,
                            "url": "https://another-example.com",
                            "tags": ["blog", "science"],
                            "filters": ["filter3:value3", "filter4:value4"],
                            "last_updated": "2023-10-02T14:00:00Z"
                        }
                    ],
                    "size": 2,
                }
            ]
        }
    }


class RemoveLinkRequest(BaseModel):
    """Модель запроса для удаления ссылки.

    :param link: URL ссылки, которую нужно прекратить отслеживать.
    """

    link: HttpUrl = Field(...)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "link": "https://example.com"
                }
            ]
        }
    }
