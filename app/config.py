"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Auth service configuration.

    All values can be overridden via environment variables or a .env file.
    """

    # Database
    DATABASE_URL: str = "mysql://auth_user:auth_pass@localhost:3306/auth_db"
    DB_POOL_MIN: int = 5
    DB_POOL_MAX: int = 20

    # JWT
    JWT_SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 90

    # SMTP
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@example.com"

    # CORS
    CORS_ORIGINS: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS comma-separated string into a list."""
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Argon2 password hashing
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 32768
    ARGON2_PARALLELISM: int = 1

    # Application
    APP_NAME: str = "Auth Service"
    DEBUG: bool = False
    PASSWORD_HASH_WORKERS: int = 2
    BASE_URL: str = "http://localhost:8000"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
