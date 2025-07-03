from pydantic import BaseModel, Field, HttpUrl
from pydantic.alias_generators import to_camel


class ApiErrorResponse(BaseModel):
    """Модель ответа для ошибок API.

    :param description: Описание ошибки.
    :param code: Код ошибки.
    :param exception_name: Имя исключения.
    :param exception_message: Сообщение исключения.
    :param stacktrace: Список строк co stacktrace.
    """

    description: str = Field(...)
    code: str = Field(...)
    exception_name: str = Field(...)
    exception_message: str = Field(...)
    stacktrace: list[str] = Field(default_factory=list)

    model_config = {
        "populate_by_name": True,
        "alias_generator": to_camel,
        "json_schema_extra": {
            "examples": [
                {
                    "description": "Некорректные параметры запроса",
                    "code": "400",
                    "exceptionName": "ValidationError",
                    "exceptionMessage": "Ошибка валидации",
                    "stacktrace": ["line1", "line2"],
                },
            ],
        },
    }


class LinkUpdate(BaseModel):
    """Модель обновления ссылки (LinkUpdate).

    :param id: Идентификатор обновления.
    :param url: URL обновления.
    :param description: Описание обновления.
    :param tg_chat_ids: Список ID Telegram-чатов, куда необходимо отправить обновление.
    """

    id: int = Field(...)
    url: HttpUrl = Field(...)
    description: str = Field(...)
    tg_chat_ids: list[int] = Field(...)

    model_config = {
        "populate_by_name": True,
        "alias_generator": to_camel,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "url": "https://example.com",
                    "description": "Новый комментарий добавлен",
                    "tgChatIds": [123456789, 987654321],
                },
            ],
        },
    }


class DigestUpdate(BaseModel):
    """Модель отправки дайджеста.

    :param id: Идентификатор дайджеста.
    :param description: Описание дайджеста.
    :param tg_chat_id: ID Telegram-чата, куда необходимо отправить дайджест.
    :param updates: Список из сообщений co ссылками, в которых было обновление.
    """

    id: int = Field(...)
    description: str = Field(...)
    tg_chat_id: int = Field(...)
    updates: list[str] = Field(...)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "description": "Полученные обновления: ",
                    "tg_chat_id": 123456789,
                    "updates": [
                        "Обновление на https://example.com!",
                        "Обновление на https://another.com!",
                    ],
                },
            ],
        },
    }
