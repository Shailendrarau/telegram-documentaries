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
from typing import Any, Protocol

from pydantic import ValidationError

from telegram_documentaries.logging import log_operation
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


@log_operation
def process_update(update: TelegramUpdate, client: PollingClient) -> None:
    """Reply to a single parsed update if it carries a message."""
    message = update.message
    if message is None:
        logger.debug("Update %s has no message; nothing to reply to", update.update_id)
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
        logger.exception("Failed to parse Telegram update; skipping: %r", raw)
        return

    try:
        process_update(update, client)
    except Exception:
        logger.exception("Failed to handle update_id=%s; continuing", update.update_id)


def run_gateway(
    token: str,
    poll_timeout: int = 30,
    *,
    client: PollingClient | None = None,
) -> None:
    """Run the long-polling gateway loop until interrupted.

    A client may be injected for testing; otherwise one is constructed from
    ``token`` and closed on shutdown.
    """
    owns_client = client is None
    polling: PollingClient = (
        client
        if client is not None
        else TelegramClient(token=token, timeout=float(poll_timeout))
    )
    offset: int | None = None

    logger.info("Gateway starting long-polling")
    try:
        while True:
            try:
                raw_updates = polling.get_updates(offset=offset, timeout=poll_timeout)
            except Exception:
                logger.exception("Failed to fetch updates; retrying")
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
