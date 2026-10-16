# requirements.md — Phase 1: Repository & gateway

## Context

This spec implements the first phase from `SPECS/ROADMAP.md`:
- **Phase 1. Repository & gateway**: Scaffold the project, wire `.env`, and get a long-polling loop answering.

Constitution references:
- `TECH.md` §Stack/Architecture/Contracts/Logging/Session/Testing/Repo hygiene/README policy
- `MISSION.md` §Transport: Telegram **long polling**; no webhooks; in-memory only
- `ROADMAP.md` Phase 1 acceptance criteria

## Goal

Provide a minimal, production-lean entrypoint that:
1. Scaffolds the Python codebase with proper packaging and toolchain (tests, lint, types).
2. Loads `.env` securely (`TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`) without hardcoding secrets.
3. Implements a Telegram **long-polling** loop that parses updates into typed Pydantic models at the edge.
4. Replies to **every incoming message update** (regardless of type, for Phase 1) with the hardcoded text `hey mate!`.

## Scope (in)

- Python project layout: `src/telegram_documentaries/` with `__init__.py`, `__main__.py`.
- **Transport**: raw HTTP calls to `https://api.telegram.org/bot<token>/getUpdates` and `/sendMessage` via `httpx` (no ADK yet). Long polling with `timeout` parameter (e.g., 30s) and `offset` to acknowledge updates.
- **Typed models at the edge**: Pydantic models for `TelegramUpdate`, `TelegramMessage`, `TelegramChat`, `TelegramUser` (minimal subset sufficient to parse updates and reply). Parse once at the edge; do not pass raw dicts across module boundaries.
- **Gateway/polling loop**: read updates in a loop, parse each, reply `hey mate!` to the update's message chat, update `offset = max(update_id)+1`. Handle graceful shutdown (SIGINT/KeyboardInterrupt).
- **Config**: Pydantic Settings to load `.env`. Do not log secrets; never commit `.env`.
- **Logging**: structured logging across the gateway/client/models boundary. Use a decorator-style helper to log operations (avoid mixing logging calls directly into every business line where practical). Follow TECH.md policy (user-visible paths: catch & degrade gracefully, log loudly; non-critical invisible paths: fail loudly and log).
- **Toolchain**: `pyproject.toml` (PEP 621) with metadata and deps. **Committed lockfile**: `requirements.txt` with pinned versions (pip-based). Dev deps: `pytest`, `ruff`, `mypy`, `httpx`, `pydantic-settings` (or pydantic[dotenv]).
- **Scripts (ground truth)**:
  - `scripts/test` — run the test suite (pass locally)
  - `scripts/hooks` — run lint and type checks (ruff + mypy; both clean)
- **Testing**: Red/Green TDD. Tests cover boundary parsing (typed models), client calls, gateway logic (replies to all message updates, respects offset), and config loading.
- `.gitignore` already ignores `.env`; `.env.example` already present with placeholders. Must remain in sync.
- `README.md` must document: what this does (Phase 1), required env vars, how to run locally, and how to run tests/lint/type via `scripts/test`/`scripts/hooks`.

## Scope (out, YAGNI)

- No ADK, no agents/LLM calls.
- No Bouncer/Interviewer/Converter/Scripter/Narrator logic beyond gateway.
- No session state (Phase 1 is stateless gateway).
- No webhooks, Docker, auth, multi-tenancy, rate limiting, DB, retry backoff infrastructure.
- No video output, no TTS, no image generation.
- No media handling beyond receiving messages in updates (we don't process photo bytes in Phase 1; we just reply to any message).

## Decisions (from clarifications)

- **Transport**: raw `httpx` + Pydantic at the edge (no python-telegram-bot, no ADK yet).
- **Reply scope**: reply `hey mate!` to **every incoming message update** regardless of content type.
- **Dependencies/toolchain**: `pyproject.toml` + committed pinned `requirements.txt` (pip-based).
- **Lint/type**: `ruff` + `mypy` in `scripts/hooks`; `pytest` in `scripts/test`.

## Contracts at boundaries

- **Telegram API boundary**: parse JSON responses to `TelegramUpdate` models. Treat Telegram payloads as untrusted (arbitrary types/size/content). Unknown or partially malformed updates must not crash the loop: log loudly and continue.
- **Internal boundaries**: never pass raw dicts. Use typed models. `chat_id` modeled as `int` (value type consistency).
- **Config boundary**: load `TELEGRAM_BOT_TOKEN` and `GEMINI_API_KEY` from `.env` via Pydantic Settings; validate presence. Never log token/key.
- **Exit boundary**: graceful shutdown on `SIGINT/KeyboardInterrupt`.

## Logging & error policy

- Structured logging (module-level loggers). Prefer decorator for cross-cutting logging.
- **User-visible conversation path**: catch, degrade gracefully, log loudly; never raise into the user's flow.
- **Non-critical invisible work** (temp file cleanup if any later, but none now): fail loudly and log (raise). For Phase 1, polling loop must be resilient to transient parse/network errors.
- **Prohibited**: bare `except: pass`, swallowed exceptions, un-logged fallbacks, silent failure paths.

## Success criteria (acceptance)

Roadmap Phase 1:
1. `scripts/test` and `scripts/hooks` exist and run clean.
2. `.env` is git-ignored; `.env.example` lists `TELEGRAM_BOT_TOKEN` and `GEMINI_API_KEY` with placeholders (already present; must stay).
3. Bot long-polls and replies to a message with a hardcoded response (`hey mate!`).
4. Boundary parsing of a Telegram update into a typed model.

Also:
- Secrets never committed (grep guard in validation not required but validated).
- README, TECH, MISSION, ROADMAP stay consistent if any change warranted (Phase 1 likely only README needs update for "how to run").
- Cross-cutting: comprehensive logging with decorator preference, typed schemas over regexes, fail-loud vs degrade correctly applied.
