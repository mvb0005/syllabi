"""Application settings loaded from environment variables."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration read from environment / .env file."""

    DATABASE_URL: str = "postgresql+asyncpg://lms_user:lms_password@db:5432/lms_db"
    SECRET_KEY: str = "change-me-in-production"  # noqa: S105
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Ensure ENVIRONMENT is one of the allowed values."""
        allowed = {"development", "production"}
        if v not in allowed:
            msg = f"ENVIRONMENT must be one of {allowed}"
            raise ValueError(msg)
        return v


settings = Settings()
