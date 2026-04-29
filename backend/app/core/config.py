from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """骨架阶段新增：集中管理运行配置，后续业务模块统一从这里读取。"""

    app_name: str = "MyMz"
    app_env: str = "development"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///../data/app.db"
    cors_origins: str = Field(
        default="http://localhost:8080,http://127.0.0.1:8080",
        description="Comma separated CORS origins for local frontend development.",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
