from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True

    # File storage
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 50
    allowed_extensions: str = "tf,tfvars,json,yaml,yml,hcl,template,dockerfile"

    # Mock AI service
    ai_service_url: str = "http://localhost:9000"
    ai_service_timeout_seconds: int = 30
    use_mock_ai: bool = True

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip().lower() for ext in self.allowed_extensions.split(",")]

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
