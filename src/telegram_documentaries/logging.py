"""Structured logging utilities."""

import functools
import logging
import sys
import time
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def setup_logging() -> logging.Logger:
    """Configure and return the package logger."""
    logger = logging.getLogger("telegram_documentaries")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    # Silence httpx's INFO logs to prevent leaking bot token in request URLs.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return logger


def log_operation(func: F) -> F:
    """Decorator to log operation start/end and duration."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Use the calling module's logger rather than the package-root logger.
        logger = logging.getLogger(func.__module__)
        start = time.perf_counter()
        logger.debug("Starting %s", func.__name__)
        try:
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start
            logger.debug("Completed %s in %.4fs", func.__name__, duration)
            return result
        except Exception:
            duration = time.perf_counter() - start
            logger.exception("Failed %s after %.4fs", func.__name__, duration)
            raise

    return wrapper  # type: ignore[return-value]
