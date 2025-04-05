from datetime import datetime

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
                        "*Как работает async в Python?* (by JohnDoe)\n 2024-06-01 12:30"
                        "\nasyncio позволяет выполнять конкурентные операции без потоков...",
                        "*Fix memory leak in database connection* (by JaneDev)\n 2024-06-02 15:45"
                        "\nЭтот PR исправляет утечку памяти в модуле обработки транзакций...",
                    ],
                },
            ],
        },
    }


class UpdateEvent(BaseModel):
    """Модель обновления для различных платформ (StackOverflow, GitHub).

    :param description: Описание обновления
    :param title: Заголовок вопроса, PR или Issue.
    :param username: Имя пользователя, который создал запись.
    :param created_at: Время создания записи в UTC.
    :param preview: Превью ответа или описания (первые 200 символов).
    """

    description: str = Field()
    title: str = Field(...)
    username: str = Field(...)
    created_at: datetime = Field(...)
    preview: str = Field(..., max_length=200)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Как работает async в Python?",
                    "username": "JohnDoe",
                    "created_at": "2024-06-01T12:30:00Z",
                    "preview": "asyncio позволяет выполнять конкурентные операции без потоков...",
                },
                {
                    "title": "Fix memory leak in database connection",
                    "username": "JaneDev",
                    "created_at": "2024-06-02T15:45:00Z",
                    "preview": "Этот PR исправляет утечку памяти в модуле обработки транзакций...",
                },
            ],
        },
    }
