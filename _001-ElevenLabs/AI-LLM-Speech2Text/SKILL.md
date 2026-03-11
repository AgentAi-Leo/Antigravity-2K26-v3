---
name:
description: Transcribes audio or video files using the ElevenLabs Speech-to-Text API. Outputs in plain text, PDF and SRT subtitles. Supports Google Drive upload and Google Sheet logging. Batched files also allowed.
---

# AI-LLM-Speech2Text Skill

## When to Use This Skill
- User says "transcribe this audio", "convert speech to text", "transcribe this video", or "generate subtitles"
- Converting meeting recordings, podcasts, or voice memos to text
- Generating SRT subtitle files for videos

---

## Prerequisites

```bash
export ELEVENLABS_API_KEY="..."    # Required — ElevenLabs API key (Creator plan or higher)
```

---

## Workflow
- [ ] 1. Ensure `ELEVENLABS_API_KEY` is available in the environment.
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

# Specify language (faster, more accurate)
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
| `--provider` | `elevenlabs` | `elevenlabs`, `gemini`, or `openai` (fallback only) |

---

## Supported Formats

`.mp3`, `.wav`, `.m4a`, `.aac`, `.ogg`, `.flac`, `.webm`, `.aiff`, `.aif`, `.wma`, `.oga`, `.opus`, `.3gp`, `.mp4`, `.mov`, `.avi`, `.mkv`

---

## Dashboard Features
- **Follow Along**: Real-time estimated word tracking that highlights text in sync with audio playback
- **Speed Controls**: Playback speed from 0.5x to 4x — word tracking stays in sync

---

## Resources
- `scripts/audio_transcribe.py` — Core script using ElevenLabs Scribe v1 STT API
