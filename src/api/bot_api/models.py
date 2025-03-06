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


class LinkUpdate(BaseModel):
    """Модель обновления ссылки (LinkUpdate).

    :param id: Идентификатор обновления.
    :param url: URL обновления.
    :param description: Описание обновления.
    :param tgChatIds: Список ID Telegram-чатов, куда необходимо отправить обновление.
    """

    id: int = Field(...)
    url: HttpUrl = Field(...)
    description: str = Field(...)
    tgChatIds: list[int] = Field(...)  # noqa: N815

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "url": "https://example.com",
                    "description": "Новый комментарий добавлен",
                    "tgChatIds": [123456789, 987654321]
                }
            ]
        }
    }
