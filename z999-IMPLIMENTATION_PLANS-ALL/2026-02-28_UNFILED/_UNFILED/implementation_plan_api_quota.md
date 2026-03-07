# API Quota Error Handling for ElevenLabs

This plan details how we will distinguish between generic errors (like invalid authentication) and rate/quota limits from the ElevenLabs API, and how we will present this information cleanly in the Antigravity Dashboard.

## Proposed Changes

We will modify the core Python scripts for the ElevenLabs skills to explicitly catch `elevenlabs.core.ApiError`. When a `429 Too Many Requests` status is encountered, we will emit a specific trigger string to `stderr`. The dashboard (`app.py`) will intercept this string and display a user-friendly popup alert instead of raw code output.

---

### ElevenLabs Text2Speech Skill
#### [MODIFY] text2speech.py
- **Location**: `_001-ElevenLabs/AI-LLM-Text2Speech/scripts/text2speech.py`
- **Changes**: Ensure `ApiError` is explicitly caught. If `e.status_code == 429`, print `__ANTIGRAVITY_API_QUOTA_EXCEEDED__` to standard error.

### ElevenLabs Speech2Text Skill
#### [MODIFY] audio_transcribe.py
- **Location**: `_001-ElevenLabs/AI-LLM-Speech2Text/scripts/audio_transcribe.py`
- **Changes**: Similarly, add error handling to catch SDK exceptions, check for a `429` status code, and emit the same target trigger string to standard error.

### Antigravity Dashboard
#### [MODIFY] app.py
- **Location**: `__000-DASHBOARD-TEST1/app.py`
- **Changes**: Update the execution failure path (after `subprocess.run`). Before blindly dumping the raw `stderr` into an `st.code` block, check `if "__ANTIGRAVITY_API_QUOTA_EXCEEDED__" in str(result.stderr)`. If found, render a clean alert:
  ```python
  st.warning("⚠️ **API Quota Exceeded:** You have reached the maximum usage allowed by your ElevenLabs active subscription/plan. Please upgrade your plan or wait for the quota to reset.")
  ```

## Verification Plan

### Manual Verification
1. I will temporarily hardcode a `429` error simulation in one of the python scripts.
2. I will execute the skill via the dashboard and verify that the clean yellow warning popup appears instead of the red generic code error.
3. I will then remove the simulation and restore the actual SDK exception check.
