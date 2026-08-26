# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL configuration.
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    REDIS_URL: str = "redis://redis:6379/0"
    # JWT security configuration.
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    # Payment webhook security.
    PAYMENT_WEBHOOK_SECRET: str
    # Build the SQLAlchemy connection URL from environment variables.
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://"
            f"{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    # Load configuration from the .env file.
    # Extra environment variables are ignored so unrelated settings
    # do not break application startup.
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


# Create one shared settings instance for the whole application.
settings = Settings()
