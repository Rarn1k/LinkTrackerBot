from pydantic import BaseModel
from pydantic_settings import BaseSettings


class GithubSettings(BaseModel):
    api_url: str = "https://api.github.com"
    accept_header: str = "application/vnd.github+json"


class StackoverflowSettings(BaseModel):
    api_url: str = "https://api.stackexchange.com/2.3"
    default_site: str = "stackoverflow"


class ClientSettings(BaseSettings):
    """Настройки клиентов c URL-адресами и таймаутами."""

    github: GithubSettings = GithubSettings()
    stackoverflow: StackoverflowSettings = StackoverflowSettings()

    client_timeout: float = 10.0


default_settings = ClientSettings()
