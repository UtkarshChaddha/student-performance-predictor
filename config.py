import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:

    database_url: str
    test_database_url: str | None

    secret_key: str

    frontend_origin: str

    cookie_secure: bool

    dqn_model_path: str


def _required_env(name: str) -> str:

    value = os.getenv(name)

    if not value or not value.strip():
        raise RuntimeError(
            f"{name} is required"
        )

    return value.strip()


def _env_bool(
    name: str,
    default: bool = False,
) -> bool:

    value = os.getenv(name)

    if value is None:
        return default

    value = value.strip().lower()

    if value in {
        "true",
        "1",
        "yes",
        "on",
    }:
        return True

    if value in {
        "false",
        "0",
        "no",
        "off",
    }:
        return False

    raise RuntimeError(
        f"{name} must be true or false"
    )


def load_settings() -> Settings:

    database_url = _required_env(
        "DATABASE_URL"
    )

    test_database_url = os.getenv(
        "TEST_DATABASE_URL"
    )

    if test_database_url:
        test_database_url = test_database_url.strip()

    secret_key = _required_env(
        "SECRET_KEY"
    )

    if len(secret_key) < 32:
        raise RuntimeError(
            "SECRET_KEY must be at least 32 characters long"
        )

    frontend_origin = _required_env(
        "FRONTEND_ORIGIN"
    )

    cookie_secure = _env_bool(
        "COOKIE_SECURE",
        default=False,
    )

    dqn_model_path = os.getenv(
        "DQN_MODEL_PATH",
        "backend/models/adhyan_dqn.pth",
    ).strip()

    return Settings(
        database_url=database_url,
        test_database_url=test_database_url,
        secret_key=secret_key,
        frontend_origin=frontend_origin,
        cookie_secure=cookie_secure,
        dqn_model_path=dqn_model_path,
    )


settings = load_settings()