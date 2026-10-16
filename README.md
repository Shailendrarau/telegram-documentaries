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

## Environment

Create a `.env` in the project root with:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

`.env` is git-ignored. Never commit real values — `.env.example` carries
placeholders only.

## Running

*(_To be documented once the gateway phase lands.)_

## Development

Ground-truth scripts for the toolchain:

- `scripts/test` — run the test suite
- `scripts/hooks` — lint and type checks

Both must pass before any phase is considered complete. Tests are written
first (Red/Green TDD).

## Constitution

Project contract lives in `SPECS/`:

- [`SPECS/MISSION.md`](SPECS/MISSION.md) — what the product does and does not do
- [`SPECS/TECH.md`](SPECS/TECH.md) — stack, architecture, and policies
- [`SPECS/ROADMAP.md`](SPECS/ROADMAP.md) — ordered build plan
