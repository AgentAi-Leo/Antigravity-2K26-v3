import os
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

# -----------------------------------------------------------------------------
# Helper: Get Python Path (prefers virtual environment)
# -----------------------------------------------------------------------------
def get_python_cmd():
    venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "bin", "python3")
    return venv_python if os.path.exists(venv_python) else "python3"

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
    st.markdown(f"<div class='centered-overlay-error' data-salt='{time.time()}'>⚠️ FILE ALREADY EXISTS!</div>", unsafe_allow_html=True)
    sound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio", "universfield-system-error-notice-132470.mp3")
    if os.path.exists(sound_path):
        with open(sound_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)

def trigger_processing_overlay():
    """Shows a centered processing banner with a dots animation."""
    placeholder = st.empty()
    with placeholder:
        st.markdown("""
            <div class='centered-overlay-processing'>
                <div style='line-height: 1.1; margin-bottom: 10px;'>
                    PROCESSING!<br>
                    <span style='font-size: 0.6em; opacity: 0.8; font-weight: normal;'>Please stand by!</span>
                </div>
                <div class='dots-container'>
                    <div class='dot'></div>
                    <div class='dot'></div>
                    <div class='dot'></div>
                </div>
                <div style='font-size: 0.9rem; color: #ffffff; font-weight: normal; margin-top: 10px;'>
                    Depending on file size: Could Take Up to 5 mins.
                </div>
            </div>
        """, unsafe_allow_html=True)
    return placeholder

