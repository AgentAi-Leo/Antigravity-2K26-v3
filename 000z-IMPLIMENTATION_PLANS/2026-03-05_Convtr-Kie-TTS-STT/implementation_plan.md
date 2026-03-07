# Implementation Plan - Text2Speech via Kie.ai

The user wants to create a new skill `AI-LLM-KIE-ElevenLabs-Text2Speech` that acts as the inverse of the Speech-to-Text skill, utilizing the same code structure but wrapping the Kie.ai Text-to-Speech API.

## Proposed Changes

### 1. Create New Skill Structure
I will create the necessary directory structure for the new skill inside `_001-KIE-AI/`:
- `_001-KIE-AI/AI-LLM-KIE-ElevenLabs-Text2Speech/SKILL.md`: Documentation for the new skill.
- `_001-KIE-AI/AI-LLM-KIE-ElevenLabs-Text2Speech/scripts/text2speech.py`: The core script that processes inputs and calls the Kie.ai API.

### 2. Implement `scripts/text2speech.py`
The script will accept arguments `--input`, `--text`, `--output`, and `--voice_id` (default: "Rachel"). 
It will:
- Read input text (handling documents/PDFs similar to the ElevenLabs version).
- Send a request to `https://api.kie.ai/api/v1/jobs/createTask` with model `elevenlabs/text-to-speech-turbo-2-5`.
- Poll `https://api.kie.ai/api/v1/jobs/recordInfo` for task completion.
- Emit `__ANTIGRAVITY_API_QUOTA_EXCEEDED__` if a 402/403 or quota error is encountered, taking advantage of the robust error mechanism added to the dashboard.
- Download the generated audio via the `resultUrls` array from the callback payload.

### 3. Update Dashboard (`app.py`)
I will modify `app.py` to route the new skill correctly:
#### [MODIFY] `__000-DASHBOARD-TEST1/app.py`
- Update `is_tts_skill` to include `"AI-LLM-KIE-ElevenLabs-Text2Speech"`:
  ```python
  is_tts_skill = selected_skill["basename"] in ["AI-LLM-Text2Speech", "AI-LLM-KIE-ElevenLabs-Text2Speech"]
  ```

## Verification Plan
1. After executing the plan, I will trigger a test generation with dummy text via the CLI script bypassing the UI.
2. The user will be requested to review and verify via the Streamlit dashboard by reloading it and selecting the new skill.
