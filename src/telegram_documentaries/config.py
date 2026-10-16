"""Application configuration loaded from the environment / ``.env``.

Secrets are modelled as ``SecretStr`` so they cannot be accidentally logged or
serialised. Values loaded here must never be written to logs.
"""

from __future__ import annotations

import pathlib

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime settings.

    Reads ``TELEGRAM_BOT_TOKEN`` and ``GEMINI_API_KEY`` from the process
    environment, falling back to a ``.env`` file when present.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    telegram_bot_token: SecretStr = Field(..., min_length=1)
    gemini_api_key: SecretStr = Field(..., min_length=1)

    @field_validator("telegram_bot_token", "gemini_api_key")
    @classmethod
    def _reject_blank(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("must not be blank")
        return value


def load_settings(env_file: str | pathlib.Path | None = ".env") -> Settings:
    """Load and validate settings.

    ``env_file`` defaults to ``.env``; pass ``None`` to disable file loading
    (environment variables still apply).
    """
    # ``_env_file`` is a documented pydantic-settings runtime argument that is
    # not part of the generated ``__init__`` signature, hence the ignore.
    return Settings(_env_file=env_file)  # type: ignore[call-arg]
