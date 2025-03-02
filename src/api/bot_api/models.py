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


class LinkUpdate(BaseModel):
    """Модель обновления ссылки (LinkUpdate).

    :param id: Идентификатор обновления.
    :param url: URL обновления.
    :param description: Описание обновления.
    :param tgChatIds: Список ID Telegram-чатов, куда необходимо отправить обновление.
    """

    id: int = Field(..., example=1)
    url: HttpUrl = Field(..., example="https://example.com")
    description: str = Field(..., example="Новый комментарий добавлен")
    tgChatIds: list[int] = Field(..., example=[123456789, 987654321])  # noqa: N815
