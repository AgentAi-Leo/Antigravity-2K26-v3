---
name: Kie-ElevenLabs-Text2Speech
description: Converts text to lifelike speech using the ElevenLabs models via the Kie.ai Provider API.
category: AI/Audio
---

# Kie-ElevenLabs Text-to-Speech Skill

This skill allows the agent and dashboard to convert written text into spoken audio files using the `elevenlabs/text-to-speech-turbo-2-5` model provided by the Kie.ai API.

## Requirements
- Python 3.10+
- The `KIE_API_KEY` environment variable must be set (or handled dynamically by the dashboard).

## Usage
The script is located at `scripts/text2speech.py`.

### Arguments:
- `--input <path>`: Path to a generic text, PDF, DOCX file to be narrated.
- `--text <string>`: OR a raw text string to narrate.
- `--output <path>`: Path to save the resulting `.mp3` file. (Defaults to `_output/speech_<timestamp>.mp3`)
- `--voice_id <string>`: The name of the voice to use (e.g., "Rachel", "Drew"). Defaults to "Rachel".

### Standard Usage Example:
```bash
python scripts/text2speech.py --text "Hello world! This is the Kie.ai ElevenLabs interface."
```

```bash
python scripts/text2speech.py --input example.txt --output result.mp3 --voice_id "Adam - Dominant, Firm"
```
