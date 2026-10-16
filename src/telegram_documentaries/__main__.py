"""Module entrypoint: ``python -m telegram_documentaries``."""

from __future__ import annotations

from telegram_documentaries.config import load_settings
from telegram_documentaries.gateway import run_gateway
from telegram_documentaries.logging import setup_logging

logger = setup_logging()


def main() -> int:
    """Load configuration and run the gateway loop."""
    try:
        settings = load_settings()
    except Exception:
        logger.exception(
            "Invalid or missing configuration; ensure .env defines "
            "TELEGRAM_BOT_TOKEN and GEMINI_API_KEY"
        )
        return 1

    logger.info("Starting The Telegram Documentaries gateway (Phase 1)")
    run_gateway(token=settings.telegram_bot_token.get_secret_value())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
