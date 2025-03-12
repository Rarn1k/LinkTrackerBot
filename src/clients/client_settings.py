from dataclasses import dataclass


@dataclass()
class ClientSettings:
    """Настройки клиентов c URL-адресами и таймаутами."""

    github_api_url: str = "https://api.github.com"
    stackoverflow_api_url: str = "https://api.stackexchange.com/2.3"
    client_timeout: float = 10.0


default_settings = ClientSettings()
