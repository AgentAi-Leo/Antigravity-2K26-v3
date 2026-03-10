from __future__ import annotations
import os
import sys
import argparse
import time
import json
import urllib.request
import urllib.error

def _extract_text_from_file(filepath: str) -> str:
    if not os.path.exists(filepath):
        sys.stderr.write(f"Error: Input file '{filepath}' not found.\n")
        sys.exit(1)
        
    ext = os.path.splitext(filepath)[1].lower()
    content = ""
    
    if ext in [".rtf", ".doc", ".docx"]:
        import subprocess
        try:
            fmt_flag = ext.replace(".", "")
            res = subprocess.run(["textutil", "-format", fmt_flag, "-convert", "txt", "-stdout", filepath],
                                 capture_output=True, text=True, check=True)
            content = res.stdout
            
            if content.strip().startswith("{\\rtf"):
                sys.stderr.write(f"Warning: textutil failed to cleanly parse {ext}, stripping manually...\n")
        except Exception as e:
            sys.stderr.write(f"Error extracting text from document: {e}\n")
            sys.exit(1)
            
    elif ext == ".pdf":
        try:
            import pypdf  # type: ignore[import-not-found]
        except ImportError:
            sys.stderr.write("Error: 'pypdf' is not installed. Run: pip install pypdf\n")
            sys.exit(1)
        try:
            with open(filepath, "rb") as f:
                reader = pypdf.PdfReader(f)
                content = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        except Exception as e:
            sys.stderr.write(f"Error parsing PDF file: {e}\n")
            sys.exit(1)
            
    else:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
    return content.strip()

