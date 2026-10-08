from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DATABASE_URL: str = (
        "postgresql+asyncpg://volley:volley@localhost:5432/volleyball"
    )

    SECRET_KEY: str = "change-me-in-.env"

    DEBUG: bool = False

    SESSION_COOKIE_NAME: str = "volleykarelia_session"

    HOST: str = "127.0.0.1"

    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
