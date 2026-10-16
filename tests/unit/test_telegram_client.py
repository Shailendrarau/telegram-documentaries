"""Tests for the raw httpx Telegram client."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx
import pytest

from telegram_documentaries.telegram_client import TelegramAPIError, TelegramClient

BOT_TOKEN = "123456:TEST-SECRET-TOKEN"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def make_client(handler: Any) -> TelegramClient:
    transport = httpx.MockTransport(handler)
    session = httpx.Client(transport=transport)
    return TelegramClient(token=BOT_TOKEN, session=session)


def test_get_updates_builds_correct_url_and_params() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json={"ok": True, "result": [{"update_id": 1}]})

    client = make_client(handler)
    updates = client.get_updates(offset=5, limit=10, timeout=30)

    assert updates == [{"update_id": 1}]
    assert captured["url"].startswith(f"{BASE_URL}/getUpdates")
    assert captured["params"]["offset"] == "5"
    assert captured["params"]["limit"] == "10"
    assert captured["params"]["timeout"] == "30"


def test_get_updates_omits_offset_when_none() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json={"ok": True, "result": []})

    client = make_client(handler)
    client.get_updates(offset=None)

    assert "offset" not in captured["params"]


def test_get_updates_passes_allowed_updates_as_json() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json={"ok": True, "result": []})

    client = make_client(handler)
    client.get_updates(allowed_updates=["message", "edited_message"])

    assert json.loads(captured["params"]["allowed_updates"]) == [
        "message",
        "edited_message",
    ]


def test_send_message_posts_correct_url_and_payload() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 77}})

    client = make_client(handler)
    result = client.send_message(chat_id=42, text="hey mate!")

    assert result == {"message_id": 77}
    assert captured["url"] == f"{BASE_URL}/sendMessage"
    assert captured["method"] == "POST"
    assert captured["body"] == {"chat_id": 42, "text": "hey mate!"}


def test_send_message_merges_extra_kwargs_into_payload() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    client = make_client(handler)
    client.send_message(chat_id=42, text="hi", parse_mode="HTML")

    assert captured["body"] == {
        "chat_id": 42,
        "text": "hi",
        "parse_mode": "HTML",
    }


def test_get_updates_raises_api_error_when_ok_false() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"ok": False, "description": "Conflict: terminated by other"}
        )

    client = make_client(handler)

    with pytest.raises(TelegramAPIError) as exc_info:
        client.get_updates()

    assert "Conflict" in str(exc_info.value)


def test_send_message_raises_api_error_on_http_error_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"ok": False, "description": "Unauthorized"})

    client = make_client(handler)

    with pytest.raises(TelegramAPIError):
        client.send_message(chat_id=1, text="hi")


def test_get_updates_raises_on_non_json_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>not json</html>")

    client = make_client(handler)

    with pytest.raises(TelegramAPIError, match="non-JSON"):
        client.get_updates()


def test_get_updates_raises_when_result_is_not_a_list() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": {"update_id": 1}})

    client = make_client(handler)

    with pytest.raises(TelegramAPIError, match="result"):
        client.get_updates()


def test_send_message_raises_when_result_is_not_a_dict() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": [1, 2, 3]})

    client = make_client(handler)

    with pytest.raises(TelegramAPIError, match="result"):
        client.send_message(chat_id=1, text="hi")


def test_api_error_message_does_not_contain_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"ok": False, "description": "Server error"})

    client = make_client(handler)

    with pytest.raises(TelegramAPIError) as exc_info:
        client.send_message(chat_id=1, text="hi")

    assert BOT_TOKEN not in str(exc_info.value)


def test_client_never_logs_the_token(caplog: pytest.LogCaptureFixture) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("getUpdates"):
            return httpx.Response(200, json={"ok": True, "result": []})
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    client = make_client(handler)

    with caplog.at_level(logging.DEBUG):
        client.get_updates(offset=1)
        client.send_message(chat_id=1, text="hey mate!")

    assert BOT_TOKEN not in caplog.text
    assert "TEST-SECRET-TOKEN" not in caplog.text


def test_close_closes_owned_session() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": []})

    transport = httpx.MockTransport(handler)
    session = httpx.Client(transport=transport)
    client = TelegramClient(token=BOT_TOKEN, session=session)

    client.close()

    assert session.is_closed
