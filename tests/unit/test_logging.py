"""Tests for structured logging setup and the log_operation decorator."""

from __future__ import annotations

import logging

import pytest

from telegram_documentaries.logging import log_operation, setup_logging


def test_setup_logging_returns_package_logger() -> None:
    logger = setup_logging()

    assert isinstance(logger, logging.Logger)
    assert logger.name == "telegram_documentaries"


def test_setup_logging_is_idempotent() -> None:
    first = setup_logging()
    second = setup_logging()

    assert first is second
    assert len(first.handlers) == 1


def test_log_operation_returns_result_and_logs_to_callers_module(
    caplog: pytest.LogCaptureFixture,
) -> None:
    @log_operation
    def add(a: int, b: int) -> int:
        return a + b

    with caplog.at_level(logging.DEBUG):
        result = add(2, 3)

    assert result == 5
    # The decorator logs to the decorated function's own module, not the
    # package-root logger.
    assert any(record.name == add.__module__ for record in caplog.records)
    assert "add" in caplog.text


def test_log_operation_reraises_and_logs_exception(
    caplog: pytest.LogCaptureFixture,
) -> None:
    @log_operation
    def boom() -> None:
        raise ValueError("nope")

    with (
        caplog.at_level(logging.DEBUG),
        pytest.raises(ValueError, match="nope"),
    ):
        boom()

    assert any(record.name == boom.__module__ for record in caplog.records)
    assert "boom" in caplog.text
