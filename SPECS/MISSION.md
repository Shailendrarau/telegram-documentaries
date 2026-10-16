# MISSION.md — Product Contract

## Vision

**The Telegram Documentaries** turns a single portrait photo into a narrated,
comedy wildlife documentary about the person in it. A user messages a Telegram
bot a photo of themselves, answers a short interview about how they behave, and
receives back a hybrid animal portrait plus a dramatic voice-over describing
them as if they were the subject of a BBC nature documentary.

The whole experience happens inside Telegram. There is no web app, no login,
and no setup beyond `/start`.

## End-to-end user experience

1. User sends `/start`.
2. User uploads a **portrait photo**.
3. **The Bouncer** checks the image. A human is admitted; anything else is
   cheekily rejected and the session resets to step 1.
4. **The Interviewer** asks **5–7 questions, one at a time**, building a
   behavioural dossier tied to the user's `chat_id`, and proposes an animal.
5. **The Converter** fuses the original photo with the dossier into a **hybrid
   animal portrait**, sent straight back to the chat.
6. **The Scripter** writes a **single paragraph (~60–90 words)** of dramatic
   British-documentary narration from the dossier.
7. **The Narrator** renders that script as speech and sends it as a
   **Telegram voice note**.

## In scope

The five stages in steps 3–7 above (Bouncer, Interviewer, Converter, Scripter,
Narrator), plus:

- Telegram **long polling** as the transport (no webhooks, no public URL).
- In-memory session state keyed by `chat_id`.
- `/start` and `/restart` purge session state and temporary media **without**
  restarting the process.
- Graceful handling of out-of-order input — text when an image is expected, an
  image when an answer is expected, or an image at the wrong stage.
- Secrets supplied via `.env`.

## Out of scope (YAGNI)

These are explicitly **not** part of this project. Do not build, configure, or
plan for them:

- **No video output.** The deliverable is an image and a voice note.
- **No webhooks.** Long polling only; no public URL, TLS certificate, or
  reverse proxy.
- **No database.** State lives in memory for the life of the process.
- **No auth / multi-tenancy / user accounts.** `chat_id` is the only identity.
- **No Docker or deployment story.** It runs locally.
- **No rate limiting, queuing, or retry backoff infrastructure.**

## Success criteria

The feature is done when all of the following hold:

1. **Happy path:** a portrait photo produces a hybrid portrait image *and* a
   playable voice note, in order, with no manual intervention.
2. **Reset:** `/restart` (and `/start`) clears the dossier, the phase pointer,
   and any downloaded media, then returns the user to the photo prompt —
   without the process restarting.
3. **Out-of-order input:** unexpected text or media at any phase is handled
   gracefully — the conversation continues, the user is nudged, and no
   exception surfaces to the user.
4. **Rejection:** a non-human image is rejected with personality and resets
   state rather than producing a documentary.

## Non-negotiables

- **Never leak another user's session.** State is partitioned strictly by
  `chat_id`; one chat must never read or write another's dossier or media.
- **Never hardcode secrets.** `TELEGRAM_BOT_TOKEN` and `GEMINI_API_KEY` come
  from `.env`, which is git-ignored. No token, key, or `.env` value ever
  appears in source, tests, logs, or commit history.
