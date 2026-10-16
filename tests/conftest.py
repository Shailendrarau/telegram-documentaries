"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest

PACKAGE_LOGGER = "telegram_documentaries"


@pytest.fixture(autouse=True)
def _propagate_package_logs() -> Iterator[None]:
    """Ensure package logs reach pytest's caplog handler.

    ``setup_logging`` may disable propagation to avoid duplicate output; tests
    that assert on captured log records need propagation enabled.
    """
    logger = logging.getLogger(PACKAGE_LOGGER)
    previous = logger.propagate
    logger.propagate = True
    try:
        yield
    finally:
        logger.propagate = previous
