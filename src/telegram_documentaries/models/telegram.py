"""Typed Pydantic boundary models for the Telegram Bot API.

Telegram payloads are untrusted external input. They are validated into these
models exactly once, at the edge, and typed models are passed onward — raw
dicts are never handed across module boundaries.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _BoundaryModel(BaseModel):
    """Base for boundary models: ignore unknown Telegram fields, allow aliases."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class TelegramUser(_BoundaryModel):
    """A Telegram user (minimal subset)."""

    id: int
    is_bot: bool | None = None
    first_name: str | None = None
    username: str | None = None


class TelegramChat(_BoundaryModel):
    """A Telegram chat (minimal subset)."""

    id: int
    type: str | None = None
    title: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None


class TelegramPhotoSize(_BoundaryModel):
    """One size variant of a photo attachment."""

    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: int | None = None


class TelegramMessage(_BoundaryModel):
    """A Telegram message (minimal subset)."""

    message_id: int
    from_: TelegramUser | None = Field(default=None, alias="from")
    chat: TelegramChat
    date: int
    text: str | None = None
    caption: str | None = None
    photo: list[TelegramPhotoSize] | None = None


class TelegramUpdate(_BoundaryModel):
    """A single Telegram update."""

    update_id: int
    message: TelegramMessage | None = None
