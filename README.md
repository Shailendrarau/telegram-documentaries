# The Telegram Documentaries

Upload a portrait to Telegram, get back a narrated wildlife documentary about
yourself — a hybrid animal portrait plus a dramatic British voice-over.

## Pipeline

| # | Stage | What it does |
|---|-------|--------------|
| 1 | **Bouncer** | Vision gate. Admits humans, cheekily rejects everything else and resets state. |
| 2 | **Interviewer** | Orchestrator. Asks 5–7 questions one at a time, builds a behavioural dossier, suggests an animal. |
| 3 | **Converter** | Fuses the photo + dossier into a hybrid animal portrait. |
| 4 | **Scripter** | Writes one paragraph (~60–90 words) of dramatic documentary narration. |
| 5 | **Narrator** | *Not an agent* — renders the script to speech and sends a voice note. |

Transport is Telegram **long polling** (no webhooks, no public URL). Session
state is held in memory keyed by `chat_id`.

## Status

The project is built one phase at a time (`SPECS/ROADMAP.md`). **Phase 1 —
Repository & gateway** is implemented: the bot **long-polls Telegram and replies
exactly `hey mate!` to every incoming message**, regardless of content type. No
agent, LLM, or session logic exists yet.

## Environment

The gateway reads secrets from the process environment, falling back to a
`.env` file in the repository root. Required variables:

| Variable | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather); used for `getUpdates` / `sendMessage`. |
| `GEMINI_API_KEY` | Gemini API key. Required by the configuration contract; unused by the Phase 1 gateway but needed by later phases. |

Copy the template and fill in real values:

```
cp .env.example .env
```

`.env` is git-ignored. Never commit real values — `.env.example` carries
placeholders only.

## Install

Requires **Python 3.11+**. From the repository root:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` is a fully-resolved, pinned lockfile (direct and transitive
dependencies) for reproducible installs.

## Running

Run from the **repository root** (the project-root `.env` is resolved relative
to the package, but running from the root keeps paths and logs predictable):

```
python -m telegram_documentaries
```

The bot long-polls Telegram (`getUpdates`) and replies `hey mate!` to every
incoming message update. `Ctrl+C` shuts it down gracefully.

## Development

Ground-truth scripts for the toolchain:

- `scripts/test` — run the test suite (pytest)
- `scripts/hooks` — lint and type checks (`ruff` + `mypy`)

Both must pass before any phase is considered complete. Tests are written
first (Red/Green TDD).

## Manual smoke test

Prereq: a valid `TELEGRAM_BOT_TOKEN` in `.env` (from the Phase 1 validation
spec, `SPECS/2026-10-16-repo-gateway/validation.md`).

1. Run the bot from the repository root: `python -m telegram_documentaries`.
2. From a Telegram client (phone or desktop), send any message to the bot
   (text or photo).
3. Expected: the bot replies exactly `hey mate!` every time, regardless of
   message content.
4. Expected: the process keeps running after the reply; `Ctrl+C` shuts it down
   gracefully.
5. Expected: logs show the update was received/replied to, **without** printing
   the token or key.

## Constitution

Project contract lives in `SPECS/`:

- [`SPECS/MISSION.md`](SPECS/MISSION.md) — what the product does and does not do
- [`SPECS/TECH.md`](SPECS/TECH.md) — stack, architecture, and policies
- [`SPECS/ROADMAP.md`](SPECS/ROADMAP.md) — ordered build plan
