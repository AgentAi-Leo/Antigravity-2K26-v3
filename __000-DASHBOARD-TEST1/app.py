import os
from typing import Any
import sys
import yaml  # type: ignore[import-not-found]
import subprocess
import glob
import streamlit as st  # type: ignore[import-not-found]
import streamlit.components.v1 as components  # type: ignore[import-not-found]
import tempfile
import mimetypes
import time
import base64
import shlex

# -----------------------------------------------------------------------------
# Helper: Get Python Path (prefers virtual environment)
# -----------------------------------------------------------------------------
def get_python_cmd():
    # Use the venv Python from the same directory as this app.py file.
    # sys.executable may point to a DIFFERENT venv (e.g. V2 symlink) that
    # lacks required packages like google-api-python-client.
    import sys
    app_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(app_dir, ".venv", "bin", "python")
    if os.path.exists(venv_python):
        return venv_python
    venv_python3 = os.path.join(app_dir, ".venv", "bin", "python3")
    if os.path.exists(venv_python3):
        return venv_python3
    # Fallback to the running interpreter
    return sys.executable

# -----------------------------------------------------------------------------
# Helper: Load External CSS
# -----------------------------------------------------------------------------
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            # Add a timestamp comment to force Streamlit to see this as new content
            css_content = f"/* {time.time()} */\n" + f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

def render_speed_controls(skill_id=None, stats_text=""):
    skill_val = f"'{skill_id}'" if skill_id else "null"
    import html as _html
    stats_html = ""
    if stats_text:
        safe_stats = _html.escape(stats_text)
        stats_html = f"""<span style="
            margin-left: 14px;
            background-color: #000;
            color: #fff;
            font-size: 15px;
            font-weight: 600;
            font-family: sans-serif;
            padding: 3px 12px;
            border-radius: 5px;
            letter-spacing: 0.02em;
            white-space: nowrap;
        ">{safe_stats}</span>"""
    components.html(
        f"""
        <style>
            body {{ margin: 0; padding: 0; background: transparent; }}
            .speed-bar {{
                display: flex;
                flex-direction: row;
                gap: 8px;
                align-items: center;
                justify-content: flex-start;
                padding: 4px 0;
            }}
            .speed-btn {{
                background: #2b2b36;
                color: #fafafa;
                border: 1px solid #454555;
                border-radius: 4px;
                padding: 4px 10px;
                font-family: sans-serif;
                font-size: 13px;
                cursor: pointer;
                transition: all 0.2s;
            }}
            .speed-btn:hover {{
                background: #3b3b4a;
                border-color: #ffd166;
            }}
        </style>
        <div class="speed-bar">
            <span style="color: #bfbfbf; font-family: sans-serif; font-size: 13px; margin-right: 4px;">Speed:</span>
            <button class="speed-btn" onclick="setSpeed(0.5)">0.5x</button>
            <button class="speed-btn" onclick="setSpeed(1.0)">1x</button>
            <button class="speed-btn" onclick="setSpeed(1.25)">1.25x</button>
            <button class="speed-btn" onclick="setSpeed(1.5)">1.5x</button>
            <button class="speed-btn" onclick="setSpeed(2.0)">2x</button>
            <button class="speed-btn" onclick="setSpeed(3.0)">3x</button>
            <button class="speed-btn" onclick="setSpeed(4.0)">4x</button>
            {stats_html}
        </div>
        <script>
            const currentSkillId = {skill_val};
            
            if (currentSkillId) {{
                // sessionStorage only persists during the tab session (lost on close)
                // whereas localStorage persists across browser sessions.
                const sessionSkillId = sessionStorage.getItem('sessionSkillId');
                
                if (sessionSkillId !== currentSkillId) {{
                    // This is either a NEW tab session or a SKILL SWITCH.
                    // Reset to 1x per user preference.
                    localStorage.setItem('audioPlaybackSpeed', '1.0');
                    sessionStorage.setItem('sessionSkillId', currentSkillId);
                    localStorage.setItem('lastSkillId', currentSkillId);
                }}
            }}

            function setSpeed(rate) {{
                localStorage.setItem('audioPlaybackSpeed', rate);
                const audios = window.parent.document.querySelectorAll('audio');
                audios.forEach(a => {{
                    a.playbackRate = rate;
                }});
                updateButtons(rate);
            }}

            function updateButtons(rate) {{
                const btns = document.querySelectorAll('.speed-btn');
                btns.forEach(btn => {{
                    const btnRate = parseFloat(btn.innerText);
                    if (btnRate === rate) {{
                        btn.style.background = '#ffd166';
                        btn.style.color = '#000';
                        btn.style.borderColor = '#ffd166';
                        btn.style.fontWeight = 'bold';
                    }} else {{
                        btn.style.background = '#2b2b36';
                        btn.style.color = '#fafafa';
                        btn.style.borderColor = '#454555';
                        btn.style.fontWeight = 'normal';
                    }}
                }});
            }}

            const applyStoredSpeed = () => {{
                const savedSpeed = parseFloat(localStorage.getItem('audioPlaybackSpeed') || '1.0');
                const audios = window.parent.document.querySelectorAll('audio');
                audios.forEach(a => {{
                    if (Math.abs(a.playbackRate - savedSpeed) > 0.01) {{
                        a.playbackRate = savedSpeed;
                    }}
                }});
                updateButtons(savedSpeed);
            }};

            window.addEventListener('load', applyStoredSpeed);
            applyStoredSpeed();
            setInterval(applyStoredSpeed, 500);
        </script>
        """,
        height=40
    )

def trigger_duplicate_error():
    """Triggers the centered animated error overlay with sound."""
    st.markdown(f"<div class='centered-overlay-error' data-salt='{time.time()}'>⚠️ FILE(S) ALREADY EXISTS!</div>", unsafe_allow_html=True)
    sound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio", "universfield-system-error-notice-132470.mp3")
    if os.path.exists(sound_path):
        with open(sound_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)

def cancel_processing():
    """Callback to instantly abort processing and clear the UI."""
    # Since Streamlit reruns on click, this callback runs before the rest of the script.
    # We clear the active triggers so the script doesn't try to auto-run again on reload
    set_skill_state("prev_upload_id", "CANCELLED")
    if get_skill_state("auto_open_result"):
        set_skill_state("auto_open_result", False)

