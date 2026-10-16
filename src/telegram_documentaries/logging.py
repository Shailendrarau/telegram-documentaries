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
    return logger


def log_operation(func: F) -> F:
    """Decorator to log operation start/end and duration."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = logging.getLogger("telegram_documentaries")
        start = time.time()
        logger.debug(f"Starting {func.__name__}")
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start
            logger.debug(f"Completed {func.__name__} in {duration:.4f}s")
            return result
        except Exception:
            duration = time.time() - start
            logger.exception(f"Failed {func.__name__} after {duration:.4f}s")
            raise

    return wrapper  # type: ignore[return-value]
