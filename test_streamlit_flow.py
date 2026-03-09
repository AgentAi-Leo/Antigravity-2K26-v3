import os
import sys

# Add directory to path so we can import app.py
sys.path.append("/Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS-v3/__000-DASHBOARD-TEST1")

import app  # type: ignore[import-not-found]

# Mock streamlit state
class MockSessionState(dict):
    def __getattr__(self, key):
        return self.get(key)
    def __setattr__(self, key, value):
        self[key] = value

app.st.session_state = MockSessionState()
app.st.session_state["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "")
app.st.session_state["ELEVENLABS_API_KEY"] = os.environ.get("ELEVENLABS_API_KEY", "dummy_key")
app.st.session_state["KIE_API_KEY"] = os.environ.get("KIE_API_KEY", "")

# Hardcode skill to avoid Streamlit state dependency
skill = {
    "script": "/Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS-v3/_001-ElevenLabs/AI-LLM-Speech2Text/scripts/audio_transcribe.py",
    "dir": "/Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS-v3/_001-ElevenLabs/AI-LLM-Speech2Text",
    "basename": "AI-LLM-Speech2Text",
    "group": "AI - ElevenLabs"
}


# Get a test file
test_file = "/Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS-v3/_001-ElevenLabs/AI-LLM-Speech2Text/test.mp3"

# Create dummy overlay and spinner
class MockOverlay:
    def empty(self): pass
class DummyEmpty:
    def info(self, msg): print("INFO:", msg)
    def error(self, msg): print("ERROR:", msg)
    def success(self, msg): print("SUCCESS:", msg)
    def empty(self): pass
app.st.empty = lambda: DummyEmpty()

def mock_st_error(msg): print(f"ST_ERROR: {msg}")
def mock_st_code(msg): print(f"ST_CODE:\n{msg}")
app.st.error = mock_st_error
app.st.code = mock_st_code

# We also want to intercept the stdout if possible, but app.py only prints stderr.
# Let's import subprocess and mock it to print inside test_streamlit_flow
import subprocess
original_run = subprocess.run
def run_and_print(*args, **kwargs):
    res = original_run(*args, **kwargs)  # type: ignore[misc]
    print(f"\n--- SUBPROCESS RUN ---")
    print(f"Args: {args[0] if args else kwargs.get('args')}")
    print(f"ReturnCode: {res.returncode}")
    print(f"STDOUT:\n{res.stdout}")
    print(f"STDERR:\n{res.stderr}")
    print(f"----------------------\n")
    return res
subprocess.run = run_and_print  # type: ignore[assignment]

# Run env
run_env = os.environ.copy()

print("Executing process_uploaded_files...")
try:
    results = app.process_uploaded_files(
        [test_file],
        skill,
        run_env,
        drive_folder="JB3/Tests/Test-001",
        google_sheet="jbtest-001",
        share_with="aileo2K26@gmail.com",
        proc_overlay=MockOverlay(),
        main_spinner=DummyEmpty()
    )

    print("\n--- RESULTS ---")
    if results:
        for r in results:
            print(f"\nFILE: {r['name']}")
            print(f"TRANSCRIPT/LOGS:\n{r['transcript']}")
    else:
        print("No files returned.")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
