from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EchoNote API"
    environment: str = "local"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./echonote_v2.db"
    cors_origins: str = "http://localhost:3000"
    supabase_url: str | None = None
    supabase_jwt_secret: str | None = None
    auth_required: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_prefix="ECHONOTE_")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def auth_enabled(self) -> bool:
        return self.auth_required and bool(self.supabase_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
