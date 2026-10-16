"""Tests for configuration loading (config.py)."""

from __future__ import annotations

import pathlib

import pytest
from pydantic import ValidationError

from telegram_documentaries.config import Settings, load_settings


def test_load_settings_reads_required_values_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:test-telegram-token")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")

    settings = load_settings(env_file=None)

    assert isinstance(settings, Settings)
    assert settings.telegram_bot_token.get_secret_value() == "123:test-telegram-token"
    assert settings.gemini_api_key.get_secret_value() == "test-gemini-key"


def test_missing_telegram_token_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")

    with pytest.raises(ValidationError):
        load_settings(env_file=None)


def test_missing_gemini_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:test-telegram-token")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ValidationError):
        load_settings(env_file=None)


@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_required_values_raise(
    monkeypatch: pytest.MonkeyPatch, blank: str
) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", blank)
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")

    with pytest.raises(ValidationError):
        load_settings(env_file=None)


def test_secrets_are_not_exposed_via_repr_or_str(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret_token = "999:super-secret-telegram-token"
    secret_key = "super-secret-gemini-key"
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", secret_token)
    monkeypatch.setenv("GEMINI_API_KEY", secret_key)

    settings = load_settings(env_file=None)

    assert secret_token not in repr(settings)
    assert secret_key not in repr(settings)
    assert secret_token not in str(settings)
    assert secret_key not in str(settings)


def test_load_settings_reads_from_env_file(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "TELEGRAM_BOT_TOKEN=from-file-token\nGEMINI_API_KEY=from-file-key\n"
    )

    settings = load_settings(env_file=env_file)

    assert settings.telegram_bot_token.get_secret_value() == "from-file-token"
    assert settings.gemini_api_key.get_secret_value() == "from-file-key"
