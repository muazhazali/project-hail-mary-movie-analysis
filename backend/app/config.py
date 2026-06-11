import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(_PROJECT_ROOT, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_pass: str = "postgres"
    db_name: str = "postgres"

    app_env: str = "development"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    embedding_model: str = "all-MiniLM-L6-v2"

    # Qdrant settings
    # For local Qdrant (host/port mode):
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    # For cloud Qdrant (URL mode) - URL format (e.g., https://qdrant.example.com)
    # Note: If qdrant_url is set, it takes precedence over host/port
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection: str = "subtitle_lines"
    qdrant_vector_size: int = 384  # all-MiniLM-L6-v2 produces 384-dim vectors
    
    @property
    def qdrant_effective_url(self) -> str | None:
        """Get effective Qdrant URL. Checks QDRANT_URL first, then QDRANT_HOST."""
        # First check if explicit URL is set
        if self.qdrant_url and len(self.qdrant_url) > 0:
            return self.qdrant_url
        # Then check if qdrant_host looks like a URL (starts with http)
        if self.qdrant_host.startswith(("http://", "https://")):
            return self.qdrant_host
        return None

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()