def trigger_processing_overlay():
    """Shows a centered processing banner with a dots animation and a cancel button."""
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
            <div class='centered-overlay-processing' style='pointer-events: auto; padding-bottom: 20px;'>
                <div style='line-height: 1.1; margin-bottom: 10px;'>
                    PROCESSING!<br>
                    <span style='font-size: 0.6em; opacity: 0.8; font-weight: normal;'>Please stand by!</span>
                </div>
                <div class='dots-container'>
                    <div class='dot'></div>
                    <div class='dot'></div>
                    <div class='dot'></div>
                </div>
                <div style='font-size: 0.9rem; color: #ffffff; font-weight: normal; margin-top: 10px; margin-bottom: 20px;'>
                    Depending on file size: Could Take Up to 5 mins.
                </div>
            </div>
            <style>
                /* Elevate the stButton above the overlay background */
                /* Streamlit renders buttons inside several wrapper divs. 
                   We need to target the top-level button container *within* this st.empty() block */
                div[data-testid="stVerticalBlock"] > div:has(button) {
                    position: fixed !important;
                    bottom: 20px !important;
                    right: 20px !important;
                    top: auto !important;
                    left: auto !important;
                    transform: none !important;
                    z-index: 999999 !important;
                    display: flex !important;
                    justify-content: center !important;
                }
                button[kind="secondary"] {
                    background-color: rgba(200, 30, 30, 0.8) !important;
                    color: rgba(255, 255, 255, 0.9) !important;
                    border: 1px solid rgba(255, 100, 100, 0.4) !important;
                    padding: 6px 20px !important;
                    font-size: 12px !important;
                    font-weight: bold !important;
                    letter-spacing: 1px !important;
                    border-radius: 8px !important;
                    transition: all 0.2s ease !important;
                    box-shadow: 0px 4px 15px rgba(0,0,0,0.5) !important;
                }
                button[kind="secondary"]:hover {
                    color: #fff !important;
                    border-color: #ffcccc !important;
                    background-color: rgba(230, 50, 50, 0.9) !important;
                    transform: scale(1.05) !important;
                }
            </style>
        """, unsafe_allow_html=True)
        # Add the actual interactive button over the HTML overlay
        st.button("CANCEL", on_click=cancel_processing, key=f"cancel_btn_{time.time()}", help="Immediately stop processing and discard results.")
    return placeholder

def trigger_complete_overlay(placeholder):
    """Replaces processing banner with a complete banner that fades out."""
    if placeholder:
        with placeholder:
            st.markdown("<div class='centered-overlay-complete'>COMPLETE!</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Helper: Process Audio/Video Transcription
# -----------------------------------------------------------------------------
def process_uploaded_files(file_paths, selected_skill, run_env, base_args_input="", drive_folder="", google_sheet="", share_with="", proc_overlay=None, main_spinner=None):
    """Executes transcription for a list of files and returns the processed data."""
    results = []
    progress_text = st.empty()
    cwd = selected_skill["dir"]
    
    python_cmd = get_python_cmd()
    
    # Generate batch ID for multi-file grouping in Google Sheets
    import datetime as _dt
    batch_id = _dt.datetime.now().strftime("%Y-%m-%d_%H:%M")
    total_words: int = 0
    
    # --- DEBUG: Log all parameters received ---
    import logging
    logging.basicConfig(level=logging.DEBUG)
    _log = logging.getLogger("process_uploaded_files")
    _log.info(f"[DEBUG] base_args_input = {repr(base_args_input)}")
    _log.info(f"[DEBUG] drive_folder = {repr(drive_folder)}")
    _log.info(f"[DEBUG] google_sheet = {repr(google_sheet)}")
    _log.info(f"[DEBUG] share_with = {repr(share_with)}")
    _log.info(f"[DEBUG] cwd = {repr(cwd)}")
    _log.info(f"[DEBUG] python_cmd = {repr(python_cmd)}")
    _log.info(f"[DEBUG] ELEVENLABS_API_KEY in env = {bool(run_env.get('ELEVENLABS_API_KEY'))}")
    _log.info(f"[DEBUG] GEMINI_API_KEY in env = {bool(run_env.get('GEMINI_API_KEY'))}")
    _log.info(f"[DEBUG] file_paths = {file_paths}")
    # --- END DEBUG ---
    
    for i, fp in enumerate(file_paths):
        progress_text.info(f"⏳ PROCESSING file {i+1} of {len(file_paths)}: `{os.path.basename(fp)}`...")
        
        # Build command with UI-provided arguments
        local_args = str(base_args_input).replace("{FILE_1}", str(fp))
        import shlex
        try:
            local_parsed = shlex.split(local_args)
        except Exception:
            local_parsed = []
            
        if "--input" not in local_parsed and "input" not in str(local_args):
            local_parsed = ["--input", fp] + local_parsed
            
        current_cmd = [python_cmd, selected_skill["script"]] + local_parsed
        if drive_folder:
            current_cmd.extend(["--drive-folder", drive_folder])
        if google_sheet:
            current_cmd.extend(["--google-sheet", google_sheet])
            current_cmd.extend(["--batch-id", batch_id])
            current_cmd.extend(["--batch-seq", str(i + 1)])
        if share_with:
            current_cmd.extend(["--share-with", share_with])
        
        # --- DEBUG: Log exact command ---
        _log.info(f"[DEBUG] FULL CMD: {current_cmd}")
        # --- END DEBUG ---
        
        # Stream the output line by line into the UI
        process = subprocess.Popen(
            current_cmd, cwd=cwd, env=run_env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, universal_newlines=True
        )
        
        full_output: list[str] = []
        output_placeholder = st.empty()
        
        stdout_stream = process.stdout
        if stdout_stream is not None:
            for line in iter(stdout_stream.readline, ""):
                full_output.append(str(line))
                # Update UI with the latest 20 lines to keep it snappy
                output_placeholder.code("".join(full_output[-20:])) # type: ignore
                
        returncode = process.wait()
        
        # Combine everything for legacy parsing logic
        final_text = "".join(full_output)
        
        # --- DEBUG: Log subprocess result ---
        _log.info(f"[DEBUG] returncode = {returncode}")
        _dbg_out: str = repr(final_text)
        _log.info(f"[DEBUG] combined output = {_dbg_out[:500]}")  # type: ignore[index]
        # --- END DEBUG ---
        
        transcript = ""
        if returncode == 0:
            ignore_prefixes = ("Transcribing:", "Saved:", "Usage:")
            lines = [l for l in final_text.splitlines() if not l.startswith(ignore_prefixes)]
            transcript = "\n".join(lines).strip()
            
            # Track words for batch summary
            total_words += len(transcript.split()) # type: ignore[operator]
            
            # Capture Google IDs from combined output for badge direct-links
            _machine_prefixes = ("Usage:", "Link:", "FolderID:", "SheetID:", "Auto-uploading", "Logging results", "Converting", "Warning:")
            for line in final_text.splitlines():
                if line.startswith("FolderID:"):
                    st.session_state["_google_folder_id"] = line.split(":", 1)[1].strip()
                elif line.startswith("SheetID:"):
                    st.session_state["_google_sheet_id"] = line.split(":", 1)[1].strip()
            
            # Show non-machine lines as warnings (but filter out machine-readable ones)
            # Since stdout and stderr are combined, this heuristic might catch script logs.
            # We'll just append the whole cleaned transcript.
            
            # Extract usage — audio_transcribe.py writes Usage: to stderr; text2speech.py uses stdout
            usage_line = next((l for l in final_text.splitlines() if l.startswith("Usage:")), None)
            if usage_line:
                transcript += f"\n\n**Statistics:** {usage_line.split(':', 1)[-1].strip()}"
            
            results.append({
                "name": os.path.basename(fp),
                "bytes": open(fp, "rb").read() if os.path.exists(fp) else b"",
                "transcript": transcript,
            })
        else:
            if "__ANTIGRAVITY_API_QUOTA_EXCEEDED__" in final_text:
                if proc_overlay:
                    proc_overlay.empty()
                if main_spinner:
                    main_spinner.empty()
                progress_text.empty()
                
                # Try to extract detailed message
                import re
                quota_msg = ""
                
                if "kie" in selected_skill["basename"].lower():
                    # Extract the custom Kie.ai msg with bracketed code
                    match = re.search(r"Kie\.ai (?:Upload |Polling )?Error \[(.*?)\]: (.*)(?:\n|$)", final_text)
                    if match:
                        err_code = match.group(1)
                        err_msg = match.group(2).strip()
                        quota_msg = f"\n\n**Details [{err_code}]:** {err_msg}"
                    else:
                        # Fallback for old/unparsed format
                        match_old = re.search(r"Kie\.ai Error: (.*?)(?:\n|$)", final_text)
                        if match_old:
                            quota_msg = f"\n\n**Details:** {match_old.group(1).strip()}"
                    
                    st.error(f"⚠️ **DENIED!** You have reached the maximum usage allowed by your **Kie.ai** balance.{quota_msg}")

                else:
                    # Standard ElevenLabs
                    match = re.search(r"['\"]message['\"]:\s*['\"](.*?)['\"]", final_text)
                    if match:
                        quota_msg = f"\n\n**Usage stats:** {match.group(1)}"
                    st.error(f"⚠️ **DENIED!** You have reached the maximum usage allowed by your **ElevenLabs** active subscription/plan. Please upgrade your plan or wait for the quota to reset.{quota_msg}")
                st.stop()
            
            st.error("Execution Error")
            st.code(final_text)
            continue
    
    progress_text.empty()
    
    # Append batch summary row if files were processed to a Google Sheet
    if google_sheet and len(results) > 0:
        try:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sheet_script = os.path.join(root_dir, "_000-Basics", "Data-GoogleSheet", "scripts", "append_to_sheet.py")
            if os.path.exists(sheet_script):
                summary_cmd = [python_cmd, sheet_script, "--title", google_sheet,
                               "--batch-id", batch_id, "--batch-summary",
                               "--data", f"{len(results)} files", f"{total_words} total words"]
                if share_with:
                    summary_cmd.extend(["--share-with", share_with])
                subprocess.run(summary_cmd, cwd=cwd, capture_output=True, text=True, env=run_env)
        except Exception:
            pass  # Summary row is non-critical
    
    return results

def process_tts_files(file_paths, selected_skill, run_env, base_args_input="", drive_folder="", google_sheet="", share_with="", proc_overlay=None, main_spinner=None):
    """Executes Text2Speech for a list of document files and returns the processed audio data."""
    results = []
    progress_text = st.empty()
    cwd = selected_skill["dir"]
    
    python_cmd = get_python_cmd()
    
    # Generate batch ID for multi-file grouping in Google Sheets
    import datetime as _dt
    batch_id = _dt.datetime.now().strftime("%Y-%m-%d_%H:%M")
    total_words: int = 0
    
    for i, fp in enumerate(file_paths):
        original_name = os.path.basename(fp)
        progress_text.info(f"⏳ PROCESSING document {i+1} of {len(file_paths)}: `{original_name}`...")
        
        local_args = str(base_args_input).replace("{FILE_1}", str(fp))
        import shlex
        try:
            local_parsed = shlex.split(local_args)
        except Exception:
            local_parsed = ["--input", fp]
            
        current_cmd = [python_cmd, selected_skill["script"]] + local_parsed
        if drive_folder:
            current_cmd.extend(["--drive-folder", drive_folder])
        if google_sheet:
            current_cmd.extend(["--google-sheet", google_sheet])
            current_cmd.extend(["--batch-id", batch_id])
            current_cmd.extend(["--batch-seq", str(i + 1)])
        if share_with:
            current_cmd.extend(["--share-with", share_with])
        res = subprocess.run(current_cmd, cwd=cwd, capture_output=True, text=True, env=run_env)
        
        if res.returncode == 0:
            saved_path = None
            for line in res.stdout.splitlines():
                if "Saved:" in line:
                    saved_path = line.split("Saved:")[1].strip()
                    break
            
            if saved_path:
                saved_path_str: str = str(saved_path)
                full_saved_path = saved_path_str if os.path.isabs(saved_path_str) else os.path.join(cwd, saved_path_str)
                if os.path.exists(str(full_saved_path)):
                    with open(str(full_saved_path), "rb") as af:
                        audio_bytes = af.read()
                    
                    # The text2speech script now outputs the parsed text alongside the audio file
                    txt_path: str = os.path.splitext(full_saved_path)[0] + ".txt"
                    content_preview = ""
                    if os.path.exists(txt_path):
                        try:
                            with open(txt_path, "r", encoding="utf-8") as tf:
                                content_preview = tf.read(5000)
                                if len(content_preview) == 5000:
                                    content_preview += "...\n\n[Preview truncated due to length. Navigate or download for full context]"
                        except:
                            content_preview = f"Narrated Document: {original_name}"
                    else:
                        content_preview = f"Narrated Document: {original_name}"
                    
                    # Extract usage (suppress for manual TTS input per user request)
                    usage_line = next((l for l in res.stdout.splitlines() if l.startswith("Usage:")), None)
                    if usage_line:
                        is_manual_input = (os.path.basename(fp) == "input_text.txt")
                        if not is_manual_input:
                            content_preview += f"\n\n**Statistics:** {usage_line.split(':', 1)[-1].strip()}"

                    # Capture Google IDs from stderr for badge direct-links
                    _tts_machine_prefixes = ("Usage:", "Link:", "FolderID:", "SheetID:", "Auto-uploading", "Logging results", "Converting", "Warning:")
                    for stderr_line in res.stderr.splitlines():
                        if stderr_line.startswith("FolderID:"):
                            st.session_state["_google_folder_id"] = stderr_line.split(":", 1)[1].strip()
                        elif stderr_line.startswith("SheetID:"):
                            st.session_state["_google_sheet_id"] = stderr_line.split(":", 1)[1].strip()

                    # Surface stderr logs as well (filter out machine-readable lines)
                    err_lines = [l for l in res.stderr.strip().splitlines() if not any(l.startswith(p) for p in _tts_machine_prefixes)]
                    if err_lines:
                        content_preview += "\n\n**Backend Logs/Warnings:**\n" + "\n".join(err_lines).strip()

                    results.append({
                        "name": os.path.basename(full_saved_path),
                        "original_name": original_name,
                        "bytes": audio_bytes,
                        "transcript": content_preview,
                        "content_preview": content_preview
                    })
                    # Track words for batch summary (use raw content, not formatted preview)
                    total_words += len(content_preview.split()) # type: ignore[operator]
                else:
                    st.error(f"Could not find output file for {original_name}: {saved_path}")
            else:
                 st.error(f"Could not parse 'Saved:' path from output for {original_name}")
        else:
            if "__ANTIGRAVITY_API_QUOTA_EXCEEDED__" in res.stderr:
                if proc_overlay:
                    proc_overlay.empty()
                if main_spinner:
                    main_spinner.empty()
                progress_text.empty()
                
                import re
                quota_msg = ""
                
                if "kie" in selected_skill["basename"].lower():
                    # Extract the custom Kie.ai msg with bracketed code
                    match = re.search(r"Kie\.ai (?:Upload |Polling )?Error \[(.*?)\]: (.*)(?:\n|$)", res.stderr)
                    if match:
                        err_code = match.group(1)
                        err_msg = match.group(2).strip()
                        quota_msg = f"\n\n**Details [{err_code}]:** {err_msg}"
                    else:
                        # Fallback
                        match_old = re.search(r"Kie\.ai Error: (.*?)(?:\n|$)", res.stderr)
                        if match_old:
                            quota_msg = f"\n\n**Details:** {match_old.group(1).strip()}"
                    st.error(f"⚠️ **DENIED!** You have reached the maximum usage allowed by your **Kie.ai** balance.{quota_msg}")

                else:
                    # Standard ElevenLabs
                    match = re.search(r"['\"]message['\"]:\s*['\"](.*?)['\"]", res.stderr)
                    if match:
                        quota_msg = f"\n\n**Usage stats:** {match.group(1)}"
                    st.error(f"⚠️ **DENIED!** You have reached the maximum usage allowed by your **ElevenLabs** active subscription/plan. Please upgrade your plan or wait for the quota to reset.{quota_msg}")
                st.stop()
            st.error("Execution Error")
            st.code(res.stderr)
    
    progress_text.empty()
    
    # Append batch summary row if files were processed to a Google Sheet
    if google_sheet and len(results) > 0:
        try:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sheet_script = os.path.join(root_dir, "_000-Basics", "Data-GoogleSheet", "scripts", "append_to_sheet.py")
            if os.path.exists(sheet_script):
                summary_cmd = [python_cmd, sheet_script, "--title", google_sheet,
                               "--batch-id", batch_id, "--batch-summary",
                               "--data", f"{len(results)} files", f"{total_words} total words"]
                if share_with:
                    summary_cmd.extend(["--share-with", share_with])
                subprocess.run(summary_cmd, cwd=cwd, capture_output=True, text=True, env=run_env)
        except Exception:
            pass  # Summary row is non-critical
    
    return results


st.set_page_config(page_title="Antigravity Skills", page_icon="🚀", layout="wide")
load_css() # Global CSS load to ensure banners work on main page

# -----------------------------------------------------------------------------
# Helper: Generate PDF via Convtr-PlainTxt2PDF Skill
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False, max_entries=50)
def generate_pdf_from_text(text: str) -> bytes:
    """Uses the PlainTxt2PDF skill to convert text to PDF bytes."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    skill_script = os.path.join(root_dir, "_000-Basics", "Convtr-PlainTxt2PDF", "scripts", "plain_txt2pdf.py")
    
    # Fallback to _100-TBD if not found in _000-Basics
    if not os.path.exists(skill_script):
        skill_script = os.path.join(root_dir, "_100-TBD", "Convtr-PlainTxt2PDF", "scripts", "plain_txt2pdf.py")
    
    if not os.path.exists(skill_script):
        return b""
        
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        input_txt = os.path.join(tmpdir, "temp_transcript.txt")
        output_pdf = os.path.join(tmpdir, "temp_transcript.pdf")
        
        with open(input_txt, "w", encoding="utf-8") as f:
            f.write(text)
            
        python_cmd = get_python_cmd()
        
        cmd = [python_cmd, skill_script, "--input", input_txt, "--output", output_pdf, "--font-size", "13"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        if os.path.exists(output_pdf):
            with open(output_pdf, "rb") as f:
                return f.read()
        else:
            try:
                with open("/tmp/antigravity_pdf_error.log", "a") as errf:
                    errf.write(f"PDF FAILED!\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}\n")
            except Exception:
                pass
            st.error(f"PDF GENERATION FAILED!\n\nSTDOUT:\n{res.stdout}\n\nSTDERR:\n{res.stderr}")
    return b""

@st.cache_data(show_spinner=False, max_entries=50)
def generate_docx_from_text(text: str) -> bytes:
    """Generates a DOCX file from text returning bytes."""
    import io
    try:
        from docx import Document  # type: ignore[import-not-found]
        from docx.enum.text import WD_ALIGN_PARAGRAPH  # type: ignore[import-not-found]
        from docx.shared import Pt  # type: ignore[import-not-found]
    except ImportError:
        return b""
    
    doc = Document()
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        p = doc.add_paragraph()
        run = p.add_run(line)
        
        # Check if this is the source file line at the very end
        if line.startswith("Source File:") and i >= len(lines) - 2:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run.font.size = Pt(9) # Keep footer small
        else:
            run.font.size = Pt(13) # Body text ~20% larger than default 11pt
            
    f = io.BytesIO()
    doc.save(f)
    return f.getvalue()

@st.cache_data(show_spinner=False, max_entries=50)
def generate_doc_rtf_from_text(text: str) -> bytes:
    """Generates a basic RTF string for .doc compatibility."""
    # Split to find the source file line
    lines = text.split('\n')
    
    rtf = "{\\rtf1\\ansi\\ansicpg1252\\deff0\\nouicompat\\deflang1033{\\fonttbl{\\f0\\fnil\\fcharset0 Calibri;}}\n"
    rtf += "{\\*\\generator Antigravity;}\\viewkind4\\uc1\n"
    
    for i, line in enumerate(lines):
        escaped_line = line.replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}')
        
        if line.startswith("Source File:") and i >= len(lines) - 2:
            # \qc = center align, \fs18 = 9pt (~15% smaller than 11pt/22 half-pts)
            rtf += "\\pard\\qc\\sa200\\sl276\\slmult1\\f0\\fs18\\lang9 " + escaped_line + "\\par\n"
        else:
            # \ql = left align, \fs26 = 13pt (20% larger than 11pt)
            rtf += "\\pard\\ql\\sa200\\sl276\\slmult1\\f0\\fs26\\lang9 " + escaped_line + "\\par\n"
            
    rtf += "}"
    return rtf.encode('utf-8')

