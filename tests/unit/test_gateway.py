"""Tests for the gateway long-polling loop."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

import pytest

from telegram_documentaries.gateway import REPLY_TEXT, run_gateway
from telegram_documentaries.telegram_client import TelegramAPIError

TOKEN = "123456:TEST-SECRET-TOKEN"


class FakeClient:
    """Scripted test double for the Telegram client boundary."""

    def __init__(
        self,
        script: Sequence[list[dict[str, Any]] | BaseException],
        send_error: BaseException | None = None,
    ) -> None:
        self._script = list(script)
        self._send_error = send_error
        self.offsets: list[int | None] = []
        self.sent: list[tuple[int, str]] = []

    def get_updates(
        self,
        offset: int | None = None,
        limit: int = 100,
        timeout: int = 30,
        allowed_updates: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        self.offsets.append(offset)
        if not self._script:
            raise KeyboardInterrupt
        item = self._script.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    def send_message(self, chat_id: int, text: str, **kwargs: Any) -> dict[str, Any]:
        if self._send_error is not None:
            raise self._send_error
        self.sent.append((chat_id, text))
        return {"message_id": len(self.sent)}


def message_update(
    update_id: int, chat_id: int, **message_fields: Any
) -> dict[str, Any]:
    message: dict[str, Any] = {
        "message_id": update_id,
        "chat": {"id": chat_id, "type": "private"},
        "date": 0,
    }
    message.update(message_fields)
    return {"update_id": update_id, "message": message}


def test_reply_text_is_exactly_hey_mate() -> None:
    assert REPLY_TEXT == "hey mate!"


def test_gateway_replies_to_text_message() -> None:
    fake = FakeClient([[message_update(1, 42, text="/start")]])

    run_gateway(token=TOKEN, client=fake)

    assert fake.sent == [(42, "hey mate!")]


def test_gateway_replies_to_photo_message_without_text() -> None:
    fake = FakeClient(
        [
            [
                message_update(
                    2,
                    42,
                    photo=[
                        {
                            "file_id": "f",
                            "file_unique_id": "u",
                            "width": 10,
                            "height": 10,
                        }
                    ],
                )
            ]
        ]
    )

    run_gateway(token=TOKEN, client=fake)

    assert fake.sent == [(42, "hey mate!")]


def test_gateway_replies_to_caption_only_message() -> None:
    fake = FakeClient([[message_update(3, 7, caption="look at this")]])

    run_gateway(token=TOKEN, client=fake)

    assert fake.sent == [(7, "hey mate!")]


def test_gateway_ignores_updates_without_message() -> None:
    fake = FakeClient([[{"update_id": 4}]])

    run_gateway(token=TOKEN, client=fake)

    assert fake.sent == []


def test_gateway_replies_to_every_message_in_a_batch() -> None:
    fake = FakeClient(
        [
            [
                message_update(1, 10, text="a"),
                message_update(2, 20, text="b"),
                message_update(3, 30, text="c"),
            ]
        ]
    )

    run_gateway(token=TOKEN, client=fake)

    assert fake.sent == [(10, "hey mate!"), (20, "hey mate!"), (30, "hey mate!")]


def test_gateway_advances_offset_to_max_update_id_plus_one() -> None:
    fake = FakeClient(
        [
            [
                message_update(3, 1, text="a"),
                message_update(7, 2, text="b"),
                message_update(5, 3, text="c"),
            ],
            [],
        ]
    )

    run_gateway(token=TOKEN, client=fake)

    assert fake.offsets[0] is None
    assert fake.offsets[1] == 8


def test_gateway_offset_does_not_advance_without_updates() -> None:
    fake = FakeClient([[], []])

    run_gateway(token=TOKEN, client=fake)

    assert fake.offsets  # the loop polled at least once
    assert all(offset is None for offset in fake.offsets)


def test_gateway_malformed_update_is_logged_and_loop_continues(
    caplog: pytest.LogCaptureFixture,
) -> None:
    fake = FakeClient(
        [
            [{"not": "a valid update"}],
            [message_update(2, 42, text="still works")],
        ]
    )

    with caplog.at_level(logging.ERROR):
        run_gateway(token=TOKEN, client=fake)

    # The malformed update did not crash the loop; the next update was handled.
    assert fake.sent == [(42, "hey mate!")]
    assert "update" in caplog.text.lower()


def test_malformed_update_with_update_id_still_advances_offset() -> None:
    fake = FakeClient([[{"update_id": 42, "message": "not-an-object"}], []])

    run_gateway(token=TOKEN, client=fake)

    assert fake.offsets[1] == 43


def test_gateway_continues_after_send_message_failure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    fake = FakeClient(
        [[message_update(1, 42, text="a"), message_update(2, 43, text="b")]],
        send_error=RuntimeError("network down"),
    )

    with caplog.at_level(logging.ERROR):
        run_gateway(token=TOKEN, client=fake)

    assert fake.offsets[1] == 3
    assert "network down" in caplog.text


def test_gateway_continues_after_client_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    fake = FakeClient(
        [
            TelegramAPIError("temporary failure"),
            [message_update(9, 42, text="recovered")],
        ]
    )

    with caplog.at_level(logging.WARNING):
        run_gateway(token=TOKEN, client=fake)

    assert fake.sent == [(42, "hey mate!")]


def test_gateway_shuts_down_gracefully_on_keyboard_interrupt(
    caplog: pytest.LogCaptureFixture,
) -> None:
    fake = FakeClient([])

    with caplog.at_level(logging.INFO):
        run_gateway(token=TOKEN, client=fake)

    assert "shut" in caplog.text.lower() or "stop" in caplog.text.lower()


def test_gateway_logs_do_not_contain_token(caplog: pytest.LogCaptureFixture) -> None:
    fake = FakeClient([[message_update(1, 42, text="hi")]])

    with caplog.at_level(logging.DEBUG):
        run_gateway(token=TOKEN, client=fake)

    assert "TEST-SECRET-TOKEN" not in caplog.text
