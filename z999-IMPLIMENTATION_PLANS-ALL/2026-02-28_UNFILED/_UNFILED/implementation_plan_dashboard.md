# Plan: Refine Dashboard for Document Visibility

The current `__000-DASHBOARD-TEST1` application is optimized for audio transcription. We need to generalize it to support document conversion skills (`Convtr-Md2PDF`, `Convtr-PlainTxt2PDF`) which produce PDF files and may not have "transcripts" in the traditional sense.

## Proposed Changes

### Dashboard Application

#### [MODIFY] [app.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/__000-DASHBOARD-TEST1/app.py)
- **Fix Popup Trigger**: Ensure the result popup opens if a file was saved (`Saved: ...`), even if the stdout (`clean_output`) is empty.
- **Support Document Previews**:
    - Update `show_result_popup` to check the mime type of the current file.
    - If the file is not audio/video, hide the audio player.
    - If the file is a text-based document (TXT, RTF), read and display its content in the `transcript-box` if no other transcript is available.
- **Prominent Download Button**: 
    - Move the "Download Original" (High-Fidelity Result) button to a more prominent position in the popup.
    - Ensure it is named appropriately for the skill (e.g., "Download PDF").

## Verification Plan

### Automated Tests
- None (UI-based dashboard).

### Manual Verification
1. Upload an `.rtf` file (e.g., `Consistency_SAMSON.rtf`).
2. Select the `Convtr-PlainTxt2PDF` skill and execute.
3. Verify that a popup opens automatically after completion.
4. Verify that the popup shows a preview of the text or a success message.
5. Verify that the "Download PDF" button is visible and works.