def trigger_complete_overlay(placeholder):
    """Replaces processing banner with a complete banner that fades out."""
    if placeholder:
        with placeholder:
            st.markdown("<div class='centered-overlay-complete'>COMPLETE!</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Helper: Process Audio/Video Transcription
# -----------------------------------------------------------------------------
def process_audio_files(file_paths, selected_skill, run_env, proc_overlay=None, main_spinner=None):
    """Executes transcription for a list of files and returns the processed data."""
    results = []
    progress_text = st.empty()
    cwd = selected_skill["dir"]
    
    python_cmd = get_python_cmd()
    
    for i, fp in enumerate(file_paths):
        progress_text.info(f"⏳ PROCESSING file {i+1} of {len(file_paths)}: `{os.path.basename(fp)}`...")
        
        current_cmd = [python_cmd, selected_skill["script"], "--input", fp]
        res = subprocess.run(current_cmd, cwd=cwd, capture_output=True, text=True, env=run_env)
        
        transcript = ""
        if res.returncode == 0:
            ignore_prefixes = ("Transcribing:", "Saved:", "Usage:")
            lines = [l for l in res.stdout.strip().splitlines() if not l.startswith(ignore_prefixes)]
            transcript = "\n".join(lines).strip()
            
            # Extract usage — audio_transcribe.py writes Usage: to stderr; text2speech.py uses stdout
            usage_line = (
                next((l for l in res.stderr.splitlines() if l.startswith("Usage:")), None)
                or next((l for l in res.stdout.splitlines() if l.startswith("Usage:")), None)
            )
            if usage_line:
                transcript += f"\n\n**Statistics:** {usage_line.split(':', 1)[-1].strip()}"
            
            results.append({
                "name": os.path.basename(fp),
                "bytes": open(fp, "rb").read() if os.path.exists(fp) else b"",
                "transcript": transcript,
            })
        else:
            if "__ANTIGRAVITY_API_QUOTA_EXCEEDED__" in res.stderr:
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
                    match = re.search(r"Kie\.ai (?:Upload |Polling )?Error \[(.*?)\]: (.*)(?:\n|$)", res.stderr)
                    if match:
                        err_code = match.group(1)
                        err_msg = match.group(2).strip()
                        quota_msg = f"\n\n**Details [{err_code}]:** {err_msg}"
                    else:
                        # Fallback for old/unparsed format
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
            continue
    
    progress_text.empty()
    return results

def process_tts_files(file_paths, selected_skill, run_env, proc_overlay=None, main_spinner=None):
    """Executes Text2Speech for a list of document files and returns the processed audio data."""
    results = []
    progress_text = st.empty()
    cwd = selected_skill["dir"]
    
    python_cmd = get_python_cmd()
    
    for i, fp in enumerate(file_paths):
        original_name = os.path.basename(fp)
        progress_text.info(f"⏳ PROCESSING document {i+1} of {len(file_paths)}: `{original_name}`...")
        
        current_cmd = [python_cmd, selected_skill["script"], "--input", fp]
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

                    results.append({
                        "name": os.path.basename(full_saved_path),
                        "bytes": audio_bytes,
                        "transcript": content_preview,
                        "content_preview": content_preview
                    })
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
    return results


st.set_page_config(page_title="Antigravity Skills", page_icon="🚀", layout="wide")
load_css() # Global CSS load to ensure banners work on main page

# -----------------------------------------------------------------------------
# Helper: Generate PDF via Convtr-PlainTxt2PDF Skill
# -----------------------------------------------------------------------------
def generate_pdf_from_text(text: str) -> bytes:
    """Uses the PlainTxt2PDF skill to convert text to PDF bytes."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
def generate_zip_of_all_transcripts(audio_files_list, format_option):
    import io
    import zipfile
    import os
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for i, f in enumerate(audio_files_list):
            fname = os.path.splitext(f["name"])[0]
            
            if format_option.startswith("MP3") or format_option == "MP3 Audio (.mp3)":
                zip_file.writestr(f"{fname}.mp3", f["bytes"])
                continue

            # Otherwise, it's a document format
            download_text = f["transcript"]
            # Inject metadata logic inside ZIP files too
            download_text += f"\n\n---\nSource File: {f['name']}"
            
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
    st.title("🔒 Antigravity Dashboard")
    # Description removed per user request
    
    
    with st.form("login_form", clear_on_submit=False, border=False):
        st.markdown('<div class="password-container">', unsafe_allow_html=True)
        password = st.text_input("Password", type="password", placeholder="Enter Password", label_visibility="collapsed")
        
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

st.sidebar.title("🚀 Antigravity Skills")
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

st.title(selected_skill["name"])
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
    st.subheader("Upload Audio Files")
    uploader_label = "Upload Audio Files"
    accepted_types = [
        "mp3", "wav", "m4a", "aac", "ogg", "flac", "webm",
        "aiff", "aif", "wma", "oga", "opus", "3gp",
        "mp4", "mov", "avi", "mkv"
    ]
elif is_tts_skill:
    st.subheader("Upload Text Files for Narration")
    uploader_label = "Upload Text Files"
    st.caption("ElevenLabs cleanly auto-extracts text from Plain Text, Markdown, PDF, RTF, DOC, and DOCX files for narration.")
    accepted_types = [
        "txt", "md", "pdf", "rtf", "doc", "docx", "csv", "json", "py", "sh", "yaml", "yml", "ini"
    ]
else:
    st.subheader("Upload Document Files")
    uploader_label = "Upload Document Files"
    accepted_types = [
        "txt", "md", "pdf", "docx", "doc", "csv", "json", "rtf", "py", "sh", "yaml", "yml"
    ]

# --- Duplicate Checking Logic ---
def check_new_uploads_for_duplicates(file_list):
    """Uses differential counting of all uploads to prevent fake triggers on rerun."""
    import collections
    if not file_list:
        set_skill_state("prev_file_counts_dict", collections.Counter())
        return
        
    processed = get_skill_state("processed_files", set())
    
    # Count ALL files currently in the widget
    current_files = [f.name + str(f.size) for f in file_list]
    curr_counts = dict(collections.Counter(current_files))
    
    # If this is the VERY FIRST time we see files in this skill session, 
    # prime the state so we don't trigger on a cold start.
    ns_key = f"{st.session_state.selected_skill_id}_prev_file_counts_dict"
    if ns_key not in st.session_state:
        set_skill_state("prev_file_counts_dict", curr_counts)
        return
        
    prev_counts_raw = get_skill_state("prev_file_counts_dict", {})
    prev_counts: dict[str, int] = dict(prev_counts_raw) if isinstance(prev_counts_raw, dict) else {}  # type: ignore[arg-type]
    
    # If any file count increased AND that file is already processed, it's a new duplicate drop!
    error_triggered = False
    for item, count in curr_counts.items():
        if count > prev_counts.get(item, 0):  # type: ignore[union-attr]
            if item in list(processed):
                error_triggered = True
                break
            
    if error_triggered:
        trigger_duplicate_error()
        
    # Update the tracking state with ALL current files
    set_skill_state("prev_file_counts_dict", curr_counts)

# File uploader OUTSIDE the form so uploads trigger immediately

uploaded_files = st.file_uploader(
    uploader_label,
    accept_multiple_files=True,
    label_visibility="collapsed",
    type=accepted_types
)

if uploaded_files:
    # Disable duplicate file tracking when navigating clips inside dialogs
    if not get_skill_state("auto_open_result", False):
        check_new_uploads_for_duplicates(uploaded_files)
        
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

# --- URL Input for Specific Skills ---
url_input = ""
html_capture = False
if url_input:
    st.info(f"Targeting URL: `{url_input}`")

# --- Specialized Skill Inputs ---
skill_args = {}
if selected_skill_id == "AI-LLM-ImageGenerate":
    skill_args["prompt"] = st.text_area("Image Prompt:", placeholder="A futuristic city with neon lights...", height=100)
    col1, col2 = st.columns(2)
    with col1:
        skill_args["count"] = st.number_input("Number of Images:", min_value=1, max_value=4, value=1)
    with col2:
        skill_args["provider"] = st.selectbox("Provider:", ["gemini", "openai"])
elif selected_skill_id == "AI-LLM-EmbedText":
    mode = st.radio("Mode:", ["Single Text", "Compare Two Texts"], horizontal=True)
    if mode == "Single Text":
        skill_args["text"] = st.text_area("Text to Embed:", height=150)
    else:
        skill_args["compare"] = [
            st.text_input("Text A:"),
            st.text_input("Text B:")
        ]
elif selected_skill_id == "AI-LLM-RAGQuery":
    skill_args["query"] = st.text_input("Your Question:", placeholder="What does this document say about...?")
    skill_args["index"] = st.checkbox("Re-index Documents", value=True)
elif selected_skill_id == "AI-LLM-TranslateText":
    skill_args["to"] = st.text_input("Target Language:", value="Spanish")
    # If no file, show text area
    if not uploaded_files:
        skill_args["text"] = st.text_area("Text to Translate:", height=150)

# --- Manual Text Input Fallback ---
manual_text = ""
if not uploaded_files and not url_input and not any(skill_args.values()):
    if selected_skill["basename"] not in [
        "AI-LLM-ImageGenerate", 
        "AI-LLM-EmbedText", 
        "AI-LLM-RAGQuery", 
        "AI-LLM-TranslateText",
        "AI-LLM-Speech2Text",
        "AI-LLM-KIE-ElevenLabs-Speech2Text"
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
if selected_skill_id == "AI-LLM-ImageGenerate" and skill_args.get("prompt"):
    has_special_input = True
elif selected_skill_id == "AI-LLM-EmbedText" and (skill_args.get("text") or (skill_args.get("compare") and all(skill_args["compare"]))):
    has_special_input = True
elif selected_skill_id == "AI-LLM-RAGQuery" and skill_args.get("query"):
    has_special_input = True
elif selected_skill_id == "AI-LLM-TranslateText" and (skill_args.get("to") and (uploaded_files or skill_args.get("text"))):
    has_special_input = True

should_run = auto_run or (url_input != "") or has_special_input or (manual_text != "" and enter_clicked) or (not is_tts_skill and manual_text != "")

if should_run:
    args_input = ""
    
    # Construct args from specialized inputs
    if selected_skill_id == "AI-LLM-ImageGenerate":
        args_input = f"--prompt {shlex.quote(str(skill_args['prompt']))} --count {skill_args['count']} --provider {str(skill_args['provider'])}"
    elif selected_skill_id == "AI-LLM-EmbedText":
        if skill_args.get("text"):
            args_input = f"--text {shlex.quote(str(skill_args['text']))}"
        elif skill_args.get("compare"):
            args_input = f"--compare {shlex.quote(str(skill_args['compare'][0]))} {shlex.quote(str(skill_args['compare'][1]))}"
    elif selected_skill_id == "AI-LLM-RAGQuery":
        args_input = f"--query {shlex.quote(str(skill_args['query']))}"
        if skill_args.get("index"):
            args_input += " --index"
        if uploaded_files:
            # We'll handle files below
            pass
    elif selected_skill_id == "AI-LLM-TranslateText":
        args_input = f"--to {shlex.quote(str(skill_args['to']))}"
        if skill_args.get("text"):
            # We'll save this to a temp file below
            pass
    
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
                
                for i, uf in enumerate(files_to_process_objs):
                    file_path = os.path.join(temp_dir, uf.name)
                    with open(file_path, "wb") as f:
                        f.write(uf.getbuffer())
                    file_paths.append(file_path)
                    
                    processed.add(uf.name + str(uf.size))
                    set_skill_state("processed_files", processed)
                    
                    # Replace {FILE_X} placeholder in the args
                    args_input = args_input.replace(f"{{FILE_{i+1}}}", file_path)
    
    # Parse the arguments string into a list safely avoiding simple split() issues with quotes
    import shlex
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
                new_files = process_audio_files(file_paths, selected_skill, run_env, proc_overlay=proc_overlay, main_spinner=main_spinner)
                existing = get_skill_state("last_audio_files", [])
                existing.extend(new_files)
                set_skill_state("last_audio_files", existing)
                if new_files:
                    set_skill_state("audio_index", max(0, len(existing) - len(new_files)))
                    set_skill_state("last_output", new_files[0]["transcript"])
                    set_skill_state("auto_open_result", True)
                    st.success(f"✅ Successfully processed {len(file_paths)} file(s)")
            elif is_tts_skill and file_paths:
                new_files = process_tts_files(file_paths, selected_skill, run_env, proc_overlay=proc_overlay, main_spinner=main_spinner)
                existing = get_skill_state("last_audio_files", [])
                existing.extend(new_files)
                set_skill_state("last_audio_files", existing)
                if new_files:
                    set_skill_state("audio_index", max(0, len(existing) - len(new_files)))
                    set_skill_state("last_output", new_files[0]["transcript"])
                    set_skill_state("auto_open_result", True)
                    st.success(f"✅ Successfully converted {len(file_paths)} document(s) to audio")
            else:
                # Standard single execution (for documents, generation, etc.)
                result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, env=run_env)
                
                if result.returncode == 0:
                    st.success("Execution Completed Successfully")
                    output_text = result.stdout.strip()
                    
                    # Detect ALL saved files (e.g., from ImageGenerate or Md2PDF)
                    saved_paths = []
                    for line in output_text.splitlines():
                        if "Saved:" in line:
                            path_str: str = str(line.split("Saved:")[1].strip())
                            # If saved_path is relative, join it with cwd
                            full_path: str = path_str if os.path.isabs(path_str) else os.path.join(str(cwd), path_str)
                            if os.path.exists(full_path):
                                saved_paths.append(full_path)
                    
                    if saved_paths:
                        # For the direct download button, we'll use the first one as primary
                        # but we'll integrate all into last_audio_files below
                        with open(saved_paths[0], "rb") as f:
                            set_skill_state("direct_download_file", {
                                "name": os.path.basename(saved_paths[0]),
                                "bytes": f.read()
                            })
                        
                        # Integrate into the "Gallery/Playlist" view
                        gallery_files = []
                        for sp in saved_paths:
                            with open(sp, "rb") as f:
                                gallery_files.append({
                                    "name": os.path.basename(sp),
                                    "bytes": f.read(),
                                    "transcript": f"✅ Generated: {os.path.basename(sp)}"
                                })
                        existing = get_skill_state("last_audio_files", [])
                        existing.extend(gallery_files)
                        set_skill_state("last_audio_files", existing)
                        if gallery_files:
                            set_skill_state("audio_index", max(0, len(existing) - len(gallery_files)))
                    else:
                        set_skill_state("direct_download_file", None)
    
                    # Filter logs: exclude diagnostic messages from the preview
                    ignore_prefixes = ("Transcribing:", "Saved:", "Fetching:", "Capturing:", "Capturing high-fidelity", "Usage:")
                    lines = [l for l in output_text.splitlines() if not l.startswith(ignore_prefixes)]
                    clean_output = "\n".join(lines).strip()
                    
                    # Extract usage stats (suppress for manual TTS input per user request)
                    usage_line = next((l for l in output_text.splitlines() if l.startswith("Usage:")), None)
                    usage_details = ""
                    if usage_line:
                        is_manual_tts = is_tts_skill and not uploaded_files and manual_text != ""
                        if not is_manual_tts:
                            usage_details = f"\n\n**Statistics:** {usage_line.split(':', 1)[-1].strip()}"
    
                    # Ensure the popup opens if a file was saved, even if no text output
                    if clean_output or saved_paths:
                        display_msg = clean_output or f"✅ Successfully generated: {os.path.basename(saved_paths[0]) if saved_paths else 'Result'}"
                        if usage_details:
                            display_msg += usage_details
                        set_skill_state("last_output", display_msg)
                        set_skill_state("auto_open_result", True)
                        
                    # Store uploaded files (only first one gets the 'clean_output' transcript in manual mode)
                    if file_paths:
                        last_audio_files = []
                        for i, fp in enumerate(file_paths):
                            with open(fp, "rb") as af:
                                # For text/rtf files, we might want to store the actual text content too
                                content_preview = ""
                                ext = os.path.splitext(fp)[1].lower()
                                if ext in [".txt", ".rtf", ".md"]:
                                    content_preview = read_text_file_preview(fp)
    
                                last_audio_files.append({
                                    "name": os.path.basename(fp),
                                    "bytes": af.read(),
                                    "transcript": clean_output if i == 0 else "",
                                    "content_preview": content_preview
                                })
                        existing = get_skill_state("last_audio_files", [])
                        existing.extend(last_audio_files)
                        set_skill_state("last_audio_files", existing)
                        if last_audio_files:
                            set_skill_state("audio_index", max(0, len(existing) - len(last_audio_files)))
                        st.success(f"✅ Successfully processed {len(file_paths)} file(s)")
                else:
                    if "__ANTIGRAVITY_API_QUOTA_EXCEEDED__" in result.stderr:
                        main_spinner.empty()
                        if proc_overlay:
                            proc_overlay.empty()
                        import re
                        quota_msg = ""
                        
                        if "kie" in str(selected_skill["basename"]).lower():
                            # Extract the custom Kie.ai msg we injected in the skills
                            match = re.search(r"Kie\.ai Error: (.*?)(?:\n|$)", result.stderr)
                            if match:
                                quota_msg = f"\n\n**Details:** {match.group(1).strip()}"
                            st.warning(f"⚠️ **DENIED!** You have reached the maximum usage allowed by your **Kie.ai** balance. Please top up your Kie.ai account to continue.{quota_msg}")
                        else:
                            # Extract ElevenLabs data
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
    
    audio_files = get_skill_state("last_audio_files", [])
    idx = get_skill_state("audio_index", 0)
    is_media = False
    is_image = False
    
    # Determine which text to display (specific clip transcript or the general output)
    display_text = text
    if audio_files:
        current_idx = get_skill_state("audio_index", 0)
        if current_idx < len(audio_files):
            current_file = audio_files[current_idx]
            display_text = current_file.get("transcript") or text
            
            # If transcript is just a success message and we have original content, show it
            if ("Successfully generated" in display_text or not display_text.strip()) and current_file.get("content_preview"):
                display_text = current_file["content_preview"]
            
    if audio_files:
        current_file = audio_files[idx]
        import mimetypes
        mime_type, _ = mimetypes.guess_type(current_file["name"])
        
        # Only show the audio player if it's actually an audio/video file
        is_media = mime_type and (mime_type.startswith("audio/") or mime_type.startswith("video/"))
        is_image = mime_type and mime_type.startswith("image/")
        
        if is_media:
            st.markdown(f"**Playing {idx + 1} of {len(audio_files)}**: `{current_file['name']}`")
            st.audio(current_file["bytes"], format=mime_type, autoplay=True, loop=True)
            # stats_badge_text extracted below — pass it here so it appears inline with speed controls
            _stats_for_speed = ""
            import re as _re_pre
            _stats_match = _re_pre.search(r"\*\*Statistics:\*\*\s*(.+)", display_text)
            if _stats_match:
                _stats_for_speed = _stats_match.group(1).strip()
            render_speed_controls(skill_id=selected_skill_id, stats_text=_stats_for_speed)

        elif is_image:
            st.markdown(f"**Viewing Image {idx + 1} of {len(audio_files)}**: `{current_file['name']}`")
            st.image(current_file["bytes"], use_container_width=True)
        else:
            st.markdown(f"**Viewing {idx + 1} of {len(audio_files)}**: `{current_file['name']}`")
            # For documents, if we have a content preview, it will be shown in the transcript box below
        
        # Show navigation buttons if there are multiple files
        if len(audio_files) > 1:
            label_type = "Clip" if is_media else "File"
            col_prev, col_next = st.columns(2)
            with col_prev:
                st.markdown("<div class='nav-btn-marker' style='display:none;'></div>", unsafe_allow_html=True)
                if st.button(f"⏮ Previous {label_type}", key="prev_clip_btn", use_container_width=True):
                    set_skill_state("audio_index", (idx - 1) % len(audio_files))
                    set_skill_state("auto_open_result", True)
                    st.rerun()
            with col_next:
                st.markdown("<div class='nav-btn-marker' style='display:none;'></div>", unsafe_allow_html=True)
                if st.button(f"Next {label_type} ⏭", key="next_clip_btn", use_container_width=True):
                    set_skill_state("audio_index", (idx + 1) % len(audio_files))
                    set_skill_state("auto_open_result", True)
                    st.rerun()
            
    # Render the transcription box BELOW the navigation buttons
    import html
    import re as _re

    # Extract and strip the Statistics line from display_text so it shows ONLY in the badge
    stats_badge_text = ""
    stats_match = _re.search(r"\*\*Statistics:\*\*\s*(.+)", display_text)
    if stats_match:
        stats_badge_text = stats_match.group(1).strip()
        display_text = _re.sub(r"\n\n\*\*Statistics:\*\*\s*.+", "", display_text).strip()
    
    if is_media or is_image:
        if display_text:
            safe_text = html.escape(display_text)
            st.markdown(
                f"<div class='transcript-box'>{safe_text.replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True
            )
    else:
        # Use st.code with no language for reliable, scrollable exact-text formatting
        st.code(display_text, language="text")
    
    # --- Direct Download Support (Moved under preview, above copy) ---
    direct_file = get_skill_state("direct_download_file")
    if direct_file:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Check if it's an audio file and play it natively
        import mimetypes
        dl_mime_type, _ = mimetypes.guess_type(direct_file["name"])
        if dl_mime_type and dl_mime_type.startswith("audio/"):
            st.audio(direct_file["bytes"], format=dl_mime_type, autoplay=True)
            render_speed_controls(skill_id=selected_skill_id)
            st.markdown("<br>", unsafe_allow_html=True)
            
        col1, col2, col3 = st.columns([2, 3, 2])
        with col2:
            st.download_button(
                label=f"📥 DOWNLOAD {os.path.splitext(direct_file['name'])[1][1:].upper()} NOW",
                data=direct_file["bytes"],
                file_name=direct_file["name"],
                mime=dl_mime_type if dl_mime_type else "application/octet-stream",
                use_container_width=True,
                type="primary",
                key="direct_download_btn_bottom"
            )
        
    # Solid Yellow "COPY" button centered — now ABOVE the stats badge
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
                btn.innerText = "✓ COPIED!";
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



    # --- Audio-Specific Download & Playlist Options ---
    # Hide all of these bottom elements if this is a document result
    if not is_media:
        st.markdown("")
        col1, col2 = st.columns([5, 1])
        with col2:
            if st.button("✖ Clear Result", key="close_popup", use_container_width=True):
                set_skill_state("last_output", None)
                set_skill_state("auto_open_result", None)
                set_skill_state("direct_download_file", None)
                st.rerun()
        return

    # --- Quick Select List & Upload (Playlist) ---
    if audio_files:
        current_file = audio_files[idx]
        import mimetypes
        mime_type, _ = mimetypes.guess_type(current_file["name"])
        is_media = mime_type and (mime_type.startswith("audio/") or mime_type.startswith("video/"))
        
        if is_media:
            st.markdown("<h3 class='centered-header'>MY CLIPS</h3>", unsafe_allow_html=True)
        
        if get_skill_state("popup_batch_success"):
            st.markdown("<div class='success-message-popup'>✅ SUCCESSFULLY ADDED!</div>", unsafe_allow_html=True)
            set_skill_state("popup_batch_success", False)
        
        st.markdown("<div class='quick-select-btns'>", unsafe_allow_html=True)
        for i, clip in enumerate(audio_files):
            is_active = (i == get_skill_state("audio_index", 0))
            if is_active:
                st.markdown(f"<div class='active-clip'>🟢 {clip['name']}</div>", unsafe_allow_html=True)
            else:
                with st.container():
                    st.markdown("<div class='playlist-clip-marker'></div>", unsafe_allow_html=True)
                    if st.button(f"⚪️ {clip['name']}", key=f"clip_btn_{i}", use_container_width=True):
                        set_skill_state("audio_index", i)
                        set_skill_state("auto_open_result", True)
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")

    # --- Download Selection & Actions (MOVED BELOW LIST) ---
    st.markdown("---")
    fname = "transcript"
    original_fullname = "Unknown Source"
    if audio_files:
        original_fullname = audio_files[idx]["name"]
        fname = os.path.splitext(original_fullname)[0]

    download_text = display_text + f"\n\n---\nSource File: {original_fullname}"

    with st.container():
        options = ["TXT (.txt)", "PDF (.pdf)", "DOCX (.docx)", "DOC (.doc)"]
        if is_tts_skill:
            options = ["MP3 Audio (.mp3)"] + options
            
        selected_format = st.selectbox(
            "Download Format:",
            options=options,
            index=0,
            key="dl_format_selection"
        )
        
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            if selected_format.startswith("MP3"):
                st.download_button(
                    label="📥 Download Current",
                    data=current_file["bytes"],
                    file_name=current_file["name"],
                    mime="audio/mpeg",
                    use_container_width=True,
                    type="primary"
                )
            elif selected_format.startswith("TXT"):
                st.download_button(
                    label="📥 Download Current",
                    data=download_text,
                    file_name=f"{fname}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    type="primary"
                )
            elif selected_format.startswith("PDF"):
                with st.spinner("Generating PDF..."):
                    pdf_bytes = generate_pdf_from_text(download_text)
                if pdf_bytes:
                    st.download_button(label="📥 Download Current", data=pdf_bytes, file_name=f"{fname}.pdf", mime="application/pdf", use_container_width=True, type="primary")
            elif selected_format.startswith("DOCX"):
                with st.spinner("Generating DOCX..."):
                    docx_bytes = generate_docx_from_text(download_text)
                if docx_bytes:
                    st.download_button(label="📥 Download Current", data=docx_bytes, file_name=f"{fname}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True, type="primary")
            elif selected_format.startswith("DOC"):
                with st.spinner("Generating DOC..."):
                    doc_bytes = generate_doc_rtf_from_text(download_text)
                st.download_button(label="📥 Download Current", data=doc_bytes, file_name=f"{fname}.doc", mime="application/msword", use_container_width=True, type="primary")
                
        with col_dl2:
            if audio_files and len(audio_files) > 0:
                with st.spinner(f"Preparing ZIP for {len(audio_files)} files..."):
                    zip_bytes = generate_zip_of_all_transcripts(audio_files, selected_format)
                st.download_button(label=f"📦 Download All ({len(audio_files)} files)", data=zip_bytes, file_name="All_Transcriptions.zip", mime="application/zip", use_container_width=True, type="tertiary")
            else:
                st.button("📦 Download All (ZIP)", disabled=True, use_container_width=True, type="tertiary")
        
        st.markdown("---")
        

            
    st.markdown("")
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("✖ Clear Result", key="close_popup", use_container_width=True):
            set_skill_state("last_output", None)
            set_skill_state("auto_open_result", None)
            set_skill_state("direct_download_file", None)
            st.rerun()

# --- ALWAYS RENDER RESULT INLINE IF IT EXISTS ---
last_output = get_skill_state("last_output")
if last_output:
    st.markdown("---")
    st.markdown("<h2 style='text-align: center; color: #eb4c1f;'>📄 PROCESSED RESULT</h2>", unsafe_allow_html=True)
    
    # We use a container to visually separate the result
    with st.container():
        show_result_popup(last_output)
