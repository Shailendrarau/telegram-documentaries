# validation.md — Phase 1: Repository & gateway

How we know Phase 1 succeeded and can be merged.

**Verified 2026-10-16 (automated + docs):** `scripts/test` → 53 passed; `scripts/hooks` → ruff check + format + mypy strict all clean; secrets hygiene confirmed; README policy satisfied. **Pending user confirmation:** the manual phone smoke test below (requires the user's real `TELEGRAM_BOT_TOKEN`) and the PR merge.

## Automated

- [x] `scripts/test` exists, is executable, and passes (all tests green).
- [x] `scripts/hooks` exists, is executable, and passes (`ruff` lint + format check, `mypy` type check clean).
- [x] Tests cover:
  - [x] Typed Telegram boundary parsing: valid text update, photo update, missing required fields, `chat_id` typed as `int`.
  - [x] Telegram client: `get_updates` and `send_message` build correct URLs/payloads and handle error responses.
  - [x] Gateway: replies `hey mate!` for every message update (text, photo, caption, etc.); advances `offset` by `max(update_id)+1`; a malformed update is logged and does not crash the loop.
  - [x] Config: loads `TELEGRAM_BOT_TOKEN` / `GEMINI_API_KEY` from env; missing values raise; values are never logged.
- [x] No `GEMINI_API_KEY` / `TELEGRAM_BOT_TOKEN` real values appear in tracked files (grep guard).
- [x] `.env` is git-ignored (already true; confirm).
- [x] `.env.example` still lists `TELEGRAM_BOT_TOKEN` and `GEMINI_API_KEY` with placeholders.

## Manual smoke test (documented in README) — **PENDING USER CONFIRMATION**

Prereq: a valid `TELEGRAM_BOT_TOKEN` in `.env`.

1. Run the bot: `python -m telegram_documentaries` (or documented run script).
2. From a Telegram client (phone or desktop), send any message to the bot (text or photo).
3. Expected: the bot replies exactly `hey mate!` every time, regardless of message content.
4. Expected: process keeps running after the reply; Ctrl+C shuts it down gracefully.
5. Expected: logs show the update was received/replied to, **without** printing the token or key.

## Spec-consistency / docs

- [x] `README.md` updated: describes Phase 1 behavior, env vars, how to run, and points to `scripts/test` and `scripts/hooks` by name (TECH.md README policy).
- [x] `TECH.md` still accurate (stack: Python; transport: Telegram long polling; boundary models: Pydantic). Update if reality diverges.
- [x] `MISSION.md` unchanged unless product behavior shifted (it should not have).
- [x] `ROADMAP.md` Phase 1 marked complete only after this validation passes.
- [x] Differences between the spec and what was actually implemented are surfaced and the specs updated with user approval.

## Merge readiness

- [x] All automated checks green.
- [ ] Manual smoke test performed by the user (bot replies `hey mate!` to any message from the phone).
- [ ] PR opened against `main`; user merges.
