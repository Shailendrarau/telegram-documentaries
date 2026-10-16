"""Raw Telegram Bot API client built on ``httpx``.

Phase 1 uses long polling only (no webhooks). The client speaks the raw HTTP
API: it builds the ``/bot<token>/<method>`` URLs, issues the request, and
returns the decoded ``result`` payload. Telegram payloads are untrusted, so
callers validate the returned data into typed models at the edge.

The bot token is never logged — only the API method name appears in logs.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger("telegram_documentaries.telegram_client")

API_BASE_URL = "https://api.telegram.org"


class TelegramAPIError(RuntimeError):
    """Raised when the Telegram Bot API returns an error response."""


class TelegramClient:
    """Minimal long-polling Telegram Bot API client."""

    def __init__(
        self,
        token: str,
        timeout: float = 30.0,
        session: httpx.Client | None = None,
    ) -> None:
        self._token = token
        # httpx logs full request URLs at INFO, and the bot token is embedded in
        # the URL path. Silence its logger so the token is never written to logs.
        logging.getLogger("httpx").setLevel(logging.WARNING)
        self._client = session if session is not None else httpx.Client(timeout=timeout)

    def _url(self, api_method: str) -> str:
        return f"{API_BASE_URL}/bot{self._token}/{api_method}"

    def _request(
        self, http_method: str, api_method: str, **kwargs: Any
    ) -> dict[str, Any]:
        url = self._url(api_method)
        logger.debug("Telegram API request method=%s", api_method)
        try:
            response = self._client.request(http_method, url, **kwargs)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise TelegramAPIError(
                f"{api_method} failed with HTTP {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise TelegramAPIError(f"{api_method} request failed") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise TelegramAPIError(
                f"{api_method} returned a non-JSON response"
            ) from exc

        if not isinstance(data, dict) or not data.get("ok"):
            description = data.get("description") if isinstance(data, dict) else None
            raise TelegramAPIError(f"{api_method} error: {description}")

        logger.debug("Telegram API response method=%s ok=true", api_method)
        return data

    def get_updates(
        self,
        offset: int | None = None,
        limit: int = 100,
        timeout: int = 30,
        allowed_updates: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Long-poll Telegram for new updates; returns the raw ``result`` list."""
        params: dict[str, Any] = {"timeout": timeout, "limit": limit}
        if offset is not None:
            params["offset"] = offset
        if allowed_updates is not None:
            params["allowed_updates"] = json.dumps(allowed_updates)

        data = self._request("GET", "getUpdates", params=params)
        result = data.get("result", [])
        if not isinstance(result, list):
            raise TelegramAPIError("getUpdates returned an unexpected 'result' type")
        return result

    def send_message(self, chat_id: int, text: str, **kwargs: Any) -> dict[str, Any]:
        """Send a text message; returns the raw ``result`` message object."""
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text, **kwargs}
        data = self._request("POST", "sendMessage", json=payload)
        result = data.get("result")
        if not isinstance(result, dict):
            raise TelegramAPIError("sendMessage returned an unexpected 'result' type")
        return result

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()
