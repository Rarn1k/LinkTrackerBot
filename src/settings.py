import typing
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ("TGBotSettings", "settings")


class TGBotSettings(BaseSettings):
    debug: bool = Field(default=False)

    api_id: int = Field(...)
    api_hash: str = Field(...)
    token: str = Field(...)
    scrapper_api_url: str = "http://localhost:7777/api/v1/scrapper"

    model_config: typing.ClassVar[SettingsConfigDict] = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        case_sensitive=False,
        env_file=Path(__file__).parent.parent / ".env",
        env_prefix="BOT_",
    )


settings = TGBotSettings()  # type: ignore[call-arg]