def _download_audio(url: str, dest_path: str):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
            with open(dest_path, "wb") as f:
                f.write(data)
    except Exception as e:
        sys.stderr.write(f"Error downloading resulting audio file: {e}\n")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Convert text to lifelike speech using Kie.ai ElevenLabs TTS.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Raw text string to convert")
    group.add_argument("--input", type=str, help="Path to a .txt file containing the text")
    parser.add_argument("--output", type=str, help="Path to save the generated .mp3 file")
    parser.add_argument("--voice_id", type=str, default="Rachel", help="ElevenLabs Voice Name (e.g. 'Rachel', 'Adam - Dominant, Firm')")
    parser.add_argument("--drive-folder", type=str, help="Optional: Google Drive folder path to upload the resulting audio")
    parser.add_argument("--google-sheet", type=str, help="Optional: Google Sheet name to log results")
    parser.add_argument("--share-with",   type=str, help="Optional: Email to share Drive files and Sheets with")
    parser.add_argument("--batch-id",     type=str, default="", help="Batch identifier for grouping sheet rows")
    parser.add_argument("--batch-seq",    type=str, default="", help="Sequence number within the batch")
    
    args = parser.parse_args()

    output_path: str = getattr(args, 'output', None) or ""
    if not output_path:
        if args.input:
            base_name = os.path.basename(args.input)
            output_path = os.path.join("_output", f"{os.path.splitext(base_name)[0]}.mp3")
        else:
            output_path = os.path.join("_output", f"speech_{int(time.time())}.mp3")
            
    output_path = os.path.abspath(output_path)

    # 1. Ensure API Key
    api_key: str = os.getenv("KIE_API_KEY") or ""
    if not api_key:
        sys.stderr.write("Error: KIE_API_KEY environment variable not found.\n")
        sys.exit(1)
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    # 2. Extract Text
    content = ""
    if args.text:
        content = args.text.strip()
    elif args.input:
        content = _extract_text_from_file(args.input)
        
    if not content:
        sys.stderr.write("Error: No text provided or extracted.\n")
        sys.exit(1)
        
    # Enforce API Limits (Kie.ai documents 5000 character limit for TTS payload)
    if len(content) > 5000:
        sys.stderr.write(f"Warning: Text length ({len(content)}) exceeds Kie.ai's 5000 character limit. Truncating.\n")
        import io as _io
        content = _io.StringIO(content).read(4995) + "..."

    # 3. Create Task
    create_task_url = "https://api.kie.ai/api/v1/jobs/createTask"
    task_body = {
        "model": "elevenlabs/text-to-speech-turbo-2-5",
        "input": {
            "text": content,
            "voice": args.voice_id
        }
    }
    
    sys.stderr.write("Creating TTS task on Kie.ai...\n")
    
    RETRY_WAITS: tuple[int, int] = (5, 15)

    def _get_wait(n: int) -> int:
        if n == 0:
            return RETRY_WAITS[0]
        return RETRY_WAITS[1]

    attempt: int = 0
    task_id = None
    
    while True:
        req = urllib.request.Request(create_task_url, data=json.dumps(task_body).encode(), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                resp_data = json.loads(resp.read())
                if resp_data.get("code") not in [0, 200]:
                    code = resp_data.get("code", "unknown")
                    msg = resp_data.get("msg", json.dumps(resp_data))
                    
                    if code == 429 and attempt < 2:
                        wait_time: int = _get_wait(attempt)
                        sys.stderr.write(f"Kie.ai rate limit (429) hit. Waiting {wait_time}s before retry...\n")
                        time.sleep(wait_time)
                        attempt += 1
                        continue
                        
                    if code in [401, 402, 403] or "balance" in str(resp_data).lower() or "quota" in str(resp_data).lower():
                        sys.stderr.write(f"__ANTIGRAVITY_API_QUOTA_EXCEEDED__\nKie.ai Error [{code}]: {msg}\n")
                        sys.exit(1)
                        
                    sys.stderr.write(f"Task creation failed. Raw response: {json.dumps(resp_data)}\n")
                    sys.exit(1)
                
                data_obj = resp_data.get("data", {})
                task_id = data_obj.get("taskId") if isinstance(data_obj, dict) else data_obj
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
                sys.stderr.write(f"__ANTIGRAVITY_API_QUOTA_EXCEEDED__\nKie.ai Error [{e.code}]: {err_msg}\n")
                sys.exit(1)
            sys.stderr.write(f"Error creating task ({e.code}): {err_msg}\n")
            sys.exit(1)
        except Exception as e:
            sys.stderr.write(f"Error creating TTS task: {e}\n")
            sys.exit(1)
            
    if not task_id:
        sys.stderr.write(f"Task creation failed: Could not find taskId.\n")
        sys.exit(1)

    # 4. Poll for results
    info_url = f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}"
    sys.stderr.write(f"Waiting for audio generation (Task ID: {task_id})...\n")
    
    max_retries = 360 # 30 mins max
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
                
                # Reset attempt count
                attempt = 0
                info = data.get("data") or {}
                state = info.get("state")
                
                if state == "success":
                    result_json_str = info.get("resultJson")
                    if isinstance(result_json_str, str):
                        try:
                            result_data = json.loads(result_json_str)
                            urls = result_data.get("resultUrls", [])
                            if urls and len(urls) > 0:
                                download_url = urls[0]
                                sys.stderr.write(f"Audio generated! Downloading to {output_path}...\n")
                                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                                _download_audio(download_url, output_path)
                                
                                # Write text preview
                                txt_output = os.path.splitext(output_path)[0] + ".txt"
                                with open(txt_output, "w", encoding="utf-8") as txt_f:
                                    txt_f.write(content)
                                    
                                content_str: str = content
                                words: int = len(content_str.split())
                                chars: int = len(content_str)
                                sys.stdout.write(f"Saved: {output_path}\n")
                                sys.stdout.write(f"Usage: {words} words, {chars} characters\n")

                                # Optional: Auto-upload to Google Drive
                                drive_link = ""
                                folder_id = ""
                                file_id = ""
                                if args.drive_folder:
                                    sys.stderr.write(f"Auto-uploading to Google Drive folder: '{args.drive_folder}'...\n")
                                    try:
                                        import subprocess
                                        current_dir = os.path.dirname(os.path.abspath(__file__))
                                        drive_script = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "_000-Basics", "Data-GoogleDrive", "scripts", "upload_to_drive.py"))
                                        if not os.path.exists(drive_script):
                                            # Fallback if __file__ relativity is broken by Streamlit execution
                                            drive_script = os.path.join(os.getcwd(), "_000-Basics", "Data-GoogleDrive", "scripts", "upload_to_drive.py")
                                        
                                        if os.path.exists(drive_script):
                                            cmd = [sys.executable, drive_script, "--file", output_path, "--folder", args.drive_folder]
                                            if args.share_with:
                                                cmd.extend(["--share-with", args.share_with])
                                                
                                            res = subprocess.run(cmd, capture_output=True, text=True)
                                            if res.returncode == 0:
                                                sys.stdout.write(res.stdout + "\n")
                                                # Extract link and IDs for sheet logging and badge links
                                                for line in res.stderr.splitlines():
                                                    if "Link:" in line:
                                                        drive_link = line.split("Link:", 1)[1].strip()
                                                    elif "FolderID:" in line:
                                                        folder_id = line.split("FolderID:", 1)[1].strip()
                                                        sys.stderr.write(line + "\n")
                                                    elif "FileID:" in line:
                                                        file_id = line.split("FileID:", 1)[1].strip()
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
                                    try:
                                        sheet_script = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "_000-Basics", "Data-GoogleSheet", "scripts", "append_to_sheet.py"))
                                        if not os.path.exists(sheet_script):
                                             sheet_script = os.path.join(os.getcwd(), "_000-Basics", "Data-GoogleSheet", "scripts", "append_to_sheet.py")
                                             
                                        if os.path.exists(sheet_script):
                                            status = "Success"
                                            # Truncate text for sheet if very long
                                            res_str = str(content)
                                            if len(res_str) > 500:
                                                preview = res_str[:500] + "..."  # type: ignore
                                            else:
                                                preview = res_str
                                            original_file = os.path.basename(args.input) if args.input else "Manual Text"
                                            
                                            cmd = [sys.executable, sheet_script, "--title", args.google_sheet, "--data", original_file, status, preview, drive_link]
                                            if args.batch_id:
                                                cmd.extend(["--batch-id", args.batch_id])
                                            if args.batch_seq:
                                                cmd.extend(["--batch-seq", args.batch_seq])
                                            if args.share_with:
                                                cmd.extend(["--share-with", args.share_with])
                                                cmd.extend(["--sharing-with-email", args.share_with])
                                            if args.drive_folder:
                                                cmd.extend(["--drive-folder-name", args.drive_folder])
                                            if folder_id:
                                                cmd.extend(["--folder-id", folder_id])
                                            if file_id:
                                                cmd.extend(["--file-id", file_id])
                                            usage_str = f"{words} words, {chars} characters"
                                            cmd.extend(["--usage", usage_str])
                                            
                                            res = subprocess.run(cmd, capture_output=True, text=True)
                                            if res.returncode == 0:
                                                sys.stdout.write(res.stdout + "\n")
                                                # Propagate SheetID for badge links
                                                for line in res.stderr.splitlines():
                                                    if "SheetID:" in line:
                                                        sys.stderr.write(line + "\n")
                                            else:
                                                sys.stderr.write(f"Warning: Sheet logging failed: {res.stderr}\n")
                                    except Exception as sheet_err:
                                        sys.stderr.write(f"Warning: Unexpected error during Sheet logging: {sheet_err}\n")

                                sys.exit(0)
                            else:
                                sys.stderr.write(f"Task succeeded but no resultUrls found in: {result_json_str}\n")
                                sys.exit(1)
                        except json.JSONDecodeError:
                            sys.stderr.write(f"Task succeeded but resultJson is invalid: {result_json_str}\n")
                            sys.exit(1)
                    else:
                        sys.stderr.write(f"Unexpected results format: {result_json_str}\n")
                        sys.exit(1)
                        
                elif state in ["fail", "error", "failed"]:
                    sys.stderr.write(f"Task failed: {info.get('failMsg', 'Unknown error')}\n")
                    sys.exit(1)
                
                if i % 3 == 0:
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
            
    sys.stderr.write("Error: TTS Timeout.\n")
    sys.exit(1)

if __name__ == "__main__":
    main()
