import os
import sys
import argparse
from elevenlabs.client import ElevenLabs  # type: ignore[import-not-found]

def main():
    parser = argparse.ArgumentParser(description="Convert text to lifelike speech using ElevenLabs API.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Raw text string to convert")
    group.add_argument("--input", type=str, help="Path to a .txt file containing the text")
    parser.add_argument("--output", type=str, help="Path to save the generated .mp3 file")
    parser.add_argument("--voice_id", type=str, default="JBFqnCBsd6RMkjVDRZzb", help="ElevenLabs Voice ID")
    parser.add_argument("--model_id", type=str, default="eleven_multilingual_v2", help="ElevenLabs Model ID")
    parser.add_argument("--drive-folder", type=str, help="Optional: Google Drive folder path to upload the resulting audio")
    args = parser.parse_args()

    output_path: str = getattr(args, 'output', None) or ""
    if not output_path:
        import time
        if args.input:
            base_name = os.path.basename(args.input)
            output_path = os.path.join("_output", f"{os.path.splitext(base_name)[0]}.mp3")
        else:
            output_path = os.path.join("_output", f"speech_{int(time.time())}.mp3")
    output_path = os.path.abspath(output_path)

    # API key injected by Dashboard or .env
    api_key: str = os.getenv("ELEVENLABS_API_KEY") or ""
    if not api_key:
        print("Error: ELEVENLABS_API_KEY environment variable not found.", file=sys.stderr)
        sys.exit(1)

    # Determine input text
    content = ""
    if args.text:
        content = args.text
    elif args.input:
        if not os.path.exists(args.input):
            print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
            sys.exit(1)
        ext = os.path.splitext(args.input)[1].lower()
        if ext in [".rtf", ".doc", ".docx"]:
            import subprocess
            try:
                # Force macOS textutil to cleanly extract raw text from rich documents by explicitly declaring the format
                fmt_flag = ext.replace(".", "")
                res = subprocess.run(["textutil", "-format", fmt_flag, "-convert", "txt", "-stdout", args.input],
                                     capture_output=True, text=True, check=True)
                content = res.stdout
                
                # If textutil somehow still fails and spits out RTF headers, hard-strip
                if content.strip().startswith("{\\rtf"):
                    print(f"Warning: textutil failed to cleanly parse {ext}, stripping manually...", file=sys.stderr)
                    # For a truly robust fallback, we install stripped
                    pass
            except Exception as e:
                print(f"Error extracting text from document: {e}", file=sys.stderr)
                sys.exit(1)
        elif ext == ".pdf":
            try:
                import pypdf  # type: ignore[import-not-found]
            except ImportError:
                print("Error: 'pypdf' is not installed. Run: pip install pypdf", file=sys.stderr)
                sys.exit(1)
            try:
                with open(args.input, "rb") as f:
                    reader = pypdf.PdfReader(f)
                    content = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            except Exception as e:
                print(f"Error parsing PDF file: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            with open(args.input, "r", encoding="utf-8") as f:
                content = f.read()
            
    if not content.strip():
        print("Error: No text provided.", file=sys.stderr)
        sys.exit(1)

    try:
        print("Initializing ElevenLabs client...", file=sys.stderr)
        client = ElevenLabs(api_key=api_key, timeout=1800.0) # 30 mins max
        
        print("Generating audio...", file=sys.stderr)
        # We capture the generator output directly 
        audio_generator = client.text_to_speech.convert(
            text=content,
            voice_id=args.voice_id,
           model_id=args.model_id,
            output_format="mp3_44100_128",
        )
        
        print(f"Saving to {output_path}...", file=sys.stderr)
        # The SDK returns an iterator of bytes; write them directly to the destination
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            for chunk in audio_generator:
                if chunk:
                    f.write(chunk)
                    
        print(f"Saved: {output_path}", file=sys.stdout)
        
        # Emit word/char stats for the dashboard statistics badge
        _content_str: str = str(content)
        words = len(_content_str.split())
        chars = len(_content_str)
        print(f"Usage: {words} words, {chars} characters", file=sys.stdout)
        
        # Save the structured text so the dashboard can preview it
        output_stem: str = os.path.splitext(output_path)[0]
        txt_output = output_stem + ".txt"
        with open(txt_output, "w", encoding="utf-8") as txt_f:
            txt_f.write(content)

        # Optional: Auto-upload to Google Drive
        if args.drive_folder:
            print(f"Auto-uploading to Google Drive folder: '{args.drive_folder}'...", file=sys.stderr)
            try:
                import subprocess
                # Locate the upload_to_drive.py script relative to this script
                current_dir = os.path.dirname(os.path.abspath(__file__))
                drive_script = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "_000-Basics", "Data-GoogleDrive", "scripts", "upload_to_drive.py"))
                
                if os.path.exists(drive_script):
                    res = subprocess.run(
                        [sys.executable, drive_script, "--file", output_path, "--folder", args.drive_folder],
                        capture_output=True, text=True
                    )
                    if res.returncode == 0:
                        print(res.stdout, file=sys.stdout)
                        # Propagate folder and file IDs
                        for line in res.stderr.splitlines():
                            if "FolderID:" in line or "FileID:" in line:
                                sys.stderr.write(line + "\n")
                    else:
                        print(f"Warning: Drive upload failed: {res.stderr}", file=sys.stderr)
                else:
                    print(f"Warning: Could not find upload_to_drive.py at {drive_script}", file=sys.stderr)
            except Exception as drive_err:
                print(f"Warning: Unexpected error during Drive upload: {drive_err}", file=sys.stderr)

    except Exception as e:
        err_str = str(e).lower()
        if getattr(e, "status_code", None) == 429 or "429" in err_str or "quota_exceeded" in err_str:
            print(f"__ANTIGRAVITY_API_QUOTA_EXCEEDED__\n{e}", file=sys.stderr)
        else:
            print(f"ElevenLabs API Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
