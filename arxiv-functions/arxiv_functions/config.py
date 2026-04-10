from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        extra="allow",
    )


class Query(BaseConfig):
    unix_socket: str  # full path


class DatabaseConfig(BaseConfig):
    drivername: str
    username: str
    password: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: str
    query: Query


class FunctionConfig(BaseConfig):
    env: str
    log_locally: bool = False
    max_event_age_in_minutes: int = 50
