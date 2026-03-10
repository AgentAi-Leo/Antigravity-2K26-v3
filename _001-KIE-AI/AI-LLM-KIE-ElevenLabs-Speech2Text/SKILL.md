---
name:
description: Transcribes audio or video files to specified Google Drive and Google Sheet. Outputs in plain text, PDF and SRT subtitles. Batched files also allowed.
---

# AI-LLM-Speech2Text Skill

## When to Use This Skill
- User says "transcribe this audio", "convert speech to text", "transcribe this video", or "generate subtitles"
- Converting meeting recordings, podcasts, or voice memos to text
- Generating SRT subtitle files for videos

---

## Prerequisites

```bash
export KIE_API_KEY="..."       # for kie.ai (ElevenLabs STT, supports most formats)
# OR: GEMINI_API_KEY             # for Gemini audio
# OR: OPENAI_API_KEY            # for Whisper
```

---

## Workflow
- [ ] 1. Set API key (`export KIE_API_KEY=...`)
- [ ] 2. Run `scripts/audio_transcribe.py --input recording.mp3`
- [ ] 3. Review the output text or SRT file

---

## Commands

```bash
# Transcribe an audio file (uses kie.ai by default)
python3 scripts/audio_transcribe.py --input meeting.mp3

# Save transcript to file
python3 scripts/audio_transcribe.py --input podcast.m4a --output transcript.txt

# Generate SRT subtitles
python3 scripts/audio_transcribe.py --input video.mp4 --format srt --output subtitles.srt

# Specify language
python3 scripts/audio_transcribe.py --input audio.wav --language Spanish

# Use Gemini
python3 scripts/audio_transcribe.py --input audio.mp3 --provider gemini

# Use Whisper (OpenAI)
python3 scripts/audio_transcribe.py --input audio.mp3 --provider openai
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--input` | *(required)* | Audio/video file path |
| `--output` | stdout | Save transcript to file |
| `--format` | `text` | `text` or `srt` (subtitles) |
| `--language` | auto-detect | Source language hint |
| `--translate-to` | off | Translate output to this language (Gemini only) |
| `--provider` | `kie` | `kie`, `gemini`, or `openai` |
| `--model` | None | Override model |

---

## Supported Formats

| Provider | Formats |
|---|---|
| kie.ai | `.mp3`, `.wav`, `.m4a`, `.aac`, `.ogg`, `.flac`, etc. |
| Gemini | `.mp3`, `.wav`, `.m4a`, `.aac`, `.ogg`, `.mp4`, `.mov` |
| OpenAI Whisper | `.mp3`, `.mp4`, `.mpeg`, `.mpga`, `.m4a`, `.wav`, `.webm` |

---

## Resources
- `scripts/audio_transcribe.py` — core script (stdlib urllib + base64, no pip required)
