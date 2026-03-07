# Walkthrough - Speech-to-Text with kie.ai

I have updated the speech-to-text skill to use the `kie.ai` API instead of the direct ElevenLabs API. This includes a new two-step process: uploading the local file to `kie.ai` temporary storage and then creating a transcription task using that URL.

## Changes Made

### [scripts/audio_transcribe.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/_001-KIE-AI/AI-LLM-KIE-ElevenLabs-Speech2Text/scripts/audio_transcribe.py)
- Replaced `_call_elevenlabs_stt` with `_call_kie_stt`.
- Implemented file upload to `api.kie.ai` with fallback to `redpandaai.co`.
- Fixed 403 Forbidden error by adding the required `uploadPath` parameter.
- Confirmed `.m4a` support for ElevenLabs STT via Kie.ai.
- Fixed `createTask` payload format to strictly use `{"input": {"audio_url": "url"}}`.
- Fixed the extraction of uploaded file URLs using `downloadUrl` instead of `url`.
- Fixed the polling/fetching logic for task results, updating it to parse `state` and handle the stringified `resultJson`.
- Updated CLI arguments to support `kie` as the default provider and use `KIE_API_KEY` environment variable.
- Confirmed `DEV-TEST3-11LABS` secret is active and available in `app.py` for direct ElevenLabs requests.

## Verification

### Dry Run
I verified that the script still correctly validates input files and provider arguments.
```bash
python3 scripts/audio_transcribe.py --input non_existent.mp3 --provider kie
# Output: Error: 'non_existent.mp3' not found.
```

### Manual Verification Instructions
To test with your real API key (retrieved from Google Cloud Secret `DEV-TEST0-KIE`):

1. Set the API key:
   ```bash
   export KIE_API_KEY=$(gcloud secrets versions access latest --secret="DEV-TEST0-KIE")
   ```
2. Run transcription on a local file:
   ```bash
   python3 scripts/audio_transcribe.py --input your_audio_file.mp3
   ```
   *Note: The script now automatically uploads the file and polls for completion.*
