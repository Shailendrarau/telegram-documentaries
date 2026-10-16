"""Boundary parsing tests for Telegram Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from telegram_documentaries.models.telegram import (
    TelegramChat,
    TelegramMessage,
    TelegramUpdate,
    TelegramUser,
)

TEXT_UPDATE: dict[str, object] = {
    "update_id": 100,
    "message": {
        "message_id": 10,
        "from": {
            "id": 7,
            "is_bot": False,
            "first_name": "Ada",
            "username": "ada",
        },
        "chat": {"id": 42, "type": "private", "first_name": "Ada"},
        "date": 1_700_000_000,
        "text": "/start",
    },
}

PHOTO_UPDATE: dict[str, object] = {
    "update_id": 101,
    "message": {
        "message_id": 11,
        "chat": {"id": 42, "type": "private"},
        "date": 1_700_000_001,
        "photo": [
            {
                "file_id": "small-file",
                "file_unique_id": "unique-small",
                "width": 90,
                "height": 80,
                "file_size": 1_234,
            },
            {
                "file_id": "large-file",
                "file_unique_id": "unique-large",
                "width": 1_280,
                "height": 960,
            },
        ],
    },
}


def test_parses_text_update_into_typed_models() -> None:
    update = TelegramUpdate.model_validate(TEXT_UPDATE)

    assert isinstance(update, TelegramUpdate)
    assert update.update_id == 100
    assert isinstance(update.message, TelegramMessage)
    message = update.message
    assert message is not None
    assert message.message_id == 10
    assert message.text == "/start"
    assert isinstance(message.chat, TelegramChat)
    assert message.chat.id == 42
    assert isinstance(message.from_, TelegramUser)
    assert message.from_ is not None
    assert message.from_.id == 7
    assert message.from_.first_name == "Ada"


def test_chat_id_is_typed_as_int() -> None:
    update = TelegramUpdate.model_validate(TEXT_UPDATE)

    assert update.message is not None
    assert isinstance(update.message.chat.id, int)
    assert type(update.message.chat.id) is int


def test_parses_photo_update_without_text() -> None:
    update = TelegramUpdate.model_validate(PHOTO_UPDATE)

    assert update.message is not None
    message = update.message
    assert message.text is None
    assert message.photo is not None
    assert len(message.photo) == 2
    assert message.photo[0].file_id == "small-file"
    assert message.photo[0].file_size == 1_234
    assert message.photo[1].file_size is None


def test_update_without_message_is_parsed() -> None:
    update = TelegramUpdate.model_validate({"update_id": 5})

    assert update.update_id == 5
    assert update.message is None
    assert update.edited_message is None
    assert update.channel_post is None
    assert update.edited_channel_post is None


def test_update_missing_update_id_fails_validation() -> None:
    with pytest.raises(ValidationError):
        TelegramUpdate.model_validate({"message": TEXT_UPDATE["message"]})


def test_message_missing_required_chat_fails_validation() -> None:
    with pytest.raises(ValidationError):
        TelegramMessage.model_validate({"message_id": 1, "date": 0})


def test_update_with_wrong_typed_field_fails_validation() -> None:
    malformed = {"update_id": 1, "message": "this-is-not-a-message-object"}

    with pytest.raises(ValidationError):
        TelegramUpdate.model_validate(malformed)


def test_from_alias_is_parsed_and_populate_by_name_is_enabled() -> None:
    by_alias = TelegramMessage.model_validate(
        {"message_id": 1, "chat": {"id": 1}, "date": 0, "from": {"id": 9}}
    )
    by_name = TelegramMessage.model_validate(
        {"message_id": 1, "chat": {"id": 1}, "date": 0, "from_": {"id": 9}}
    )

    assert by_alias.from_ is not None and by_alias.from_.id == 9
    assert by_name.from_ is not None and by_name.from_.id == 9


def test_unknown_fields_are_ignored() -> None:
    update = TelegramUpdate.model_validate(
        {"update_id": 1, "unknown_field": {"nested": True}}
    )

    assert update.update_id == 1
