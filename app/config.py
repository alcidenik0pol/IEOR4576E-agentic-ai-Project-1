"""Centralized configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Google Cloud configuration
    google_cloud_project: str = "agenticaicolumbia"
    google_cloud_location: str = "us-central1"
    vertex_model_id: str = "gemini-2.0-flash-exp"

    # Application configuration
    environment: str = "development"
    port: int = 8080
    debug: bool = False

    # Rate limiting
    rate_limit_requests: int = 20
    rate_limit_period: str = "minute"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def allowed_origins(self) -> list[str]:
        """Get allowed CORS origins based on environment."""
        if self.is_production:
            # In production, configure your actual domain
            prod_origin = "https://your-frontend-domain.com"
            return [prod_origin]
        return ["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:8080"]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
