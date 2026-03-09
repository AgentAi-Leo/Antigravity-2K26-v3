import subprocess
import os
import sys

# setup exactly like app.py
python_cmd = "/Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS-v3/__000-DASHBOARD-TEST1/.venv/bin/python"
script = "scripts/audio_transcribe.py"
fp = "/Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS-v3/__000-DASHBOARD-TEST1/JB2GIGI_ElevenLabs_2024-05-18T01_02_22_Gigi.mp3"
cwd = "/Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS-v3/_001-ElevenLabs/AI-LLM-Speech2Text"

current_cmd = [python_cmd, script, "--input", fp, "--drive-folder", "JB3/Tests/Test-001", "--google-sheet", "jbtest-001", "--share-with", "aileo2K26@gmail.com"]

run_env = os.environ.copy()
# NOTE: Need to ensure API key is present!
if "ELEVENLABS_API_KEY" not in run_env:
    print("WARNING: ELEVENLABS_API_KEY NOT SET in test_exec!")

res = subprocess.run(current_cmd, cwd=cwd, capture_output=True, text=True, env=run_env)

print("----- STDOUT -----")
print(res.stdout)
print("----- STDERR -----")
print(res.stderr)
print(f"Return code: {res.returncode}")
