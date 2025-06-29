import typing
from pathlib import Path

from pydantic import BaseModel, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ("TGBotSettings", "settings")


class DatabaseConfig(BaseModel):
    access_type: str = "ORM"
    orm_url: PostgresDsn
    sql_url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10
    limit_batching: int = 100


class KafkaConfig(BaseModel):
    bootstrap_servers: str
    topic_updates: str
    topic_digest: str
    topic_dlq: str = "bot_dlq"


class RedisConfig(BaseModel):
    url: str
    list_key: str


class TGBotSettings(BaseSettings):
    debug: bool = Field(default=False)

    api_id: int = Field(default=12345)
    api_hash: str = Field(default="default_hash")
    token: str = Field(default="default_token")

    scrapper_api_url: str = "http://localhost:7777/api/v1/scrapper"
    bot_api_url: str = "http://localhost:7777/api/v1/bot"
    tg_api_url: str = "https://api.telegram.org"

    db: DatabaseConfig
    kafka: KafkaConfig
    redis: RedisConfig

    hour_digest: int = 0
    minute_digest: int = 26

    message_transport: str = Field(default="HTTP")

    model_config: typing.ClassVar[SettingsConfigDict] = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        case_sensitive=False,
        env_file=Path(__file__).parent.parent / ".env",
        env_nested_delimiter="__",
        env_prefix="BOT_",
    )


settings = TGBotSettings()  # type: ignore[call-arg]
