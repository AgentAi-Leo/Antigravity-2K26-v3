# Implementation Plan: Document Navigation Controls

The user wants to navigate between multiple uploaded documents in the dashboard using arrow buttons, similar to how audio clips are navigated.

## Proposed Changes

### Dashboard Application

#### [MODIFY] [app.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/__000-DASHBOARD-TEST1/app.py)

1.  **Enable Navigation for All Files**: Update the condition for showing navigation buttons from `if is_media and len(audio_files) > 1:` to `if len(audio_files) > 1:`.
2.  **Context-Aware Button Labels**: Change the button labels from "⏮ Previous Clip" and "Next Clip ⏭" to more generic "⏮ Previous" and "Next ⏭", or dynamically use "Clip" vs "File" based on `is_media`.
3.  **UI refinements**: Ensure the "Viewing X of Y" text and buttons look consistent for both media and documents.

## Verification Plan

### Manual Verification
1. Upload multiple `.rtf` or `.txt` files to a document skill (e.g., Convtr-PlainTxt2PDF).
2. Confirm that navigation buttons appear.
3. Click "Next" and "Previous" and verify that the "Viewing X of Y" text updates and the displayed content changes.
4. Verify that this doesn't break existing audio navigation.
