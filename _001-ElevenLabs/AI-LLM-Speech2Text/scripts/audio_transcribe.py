import os
import sys
import json
import base64
import argparse
import urllib.request
import urllib.error


SUPPORTED_AUDIO = {
    ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".webm",
    ".aiff", ".aif", ".wma", ".oga", ".opus", ".3gp"
}
SUPPORTED_VIDEO = {".mp4", ".mov", ".avi", ".mkv"}
GEMINI_MIME = {
    ".mp3": "audio/mpeg", ".wav": "audio/wav", ".m4a": "audio/mp4",
    ".aac": "audio/aac", ".ogg": "audio/ogg", ".flac": "audio/flac",
    ".webm": "audio/webm", ".mp4": "video/mp4", ".mov": "video/quicktime",
    ".aiff": "audio/aiff", ".aif": "audio/aiff", ".wma": "audio/x-ms-wma",
    ".oga": "audio/ogg", ".opus": "audio/ogg", ".3gp": "audio/3gpp"
}


def _call_gemini_audio(audio_b64: str, mime_type: str, prompt: str, model: str, api_key: str) -> str:
    body = {
        "contents": [{
            "role": "user",
            "parts": [
                {"inline_data": {"mime_type": mime_type, "data": audio_b64}},
                {"text": prompt}
            ]
        }],
        "generationConfig": {"maxOutputTokens": 8192}
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        import io as _io_err
        print(f"HTTP {e.code}: {_io_err.StringIO(err).read(400)}", file=sys.stderr)
        sys.exit(1)


def _call_whisper(audio_path: str, language: str | None, translate: bool, api_key: str) -> str:
    """Call OpenAI Whisper via multipart form upload."""
    import io
    ext = os.path.splitext(audio_path)[1].lower().lstrip(".")
    mime = f"audio/{ext}" if ext != "mp4" else "video/mp4"

    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    parts = []
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="model"\r\n\r\nwhisper-1'.encode())
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{os.path.basename(audio_path)}"\r\nContent-Type: {mime}\r\n\r\n'.encode() + audio_bytes)
    if language:
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="language"\r\n\r\n{language}'.encode())
    endpoint = "translations" if translate else "transcriptions"
    parts.append(f"--{boundary}--".encode())
    body = b"\r\n".join(parts)

    req = urllib.request.Request(
        f"https://api.openai.com/v1/audio/{endpoint}",
        data=body,
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())["text"].strip()


def _call_elevenlabs_stt(audio_path: str, language: str | None, api_key: str) -> str:
    """Call ElevenLabs Speech-to-Text via multipart form upload."""
    ext = os.path.splitext(audio_path)[1].lower().lstrip(".")
    mime = GEMINI_MIME.get(f".{ext}", f"audio/{ext}")

    boundary = "----FormBoundaryEL11Labs"
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    parts = []
    # model_id field
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="model_id"\r\n\r\nscribe_v1'.encode())
    # audio file
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{os.path.basename(audio_path)}"\r\nContent-Type: {mime}\r\n\r\n'.encode() + audio_bytes)
    if language:
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="language_code"\r\n\r\n{language}'.encode())
    parts.append(f"--{boundary}--".encode())
    body = b"\r\n".join(parts)

    req = urllib.request.Request(
        "https://api.elevenlabs.io/v1/speech-to-text",
        data=body,
        headers={"xi-api-key": api_key,
                 "Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            return data.get("text", "").strip()
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        if e.code == 429 or "quota_exceeded" in err.lower():
            print(f"__ANTIGRAVITY_API_QUOTA_EXCEEDED__\n{err}", file=sys.stderr)
            sys.exit(1)
        import io as _io_err2
        print(f"HTTP {e.code}: {_io_err2.StringIO(err).read(400)}", file=sys.stderr)
        sys.exit(1)


def _to_srt(text: str) -> str:
    """Convert plain transcript to a simple SRT file (one block per sentence)."""
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    lines = []
    for i, sentence in enumerate(sentences, 1):
        start_s = (i - 1) * 5
        end_s = i * 5
        start = f"00:00:{start_s:02d},000"
        end = f"00:00:{end_s:02d},000"
        lines.append(f"{i}\n{start} --> {end}\n{sentence}\n")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe audio/video files to text.")
    parser.add_argument("--input",       required=True,  help="Audio/video file path")
    parser.add_argument("--output",      default=None,   help="Save transcript to file")
    parser.add_argument("--format",      default="text", choices=["text", "srt"])
    parser.add_argument("--language",    default=None,   help="Source language hint (e.g. Spanish)")
    parser.add_argument("--translate-to", default=None,  dest="translate_to",
                        help="Translate transcript to this language (Gemini only)")
    parser.add_argument("--provider",    default="elevenlabs", choices=["gemini", "openai", "elevenlabs"])
    parser.add_argument("--model",       default=None,   help="Override model")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: '{args.input}' not found."); sys.exit(1)

    ext = os.path.splitext(args.input)[1].lower()
    if ext not in SUPPORTED_AUDIO | SUPPORTED_VIDEO:
        print(f"Error: unsupported format '{ext}'. Supported: {', '.join(sorted(SUPPORTED_AUDIO | SUPPORTED_VIDEO))}")
        sys.exit(1)

    print(f"Transcribing: {args.input}  (provider: {args.provider})")

    if args.provider == "elevenlabs":
        api_key = os.environ.get("ELEVENLABS_API_KEY", "")
        if not api_key: print("Error: ELEVENLABS_API_KEY not set."); sys.exit(1)
        result = _call_elevenlabs_stt(args.input, args.language, api_key)
    elif args.provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key: print("Error: OPENAI_API_KEY not set."); sys.exit(1)
        translate_flag = bool(args.translate_to and args.translate_to.lower() == "english")
        result = _call_whisper(args.input, args.language, translate_flag, api_key)
    else:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key: print("Error: GEMINI_API_KEY not set.\nGet one free at: https://aistudio.google.com"); sys.exit(1)
        with open(args.input, "rb") as f:
            audio_b64 = base64.standard_b64encode(f.read()).decode()
        mime_type = GEMINI_MIME.get(ext, "audio/mpeg")
        lang_hint = f" The audio language is {args.language}." if args.language else ""
        translate_hint = f" After transcribing, translate to {args.translate_to}." if args.translate_to else ""
        prompt = f"Transcribe all speech in this audio accurately.{lang_hint}{translate_hint} Return only the transcript text."
        model = args.model or "gemini-2.0-flash"
        result = _call_gemini_audio(audio_b64, mime_type, prompt, model, api_key)

    if args.format == "srt":
        result = _to_srt(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result + "\n")
        print(f"Saved: {args.output}")
    else:
        print(result)
        # Emit word/char stats for the dashboard statistics badge
        sys.stderr.write(f"Usage: {len(result.split())} words, {len(result)} characters\n")


if __name__ == "__main__":
    main()
