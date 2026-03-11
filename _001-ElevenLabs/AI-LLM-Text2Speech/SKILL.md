---
name:
description: Converts text documents or prompts directly into lifelike MP3 audio files using the ElevenLabs API. Use when the user asks to generate audio, narrate text, or trigger text-to-speech.
---

# AI-LLM-Text2Speech Skill

## When to Use This Skill
- User says "convert this text to speech", "generate audio", or "narrate this"
- User provides a `.txt` file and requests an MP3 version
- User wants to use ElevenLabs models for lifelike voice generation

---

## Workflow
- [ ] 1. Ensure `ELEVENLABS_API_KEY` is available in the environment.
- [ ] 2. If passing a file, read the content of the `.txt` file.
- [ ] 3. Run `scripts/text2speech.py` with the raw text.
- [ ] 4. Save the combined output `.mp3` and `.alignment.json` to `_output/`.
- [ ] 5. Surface the `.mp3` for playback or download.

---

## Instructions

This skill utilizes the official `elevenlabs` Python SDK to synthesize speech via `convert_with_timestamps()`.

### Key Rules
- Use `/` for all paths, never `\`.
- Use the shared project environment (`.venv`) which has `elevenlabs` and `python-dotenv` installed.
- Do not immediately play the audio via speakers when running as part of the dashboard; always save it to a file.

---

## Dashboard Features
- **Follow Along**: Real-time word tracking with precise timestamps from ElevenLabs — highlights each word as it's spoken
- **Speed Controls**: Playback speed from 0.5x to 4x — word tracking stays perfectly in sync
- **Toggle**: ON by default, can be toggled OFF via the 📖 Follow Along button

---

## Resources
- `scripts/text2speech.py` — Core script using ElevenLabs `convert_with_timestamps()` API
- `_input/` — Directory for sample or temporary input text files
- `_output/` — Directory where generated MP3s and `.alignment.json` timing files are saved
