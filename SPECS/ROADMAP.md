# ROADMAP.md — Ordered Build Plan

One phase per pipeline capability, in dependency order. A phase is marked
**complete only when verified** — code running is not verification; a red test
turned green is.

## 1. Repository & gateway

Scaffold the project, wire `.env`, and get a long-polling loop answering.

- **Acceptance criteria**
  - `scripts/test` and `scripts/hooks` exist and run clean.
  - `.env` is git-ignored; `.env.example` lists `TELEGRAM_BOT_TOKEN` and
    `GEMINI_API_KEY` with placeholders.
  - The bot long-polls and replies to a message with a hardcoded response.
  - Boundary parsing of a Telegram update into a typed model.
- **Rubric criterion:** project runs end-to-end; secrets never committed.

## 2. Bouncer — vision gate

Confirm a human is in the photo; cheekily reject anything else and reset.

- **Acceptance criteria**
  - A human portrait advances to the Interviewer phase.
  - A non-human image receives a rejection message and **resets session state**
    to the photo prompt.
  - Rejection is a logged, typed outcome — not a string match.
  - Out-of-scope for this stage: no TTS, no video, text/image classification
    only.
- **Rubric criterion:** input validation with personality; state reset works.

## 3. Interviewer — orchestrator & dossier

Sequential stateful Q&A that accumulates the behavioural dossier.

- **Acceptance criteria**
  - Asks **5–7 questions, one at a time**; never dumps them as a batch.
  - Answers accumulate into a dossier keyed to `chat_id`.
  - Produces a **suggested animal** alongside the dossier summary.
  - Acts as the orchestrator, dispatching to the Converter and Scripter.
  - Unexpected text/media mid-interview is handled without raising to the user.
- **Rubric criterion:** stateful multi-turn conversation; orchestrator role.

## 4. Converter — hybrid portrait

Fuse the original photo with the dossier into one image.

- **Acceptance criteria**
  - Sends photo + dossier to Gemini 3.1 Flash Image and returns the hybrid
    portrait **directly to Telegram** with no intermediate text hop.
  - Result is a Telegram-compatible image format.
  - Model refusal or malformed output degrades gracefully, logged loudly.
- **Rubric criterion:** multimodal image generation delivered to chat.

## 5. Scripter — narration

One paragraph of dramatic British-documentary narration.

- **Acceptance criteria**
  - Output is a **single paragraph, ~60–90 words**, built from the dossier.
  - Tone is dramatic British documentary.
  - Word count is asserted by a test, not eyeballed.
- **Rubric criterion:** LLM text generation from accumulated state.

## 6. Narrator — TTS delivery

Synthesize the script and send it as a voice note. Not an agent.

- **Acceptance criteria**
  - Script routes to `gemini-3.1-flash-tts-preview`.
  - Output is rendered to a **Telegram-compatible audio format (OGG/MP3)**.
  - Audio is sent to the chat and plays.
  - Failure to synthesize falls back to sending the script as text, logged.
- **Rubric criterion:** text-to-speech delivered into the conversation.

## 7. Resilience

Make the happy path survive real users.

- **Acceptance criteria**
  - `/restart` and `/start` **purge session state and temporary media** without
    restarting the process, then return to the photo prompt.
  - Wrong-payload-at-wrong-stage guards: text when an image is expected, an
    image when an answer is expected, media at the Converter/Scripter stages.
  - API timeouts and errors do not crash the loop; conversation continues.
  - No cross-`chat_id` state leakage under interleaved chats.
- **Rubric criterion:** graceful degradation; reset semantics; no session leaks.

---

Phases are dependency-ordered: 2 depends on 1, 3 on 2, 4 and 5 on 3, 6 on 5,
and 7 is validated against all of the above.
