"""Application configuration loaded from the environment / ``.env``.

Secrets are modelled as ``SecretStr`` so they cannot be accidentally logged or
serialised. Values loaded here must never be written to logs.
"""

from __future__ import annotations

import pathlib

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository root when running from the src/ layout
# (src/telegram_documentaries/config.py -> parents[2]).
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _resolve_env_file(env_file: str | pathlib.Path) -> str | pathlib.Path:
    """Resolve ``env_file`` against the project root, not the CWD.

    A relative path (e.g. the default ``".env"``) is looked up in the project
    root first so the bot works regardless of where it is invoked from; the
    CWD-relative path is kept as a fallback. Absolute paths and paths that
    already exist are returned unchanged.
    """
    candidate = pathlib.Path(env_file)
    if candidate.is_absolute():
        return env_file
    root_candidate = _PROJECT_ROOT / candidate
    if root_candidate.is_file():
        return root_candidate
    return env_file


class Settings(BaseSettings):
    """Validated runtime settings.

    Reads ``TELEGRAM_BOT_TOKEN`` and ``GEMINI_API_KEY`` from the process
    environment, falling back to a ``.env`` file when present.
    """

    model_config = SettingsConfigDict(
        # ``env_file`` is resolved per-call by ``load_settings`` (project-root
        # first, CWD fallback); direct instantiation reads env vars only.
        env_file=None,
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

    ``env_file`` defaults to ``.env`` resolved against the project root (with a
    CWD fallback); pass ``None`` to disable file loading (environment variables
    still apply).
    """
    resolved = env_file if env_file is None else _resolve_env_file(env_file)
    # ``_env_file`` is a documented pydantic-settings runtime argument that is
    # not part of the generated ``__init__`` signature, hence the ignore.
    return Settings(_env_file=resolved)  # type: ignore[call-arg]
