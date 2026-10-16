# plan.md — Phase 1: Repository & gateway

Implement Red/Green TDD. All checks must run via `scripts/test` and `scripts/hooks`.

## Task groups

### 1) Project scaffolding
- [x] Create `pyproject.toml` (PEP 621): name, version, description, requires-python >=3.11, dependencies (httpx, pydantic, pydantic-settings, python-dotenv), dev-dependencies (pytest, ruff, mypy).
- [x] Create pinned `requirements.txt` (committed lockfile). Mirror deps + dev-deps (or include all).
- [x] Create `src/telegram_documentaries/__init__.py` (version etc.).
- [x] Create `src/telegram_documentaries/__main__.py` (entrypoint).
- [x] Add `.gitignore` entries if needed (already covers `.env` and node_modules; no Python build artifacts to add unless desired, but keep minimal). Ensure `.env` remains ignored.

### 2) Config & logging foundation
- [x] Create `src/telegram_documentaries/logging.py` with structured logging setup (`setup_logging()` returning logger) and a `@log_operation` decorator (logs start/end, duration, and exceptions). 
  - Non-critical invisible: decorator can let exceptions propagate (fail loud). User-visible paths use try/except in caller.
- [x] Create `src/telegram_documentaries/config.py` with Pydantic Settings: `TELEGRAM_BOT_TOKEN` (str, required), `GEMINI_API_KEY` (str, required). Load from `.env`. Do **not** log values.

### 3) Typed boundary models (Telegram)
- [x] Create `src/telegram_documentaries/models/__init__.py` and `src/telegram_documentaries/models/telegram.py`.
- [x] Define Pydantic models (minimal subset): `TelegramUser` (id:int, is_bot:bool|None=None, first_name:str|None=None, username:str|None=None), `TelegramChat` (id:int, type:str|None=None, title:str|None=None, first_name:str|None=None, last_name:str|None=None, username:str|None=None), `TelegramMessage` (message_id:int, from_:User|None=None, chat:Chat, date:int, text:str|None=None, photo:list|None=None, caption:str|None=None), `TelegramUpdate` (update_id:int, message:Message|None=None, edited_message:Message|None=None, channel_post:Message|None=None, edited_channel_post:Message|None=None). 
  - Use `from_` alias with `Field(..., alias="from")` and `model_config = ConfigDict(populate_by_name=True)` or Pydantic v2 style. 
  - Keep minimal; parse at edge.
- [x] Write unit tests first for models (Red): valid update with text, update with photo (no text), missing required fields (should fail validation), typed chat_id is int.

### 4) Telegram client (raw httpx)
- [x] Create `src/telegram_documentaries/telegram_client.py`. Methods:
  - `__init__(self, token: str, timeout: float = 30.0, session: httpx.Client | None = None)`
  - `get_updates(self, offset: int | None = None, limit: int = 100, timeout: int = 30, allowed_updates: list[str] | None = None) -> list[dict]` — returns raw JSON 'result' (or parsed). But return list of update dicts.
  - `send_message(self, chat_id: int, text: str, **kwargs) -> dict` 
  - Build URL from token; use httpx. Log request context without logging token.
- [x] Write tests first (Red) mocking httpx: get_updates returns payload, send_message posts correctly, handles errors. (Use httpx mocking or fake client.)

### 5) Gateway / polling loop
- [x] Create `src/telegram_documentaries/gateway.py`. 
  - `run_gateway(token: str, poll_timeout: int = 30) -> None` — long-poll loop. 
  - For each update: parse via Pydantic models at edge. If update.message exists, reply "hey mate!" to update.message.chat.id. 
  - `offset = update.update_id + 1` after processing. 
  - Handle parse failures: log loudly and continue (don't crash). Network errors: log and continue/backoff? Keep simple: catch Exception in loop body, log, continue (user-visible path degrade gracefully). 
  - Graceful shutdown on SIGINT/KeyboardInterrupt.
- [x] Write tests first (Red): fake client returns updates with/without message; replies sent; offset advances; malformed update doesn't crash loop.
- [x] Wire `__main__` to call `run_gateway` from config.

### 6) Scripts (ground truth)
- [x] Create `scripts/test` (executable) — runs pytest. Example: `#!/usr/bin/env bash; set -e; python -m pytest -q` (or `PYTHONPATH=src python -m pytest -q`).
- [x] Create `scripts/hooks` (executable) — runs ruff + mypy. Example: `#!/usr/bin/env bash; set -e; python -m ruff check .; python -m ruff format --check .; python -m mypy src tests` (adjust as needed).

### 7) README update
- [x] Update `README.md`: document what Phase 1 does (gateway replies "hey mate!"), required env vars, how to run locally (`python -m telegram_documentaries` or console script), how to run tests/lint/type via `scripts/test` and `scripts/hooks`. Keep consistent with constitution.

### 8) Green phase (make tests pass)
- [x] Implement models to make model tests pass.
- [x] Implement client to pass client tests.
- [x] Implement gateway/logging/config to pass integration tests.
- [x] Ensure `scripts/test` and `scripts/hooks` pass.

### 9) Hygiene & verification
- [x] Verify `.env` not committed, `.env.example` unchanged in content except maybe not needed. No secrets in source/logs/tests.
- [x] Verify boundary parsing is enforced (no raw dicts passed across modules beyond boundary call sites).
- [x] All acceptance criteria from requirements satisfied.

## Deviations from plan (recorded at verification, 2026-10-16)

- **Task 3 — `TelegramUpdate` narrowed.** The plan listed `edited_message`,
  `channel_post`, and `edited_channel_post` fields. The implementation models
  only `update_id` + `message` (with `extra="ignore"`), because the gateway
  requests `allowed_updates=["message"]` so those variants never arrive;
  if they do, they parse with `message = None` and are skipped.
  Covered by `test_unmodelled_message_variant_fields_are_ignored`.
- **Task 3 — `photo` typed more strongly.** Modelled as
  `list[TelegramPhotoSize] | None` (new `TelegramPhotoSize` model) instead of
  a bare `list | None`. Strictly stronger than planned.
- **Task 5 — `run_gateway` signature extended** with keyword-only `client`
  (test injection) and `poll_interval` (failure backoff pause).
  Offset semantics follow validation.md: `max(update_id) + 1` per batch,
  not `update.update_id + 1` per update.
- **Task 2/5 — extras beyond plan:** config resolves `.env` against the
  project root (CWD-independent) and stores secrets as `SecretStr`;
  the gateway truncates logged raw payloads (untrusted-input size cap),
  silences httpx INFO logs (token lives in request URLs), and closes
  an owned client on shutdown.
