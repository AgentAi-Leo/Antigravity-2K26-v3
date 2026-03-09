from __future__ import annotations
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
        err_detail: str = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {err_detail}")
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


def _call_kie_stt(audio_path: str, language: str | None, api_key: str) -> str:
    """Call kie.ai Speech-to-Text via file upload, task creation, and polling."""
    import time
    
    # 1. Upload local file to kie.ai temporary storage
    try:
        with open(audio_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()
    except Exception as e:
        sys.stderr.write(f"Error reading file: {e}\n")
        sys.exit(1)
        
    # Documented base64 upload endpoint
    upload_url = "https://kieai.redpandaai.co/api/file-base64-upload"
    upload_body = {
        "base64Data": f"data:audio/{os.path.splitext(audio_path)[1].lower().lstrip('.')};base64,{audio_b64}",
        "fileName": os.path.basename(audio_path),
        "uploadPath": "transcription-uploads"
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" # Generic UA
    }
    
    sys.stderr.write(f"Uploading {os.path.basename(audio_path)} to kie.ai storage...\n")
    
    RETRY_WAITS: tuple[int, int] = (5, 15)

    def _get_wait(n: int) -> int:
        if n == 0:
            return RETRY_WAITS[0]
        return RETRY_WAITS[1]

    attempt = 0
    audio_url = None
    
    while True:
        req = urllib.request.Request(upload_url, data=json.dumps(upload_body).encode(), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                resp_data = json.loads(resp.read())
                if resp_data.get("code") not in [0, 200]:
                    code = resp_data.get("code", "unknown")
                    msg = resp_data.get("message", json.dumps(resp_data))
                    
                    if code == 429 and attempt < 2:
                        wait_time: int = _get_wait(attempt)
                        sys.stderr.write(f"Kie.ai rate limit (429) hit. Waiting {wait_time}s before retry...\n")
                        time.sleep(wait_time)
                        attempt += 1
                        continue
                        
                    if code in [401, 402, 403] or "balance" in str(resp_data).lower() or "quota" in str(resp_data).lower():
                        sys.stderr.write(f"__ANTIGRAVITY_API_QUOTA_EXCEEDED__\nKie.ai Upload Error [{code}]: {msg}\n")
                        sys.exit(1)
                    sys.stderr.write(f"Upload failed (Code {code}): {msg}\n")
                    sys.exit(1)
                data_obj = resp_data.get("data")
                if isinstance(data_obj, dict):
                    audio_url = data_obj.get("downloadUrl") or data_obj.get("url")
                else:
                    audio_url = data_obj
                break
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode() if hasattr(e, 'read') else str(e)
            if e.code == 429 and attempt < 2:
                wait_time = _get_wait(attempt)
                sys.stderr.write(f"Kie.ai rate limit (429) hit. Waiting {wait_time}s before retry...\n")
                time.sleep(wait_time)
                attempt += 1
                continue
                
            if "balance" in err_msg.lower() or "quota" in err_msg.lower() or e.code in [401, 402, 403]:
                sys.stderr.write(f"__ANTIGRAVITY_API_QUOTA_EXCEEDED__\nKie.ai Upload Error [{e.code}]: {err_msg}\n")
                sys.exit(1)
            sys.stderr.write(f"Error during upload ({e.code}): {err_msg}\n")
            sys.exit(1)
        except Exception as e:
            sys.stderr.write(f"Error during upload: {e}\n")
            sys.exit(1)
            
    if not audio_url:
        sys.stderr.write(f"Upload failed: Could not find URL in response.\n")
        sys.exit(1)

    # 2. Create Transcription Task
    create_task_url = "https://api.kie.ai/api/v1/jobs/createTask"
    task_input = {"audio_url": audio_url}
    if language:
        task_input["language_code"] = language
        
    task_body = {
        "model": "elevenlabs/speech-to-text",
        "input": task_input
    }

    sys.stderr.write("Creating transcription task...\n")
    creation_attempt = 0
    task_id = None
    
    while True:
        req = urllib.request.Request(create_task_url, data=json.dumps(task_body).encode(), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                resp_data = json.loads(resp.read())
                if resp_data.get("code") not in [0, 200]:
                    if resp_data.get("code") in [401, 402, 403] or "balance" in str(resp_data).lower() or "quota" in str(resp_data).lower():
                        code = resp_data.get("code", "unknown")
                        msg = resp_data.get("msg", json.dumps(resp_data))
                        
                        if code == 429 and creation_attempt < 2:
                            wait_time = _get_wait(creation_attempt)
                            sys.stderr.write(f"Kie.ai rate limit (429) hit. Waiting {wait_time}s before retry...\n")
                            time.sleep(wait_time)
                            creation_attempt += 1
                            continue
                            
                        sys.stderr.write(f"__ANTIGRAVITY_API_QUOTA_EXCEEDED__\nKie.ai Error [{code}]: {msg}\n")
                        sys.exit(1)
                    sys.stderr.write(f"Task creation failed. Raw response: {json.dumps(resp_data)}\n")
                    sys.exit(1)
                data_obj = resp_data.get("data")
                if isinstance(data_obj, dict):
                    task_id = data_obj.get("taskId")
                else:
                    task_id = data_obj
                break
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode() if hasattr(e, 'read') else str(e)
            if e.code == 429 and creation_attempt < 2:
                wait_time = _get_wait(creation_attempt)
                sys.stderr.write(f"Kie.ai rate limit (429) hit. Waiting {wait_time}s before retry...\n")
                time.sleep(wait_time)
                creation_attempt += 1
                continue
                
            if "balance" in err_msg.lower() or "quota" in err_msg.lower() or e.code in [401, 402, 403]:
                sys.stderr.write(f"__ANTIGRAVITY_API_QUOTA_EXCEEDED__\nKie.ai Error [{e.code}]: {err_msg}\n")
                sys.exit(1)
            sys.stderr.write(f"Error creating task ({e.code}): {err_msg}\n")
            sys.exit(1)
        except Exception as e:
            sys.stderr.write(f"Error creating task: {e}\n")
            sys.exit(1)
            
    if not task_id:
        sys.stderr.write(f"Task creation failed: Could not find taskId.\n")
        sys.exit(1)

    # 3. Poll for results
    info_url = f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}"
    sys.stderr.write(f"Waiting for transcription (Task ID: {task_id})...\n")
    
    max_retries = 360 # 30 minutes max
    attempt = 0
    
    for i in range(max_retries):
        try:
            req = urllib.request.Request(info_url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                if data.get("code") not in [0, 200]:
                    code = data.get("code", "unknown")
                    msg = data.get("msg", json.dumps(data))
                    
                    if code == 429 and attempt < 2:
                        wait_time = _get_wait(attempt)
                        sys.stderr.write(f"Kie.ai rate limit (429) hit during polling. Waiting {wait_time}s before retry...\n")
                        time.sleep(wait_time)
                        attempt += 1
                        continue
                        
                    if data.get("code") in [401, 402, 403] or "balance" in str(data).lower() or "quota" in str(data).lower():
                        sys.stderr.write(f"__ANTIGRAVITY_API_QUOTA_EXCEEDED__\nKie.ai Error [{code}]: {msg}\n")
                        sys.exit(1)
                    sys.stderr.write(f"Task polling returned error: {json.dumps(data)}\n")
                    sys.exit(1)
                
                # Reset attempt count on success or valid intermediate state
                attempt = 0
                info = data.get("data") or {}
                state = info.get("state")
                
                if state == "success":
                    result_json_str = info.get("resultJson")
                    if isinstance(result_json_str, str):
                        try:
                            result_data = json.loads(result_json_str)
                            return result_data.get("resultObject", {}).get("text", "").strip()
                        except json.JSONDecodeError:
                            sys.stderr.write(f"Task succeeded but resultJson is invalid: {result_json_str}\n")
                            sys.exit(1)
                    else:
                        sys.stderr.write(f"Unexpected results format: {result_json_str}\n")
                        sys.exit(1)
                elif state in ["fail", "error", "failed"]:
                    sys.stderr.write(f"Task failed: {info.get('failMsg', 'Unknown error')}\n")
                    sys.exit(1)
                
                if i % 5 == 0:
                    sys.stderr.write(f"Status: {state}...\n")
                time.sleep(5)
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode() if hasattr(e, 'read') else str(e)
            if e.code == 429 and attempt < 2:
                wait_time = _get_wait(attempt)
                sys.stderr.write(f"Kie.ai rate limit (429) hit during polling. Waiting {wait_time}s before retry...\n")
                time.sleep(wait_time)
                attempt += 1
                continue
                
            if "balance" in err_msg.lower() or "quota" in err_msg.lower() or e.code in [401, 402, 403]:
                sys.stderr.write(f"__ANTIGRAVITY_API_QUOTA_EXCEEDED__\nKie.ai Polling Error [{e.code}]: {err_msg}\n")
                sys.exit(1)
            sys.stderr.write(f"HTTP Error polling task ({e.code}): {err_msg}\n")
            time.sleep(5)
        except Exception as e:
            sys.stderr.write(f"Error polling task: {e}\n")
            time.sleep(5)
            
    sys.stderr.write("Error: Transcription timed out.\n")
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
    parser.add_argument("--provider",    default="kie", choices=["gemini", "openai", "kie"])
    parser.add_argument("--model",       default=None,   help="Override model")
    parser.add_argument("--drive-folder", help="Optional: Google Drive folder path to upload the input audio")
    parser.add_argument("--google-sheet", help="Optional: Google Sheet name to log results")
    parser.add_argument("--share-with",   help="Optional: Email to share Drive files and Sheets with")
    parser.add_argument("--batch-id",     default="", help="Batch identifier for grouping sheet rows")
    parser.add_argument("--batch-seq",    default="", help="Sequence number within the batch")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        sys.stderr.write(f"Error: '{args.input}' not found."); sys.exit(1)

    ext = os.path.splitext(args.input)[1].lower()
    if ext not in SUPPORTED_AUDIO | SUPPORTED_VIDEO:
        sys.stderr.write(f"Error: unsupported format '{ext}'. Supported: {', '.join(sorted(SUPPORTED_AUDIO | SUPPORTED_VIDEO))}")
        sys.exit(1)

    sys.stderr.write(f"Transcribing: {args.input}  (provider: {args.provider})\n")

    if args.provider == "kie":
        api_key = os.environ.get("KIE_API_KEY", "")
        if not api_key: sys.stderr.write("Error: KIE_API_KEY not set."); sys.exit(1)
        try:
            result = _call_kie_stt(args.input, args.language, api_key)
            if result:
                words = len(result.split())
                chars = len(result)
                sys.stderr.write(f"Usage: {words} words, {chars} characters\n")
        except Exception as e:
            sys.stderr.write(f"Error: {str(e)}"); sys.exit(1)
    elif args.provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key: sys.stderr.write("Error: OPENAI_API_KEY not set."); sys.exit(1)
        translate_flag = bool(args.translate_to and args.translate_to.lower() == "english")
        result = _call_whisper(args.input, args.language, translate_flag, api_key)
    else:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key: sys.stderr.write("Error: GEMINI_API_KEY not set.\nGet one free at: https://aistudio.google.com"); sys.exit(1)
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

    # Optional: Auto-upload to Google Drive
    drive_link = ""
    if args.drive_folder:
        upload_target = args.input
        ext_lower = os.path.splitext(args.input)[1].lower()
        
        if ext_lower != ".mp3":
            sys.stderr.write(f"Converting '{ext_lower}' to '.mp3' for Google Drive browser compatibility...\n")
            import tempfile
            import subprocess
            temp_dir = tempfile.mkdtemp()
            base_name = os.path.splitext(os.path.basename(args.input))[0]
            mp3_path = os.path.join(temp_dir, f"{base_name}.mp3")
            
            # Use ffmpeg to convert the audio
            conv_res = subprocess.run(
                ["ffmpeg", "-y", "-i", args.input, "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", mp3_path],
                capture_output=True, text=True
            )
            if conv_res.returncode == 0 and os.path.exists(mp3_path):
                upload_target = mp3_path
            else:
                sys.stderr.write(f"Warning: MP3 conversion failed, proceeding with original file. Error: {conv_res.stderr}\n")
                
        sys.stderr.write(f"Auto-uploading to Google Drive folder: '{args.drive_folder}'...\n")
        try:
            import subprocess
            current_dir = os.path.dirname(os.path.abspath(__file__))
            drive_script = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "_000-Basics", "Data-GoogleDrive", "scripts", "upload_to_drive.py"))
            
            if os.path.exists(drive_script):
                cmd = [sys.executable, drive_script, "--file", upload_target, "--folder", args.drive_folder]
                if args.share_with:
                    cmd.extend(["--share-with", args.share_with])
                
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    sys.stdout.write(res.stdout + "\n")
                    # Extract link and folder ID for sheet logging and badge links
                    for line in res.stderr.splitlines():
                        if "Link:" in line:
                            drive_link = line.split("Link:", 1)[1].strip()
                        elif "FolderID:" in line:
                            sys.stderr.write(line + "\n")
                else:
                    sys.stderr.write(f"Warning: Drive upload failed: {res.stderr}\n")
            else:
                sys.stderr.write(f"Warning: Could not find upload_to_drive.py at {drive_script}\n")
        except Exception as drive_err:
            sys.stderr.write(f"Warning: Unexpected error during Drive upload: {drive_err}\n")

    # Optional: Log to Google Sheet
    if args.google_sheet:
        sys.stderr.write(f"Logging results to Google Sheet: '{args.google_sheet}'...\n")
        # Debug: log to file to trace missing file #1 issue
        with open('/tmp/sheet_debug.log', 'a') as _dbg:
            _dbg.write(f"\n--- audio_transcribe.py: batch_seq={args.batch_seq}, file={os.path.basename(args.input)} ---\n")
            _dbg.write(f"  drive_link={drive_link[:80] if drive_link else 'EMPTY'}\n")
        try:
            import subprocess
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sheet_script = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "_000-Basics", "Data-GoogleSheet", "scripts", "append_to_sheet.py"))
            
            if os.path.exists(sheet_script):
                # Data: [Original File, Status, Transcript/Text, Drive Link]
                status = "Success"
                # Truncate transcript for sheet if very long
                res_str = str(result)
                if len(res_str) > 5000:
                    preview = res_str[:5000] + "..."  # type: ignore
                else:
                    preview = res_str
                
                cmd = [sys.executable, sheet_script, "--title", args.google_sheet, "--data", os.path.basename(args.input), status, preview, drive_link]
                if args.batch_id:
                    cmd.extend(["--batch-id", args.batch_id])
                if args.batch_seq:
                    cmd.extend(["--batch-seq", args.batch_seq])
                if args.share_with:
                    cmd.extend(["--share-with", args.share_with])
                
                with open('/tmp/sheet_debug.log', 'a') as _dbg:
                    _dbg.write(f"  Calling append_to_sheet.py with seq={args.batch_seq}\n")
                
                res = subprocess.run(cmd, capture_output=True, text=True)
                
                with open('/tmp/sheet_debug.log', 'a') as _dbg:
                    _dbg.write(f"  returncode={res.returncode}\n")
                    _dbg.write(f"  stdout={res.stdout[:200]}\n")
                    _dbg.write(f"  stderr={res.stderr[:200]}\n")
                
                if res.returncode == 0:
                    sys.stdout.write(res.stdout + "\n")
                    # Propagate SheetID for badge links
                    for line in res.stderr.splitlines():
                        if "SheetID:" in line:
                            sys.stderr.write(line + "\n")
                else:
                    sys.stderr.write(f"Warning: Sheet logging failed: {res.stderr}\n")
            else:
                sys.stderr.write(f"Warning: Could not find append_to_sheet.py at {sheet_script}\n")
        except Exception as sheet_err:
            sys.stderr.write(f"Warning: Unexpected error during Sheet logging: {sheet_err}\n")


if __name__ == "__main__":
    main()
