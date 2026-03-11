---
name:
description: Transcribes audio or video files using the Kie.ai API. Outputs in plain text, PDF and SRT subtitles. Supports Google Drive upload and Google Sheet logging. Batched files also allowed.
---

# AI-LLM-KIE-Speech2Text Skill

> **API**: This skill strictly uses the **Kie.ai API** for all transcription.

## When to Use This Skill
- User says "transcribe this audio", "convert speech to text", "transcribe this video", or "generate subtitles"
- Converting meeting recordings, podcasts, or voice memos to text
- Generating SRT subtitle files for videos

---

## Prerequisites

```bash
export KIE_API_KEY="..."    # Required — Kie.ai API key
```

---

## Workflow
- [ ] 1. Ensure `KIE_API_KEY` is available in the environment.
- [ ] 2. Run `scripts/audio_transcribe.py --input recording.mp3`
- [ ] 3. Review the output text or SRT file

---

## Commands

```bash
# Transcribe an audio file
python3 scripts/audio_transcribe.py --input meeting.mp3

# Save transcript to file
python3 scripts/audio_transcribe.py --input podcast.m4a --output transcript.txt

# Generate SRT subtitles
python3 scripts/audio_transcribe.py --input video.mp4 --format srt --output subtitles.srt

# Specify language
python3 scripts/audio_transcribe.py --input audio.wav --language Spanish
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--input` | *(required)* | Audio/video file path |
| `--output` | stdout | Save transcript to file |
| `--format` | `text` | `text` or `srt` (subtitles) |
| `--language` | auto-detect | Source language hint |
| `--provider` | `kie` | Strictly `kie` — Kie.ai API only |

---

## Supported Formats

`.mp3`, `.wav`, `.m4a`, `.aac`, `.ogg`, `.flac`, `.webm`, `.aiff`, `.aif`, `.wma`, `.oga`, `.opus`, `.3gp`, `.mp4`, `.mov`, `.avi`, `.mkv`

---

## Resources
- `scripts/audio_transcribe.py` — Core script using Kie.ai STT API
