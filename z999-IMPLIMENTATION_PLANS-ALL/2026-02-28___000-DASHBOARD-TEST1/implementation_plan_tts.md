# Implementation Plan: AI-LLM-Text2Speech Skill

The goal is to create a new skill named `AI-LLM-Text2Speech` that leverages the ElevenLabs Python SDK to convert text (from prompts, files, or direct input) into lifelike speech (.mp3).

## Proposed Changes

### 1. Directory Structure

Create a new skill folder: `___000A-ANTIGRAVITY-SKILLS/AI-LLM-Text2Speech`
Inside it, create:
- `SKILL.md`
- `scripts/text2speech.py`
- `_input/` (For holding temporary text files)
- `_output/` (For holding generated .mp3 files)

### 2. [NEW] SKILL.md
Create the standard Antigravity skill metadata file following the `SKILL_CREATOR` templates:
```yaml
---
name: generating-text-to-speech
description: Converts text documents or prompts directly into lifelike MP3 audio files using the ElevenLabs API. Use when the user asks to generate audio, narrate text, or trigger text-to-speech.
---

# AI-LLM-Text2Speech Skill

## When to Use This Skill
- User says "convert this text to speech"
- User wants an MP3 narration of a document
...
```

### 3. [NEW] scripts/text2speech.py
Create the core script based on the provided ElevenLabs Quickstart. It will:
- Accept an `--input` argument (pointing to a `.txt` file) or `--text` argument for raw strings.
- Accept an optional `--output` argument for the resulting `.mp3`.
- Authenticate automatically via `os.getenv("ELEVENLABS_API_KEY")`.
- Save the binary audio directly to the `_output` folder (skipping direct playback `play(audio)` so it acts as a headless service for the dashboard).

### 4. Dependencies
Run a `pip install elevenlabs python-dotenv` into the project's shared virtual environment (`.venv`) so the dashboard and the skill can access it.

## Verification Plan

### Manual Verification
1. Open the dashboard and verify "AI LLM Text2Speech" appears in the skill list.
2. Select the skill, type a test sentence, and hit run.
3. Verify an `.mp3` file is generated and returned by the dashboard for playback or download.