def read_text_file_preview(path: str) -> str:
    """Reads a text, md, or rtf file for preview purposes."""
    ext = os.path.splitext(path)[1].lower()
    
    # Skip PDF files as they are binary and not human-readable in raw text format
    if ext == ".pdf":
        return ""
    
    # Pre-flight check for RTF files hiding under .txt extension (common with Mac TextEdit)
    is_actually_rtf = ext == ".rtf"
    if not is_actually_rtf and os.path.getsize(path) > 0:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                if f.read(5).startswith("{\\rtf"):
                    is_actually_rtf = True
        except Exception:
            pass

    try:
        # Use native mac util for RTF and legacy DOC files for perfect text matching (via HTML for lists)
        if is_actually_rtf or ext == ".doc":
            import subprocess
            try:
                res = subprocess.run(["textutil", "-convert", "html", "-stdout", path],
                                     capture_output=True, text=True, check=True)
                from html.parser import HTMLParser
                import re
                
                class RTFListParser(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.text = []
                        self.in_body = False
                        self.list_stack = []
                        self.ol_counters = []

                    def _add_newline_if_needed(self):
                        if self.text and not self.text[-1].endswith('\n') and not self.text[-1].endswith('\n '):
                            self.text.append('\n')

                    def get_indent(self):
                        level = len(self.list_stack)
                        return "  " * level if level > 0 else ""

                    def handle_starttag(self, tag, attrs):
                        if tag == 'body':
                            self.in_body = True
                        elif tag in ('p', 'div'):
                            self._add_newline_if_needed()
                        elif tag == 'br' and self.in_body:
                            self.text.append('\n')
                        elif tag == 'ul':
                            self.list_stack.append('ul')
                            self.ol_counters.append(0)
                            self._add_newline_if_needed()
                        elif tag == 'ol':
                            self.list_stack.append('ol')
                            self.ol_counters.append(1)
                            self._add_newline_if_needed()
                        elif tag == 'li':
                            self._add_newline_if_needed()
                            indent = self.get_indent()
                            if self.list_stack:
                                list_type = self.list_stack[-1]
                                if list_type == 'ul':
                                    self.text.append(f"{indent}\u2022 ")
                                elif list_type == 'ol':
                                    count = self.ol_counters[-1]
                                    self.text.append(f"{indent}{count}. ")
                                    self.ol_counters[-1] += 1

                    def handle_endtag(self, tag):
                        if tag == 'body':
                            self.in_body = False
                        elif tag in ('p', 'div'):
                            self._add_newline_if_needed()
                        elif tag in ('ul', 'ol'):
                            if self.list_stack:
                                self.list_stack.pop()
                                self.ol_counters.pop()
                            self._add_newline_if_needed()

                    def handle_data(self, data):
                        if self.in_body:
                            if not data.strip():
                                pass
                            else:
                                cleaned = re.sub(r'[\r\n]+', '', data)
                                if cleaned:
                                    self.text.append(cleaned.strip() + " ")
                                
                parser = RTFListParser()
                parser.feed(res.stdout)
                extracted = "".join(parser.text).strip()
                import io as _io
                extracted_str: str = "".join(parser.text).strip()
                return _io.StringIO(re.sub(r'\n{3,}', '\n\n', extracted_str)).read(10000)
            except Exception:
                pass # Fallback below
                
        # Use python-docx for DOCX files
        elif ext == ".docx":
            try:
                import docx  # type: ignore[import-not-found]
                doc = docx.Document(path)
                fullText = []
                for para in doc.paragraphs:
                    fullText.append(para.text)
                import io as _io2
                return _io2.StringIO('\n'.join(fullText)).read(10000)
            except Exception:
                pass # Fallback below

        # Raw read fallback for TXT, MD, Code or failed RTF
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read(10000)
            
        if is_actually_rtf:
            # Simple RTF stripper fallback if textutil failed (Note: strips newlines)
            import re
            text = re.sub(r"\\'[0-9a-fA-F]{2}", "", raw)
            text = re.sub(r"\\[a-z*]+\-?\d*[ ]?", " ", text)
            text = re.sub(r"\\[{}\\]", "", text)
            for _ in range(5): text = re.sub(r"\{[^{}]*\}", " ", text)
            text = re.sub(r"[{}]", "", text)
            text = re.sub(r"\n{3,}", "\n\n", text)
            return text.strip()
            
        return raw

    except Exception as e:
        return f"(Could not generate preview: {e})"
   # Helper: Generate a ZIP file of all transcripts dynamically
@st.cache_data(show_spinner=False, max_entries=50)
def generate_zip_of_all_transcripts(processed_files_list, format_option, include_sources=False):
    import io
    import zipfile
    import os
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for i, f in enumerate(processed_files_list):
            fname = os.path.splitext(f["name"])[0]
            
            if format_option.startswith("MP3") or format_option == "MP3 Audio (.mp3)":
                zip_file.writestr(f"{fname}.mp3", f["bytes"])
                continue

            # --- Smart ZIP Pass-through ---
            # If we don't need sources and the file is already the requested format, use its raw bytes directly.
            # This preserves 100% quality and prevents blank pages from empty previews.
            current_ext = os.path.splitext(f["name"])[1].lower()
            is_matching_pdf = format_option.startswith("PDF") and current_ext == ".pdf"
            is_matching_docx = format_option.startswith("DOCX") and current_ext == ".docx"
            
            if not include_sources and (is_matching_pdf or is_matching_docx):
                zip_file.writestr(f["name"], f["bytes"])
                continue

            # Otherwise, it's a document format
            download_text = f.get("content_preview") or ""
            if not download_text.strip():
                transcript = f.get("transcript", "")
                # Filter out success messages if falling back to transcript
                if not any(x in transcript for x in ["Successfully", "Generated:", "✅"]):
                    download_text = transcript
            
            # Prepend Source Header if requested (matching Merge Source style)
            if include_sources:
                header = f"--- Document: {f['name']} ---\n\n"
                download_text = header + download_text
            
            if format_option == "TXT (.txt)" or "TXT" in format_option:
                zip_file.writestr(f"{fname}.txt", download_text)
            elif format_option == "PDF (.pdf)" or "PDF" in format_option:
                pdf_bytes = generate_pdf_from_text(download_text)
                if pdf_bytes:
                    zip_file.writestr(f"{fname}.pdf", pdf_bytes)
                else:
                    zip_file.writestr(f"{fname}_PDF_Generation_Failed.txt", "PDF conversion failed for this file. Please check logs.")
            elif format_option == "DOCX (.docx)" or "DOCX" in format_option:
                docx_bytes = generate_docx_from_text(download_text)
                if docx_bytes:
                    zip_file.writestr(f"{fname}.docx", docx_bytes)
                else:
                    zip_file.writestr(f"{fname}_DOCX_Generation_Failed.txt", "DOCX conversion failed for this file.")
            elif format_option == "DOC (.doc)" or "DOC" in format_option:
                doc_bytes = generate_doc_rtf_from_text(download_text)
                if doc_bytes:
                    zip_file.writestr(f"{fname}.doc", doc_bytes)
                else:
                    zip_file.writestr(f"{fname}_DOC_Generation_Failed.txt", "DOC conversion failed for this file.")
                    
        # Add direct high-fidelity file to ZIP if available and not already included
        direct_file = st.session_state.get("direct_download_file")
        if direct_file:
            zip_file.writestr(direct_file["name"], direct_file["bytes"])
            
    return zip_buffer.getvalue()

# initialization session state tracking 
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Helper: get the absolute path to the secret manager script
def _sm_script_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "000C-SKILL_SECURITY-GCSecrtMgr", "scripts", "secret_manager.py")

def _fetch_gcp_secret(secret_name: str) -> str:
    """Fetch a secret value from GCP Secret Manager by calling gcloud directly."""
    try:
        # Setup environment PATH to include the local gcloud SDK if it exists
        env = os.environ.copy()
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        gcloud_bin = os.path.join(base_dir, "google-cloud-sdk", "bin")
        if os.path.isdir(gcloud_bin):
            env["PATH"] = gcloud_bin + ":" + env.get("PATH", "")
        
        # Use gcloud directly — it was confirmed to work in the terminal
        # omitting --project so it uses the active account's project context
        res = subprocess.run(
            ["gcloud", "secrets", "versions", "access", "latest", f"--secret={secret_name}"],
            capture_output=True, text=True, timeout=15, env=env
        )
        if res.returncode != 0:
            # Silently log error for developer debugging
            with open("/tmp/gcp_secret_error.log", "a") as f:
                f.write(f"Error fetching {secret_name}: {res.stderr}\n")
            return ""
        return res.stdout.strip()
    except Exception as e:
        with open("/tmp/gcp_secret_error.log", "a") as f:
            f.write(f"Exception fetching {secret_name}: {str(e)}\n")
        return ""

# -----------------------------------------------------------------------------
# 1. Authentication via GCP Secret Manager
# -----------------------------------------------------------------------------
def check_password():
    """Returns True if the user has entered the correct GCP secret password."""
    load_css() # Apply styles to login screen
    if st.session_state.get("authenticated", False):
        return True



    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.title("🔒 Antigravity Dashboard", anchor=False)
    # Description removed per user request
    
    
    with st.form("login_form", clear_on_submit=False, border=False):
        st.markdown('<div class="password-container">', unsafe_allow_html=True)
        password = st.text_input("Password", type="password", placeholder="Enter Password", label_visibility="collapsed")
        
        # Keybind TAB to focus the password input field
        st.components.v1.html(
            """
            <script>
            const doc = window.parent.document;
            if (!doc._tabKeyBound) {
                doc._tabKeyBound = true;
                doc.addEventListener('keydown', function(e) {
                    if (e.key === 'Tab' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                        const pwInput = doc.querySelector('input[type="password"]');
                        if (pwInput) {
                            pwInput.focus();
                            e.preventDefault();
                        }
                    }
                });
            }
            </script>
            """,
            height=0
        )
        
        # Container for reliable yellow styling
        st.markdown("<div class='unlock-btn-container'>", unsafe_allow_html=True)
        unlock_clicked = st.form_submit_button("Unlock", use_container_width=False)
        st.markdown("</div>", unsafe_allow_html=True)
    
    if unlock_clicked:
        with st.spinner("Verifying via Google Cloud Secret Manager..."):
            try:
                real_secret = _fetch_gcp_secret("DEV-TEST1-LOGIN")
                if not real_secret:
                    st.error("Failed to fetch secret from GCP. Check your gcloud auth.")
                    return False
                    
                if password == real_secret:
                    st.session_state["authenticated"] = True

                    
                    # Auto-fetch API keys from GCP secrets at login
                    with st.spinner("Loading API keys from GCP..."):
                        gemini_key = _fetch_gcp_secret("DEV-TEST2-GEMINI")
                        if gemini_key:
                            st.session_state["GEMINI_API_KEY"] = gemini_key
                        elevenlabs_key = _fetch_gcp_secret("DEV-TEST3-11LABS")
                        if elevenlabs_key:
                            st.session_state["ELEVENLABS_API_KEY"] = elevenlabs_key
                        kie_key = _fetch_gcp_secret("DEV-TEST0-KIE")
                        if kie_key:
                            st.session_state["KIE_API_KEY"] = kie_key
                        
                        g_user_email = _fetch_gcp_secret("DEV-TEST5-G_USER")
                        if g_user_email:
                            st.session_state["GCP_USER_EMAIL"] = g_user_email
                    
                    st.rerun()
                else:
                    st.error("Incorrect password or failed to fetch secret. Ensure you are logged in to gcloud (`gcloud auth login`).")
            except Exception as e:
                st.error(f"An error occurred: {e}")
    st.markdown("</div>", unsafe_allow_html=True)
    return False

if not check_password():
    st.stop()  # Do not render the rest of the app until authenticated


