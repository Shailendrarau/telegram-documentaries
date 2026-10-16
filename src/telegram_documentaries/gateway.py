"""Gateway long-polling loop.

Reads updates from Telegram, parses each raw payload into a typed
``TelegramUpdate`` at the edge, and replies with a hardcoded greeting for every
incoming message update regardless of content type.

Resilience: this runs on the user-visible conversation path, so transient
network and parse errors are caught, logged loudly, and the loop continues
rather than crashing. Shutdown is graceful on ``SIGINT`` / ``KeyboardInterrupt``.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any, Protocol

from pydantic import ValidationError

from telegram_documentaries.models.telegram import TelegramUpdate
from telegram_documentaries.telegram_client import TelegramClient

logger = logging.getLogger("telegram_documentaries.gateway")

REPLY_TEXT = "hey mate!"


class PollingClient(Protocol):
    """Structural interface the gateway needs from a Telegram client."""

    def get_updates(
        self,
        offset: int | None = None,
        limit: int = 100,
        timeout: int = 30,
        allowed_updates: list[str] | None = None,
    ) -> list[dict[str, Any]]: ...

    def send_message(
        self, chat_id: int, text: str, **kwargs: Any
    ) -> dict[str, Any]: ...


def _extract_update_id(raw: object) -> int | None:
    if isinstance(raw, dict):
        value = raw.get("update_id")
        if isinstance(value, int):
            return value
    return None


def process_update(update: TelegramUpdate, client: PollingClient) -> None:
    """Reply to a single parsed update if it carries a message.

    Not decorated with ``@log_operation``: failures here are already logged
    once (with ``update_id`` context) by ``_process_raw``, the boundary that
    owns the conversation path. Logging the exception twice would duplicate
    the traceback.
    """
    message = update.message
    if message is None:
        logger.info("Update %s has no message; skipping", update.update_id)
        return
    client.send_message(chat_id=message.chat.id, text=REPLY_TEXT)
    logger.info(
        "Replied to update_id=%s in chat_id=%s",
        update.update_id,
        message.chat.id,
    )


def _process_raw(raw: dict[str, Any], client: PollingClient) -> None:
    """Parse a raw update at the edge, then handle it without crashing the loop."""
    try:
        update = TelegramUpdate.model_validate(raw)
    except ValidationError:
        # Telegram payloads are untrusted and may be arbitrarily large; log a
        # truncated preview with its size, never the full payload.
        raw_repr = repr(raw)
        truncated = raw_repr[:500]
        ellipsis = "..." if len(raw_repr) > 500 else ""
        logger.error(
            "Failed to parse Telegram update (len=%s keys=%s); skipping: %s%s",
            len(raw_repr),
            list(raw),
            truncated,
            ellipsis,
        )
        return

    try:
        process_update(update, client)
    except Exception:
        logger.exception("Failed to handle update_id=%s; continuing", update.update_id)


def _handle_poll_failure(
    exc: Exception,
    poll_interval: float = 5.0,
    sleep: Callable[[float], None] | None = None,
) -> None:
    """Log a polling failure loudly, then pause before the next poll.

    The pause (default 5s, injectable for tests) prevents a tight CPU/log
    spin when polling fails persistently (e.g. a 401 bad token or a 409
    getUpdates conflict).
    """
    logger.exception(
        "Failed to fetch updates (%s); retrying in %.1fs", exc, poll_interval
    )
    if poll_interval > 0:
        (sleep if sleep is not None else time.sleep)(poll_interval)


def run_gateway(
    token: str,
    poll_timeout: int = 30,
    *,
    client: PollingClient | None = None,
    poll_interval: float = 5.0,
) -> None:
    """Run the long-polling gateway loop until interrupted.

    A client may be injected for testing; otherwise one is constructed from
    ``token`` and closed on shutdown.
    """
    owns_client = client is None
    polling: PollingClient = (
        client
        if client is not None
        else TelegramClient(token=token, timeout=float(poll_timeout) + 5.0)
    )
    offset: int | None = None

    logger.info("Gateway starting long-polling")
    try:
        while True:
            try:
                raw_updates = polling.get_updates(
                    offset=offset,
                    timeout=poll_timeout,
                    allowed_updates=["message"],
                )
            except Exception as exc:
                _handle_poll_failure(exc, poll_interval=poll_interval)
                continue

            max_update_id: int | None = None
            for raw in raw_updates:
                raw_id = _extract_update_id(raw)
                if raw_id is not None and (
                    max_update_id is None or raw_id > max_update_id
                ):
                    max_update_id = raw_id
                _process_raw(raw, polling)

            if max_update_id is not None:
                offset = max_update_id + 1
    except KeyboardInterrupt:
        logger.info("Gateway shut down gracefully")
    finally:
        if owns_client and isinstance(polling, TelegramClient):
            polling.close()
