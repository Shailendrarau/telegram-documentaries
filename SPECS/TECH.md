# TECH.md — Technical Contract

This file is the contract every agent and feature spec is judged against.
Policies here are binding.

## Stack

| Concern | Choice |
| --- | --- |
| Language | Python |
| Agent framework | Google Agent Development Kit (ADK) |
| Transport | Telegram Bot API, **long polling** |
| Vision gate / interview / script | Gemini 3.1 Flash Lite |
| Image generation | Gemini 3.1 Flash Image |
| Speech synthesis | `gemini-3.1-flash-tts-preview` (Gemini TTS) |
| Boundary models | Pydantic |
| Secrets | `.env` (`TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`) |

## Architecture

- **ADK hub-and-spoke.** The **Interviewer is the orchestrator**. Other stages
  are discrete agents/modules it dispatches to — they do not call each other
  directly.
- Each pipeline stage is a **separate, independently testable module**: Bouncer,
  Interviewer, Converter, Scripter. The Narrator is **not an agent**; it is a
  synthesis + delivery step.
- **Explicit state-machine phases.** The current phase is a named, typed value
  on the session record. Transitions are deliberate and logged — never inferred
  from incidental data.
- **Telegram long polling.** No webhooks, no public endpoint.

## Contracts at boundaries

- Parse **Telegram updates**, **Gemini responses**, and **TTS output** into
  typed Pydantic models at the edge.
- **Never pass raw dicts or unvalidated payloads across module boundaries.**
  Once validated, hand the typed model on.
- Treat all external input — Telegram messages, uploaded media, model output —
  as **untrusted and arbitrary in size, type, and content**. Validate before
  use; do not assume the model returns what was asked for.
- Prefer **schemas over regexes** for anything structured.

## Logging & error policy

- **Comprehensive structured logging** across the pipeline.
- Prefer **decorators** for logging cross-cutting concerns rather than mixing
  logging calls into business logic.
- Two rules, applied by where the code runs:
  - **Non-critical, user-invisible work** (temp file cleanup, post-response
    bookkeeping): **fail loudly and log** — raise, do not swallow.
  - **On a validated user's conversation path**: **catch and degrade
    gracefully** so the conversation continues. Log loudly, never raise into
    the user's flow.
- **Prohibited:** bare `except: pass`, swallowed exceptions, un-logged
  fallbacks, or any silent failure path.

## Session state

- **Versioned, per-`chat_id` schema.** Each session carries an explicit schema
  version so stale in-memory shapes are detectable rather than silently
  misread.
- **One shared state driver** is the sole reader/writer of session records.
  Stages never mutate session state directly.
- **Reset semantics:** `/start` and `/restart` purge the dossier, phase
  pointer, and any temporary media on disk, then return to the photo-prompt
  phase — **without restarting the process**.
- Sessions are strictly partitioned by `chat_id`; cross-chat access is a bug.

## Testing

- **Red/Green TDD.** Tests are written **before** code. A phase is not
  complete because the code runs — it is complete because a failing test was
  written first and then made to pass.
- Dev scripts live in `scripts/` and are **the ground truth** for the
  toolchain:
  - `scripts/test` — run the test suite
  - `scripts/hooks` — lint and type checks
- If a script does not exist yet, it must be created before a phase claims
  verification. Both must be documented here **and** in the README.

## Repo hygiene

- `.env` **must** be in `.gitignore`. Never commit `.env` or any real token.
- `.env.example` documents the required variable names with placeholder values
  only.
- Dependencies must be declared and reproducible (lockfile committed);
  `node_modules/`-style vendored dependency trees stay out of the repo.

## README policy

The README is developer-facing and must stay in sync with reality. It must
document:

- What the project does and the pipeline stages at a high level.
- Required environment variables and how to supply `.env`.
- How to run the bot locally.
- How to run tests, lint, and type checks — via `scripts/test` and
  `scripts/hooks`, by name.

Any change to the above is incomplete until the README is updated.
