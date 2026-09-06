import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    test_database_url: str | None
    secret_key: str


def _required_env(name: str) -> str:
    value = os.getenv(name)

    if not value or not value.strip():
        raise RuntimeError(f"{name} is required")

    return value.strip()


def load_settings() -> Settings:
    database_url = _required_env("DATABASE_URL")

    test_database_url = os.getenv("TEST_DATABASE_URL")
    if test_database_url:
        test_database_url = test_database_url.strip()

    secret_key = _required_env("SECRET_KEY")

    if len(secret_key) < 32:
        raise RuntimeError(
            "SECRET_KEY must be at least 32 characters long"
        )

    return Settings(
        database_url=database_url,
        test_database_url=test_database_url,
        secret_key=secret_key,
    )


settings = load_settings()