# Google Drive & Sheets Integration Fixes

This plan addresses the issue of "invisible" file uploads to Google Drive/Sheets when using Service Account credentials and implements custom naming/logging for ElevenLabs skills.

## User Review Required

> [!IMPORTANT]
> The `DEV-TEST4-GSHEETS` secret has been verified to contain **OAuth Desktop Client** credentials (not a Service Account). 
> - This means files are uploaded to the **primary Drive** of the authenticating user.
> - A `ModuleNotFoundError` in some environments was fixed by installing `google-api-python-client` and `google-auth` into the dashboard's `.venv`.

## Proposed Changes

---

### [Component] Google API Scripts

#### [MODIFY] [upload_to_drive.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS-v3/_000-Basics/Data-GoogleDrive/scripts/upload_to_drive.py)
- Detect if using a Service Account and print the email address to console for the user.
- Add an optional `--share-with` flag to auto-share uploaded files with a specific email.

#### [MODIFY] [generate_sheet.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS-v3/_000-Basics/Data-CustomGoogleSheet/scripts/generate_sheet.py)
- Similar to above: detect and print Service Account email.
- Add `--share-with` flag for auto-sharing created sheets.

#### [MODIFY] [audio_transcribe.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS-v3/_001-KIE-AI/AI-LLM-KIE-ElevenLabs-Speech2Text/scripts/audio_transcribe.py) & [text2speech.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS-v3/_001-KIE-AI/AI-LLM-KIE-ElevenLabs-Text2Speech/scripts/text2speech.py)
- Add `--google-sheet` flag to log results (original filename, transcript/text, Drive URL) to a specified sheet.
- Integrate the `--share-with` logic when calling child scripts.

---

### [Component] Dashboard

#### [MODIFY] [app.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS-v3/__000-DASHBOARD-TEST1/app.py)
- Add "Google Sheet Name (Optional):" input field for ElevenLabs skills.
- Add "User Email (for auto-sharing):" field or detect from environment.
- Pass these new arguments to the backend processing functions.

---

### [Component] Environment & Auth
- [NEW] **google-api-python-client** installation in `__000-DASHBOARD-TEST1/.venv`.
- [VERIFIED] `DEV-TEST4-GSHEETS` secret content: OAuth Desktop Client.

## Verification Plan

### Automated Tests
- Run `python3 upload_to_drive.py` locally and verify console output includes "Service Account Email: ...".
- Verify that if a `--share-with` email is provided, the file appears in that user's "Shared with me" section.

### Manual Verification
1.  Run the **ElevenLabs Speech-to-Text** skill with a Google Drive folder and a Google Sheet name specified.
2.  Confirm that the audio file is uploaded to the Drive folder.
3.  Confirm that a row is added to the specified Google Sheet with the transcript and link.
4.  Confirm visibility in the user's primary Google account.
