from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "radar_trabalhista"
    postgres_user: str = "postgres"
    postgres_password: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379"

    # App
    api_env: str = "development"
    api_port: int = 8000

    # Cache TTLs
    cache_ttl_caged: int = 3600  # 1h
    cache_ttl_cbo: int = 86400  # 24h

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