# -----------------------------------------------------------------------------
# 2. Skill Discovery & Parsing
# -----------------------------------------------------------------------------
def discover_skills():
    """Scans the parent directory recursively for all SKILL.md files and extracts their info."""
    skills = []
    # Build absolute path to the skills root based on this app.py
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Exclude the dashboard and backup folders from the search
    excludes = ["__000-DASHBOARD-TEST1", "000A_BKUP", ".venv", "__pycache__", ".git"]
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Modification: avoid searching inside excluded directories
        dirnames[:] = [d for d in dirnames if not any(ex in d for ex in excludes)]  # type: ignore[index]
        
        if "SKILL.md" in filenames:
            # Skill ID is now the relative path from root_dir for uniqueness
            skill_rel_path = os.path.relpath(dirpath, root_dir)
            skill_dir_name = os.path.basename(dirpath)
            
            # Category is the top-level directory name relative to root
            rel_parts = skill_rel_path.split(os.sep)
            # If skill is in root, it has no specific category folder
            category = rel_parts[0] if len(rel_parts) > 1 else "General"
            
            skill_md_path = os.path.join(dirpath, "SKILL.md")
            
            try:
                # Parse the YAML frontmatter
                with open(skill_md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                parts = content.split("---")
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    # The "name" from YAML is now a "display_title" (subtitle)
                    # The primary 'name' used in the dashboard is the folder basename
                    display_title = frontmatter.get("name", skill_dir_name)
                    desc = frontmatter.get("description", "No description provided.")
                else:
                    display_title = skill_dir_name
                    desc = "No frontmatter found in SKILL.md"
                    
                # Unified Antigravity naming: Primary name = folder basename
                name = skill_dir_name
                    
                # Look for the main python script
                # 1. Check if frontmatter specifies a script
                fm_script = frontmatter.get("script")
                if fm_script:
                    main_script = os.path.join(dirpath, fm_script)
                else:
                    # 2. Fallback to glob (take the first one)
                    scripts = glob.glob(os.path.join(dirpath, "scripts", "*.py"))
                    main_script = scripts[0] if scripts else None
                
                skills.append({
                    "id": skill_rel_path,
                    "basename": skill_dir_name,
                    "name": name,
                    "display_title": display_title,
                    "category": category,
                    "desc": desc,
                    "dir": dirpath,
                    "script": main_script
                })
                
                # Once a skill is found, we stop walking deeper into THIS specific directory tree
                dirnames[:] = []  # type: ignore[index]
                
            except Exception:
                # Silently fail discovery for malformed/missing SKILL.md
                pass
                
    return skills


# -----------------------------------------------------------------------------
# 3. Main Dashboard UI
# -----------------------------------------------------------------------------
skills = discover_skills()

st.sidebar.title("🚀 Antigravity Skills", anchor=False)
st.sidebar.markdown(f"**{len(skills)} skills loaded**")

# Add Search Box
query_params = st.query_params
default_search = query_params.get("search", "")
search_query = st.sidebar.text_input("🔍 Search skills...", value=default_search).lower()

# Sync search to query params
if search_query:
    st.query_params["search"] = search_query
elif "search" in query_params:
    # Clear search if input is empty
    st.query_params.pop("search")

# Filter skills dynamically
if search_query:
    display_skills = [
        s for s in skills 
        if (s.get('name') and search_query in str(s.get('name')).lower()) or 
           (s.get('desc') and search_query in str(s.get('desc')).lower()) or
           (s.get('category') and search_query in str(s.get('category')).lower())
    ]
else:
    display_skills = skills

# Show API key status
if st.session_state.get("GEMINI_API_KEY"):
    st.sidebar.success("🔑 GEMINI_API_KEY loaded from GCP")
else:
    st.sidebar.warning("⚠️ GEMINI_API_KEY not found (DEV-TEST2-GEMINI)")
if st.session_state.get("ELEVENLABS_API_KEY"):
    st.sidebar.success("🔑 ELEVENLABS_API_KEY loaded from GCP")
else:
    st.sidebar.warning("⚠️ ELEVENLABS_API_KEY not found (DEV-TEST3-11LABS)")

if not skills:
    st.error("No skills found. Please ensure SKILL.md files exist in the parent directories.")
    st.stop()
    
# Sort final list by display name alphabetically so it makes sense to the user
display_skills = sorted(display_skills, key=lambda s: (s.get('name') or '').lower())

if not display_skills:
    st.sidebar.warning(f"No skills match '{search_query}'.")
    st.warning("Please clear the search to see all available skills.")
    st.stop()

import json

# Setup Recent Skills
RECENT_SKILLS_FILE = os.path.join(os.path.dirname(__file__), "recent_skills.json")

def load_recent_skills():
    if os.path.exists(RECENT_SKILLS_FILE):
        try:
            with open(RECENT_SKILLS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_recent_skill(skill_id):
    recents = load_recent_skills()
    if skill_id in recents:
        recents.remove(skill_id)
    recents.insert(0, skill_id)
    import io as _io_r
    _joined = " ".join(str(r) for r in recents)
    recents = _joined.split()[:4]  # type: ignore[misc]  # Keep top 4
    try:
        with open(RECENT_SKILLS_FILE, "w") as f:
            json.dump(recents, f)
    except Exception:
        pass
    return recents

# Helper: Skill-Specific Session State Namespacing
def get_skill_state(key, default=None):
    """Returns a namespaced session state key for the current skill."""
    if "selected_skill_id" not in st.session_state:
        return default
    ns_key = f"{st.session_state.selected_skill_id}_{key}"
    return st.session_state.get(ns_key, default)

def set_skill_state(key, value):
    """Sets a namespaced session state key for the current skill."""
    if "selected_skill_id" not in st.session_state:
        return
    ns_key = f"{st.session_state.selected_skill_id}_{key}"
    st.session_state[ns_key] = value

# Render Recent Skills
recent_ids = load_recent_skills()
valid_recent_skills = [s for id_ in recent_ids for s in skills if s["id"] == id_]

if valid_recent_skills:
    st.sidebar.markdown("### Recent Used:")
    for rs in valid_recent_skills:
        if st.sidebar.button(rs["name"], use_container_width=True, key=f"recent_{rs['id']}"):
            st.session_state.selected_skill_id = rs["id"]
            st.query_params["skill"] = rs["id"] # NEW: Sync on update
            st.rerun()
    st.sidebar.markdown("---")

# Skill selection
# NEW: Check query params for skill persistence
query_params = st.query_params
if "skill" in query_params:
    p_id = query_params["skill"]
    # Check against FULL skills list, not filtered display_skills
    if any(s["id"] == p_id for s in skills):
        st.session_state.selected_skill_id = p_id
    else:
        # Fallback if invalid ID
        default_id = None
        recents = load_recent_skills()
        if recents and any(s["id"] == recents[0] for s in display_skills):
            default_id = recents[0]
        if not default_id:
            default_id = next((s["id"] for s in display_skills if s["basename"] == "AI-LLM-Text2Speech"), 
                              display_skills[0]["id"] if display_skills else None)
        st.session_state.selected_skill_id = default_id
else:
    # Default selection logic: prefer last used
    default_id = None
    recents = load_recent_skills()
    if recents:
        # Verify the requested recent skill actually still exists in loaded skills
        if any(s["id"] == recents[0] for s in display_skills):
            default_id = recents[0]
            
    # Fallback if no valid recent skill was found
    if not default_id:
        default_id = next((s["id"] for s in display_skills if s["basename"] == "AI-LLM-Text2Speech"), 
                          display_skills[0]["id"] if display_skills else None)
    st.session_state.selected_skill_id = default_id

# Sync query params
if st.session_state.get("selected_skill_id"):
    st.query_params["skill"] = st.session_state.selected_skill_id

selected_skill_id = st.session_state.get("selected_skill_id")
selected_skill = next((s for s in skills if s["id"] == selected_skill_id), None)

if selected_skill_id:
    save_recent_skill(selected_skill_id)

# Group skills by category for display
categories = sorted(list(set(s["category"] for s in display_skills)))

for cat in categories:
    cat_skills = [s for s in display_skills if s["category"] == cat]
    if not cat_skills:
        continue
        
    with st.sidebar.expander(f"📁 {cat}", expanded=bool(selected_skill and selected_skill.get("category") == cat)):  # type: ignore[union-attr]
        for s in cat_skills:
            # Highlight selected skill
            is_selected = st.session_state.selected_skill_id == s["id"]
            btn_label = f"🚀 {s['name']}" if is_selected else s["name"]
            if st.button(btn_label, key=f"select_{s['id']}", use_container_width=True):
                st.session_state.selected_skill_id = s["id"]
                st.query_params["skill"] = s["id"] # NEW: Sync on update
                st.rerun()

if not selected_skill:
    st.error("Failed to load the selected skill.")
    st.stop()


if selected_skill is None:
    st.stop()
assert selected_skill is not None

st.title(selected_skill["name"], anchor=False)
if selected_skill.get("display_title") and selected_skill["display_title"] != selected_skill["name"]:
    st.markdown(f"### *{selected_skill['display_title']}*")
st.info(selected_skill["desc"])

if not selected_skill["script"]:
    st.warning("No executable python script found in the 'scripts' folder for this skill.")
    st.stop()
    
st.markdown("---")

is_audio_skill = selected_skill["basename"] in ["AI-LLM-Speech2Text", "AI-LLM-KIE-ElevenLabs-Speech2Text"]
is_tts_skill = selected_skill["basename"] in ["AI-LLM-Text2Speech", "AI-LLM-KIE-ElevenLabs-Text2Speech"]
is_image_skill = selected_skill["basename"] == "AI-LLM-ImageGenerate"
is_embed_skill = selected_skill["basename"] == "AI-LLM-EmbedText"
is_rag_skill = selected_skill["basename"] == "AI-LLM-RAGQuery"
is_translate_skill = selected_skill["basename"] == "AI-LLM-TranslateText"

if is_audio_skill:
    st.subheader("Upload Audio Files", anchor=False)
    uploader_label = "Upload Audio Files"
    accepted_types = [
        "mp3", "wav", "m4a", "aac", "ogg", "flac", "webm",
        "aiff", "aif", "wma", "oga", "opus", "3gp",
        "mp4", "mov", "avi", "mkv"
    ]
elif is_tts_skill:
    st.subheader("Upload Text Files for Narration", anchor=False)
    uploader_label = "Upload Text Files"
    st.caption("ElevenLabs cleanly auto-extracts text from Plain Text, Markdown, RTF, DOC, and DOCX files for narration.")
    accepted_types = [
        "txt", "md", "rtf", "doc", "docx", "csv", "json", "py", "sh", "yaml", "yml", "ini"
    ]
else:
    st.subheader("Upload Document Files", anchor=False)
    uploader_label = "Upload Document Files"
    accepted_types = [
        "txt", "md", "docx", "doc", "csv", "json", "rtf", "py", "sh", "yaml", "yml"
    ]

# --- Duplicate Checking Logic ---
def check_new_uploads_for_duplicates(file_list):
    """
    Checks incoming files against processed files.
    Triggers an error if duplicates exist and RETURNS a filtered list of only NEW files.
    """
    import collections
    if not file_list:
        set_skill_state("prev_file_counts_dict", collections.Counter())
        return file_list
        
    processed_raw = get_skill_state("processed_files", set())
    processed: set[str] = processed_raw if isinstance(processed_raw, set) else set()
    
    # Count ALL files currently in the widget
    current_files = [f.name + str(f.size) for f in file_list]
    curr_counts: dict[str, int] = dict(collections.Counter(current_files))
    
    # Prime state on cold start
    ns_key = f"{st.session_state.selected_skill_id}_prev_file_counts_dict"
    if ns_key not in st.session_state:
        set_skill_state("prev_file_counts_dict", curr_counts)
        return file_list
        
    prev_counts_raw = get_skill_state("prev_file_counts_dict", {})
    prev_counts: dict[str, int] = dict(prev_counts_raw) if isinstance(prev_counts_raw, dict) else {}  # type: ignore[arg-type]
    
    error_triggered = False
    clean_list = []
    
    for f in file_list:
        file_id = f.name + str(f.size)
        # If this exact file ID is in our totally processed set, it's a duplicate
        if file_id in processed: # type: ignore
            # We also check if the user *just* added it (count increased), which triggers the visual error
            # If they just hit refresh and the count is the same, we silently remove it without screaming
            if curr_counts.get(file_id, 0) > prev_counts.get(file_id, 0): # type: ignore
                error_triggered = True
        else:
            # Not processed yet, keep it!
            clean_list.append(f)
            
    if error_triggered:
        trigger_duplicate_error()
        # We simply drop the file from the processing queue, but don't stop the script.
        # This prevents locking the UI out of processing newly dragged valid files.
    # Update tracking state with what the UI actually holds right now
    set_skill_state("prev_file_counts_dict", curr_counts)
    
    return clean_list

# File uploader OUTSIDE the form so uploads trigger immediately
skill_args: dict[str, Any] = {}

# --- Specialized Skill Inputs (Part 1: Above Uploader) ---
if selected_skill and selected_skill.get("basename") in ["AI-LLM-Speech2Text", "AI-LLM-KIE-ElevenLabs-Speech2Text", "AI-LLM-Text2Speech", "AI-LLM-KIE-ElevenLabs-Text2Speech"]:
    def copy_folder_to_sheet():
        st.session_state["google_sheet_input"] = st.session_state.get("drive_folder_input", "")

    col1, col_btn, col2 = st.columns([3, 1, 3])
    with col1:
        skill_args["drive_folder"] = st.text_input(
            "Google Drive Folder (Optional):", 
            placeholder="e.g. AI-Audio/Podcasts",
            key="drive_folder_input"
        )
    with col_btn:
        st.write("") # Spacer
        st.button(
            "Copy ➜", 
            on_click=copy_folder_to_sheet, 
            help="Copy Folder Name to Sheet Name",
            use_container_width=True
        )
        
        # Streamlit doesn't support custom button colors natively without 'type'.
        # We target the button specifically within this column to make it yellow.
        st.markdown(
            """
            <style>
            div[data-testid="column"]:nth-of-type(2) button {
                background-color: #ffd700;
                color: #111;
                font-weight: 700;
                border: none;
                transition: transform 0.2s;
            }
            div[data-testid="column"]:nth-of-type(2) button:hover {
                background-color: #ffe44d;
                color: #000;
                border: none;
                transform: scale(1.02);
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    with col2:
        skill_args["google_sheet"] = st.text_input(
            "Google Sheet Name (Optional):", 
            placeholder="e.g. Transcription Database",
            key="google_sheet_input"
        )
    
    default_email = st.session_state.get("GCP_USER_EMAIL", os.environ.get("GCP_USER_EMAIL", ""))
    skill_args["share_with"] = st.text_input("User Email for Auto-Sharing (Optional):", 
                                            value=default_email,
                                            type="password",
                                            placeholder="e.g. user@gmail.com")
    # Show direct-link badges ONLY after a successful upload has stored real IDs
    _has_folder_id = bool(st.session_state.get("_google_folder_id"))
    _has_sheet_id = bool(st.session_state.get("_google_sheet_id"))
    if _has_folder_id or _has_sheet_id:
        badge_html = '<style>@keyframes badgeFadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}</style>'
        badge_html += '<div style="display:flex;gap:10px;margin:8px 0 4px 0;animation:badgeFadeIn 1s ease-out;">'
        if _has_folder_id:
            drive_url = f"https://drive.google.com/drive/folders/{st.session_state['_google_folder_id']}"
            badge_html += f'<a href="{drive_url}" target="_blank" style="display:inline-flex;align-items:center;gap:6px;background:#1a73e8;color:#fff;padding:5px 14px;border-radius:20px;font-size:13px;font-weight:600;text-decoration:none;font-family:sans-serif;">📁 Google Drive</a>'
        if _has_sheet_id:
            sheet_url = f"https://docs.google.com/spreadsheets/d/{st.session_state['_google_sheet_id']}"
            badge_html += f'<a href="{sheet_url}" target="_blank" style="display:inline-flex;align-items:center;gap:6px;background:#0f9d58;color:#fff;padding:5px 14px;border-radius:20px;font-size:13px;font-weight:600;text-decoration:none;font-family:sans-serif;">📊 Google Sheet</a>'
        badge_html += '</div>'
        st.markdown(badge_html, unsafe_allow_html=True)
if selected_skill and selected_skill.get("basename") in ["Data-GoogleSheet", "Data-CustomGoogleSheet"]:
    uploaded_files = []
    # Optionally display a nice instruction block instead of the uploader
    st.info("📊 **Google Sheet Generator**\nConfigure your desired spreadsheet below.")
else:
    # Restrict to CSV only if the CSV-to-Sheet skill is selected
    allowed_types = ["csv"] if selected_skill and selected_skill.get("basename") == "Data-CSV2GoogleSheet" else accepted_types
    
    uploaded_files = st.file_uploader(
        uploader_label,
        accept_multiple_files=True,
        label_visibility="collapsed",
        type=allowed_types
    )

# --- PDF Restriction Safeguard ---
if uploaded_files:
    pdf_files = [f for f in uploaded_files if f.name.lower().endswith(".pdf")]
    if pdf_files:
        st.warning("⚠️ **PDF files are not allowed for upload.** These files have been removed from your selection.")
        uploaded_files = [f for f in uploaded_files if not f.name.lower().endswith(".pdf")]

# Keybind ENTER to the Browse files button
st.components.v1.html(
    """
    <script>
    const doc = window.parent.document;
    if (!doc._enterKeyBound) {
        doc._enterKeyBound = true;
        doc.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                // Don't trigger Browse if a result is being displayed or a button has focus
                const resultHeader = Array.from(doc.querySelectorAll('h2')).find(h => h.innerText.includes('PROCESSED RESULT'));
                if (resultHeader || doc.querySelector('button.kb-focus')) return;
                // Try multiple selectors to find the Browse button
                const browseBtn = doc.querySelector('[data-testid="stFileUploaderDropzone"] button')
                    || doc.querySelector('[data-testid="baseButton-secondary"]')
                    || doc.querySelector('section[data-testid="stFileUploader"] button');
                if (browseBtn) {
                    browseBtn.click();
                    e.preventDefault();
                }
            }
        });
    }
    </script>
    """,
    height=0
)
if uploaded_files and not is_audio_skill and not is_tts_skill:
    # Server-side filter: remove any .pdf files that slipped through (e.g. from prior session)
    uploaded_files = [f for f in uploaded_files if not f.name.lower().endswith('.pdf')]

# ALWAYS check for duplicates to synchronize state when the user clears the widget
uploaded_files = check_new_uploads_for_duplicates(uploaded_files if uploaded_files else [])
        
if uploaded_files:
    file_names = ", ".join([f.name for f in uploaded_files])
    st.success(f"📎 {len(uploaded_files)} file(s) uploaded: **{file_names}**")

# Detect if a NEW file was just uploaded (auto-run trigger)
# Auto-run for ALL files over riding the previous logic
current_upload_id = None
if uploaded_files:
    current_upload_id = "|".join(sorted(f.name + str(f.size) for f in uploaded_files))

auto_run = False
if current_upload_id and current_upload_id != get_skill_state("prev_upload_id"):
    set_skill_state("prev_upload_id", current_upload_id)
    
    # Filter out files that have already been processed in this session
    processed = get_skill_state("processed_files", set())
    new_files = [f for f in uploaded_files if (f.name + str(f.size)) not in processed]

    if new_files:
        auto_run = True

manual_run_clicked = False

# --- URL Input for Specific Skills ---
url_input = ""
html_capture = False
if url_input:
    st.info(f"Targeting URL: `{url_input}`")

# --- Specialized Skill Inputs (Part 2: Below Uploader) ---
if selected_skill and selected_skill.get("basename") == "AI-LLM-ImageGenerate":
    skill_args["prompt"] = st.text_area("Image Prompt:", placeholder="A futuristic city with neon lights...", height=100)
    col1, col2 = st.columns(2)
    with col1:
        skill_args["count"] = st.number_input("Number of Images:", min_value=1, max_value=4, value=1)
    with col2:
        skill_args["provider"] = st.selectbox("Provider:", ["gemini", "openai"])
elif selected_skill and selected_skill.get("basename") == "AI-LLM-EmbedText":
    mode = st.radio("Mode:", ["Single Text", "Compare Two Texts"], horizontal=True)
    if mode == "Single Text":
        skill_args["text"] = st.text_area("Text to Embed:", height=150)
    else:
        skill_args["compare"] = [
            st.text_input("Text A:"),
            st.text_input("Text B:")
        ]
elif selected_skill and selected_skill.get("basename") == "AI-LLM-RAGQuery":
    skill_args["query"] = st.text_input("Your Question:", placeholder="What does this document say about...?")
    skill_args["index"] = st.checkbox("Re-index Documents", value=True)
elif selected_skill and selected_skill.get("basename") == "AI-LLM-TranslateText":
    skill_args["to"] = st.text_input("Target Language:", value="Spanish")
    # If no file, show text area
    if not uploaded_files:
        skill_args["text"] = st.text_area("Text to Translate:", height=150)
elif selected_skill and selected_skill.get("basename") in ["Data-GoogleSheet", "Data-CustomGoogleSheet"]:
    # Proactive check for credentials.json
    creds_path = os.path.join(str(selected_skill["dir"]), "credentials.json")
    if not os.path.exists(creds_path):
        pass
        
    st.markdown('<div class="google-sheet-input-wrapper">', unsafe_allow_html=True)
    skill_args["title"] = st.text_input("Google Sheet Title:", placeholder="e.g. Q3 Sales Tracking")
    skill_args["fields"] = st.text_input("Column Headers (comma separated):", placeholder="e.g. First Name, Last Name, Email, Phone")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        enter_clicked = st.button("✨ GENERATE GOOGLE SHEET", use_container_width=True, type="primary")
        if enter_clicked:
            skill_args["_force_run"] = "True" # type: ignore
            
        # JS to Bind Return key (Enter) to the button specifically for these inputs
        st.markdown(
            """
            <script>
            {
                const doc = window.parent.document;
                const bindEnter = () => {
                    const wrapper = doc.querySelector('.google-sheet-input-wrapper');
                    if (wrapper) {
                        const inputs = wrapper.querySelectorAll('input');
                        inputs.forEach(input => {
                            if (!input._gsBound) {
                                input._gsBound = true;
                                input.addEventListener('keydown', function(ev) {
                                    if (ev.key === 'Enter') {
                                        ev.preventDefault();
                                        const buttons = Array.from(doc.querySelectorAll('button'));
                                        const genBtn = buttons.find(b => b.innerText.includes('GENERATE GOOGLE SHEET'));
                                        if (genBtn) genBtn.click();
                                    }
                                });
                            }
                        });
                    }
                };
                
                // Try binding immediately and also a few times after UI refreshes
                bindEnter();
                setTimeout(bindEnter, 500);
                setTimeout(bindEnter, 1000);
            }
            </script>
            """,
            unsafe_allow_html=True
        )

# --- Manual Text Input Fallback ---
manual_text = ""
# Check for any values in skill_args EXCEPT drive_folder
has_other_skill_args = any(v for k, v in skill_args.items() if k != "drive_folder")
if not uploaded_files and not url_input and not has_other_skill_args:
    if selected_skill["basename"] not in [
        "AI-LLM-ImageGenerate", 
        "AI-LLM-EmbedText", 
        "AI-LLM-RAGQuery", 
        "AI-LLM-TranslateText",
        "AI-LLM-Speech2Text",
        "AI-LLM-KIE-ElevenLabs-Speech2Text",
        "Data-GoogleSheet",
        "Data-CustomGoogleSheet",
        "Data-CSV2GoogleSheet"
    ]:
        if is_tts_skill:
            with st.form("manual_tts_input_form", clear_on_submit=True):
                st.markdown('<div class="tts-manual-input-wrapper">', unsafe_allow_html=True)
                manual_text = st.text_area("Manual Text Input (Optional):", placeholder="Paste text here to process instead of uploading a file...", height=200)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # JS to Bind Enter key (without Shift) to the form submission
                st.markdown("""
                    <script>
                    const doc = window.parent.document;
                    const wrapper = doc.querySelector('.tts-manual-input-wrapper');
                    if (wrapper) {
                        const textarea = wrapper.querySelector('textarea');
                        if (textarea) {
                            textarea.addEventListener('keydown', function(e) {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    const submitBtn = wrapper.closest('form').querySelector('button[kind="formSubmit"]');
                                    if (submitBtn) submitBtn.click();
                                }
                            });
                        }
                    }
                    </script>
                """, unsafe_allow_html=True)
                
                st.markdown('<div class="tts-enter-marker"></div>', unsafe_allow_html=True)
                enter_clicked = st.form_submit_button("ENTER", use_container_width=False)
        else:
            manual_text = st.text_area("Manual Text Input (Optional):", placeholder="Paste text here to process instead of uploading a file...", height=200)
            enter_clicked = False
    else:
        enter_clicked = False

# Handle Execution
has_special_input = False
if selected_skill and selected_skill.get("basename") == "AI-LLM-ImageGenerate" and skill_args.get("prompt"):
    has_special_input = True
elif selected_skill and selected_skill.get("basename") == "AI-LLM-EmbedText" and (skill_args.get("text") or (skill_args.get("compare") and all(skill_args["compare"]))):
    has_special_input = True
elif selected_skill and selected_skill.get("basename") == "AI-LLM-RAGQuery" and skill_args.get("query"):
    has_special_input = True
elif selected_skill and selected_skill.get("basename") == "AI-LLM-TranslateText" and (skill_args.get("to") and (uploaded_files or skill_args.get("text"))):
    has_special_input = True
elif selected_skill and selected_skill.get("basename") in ["Data-GoogleSheet", "Data-CustomGoogleSheet"] and skill_args.get("title") and skill_args.get("fields") and skill_args.get("_force_run") == "True":
    has_special_input = True

should_run = auto_run or manual_run_clicked or (url_input != "") or has_special_input or (manual_text != "" and enter_clicked) or (not is_tts_skill and manual_text != "")

if should_run:
    args_input = ""
    
    # Construct args from specialized inputs
    if selected_skill and selected_skill.get("basename") == "AI-LLM-ImageGenerate":
        args_input = f"--prompt {shlex.quote(str(skill_args['prompt']))} --count {skill_args['count']} --provider {str(skill_args['provider'])}"
    elif selected_skill and selected_skill.get("basename") == "AI-LLM-EmbedText":
        if skill_args.get("text"):
            args_input = f"--text {shlex.quote(str(skill_args['text']))}"
        elif skill_args.get("compare"):
            args_input = f"--compare {shlex.quote(str(skill_args['compare'][0]))} {shlex.quote(str(skill_args['compare'][1]))}"
    elif selected_skill and selected_skill.get("basename") == "AI-LLM-RAGQuery":
        args_input = f"--query {shlex.quote(str(skill_args['query']))}"
        if skill_args.get("index"):
            args_input += " --index"
        if uploaded_files:
            # We'll handle files below
            pass
    elif selected_skill and selected_skill.get("basename") == "AI-LLM-TranslateText":
        args_input = f"--to {shlex.quote(str(skill_args['to']))}"
        if skill_args.get("text"):
            # We'll save this to a temp file below
            pass
    elif selected_skill and selected_skill.get("basename") in ["Data-GoogleSheet", "Data-CustomGoogleSheet"]:
        fields = [shlex.quote(f.strip()) for f in str(skill_args.get("fields", "")).split(",") if f.strip()]
        fields_str = " ".join(fields)
        args_input = f"--title {shlex.quote(str(skill_args.get('title', '')))} --fields {fields_str}"
    elif selected_skill and selected_skill.get("basename") == "Data-CSV2GoogleSheet":
        args_input = "--file {FILE_1}"
    
    if url_input:
        args_input = f"--url \"{url_input}\""
        if html_capture:
            args_input += " --capture"
    
    # Handle uploaded files by saving them to a temporary directory so the script can read them
    temp_dir = None
    file_paths = []
    
    if uploaded_files or manual_text or skill_args.get("text"):
        # Filter uploaded_files to only process NEW ones
        processed = get_skill_state("processed_files", set())
        
        # Combine uploaded files and manual text
        files_to_process_objs = [uf for uf in uploaded_files if (uf.name + str(uf.size)) not in processed]
        
        if not files_to_process_objs and not url_input and not manual_text and not skill_args.get("text") and not has_special_input:
            should_run = False # Cancel execution if no new files, no URL, no manual text
        
        else:
            temp_dir = tempfile.mkdtemp()
            
            # Handle Manual Text Input
            if (manual_text or skill_args.get("text")) and not files_to_process_objs:
                text_content = manual_text or skill_args.get("text")
                
                # Use a counter to ensure unique filenames for manual entries
                if "manual_tts_counter" not in st.session_state:
                    st.session_state["manual_tts_counter"] = 1
                else:
                    st.session_state["manual_tts_counter"] += 1
                
                counter = st.session_state["manual_tts_counter"]
                text_file_path = os.path.join(temp_dir, f"input_text_{counter}.txt")
                
                with open(text_file_path, "w", encoding="utf-8") as f:
                    f.write(str(text_content))
                file_paths.append(text_file_path)
                
                # For RAGQuery, --docs is required
                if selected_skill_id == "AI-LLM-RAGQuery":
                    args_input += f" --docs {text_file_path}"
                # For Translate/General, if args empty, use as --input
                elif not args_input.strip() or "--to" in args_input:
                     args_input += f" --input {text_file_path}"
            
            # Handle Uploaded Files
            elif files_to_process_objs:
                if not args_input.strip() or ("--to" in args_input and "--input" not in args_input):
                    # Only auto-inject if it's not already specialized except for Translate which needs --input
                    if selected_skill_id == "AI-LLM-RAGQuery":
                         args_input += " --docs {FILE_1}"
                    else:
                         args_input += " --input {FILE_1}"
                
                # Preserve the base args so we don't lose the {FILE_1} placeholder when looping
                base_args_input = str(args_input)
                
                for i, uf in enumerate(files_to_process_objs):
                    file_path = os.path.join(temp_dir, uf.name)
                    with open(file_path, "wb") as f:
                        f.write(uf.getbuffer())
                    file_paths.append(file_path)
                    
                    processed.add(uf.name + str(uf.size)) # type: ignore
                    set_skill_state("processed_files", processed)
                    
                    # Replace {FILE_X} placeholder in the args for THIS SPECIFIC file (for single-run fallback)
                    # We only do this for the *first* file because single execution assumes args_input is fully resolved.
                    # The batch loop relies on base_args_input later.
                    if i == 0:
                        args_input = base_args_input.replace("{FILE_1}", file_path)
    
    # Parse the arguments string into a list safely avoiding simple split() issues with quotes
    try:
        parsed_args = shlex.split(args_input)
    except Exception as e:
        st.error(f"Error parsing arguments: {e}")
        st.stop()
        
    python_cmd: str = str(get_python_cmd())
    script_path: str = str(selected_skill["script"])
    command: list[str] = [python_cmd, script_path] + parsed_args
    
    cwd: str = str(selected_skill["dir"])
    
    # Use manual status instead of with st.spinner so we can clear it before st.stop()
    output_expander = st.expander("📄 Output", expanded=False)
    
    # Reset the playlist/gallery at the start of a fresh processing batch
    # This addresses the "Viewing 1 of 4" issue and prevents result leakage.
    set_skill_state("last_processed_files", [])
    set_skill_state("file_index", 0)
    
    proc_overlay = trigger_processing_overlay()
    with output_expander:
        main_spinner = st.empty()
        main_spinner.info("⏳ PROCESSING...")
        try:
            # We stream the output to a preformatted block
            # For simplicity in Streamlit, we capture combined output
            # Inject API keys from session state (auto-fetched from GCP at login)
            run_env = os.environ.copy()
            if st.session_state.get("GEMINI_API_KEY"):
                run_env["GEMINI_API_KEY"] = st.session_state["GEMINI_API_KEY"]
            if st.session_state.get("ELEVENLABS_API_KEY"):
                run_env["ELEVENLABS_API_KEY"] = st.session_state["ELEVENLABS_API_KEY"]
            if st.session_state.get("KIE_API_KEY"):
                run_env["KIE_API_KEY"] = st.session_state["KIE_API_KEY"]
            
            if is_audio_skill:
                new_files = process_uploaded_files(file_paths, selected_skill, run_env, 
                                                   base_args_input=locals().get("base_args_input", args_input),
                                                   drive_folder=skill_args.get("drive_folder", ""), 
                                                   google_sheet=skill_args.get("google_sheet", ""),
                                                   share_with=skill_args.get("share_with", ""),
                                                   proc_overlay=proc_overlay, main_spinner=main_spinner)
                existing = get_skill_state("last_processed_files", [])
                existing.extend(new_files)
                set_skill_state("last_processed_files", existing)
                if new_files:
                    set_skill_state("file_index", max(0, len(existing) - len(new_files)))
                    set_skill_state("last_output", new_files[0]["transcript"])
                    set_skill_state("auto_open_result", True)
                    st.success(f"✅ Successfully processed {len(file_paths)} file(s)")
            elif is_tts_skill and file_paths:
                new_files = process_tts_files(file_paths, selected_skill, run_env, 
                                              base_args_input=locals().get("base_args_input", args_input),
                                              drive_folder=skill_args.get("drive_folder", ""), 
                                              google_sheet=skill_args.get("google_sheet", ""),
                                              share_with=skill_args.get("share_with", ""),
                                              proc_overlay=proc_overlay, main_spinner=main_spinner)
                existing = get_skill_state("last_processed_files", [])
                existing.extend(new_files)
                set_skill_state("last_processed_files", existing)
                if new_files:
                    set_skill_state("file_index", max(0, len(existing) - len(new_files)))
                    set_skill_state("last_output", new_files[0]["transcript"])
                    set_skill_state("auto_open_result", True)
                    st.success(f"✅ Successfully converted {len(file_paths)} document(s) to audio")
            else:
                # Standard execution PATH
                all_execution_results = []
                
                # Check if we should loop (multiple files and {FILE_1} placeholder exists in base_args)
                # This ensures skills like Convtr-PlainTxt2PDF process ALL uploads.
                # If base_args_input wasn't created (e.g., text area input), it falls back to single execution.
                # --- NEW: Streaming Execution Engine ---
                def run_and_stream(cmd, cwd, env):
                    """Helper to run a command and stream its output to the UI."""
                    process = subprocess.Popen(
                        cmd, cwd=cwd, env=env,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, bufsize=1, universal_newlines=True
                    )
                    
                    full_output: list[str] = []
                    output_placeholder = st.empty()
                    
                    # Read output line by line as it arrives
                    stdout_pipe = process.stdout
                    if stdout_pipe:
                        for line in iter(stdout_pipe.readline, ""):
                            full_output.append(str(line))
                            # Update the UI with the latest 20 lines to keep it snappy
                            output_placeholder.code("".join(full_output[-20:])) # type: ignore
                    
                    returncode = process.wait()
                    final_text = "".join(full_output)
                    
                    # Create a compatibility object for the existing result loop
                    class ProcessResult:
                        def __init__(self, stdout, stderr, returncode):
                            self.stdout = stdout
                            self.stderr = stderr
                            self.returncode = returncode
                            
                    return ProcessResult(final_text, final_text if returncode != 0 else "", returncode)

                base_loop_args = locals().get('base_args_input', args_input)
                should_loop = len(file_paths) > 1 and "{FILE_1}" in str(base_loop_args)
                
                if should_loop:
                    for i, fp in enumerate(file_paths):
                        local_args = str(base_loop_args).replace("{FILE_1}", str(fp))
                        try:
                            local_parsed = shlex.split(local_args)
                            local_cmd = [python_cmd, script_path] + local_parsed
                            main_spinner.info(f"⏳ PROCESSING file {i+1}/{len(file_paths)}: `{os.path.basename(fp)}`...")
                            res = run_and_stream(local_cmd, cwd, run_env)
                            all_execution_results.append((fp, res))
                        except Exception as e:
                            st.error(f"Error processing {fp}: {e}")
                else:
                    # Single execution (Google Sheets, Image Gen, etc.)
                    res = run_and_stream(command, cwd, run_env)
                    all_execution_results.append((file_paths[0] if file_paths else None, res))

                # Now aggregate all results into the playlist
                last_processed_files = []
                
                for fp, result in all_execution_results:
                    if result.returncode == 0:
                        output_text = result.stdout.strip()
                        
                        # Detect generated files for this specific execution
                        res_bytes = None
                        res_name = None
                        saved_paths = []
                        for line in output_text.splitlines():
                            if "Saved:" in line:
                                path_str = str(line.split("Saved:")[1].strip())
                                full_path = path_str if os.path.isabs(path_str) else os.path.join(str(cwd), path_str)
                                if os.path.exists(full_path):
                                    saved_paths.append(full_path)
                                    
                        if saved_paths:
                            # Capture the first saved file as the primary result for this entry
                            res_name = os.path.basename(saved_paths[0])
                            with open(saved_paths[0], "rb") as f:
                                res_bytes = f.read()

                        # Capture preview for the input file (if it exists)
                        content_preview = ""
                        if fp:
                            ext = os.path.splitext(fp)[1].lower()
                            if ext in [".txt", ".rtf", ".md", ".docx", ".doc", ".rtfd"] or (ext != ".pdf" and os.path.getsize(fp) < 1024 * 1024):
                                content_preview = read_text_file_preview(fp)

                        # Clean output (filter success messages)
                        ignore_prefixes = ("Transcribing:", "Saved:", "Fetching:", "Capturing:", "Capturing high-fidelity", "Usage:")
                        lines = [l for l in output_text.splitlines() if not l.startswith(ignore_prefixes)]
                        clean_output = "\n".join(lines).strip()
                        
                        # Extract usage stats
                        usage_line = next((l for l in output_text.splitlines() if l.startswith("Usage:")), None)
                        usage_details = ""
                        if usage_line:
                            usage_details = f"\n\n**Statistics:** {usage_line.split(':', 1)[-1].strip()}"

                        last_processed_files.append({
                            "original_name": os.path.basename(fp) if fp else (res_name or "Result"),
                            "name": os.path.basename(fp) if fp else (res_name or "Result"),
                            "bytes": open(fp, "rb").read() if fp and os.path.exists(fp) else (res_bytes or b""),
                            "transcript": (clean_output + usage_details) if clean_output or usage_details else f"✅ Generated: {res_name}",
                            "content_preview": content_preview,
                            "result_bytes": res_bytes,
                            "result_name": res_name
                        })
                    else:
                        # Handle errors (Quota, etc.)
                        if "__ANTIGRAVITY_API_QUOTA_EXCEEDED__" in result.stderr:
                            main_spinner.empty()
                            if proc_overlay:
                                proc_overlay.empty()
                            import re
                            quota_msg = ""
                            
                            if "kie" in str(selected_skill["basename"]).lower():
                                match = re.search(r"Kie\.ai Error: (.*?)(?:\n|$)", result.stderr)
                                if match:
                                    quota_msg = f"\n\n**Details:** {match.group(1).strip()}"
                                st.warning(f"⚠️ **DENIED!** You have reached the maximum usage allowed by your **Kie.ai** balance. Please top up your Kie.ai account to continue.{quota_msg}")
                            else:
                                match = re.search(r"['\"]message['\"]:\s*['\"](.*?)['\"]", result.stderr)
                                if match:
                                    quota_msg = f"\n\n**Usage stats:** {match.group(1)}"
                                st.warning(f"⚠️ **DENIED!** You have reached the maximum usage allowed by your **ElevenLabs** active subscription/plan. Please upgrade your plan or wait for the quota to reset.{quota_msg}")
                            st.stop()
                        else:
                            st.error("Execution Error")
                            st.code(result.stderr)
                            if result.stdout:
                                st.code(result.stdout)

                # Final integration
                set_skill_state("last_processed_files", last_processed_files)
                if last_processed_files:
                    set_skill_state("file_index", 0)
                    set_skill_state("last_output", last_processed_files[0]["transcript"])
                    set_skill_state("auto_open_result", True)
                    st.success(f"✅ Successfully processed {len(all_execution_results)} item(s)")
                    
        except Exception as e:
            st.error(f"❌ Error executing skill: {str(e)}")
        finally:
            main_spinner.empty()
            trigger_complete_overlay(proc_overlay)
            time.sleep(2)

# -----------------------------------------------------------------------------
# 5. Result Display (Inline instead of Popup)
# -----------------------------------------------------------------------------
def show_result_popup(text: str):
    load_css() # Ensure styles are applied
    processed_files: list = get_skill_state("last_processed_files", []) # type: ignore
    idx: int = int(get_skill_state("file_index", 0))
    selected_skill_id_raw = st.session_state.get("selected_skill_id", "")
    is_google_sheet = any(name in str(selected_skill_id_raw) for name in ["Data-GoogleSheet", "Data-CustomGoogleSheet", "Data-CSV2GoogleSheet"])
    is_media = False
    is_image = False
    
    # 0. Header & Type Info
    if is_google_sheet:
        st.markdown("<h1 class='processed-header'><span style='filter:none;'>📄</span> GOOGLE SHEET GENERATED</h1>", unsafe_allow_html=True)
    else:
        st.markdown("<h1 class='processed-header'><span style='filter:none;'>📄</span> PROCESSED RESULT</h1>", unsafe_allow_html=True)
    
    # Show Google Drive / Sheets badges if IDs were captured during processing
    _popup_has_folder = bool(st.session_state.get("_google_folder_id"))
    _popup_has_sheet = bool(st.session_state.get("_google_sheet_id"))
    if _popup_has_folder or _popup_has_sheet:
        _badge_html = '<style>@keyframes badgeFadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}</style>'
        _badge_html += '<div style="display:flex;gap:10px;margin:8px 0 12px 0;animation:badgeFadeIn 1s ease-out;">'
        if _popup_has_folder:
            _drive_url = f"https://drive.google.com/drive/folders/{st.session_state['_google_folder_id']}"
            _badge_html += f'<a href="{_drive_url}" target="_blank" style="display:inline-flex;align-items:center;gap:6px;background:#1a73e8;color:#fff;padding:5px 14px;border-radius:20px;font-size:13px;font-weight:600;text-decoration:none;font-family:sans-serif;">📁 Google Drive</a>'
        if _popup_has_sheet:
            _sheet_url = f"https://docs.google.com/spreadsheets/d/{st.session_state['_google_sheet_id']}"
            _badge_html += f'<a href="{_sheet_url}" target="_blank" style="display:inline-flex;align-items:center;gap:6px;background:#0f9d58;color:#fff;padding:5px 14px;border-radius:20px;font-size:13px;font-weight:600;text-decoration:none;font-family:sans-serif;">📊 Google Sheet</a>'
        _badge_html += '</div>'
        st.markdown(_badge_html, unsafe_allow_html=True)

    if processed_files:
        current_file: dict = processed_files[min(idx, len(processed_files)-1)] # type: ignore
        import mimetypes
        file_name = current_file.get("name") or "Result"
        mime_type, _ = mimetypes.guess_type(file_name)
        is_media = mime_type and (mime_type.startswith("audio/") or mime_type.startswith("video/"))
    
    # Identify which text to display (specific clip transcript or the general output)
    display_text = text
    if processed_files:
        current_idx = get_skill_state("file_index", 0)
        if current_idx < len(processed_files):
            current_file = processed_files[current_idx]
            file_transcript = current_file.get("transcript", "")
            content_preview = current_file.get("content_preview", "")
            
            # Identify if the transcript or global text are just status/success messages
            is_file_success = any(x in file_transcript for x in ["Successfully", "Generated:", "✅"]) or not file_transcript.strip()
            is_global_success = any(x in text for x in ["Successfully", "Generated:", "✅"])
            
            if not is_google_sheet:
                if content_preview.strip():
                    # If we have a preview, favor it over any success/batch messages
                    if is_file_success or is_global_success:
                        display_text = content_preview
                    else:
                        display_text = file_transcript or content_preview
                else:
                    # If no preview, only show transcripts if they aren't just success messages
                    # This prevents "✅ Generated: ..." from appearing when navigating between files
                    ft_clean = file_transcript if not any(x in file_transcript for x in ["Successfully", "Generated:", "✅"]) else ""
                    txt_clean = text if not any(x in text for x in ["Successfully", "Generated:", "✅"]) else ""
                    display_text = ft_clean or txt_clean
            else:
                # For Google Sheets, we explicitly NEED the success messages to parse URL/Title
                display_text = file_transcript or text
            
    if processed_files:
        current_file: dict = processed_files[idx] # type: ignore
        import mimetypes
        file_name = current_file.get("name") or "Result"
        mime_type, _ = mimetypes.guess_type(file_name)
        
        # Only show the audio player if it's actually an audio/video file
        is_media = mime_type and (mime_type.startswith("audio/") or mime_type.startswith("video/"))
        is_image = mime_type and mime_type.startswith("image/")


        
        if is_media:
            st.markdown(f"**Playing {idx + 1} of {len(processed_files)}**: `{current_file['name']}`") # type: ignore
            st.audio(current_file["bytes"], format=mime_type, autoplay=True, loop=True) # type: ignore
            # stats_badge_text extracted below — pass it here so it appears inline with speed controls
            _stats_for_speed = ""
            import re as _re_pre
            _stats_match = _re_pre.search(r"\*\*Statistics:\*\*\s*(.+)", display_text)
            if _stats_match:
                _stats_for_speed = _stats_match.group(1).strip()
            render_speed_controls(skill_id=selected_skill_id, stats_text=_stats_for_speed)

        elif is_image:
            st.markdown(f"**Viewing Image {idx + 1} of {len(processed_files)}**: `{current_file['name']}`") # type: ignore
            st.image(current_file["bytes"], use_container_width=True) # type: ignore
        else:
            display_name = current_file.get('original_name') # type: ignore
            if not display_name:
                # Fallback: strip .pdf from output name for document converters
                name = current_file['name'] # type: ignore
                if name.lower().endswith('.pdf'):
                    display_name = os.path.splitext(name)[0]
                else:
                    display_name = name
            # Extract stats for inline badge — API stats or native word/char count
            import re as _re_doc
            _doc_stats = ""
            _doc_stats_match = _re_doc.search(r"\*\*Statistics:\*\*\s*(.+)", display_text)
            if _doc_stats_match:
                _doc_stats = _doc_stats_match.group(1).strip()
            elif display_text.strip():
                # Native word & character count
                _word_count = len(display_text.split())
                _char_count = len(display_text)
                _doc_stats = f"{_word_count:,} words · {_char_count:,} chars"
            if _doc_stats and not is_google_sheet:
                st.markdown(f"**Viewing {idx + 1} of {len(processed_files)}**: `{display_name}`  &nbsp; <span style='background:#444;color:#ccc;padding:2px 8px;border-radius:6px;font-size:0.8em;'>{_doc_stats}</span>", unsafe_allow_html=True)
        # Show navigation buttons if there are multiple files
        if len(processed_files) > 1:
            label_type = "Clip" if is_media else "File"
            st.markdown("<div class='nav-button-container'>", unsafe_allow_html=True)
            col_prev, col_next = st.columns(2)
            with col_prev:
                st.markdown("<div class='nav-btn-marker' style='display:none;'></div>", unsafe_allow_html=True)
                if st.button(f"⏮ Previous {label_type}", key="prev_clip_btn", use_container_width=True):
                    # Prevent going below 0
                    set_skill_state("file_index", max(0, idx - 1))
                    set_skill_state("auto_open_result", True)
                    st.rerun()
            with col_next:
                st.markdown("<div class='nav-btn-marker' style='display:none;'></div>", unsafe_allow_html=True)
                if st.button(f"Next {label_type} ⏭", key="next_clip_btn", use_container_width=True):
                    set_skill_state("file_index", min(idx + 1, len(processed_files) - 1))
                    set_skill_state("auto_open_result", True)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.components.v1.html(
                """
                <script>
                const doc = window.parent.document;
                
                // Remove existing listener to avoid duplicates on reruns
                if (doc.windowKeydownListener) {
                    doc.removeEventListener('keydown', doc.windowKeydownListener);
                }
                
                // Clear any stale focus/inline styles from previous rerun
                doc.querySelectorAll('button').forEach(b => {
                    b.blur();
                    b.classList.remove('kb-focus');
                });
                
                doc.windowKeydownListener = function(e) {
                    // Don't trigger if user is typing in an input field
                    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
                    
                    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                        const allBtns = Array.from(doc.querySelectorAll('button'));
                        // Clear highlight on ALL buttons first for a clean state
                        allBtns.forEach(b => { b.classList.remove('kb-focus'); b.blur(); });

                        // Search the button's inner text case-insensitively
                        const targetStr = e.key === 'ArrowLeft' ? 'PREVIOUS' : 'NEXT';
                        const targetBtn = allBtns.find(b => {
                            const t = b.innerText || "";
                            return t.toUpperCase().includes(targetStr);
                        });
                        
                        if (targetBtn) {
                            targetBtn.focus();
                            targetBtn.classList.add('kb-focus');
                            setTimeout(() => { targetBtn.click(); }, 300);
                        }
                    } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                        // Only target download/merge buttons (with emoji icons), NOT the COPY button
                        const buttons = Array.from(doc.querySelectorAll('button')).filter(b => {
                            const text = b.innerText || "";
                            return text.includes("📥") || text.includes("📦") || text.includes("📑");
                        });
                        
                        if (buttons.length === 0) return;
                        
                        // Use the currently kb-focused button for indexing, fallback to activeElement
                        let currentIndex = buttons.indexOf(doc.querySelector('button.kb-focus'));
                        if (currentIndex === -1) currentIndex = buttons.indexOf(doc.activeElement);

                        if (e.key === 'ArrowDown') {
                            currentIndex = (currentIndex + 1) % buttons.length;
                        } else {
                            if (currentIndex <= 0) {
                                currentIndex = buttons.length - 1;
                            } else {
                                currentIndex = currentIndex - 1;
                            }
                        }
                        // Clear kb-focus and blur ALL buttons first
                        doc.querySelectorAll('button').forEach(b => { b.classList.remove('kb-focus'); b.blur(); });
                        
                        const targetBtn = buttons[currentIndex];
                        targetBtn.focus();
                        targetBtn.classList.add('kb-focus');
                        e.preventDefault();
                    } else if (e.key === 'Enter') {
                        // Click the currently kb-focused button
                        const focused = doc.querySelector('button.kb-focus');
                        if (focused) {
                            e.preventDefault();
                            e.stopImmediatePropagation();
                            const text = (focused.innerText || '').toUpperCase();
                            const link = focused.querySelector('a');
                            
                            // Top "DOWNLOAD [TYPE] NOW" button — immediate download
                            if (text.includes('DOWNLOAD') && text.includes('NOW')) {
                                if (link) {
                                    link.click();
                                } else {
                                    focused.click();
                                }
                            } else {
                                // All other buttons (ZIP, Merge) — trigger Save As dialog
                                if (link) {
                                    const origDownload = link.getAttribute('download');
                                    link.removeAttribute('download');
                                    link.click();
                                    // Restore download attribute after a tick
                                    setTimeout(() => {
                                        if (origDownload !== null) link.setAttribute('download', origDownload);
                                    }, 100);
                                } else {
                                    focused.click();
                                }
                            }
                        }
                    }
                };
                
                doc.addEventListener('keydown', doc.windowKeydownListener);
                
                // Apply specific classes to Streamlit buttons AND inject CSS into PARENT document
                if (doc.applyButtonClassesInterval) clearInterval(doc.applyButtonClassesInterval);
                doc.applyButtonClassesInterval = setInterval(() => {
                    doc.querySelectorAll('button').forEach(b => {
                        const t = (b.innerText || "").toUpperCase();
                        if (t.includes('DOWNLOAD ALL')) {
                            b.classList.add('merge-btn-cyan');
                        }
                        if (t.includes('PREVIOUS') || t.includes('NEXT')) {
                            b.classList.add('nav-btn-15px');
                            // On mouseover, clear keyboard focus class from ALL nav buttons
                            if (!b._hoverBound) {
                                b._hoverBound = true;
                                b.addEventListener('mouseenter', () => {
                                    doc.querySelectorAll('button.nav-btn-15px').forEach(nb => {
                                        nb.classList.remove('kb-focus');
                                    });
                                });
                            }
                        }
                        // Download/merge buttons — clear keyboard focus class on hover
                        if (t.includes('📥') || t.includes('📦') || t.includes('📑')) {
                            if (!b._dlHoverBound) {
                                b._dlHoverBound = true;
                                b.addEventListener('mouseenter', () => {
                                    doc.querySelectorAll('button').forEach(ob => {
                                        const ot = ob.innerText || '';
                                        if (ot.includes('📥') || ot.includes('📦') || ot.includes('📑')) {
                                            ob.classList.remove('kb-focus');
                                        }
                                    });
                                });
                            }
                        }
                    });
                }, 100);
                
                // Inject CSS into the PARENT document (not the iframe) so it actually applies
                if (!doc.getElementById('ag-custom-btn-styles')) {
                    const style = doc.createElement('style');
                    style.id = 'ag-custom-btn-styles';
                    style.textContent = `
                        /* White outline on hover only - focus-visible for keyboard only */
                        .stApp button:hover {
                            border: 2px solid #ffffff !important;
                            box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.85) !important;
                            outline: none !important;
                        }
                        .stApp button:focus {
                            outline: none !important;
                            border-color: transparent !important;
                            box-shadow: none !important;
                        }
                        /* Keyboard focus class - overrides :focus suppression */
                        .stApp button.kb-focus {
                            border: 2px solid #ffffff !important;
                            box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.85) !important;
                        }
                        /* Specific Cyan override for Merge buttons - all states */
                        .stApp button.merge-btn-cyan,
                        .stApp button.merge-btn-cyan:hover,
                        .stApp button.merge-btn-cyan:active,
                        .stApp button.merge-btn-cyan:focus {
                            background-color: #00FFFF !important;
                            color: black !important;
                            border-color: #00cccc !important;
                        }
                        .stApp button.merge-btn-cyan:hover {
                            background-color: #00e5e5 !important;
                            border: 2px solid #ffffff !important;
                            box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.85) !important;
                        }
                        .stApp button.merge-btn-cyan p,
                        .stApp button.merge-btn-cyan div,
                        .stApp button.merge-btn-cyan:hover p,
                        .stApp button.merge-btn-cyan:hover div {
                            color: black !important;
                        }
                    `;
                    doc.head.appendChild(style);
                }
                </script>
                """,
                height=0
            )

        # --- Quick Select List & Upload (Playlist) ---
        # Hide for Google Sheet skill as it's redundant (always just one "Result")
        if not is_google_sheet:
            with st.expander("ALL DOCUMENTS", expanded=False):
                if is_media:
                    st.markdown("<h3 class='centered-header'>MY CLIPS</h3>", unsafe_allow_html=True)
                else:
                    st.markdown("<h3 class='centered-header'>MY DOCUMENTS</h3>", unsafe_allow_html=True)
                
                if get_skill_state("popup_batch_success"):
                    st.markdown("<div class='success-message-popup'>✅ SUCCESSFULLY ADDED!</div>", unsafe_allow_html=True)
                    set_skill_state("popup_batch_success", False)
                
                st.markdown("<div class='quick-select-btns'>", unsafe_allow_html=True)
                for i, clip in enumerate(processed_files):
                    is_active = (i == get_skill_state("file_index", 0))
                    if is_active:
                        st.markdown(f"<div class='active-clip'>🟢 {clip['name']}</div>", unsafe_allow_html=True)
                    else:
                        with st.container():
                            st.markdown("<div class='playlist-clip-marker'></div>", unsafe_allow_html=True)
                            if st.button(f"⚪️ {clip['name']}", key=f"clip_btn_{i}", use_container_width=True):
                                set_skill_state("file_index", i)
                                set_skill_state("auto_open_result", True)
                                st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            
    # Render the transcription box BELOW the navigation buttons
    import html
    import re as _re

    # Extract and strip the Statistics line from display_text so it shows ONLY in the badge
    stats_badge_text = ""
    stats_match = _re.search(r"\*\*Statistics:\*\*\s*(.+)", display_text)
    if stats_match:
        stats_badge_text = stats_match.group(1).strip()
        display_text = _re.sub(r"\n\n\*\*Statistics:\*\*\s*.+", "", display_text).strip()
    
    # --- COPY button ABOVE preview ---
    if is_google_sheet:
        import re
        sheet_title = "Google Sheet"
        sheet_url = "#"
        
        # Strip ANSI escape codes that might be polluting the terminal stream
        clean_text = _re.sub(r'\x1b\[[0-9;]*[mG]', '', display_text)
        
        # Extract title from the script's output "Creating Google Sheet: '...'"
        title_match = re.search(r"Creating Google Sheet:\s*['\"]?(.*?)['\"]?\s*(?:\.\.\.|\n|$)", clean_text)
        if title_match:
            sheet_title = title_match.group(1).strip()
            
        # Extract the URL from the script's output
        url_match = re.search(r"https://docs\.google\.com/spreadsheets/d/[a-zA-Z0-9_-]+[^\s\"']*", clean_text)
        if url_match:
            sheet_url = url_match.group(0).strip()
            
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center; margin-top: 10px; margin-bottom: 20px;">
                <a href="{sheet_url}" target="_blank" style="
                    background-color: #1e1e1e;
                    color: #00FFCC;
                    border: 2px solid #00FFCC;
                    border-radius: 6px;
                    padding: 8px 24px;
                    font-size: 1.2rem;
                    font-family: sans-serif;
                    font-weight: bold;
                    text-align: center;
                    text-decoration: none;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                    transition: background-color 0.2s, transform 0.1s;
                " onmouseover="this.style.backgroundColor='#003322'; this.style.transform='scale(1.02)';" onmouseout="this.style.backgroundColor='#1e1e1e'; this.style.transform='scale(1)';">
                    📊 {sheet_title}
                </a>
            </div>
            """, unsafe_allow_html=True
        )
    else:
        import json
        js_escaped_text = json.dumps(display_text)
        st.components.v1.html(
            f"""
            <div style="display: flex; justify-content: center; margin-top: 5px;">
                <button id="copy-btn" style="
                    background-color: #ffe700;
                    color: #000000;
                    border: 1px solid #ffe700;
                    border-radius: 4px;
                    padding: 0px 16px;
                    height: 38px;
                    font-size: 1rem;
                    cursor: pointer;
                    font-family: sans-serif;
                    font-weight: bold;
                    transition: all 0.2s;
                    min-width: 100px;
                    text-transform: uppercase;
                ">COPY</button>
            </div>
            <script>
            const btn = document.getElementById('copy-btn');
            btn.onclick = function() {{
                navigator.clipboard.writeText({js_escaped_text}).then(() => {{
                    btn.innerText = "\u2713 COPIED!";
                    btn.style.backgroundColor = "#8cd775";
                    btn.style.borderColor = "#8cd775";
                    setTimeout(() => {{
                        btn.innerText = "COPY";
                        btn.style.backgroundColor = "#ffe700";
                        btn.style.borderColor = "#ffe700";
                    }}, 2000);
                }});
            }};
            btn.onmouseover = function() {{ this.style.backgroundColor = '#ffd600'; this.style.borderColor = '#ffd600'; }};
            btn.onmouseout = function() {{
                if (this.innerText === "COPY") {{
                    this.style.backgroundColor = '#ffe700';
                    this.style.borderColor = '#ffe700';
                }}
            }};
            </script>
            """,
            height=60,
        )

    # --- Preview box BELOW copy button ---
    if is_media or is_image:
        if display_text:
            safe_text = html.escape(display_text)
            st.markdown(
                f"<div class='transcript-box'>{safe_text.replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True
            )
    else:
        # Use the same transcript-box styling for document previews
        if display_text and not is_google_sheet:
            safe_text = html.escape(display_text)
            st.markdown(
                f"<div class='transcript-box'>{safe_text.replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True
            )
    
    # --- Dynamic Direct Download Support (Top level, synced to active file) ---
    if processed_files:
        current_item = processed_files[idx]
        res_bytes = current_item.get("result_bytes")
        res_name = current_item.get("result_name")
        
        if res_bytes and res_name:
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Use mimetypes for clean extension labeling
            import mimetypes
            dl_mime, _ = mimetypes.guess_type(res_name)
            ext_label = os.path.splitext(res_name)[1][1:].upper()
            
            # Specialized player for audio results (like TTS)
            if dl_mime and dl_mime.startswith("audio/"):
                st.audio(res_bytes, format=dl_mime, autoplay=True) # type: ignore
                render_speed_controls(skill_id=selected_skill_id)
                st.markdown("<br>", unsafe_allow_html=True)
                
            col1, col2, col3 = st.columns([2, 3, 2])
            with col2:
                st.download_button(
                    label=f"📥 DOWNLOAD {ext_label} NOW",
                    data=res_bytes,
                    file_name=res_name,
                    mime=dl_mime if dl_mime else "application/octet-stream",
                    use_container_width=True,
                    type="primary",
                    key=f"direct_download_btn_sync_{idx}" # Key must be index-specific to prevent state reuse
                ) # type: ignore
            
            # --- TOP BATCH ACTIONS (For PDF Converter) ---
            if selected_skill["basename"] == "Convtr-PlainTxt2PDF" and len(processed_files) > 1: # type: ignore
                st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
                
                # Use same column constraints as "DOWNLOAD PDF NOW" to match button size
                col_b1, col_b2, col_b3 = st.columns([2, 3, 2])
                with col_b2:
                    # 1. Top Buttons: ZIP All (Cyan overridden in JS/Tertiary base)
                    zip_bytes_clean = generate_zip_of_all_transcripts(processed_files, "PDF (.pdf)", include_sources=False)
                    if zip_bytes_clean:
                        st.download_button(label=f"📦 DOWNLOAD ALL (CLEAN)", data=zip_bytes_clean, file_name="All_Files_Clean.zip", mime="application/zip", use_container_width=True, type="tertiary", key="popup_dl_all_zip_clean_top")
                    
                    zip_bytes_sourced = generate_zip_of_all_transcripts(processed_files, "PDF (.pdf)", include_sources=True)
                    if zip_bytes_sourced:
                        st.download_button(label=f"📦 DOWNLOAD ALL (INCLUDE SOURCES)", data=zip_bytes_sourced, file_name="All_Files_Sourced.zip", mime="application/zip", use_container_width=True, type="tertiary", key="popup_dl_all_zip_sourced_top")

                    # 2. Bottom Buttons: Merge All (Orange/Tertiary)
                    merged_parts_clean = []
                    merged_parts_sourced = []
                    for f in processed_files:
                        content = f.get("content_preview") or ""
                        if not content.strip():
                            transcript = f.get("transcript", "")
                            if not any(x in transcript for x in ["Successfully", "Generated:", "✅"]):
                                content = transcript
                        if content.strip():
                            merged_parts_clean.append(content)
                            merged_parts_clean.append("\n")
                            merged_parts_sourced.append(f"Sourced from: {f['name']}") # Matches orange styling in script
                            merged_parts_sourced.append("\n\n")
                            merged_parts_sourced.append(content)
                            merged_parts_sourced.append("\n")
                    
                    merged_bytes_clean = generate_pdf_from_text("\n".join(merged_parts_clean))
                    merged_bytes_sourced = generate_pdf_from_text("\n".join(merged_parts_sourced))
                    if merged_bytes_clean:
                        st.download_button(label=f"📑 MERGE ALL (CLEAN)", data=merged_bytes_clean, file_name="Merged_Document_Clean.pdf", mime="application/pdf", use_container_width=True, type="tertiary", key="popup_merge_pdf_clean_top") # type: ignore
                    if merged_bytes_sourced:
                        st.download_button(label=f"📑 MERGE ALL (INCLUDE SOURCES)", data=merged_bytes_sourced, file_name="Merged_Document_Sourced.pdf", mime="application/pdf", use_container_width=True, type="tertiary", key="popup_merge_pdf_sourced_top") # type: ignore


    # --- Bottom Clear Buttons ---
    st.markdown("---")
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("✖ Clear Result", key="close_popup_final", use_container_width=True):
            set_skill_state("last_output", None)
            set_skill_state("auto_open_result", None)
            set_skill_state("direct_download_file", None)
            st.rerun()


# --- ALWAYS RENDER RESULT INLINE IF IT EXISTS ---
last_output = get_skill_state("last_output")
if last_output:
    # We use a container to visually separate the result
    with st.container():
        show_result_popup(last_output)
